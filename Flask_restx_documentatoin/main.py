from flask import Flask, request,jsonify
from pymongo import MongoClient
import datetime
import jwt
import bcrypt
from bson import ObjectId, Binary
from flask_restx import Api, Resource, fields,reqparse
from flask_uploads import UploadSet, configure_uploads, IMAGES
from werkzeug.datastructures import FileStorage

connection_string = 'mongodb+srv://sikandarnust1140:ZBXI5No3tsTeKb0u@cluster0.mo69b0z.mongodb.net/newDB?retryWrites=true&w=majority'
client = MongoClient(connection_string)
app = Flask(__name__)
app.config['SECRET_KEY'] = "your_secret_key_here"
#configuring the flask uploads
api = Api(app, version='1.0', title='User API', description='A simple User API')

auth_ns = api.namespace('Swagger Documentation', description='Swagger Documentation')
# Configure Flask-Uploads
photos = UploadSet('photos', IMAGES)
app.config['UPLOADED_PHOTOS_DEST'] = 'uploads/photos'
configure_uploads(app, photos)


upload_parser = reqparse.RequestParser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True)
upload_parser.add_argument('title', type=str, required=True)
upload_parser.add_argument('text', type=str, required=True)
upload_parser.add_argument('tags', type=str, required=True)
upload_parser.add_argument('x-access-token', type=str, required=True)

database = client['Authentication']
database2 = client['userCollection']

# collections
collection = database2['user']
posts_collection= database['posts_collection']



# Define a model for the headers

register_model = auth_ns.model('Register', {
    'username': fields.String(required=True, description='The user username'),
    'password': fields.String(required=True, description='The user password'),
    'name': fields.String(required=True, description='The user name'),
    'email': fields.String(required=True, description='The user email'),
    'phone_no': fields.String(required=True, description='The user phone number'),
})
login_model = auth_ns.model('Login', {
    'username': fields.String(required=True, description='The user username'),
    'password': fields.String(required=True, description='The user password')
})
get_post_comment_request_model = api.model('Get Comment Request', {
    'x-access-token': fields.String(required=True, description="x-access-token"),
    'id': fields.String(required=True, description='The post ID'),
})
add_post_comment_request_model = api.model('Add Comments Request', {
     'x-access-token': fields.String(required=True, description="x-access-token"),
    'id': fields.String(required=True, description='The post ID'),
    'comment': fields.String(required=True, description='The comment to add'),
})
delete_post_comment_request_model = api.model('Delete Comment Request', {
    'x-access-token': fields.String(required=True, description="x-access-token"),
    "id": fields.String(required=True, description="Post ID"),
    "comment": fields.String(required=True, description="Delete post comment")
})
delete_post_request_model = api.model('Post Request', {
    'x-access-token': fields.String(required=True, description="x-access-token"),
     "id": fields.String(required=True, description="Post ID")
})
update_post_request_model1 = api.model('Post Request', {
    'x-access-token': fields.String(required=True, description="x-access-token"),
    'id': fields.String(required=True, description='The post ID'),
    'title': fields.String(required=False, description='The post title'),
    'text': fields.String(required=False, description='The post text'),
    'tags': fields.String(required=False, description='The post tags'),
    'thumbnail': fields.String(required=False, description='The post thumbnail'),
    'comments': fields.String(required=False, description='The post comments'),
})
Update_post_comment_request_model = api.model('Update Comments Request', {
    'x-access-token': fields.String(required=True, description="x-access-token"),
    'id': fields.String(required=True, description='The post ID'),
    'author_id': fields.String(required=True, description='Author ID'),
    'new_comment': fields.String(required=True, description='New comment text'),
    'pre_comment': fields.String(required=True, description='Previous comment text'),
})
likeDislike_post_request_model = api.model('Post Request', {
    'id': fields.String(required=True, description='The post ID'),
    'reaction': fields.String(required=True, description='Post reaction (like/dislike)')
})
get_post_model_request = auth_ns.model("Get Post", {
    'x-access-token': fields.String(required=True, description="x-access-token"),
    "id": fields.String(required=True, description="Post ID")
})

refresh_model = auth_ns.model('Refresh', {
    'refresh_token': fields.String(required=True, description='The refresh token')
})

def generate_access_token(user_id):
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
            'iat': datetime.datetime.utcnow(),
            '_id': str(user_id)
        }
        return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    except Exception as e:
        return e

def generate_refresh_token(user_id):
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30),
            'iat': datetime.datetime.utcnow(),
            '_id': str(user_id)
        }
        refresh_token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
        return refresh_token
    except Exception as e:
        return e
@auth_ns.route("/refresh_token")
class RefreshToken(Resource):
    @auth_ns.expect(refresh_model)
    def post(self):
        try:
            refresh_token = request.json.get('refresh_token')
            if not refresh_token:
                return {"error": "Refresh token is required"}, 400

            data = jwt.decode(refresh_token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = collection.find_one({"_id": ObjectId(data['_id'])})
            if not current_user:
                return {"message": "Invalid token"}, 401

            new_access_token = generate_access_token(data['_id'])
            return {"access_token": new_access_token}, 200

        except jwt.ExpiredSignatureError:
            return {"message": "Refresh token has expired"}, 401
        except jwt.InvalidTokenError:
            return {"message": "Invalid refresh token"}, 401
        except Exception as e:
            return {"error": str(e)}, 500

def token_required(token):
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        current_user = collection.find_one({"_id": ObjectId(data['_id'])})
        if not current_user:
            return {"message": "Invalid token"}, 401
    except jwt.ExpiredSignatureError:
        return {"message": "Token has expired"}, 401
    except jwt.InvalidTokenError:
        return {"message": "Invalid token"}, 401
    return current_user


@auth_ns.route('/create_post')
class PostCreation(Resource):
    @auth_ns.expect(upload_parser)
    def post(self):
        args = upload_parser.parse_args()
        try:
            title = args["title"]
            text = args["text"]
            tags = args["tags"]
            token = args['x-access-token']
        except Exception as e:
            return {"error": f"Error in taking body input: {str(e)}"}, 400

        if not title or not text or not tags:
            return {"error": "Invalid input"}, 400
        try:
            current_user =token_required(token)
        except:
            return "error in getting the current user"
        try:
            args = upload_parser.parse_args()
            uploaded_file = args['file']
            if not uploaded_file:
                return {"error": "in uploaded args"}
            file_data = Binary(uploaded_file.read())
        except:
            return {"error": " in getting file"}

        post_data = {
            'title': title,
            "text": text,
            "tags": [tags] if isinstance(tags, str) else tags,
            "thumbnail" : file_data,
            "comments": [],
            "likes": 0,
            "dislikes": 0,
            'author_id': current_user['_id'],
            'created_at': datetime.datetime.utcnow()
        }

        try:
            posts_collection.insert_one(post_data)
            return {'message': 'Post created successfully'}, 201
        except Exception as e:
            return {'error': str(e)}, 500  # Internal server error

@auth_ns.route("/get_post")
class PostGet(Resource):
    @auth_ns.expect(get_post_model_request)
    def post(self):
        token = request.json.get("x-access-token")
        if not token:
            return {"error": "Token is required"}, 400

        current_user = token_required(token)
        if "error" in current_user:
            return current_user

        post_id = request.json.get("id")
        if not post_id:
            return {"error": "Post ID is required"}, 400

        try:
            post = posts_collection.find_one({"_id": ObjectId(post_id)})
            if post:
                post_data = {
                    "ID" : str(post['_id']),
                    "Title" : str(post['title']),
                    "text":str(post['text']),
                    "tags": str(post['tags']),
                #"thumbnail" : file_data,
                "comments": str(post['comments']),
                "likes": str(post['likes']),
                "dislikes": str(post['dislikes']),
                'author_id': str(post['author_id']),
                'created_at': str(post['created_at'])
            }
                return {"message": post_data}, 200
            else:
                return {"error": "Post not found"}, 404
        except Exception as e:
            return {"error": "An error occurred while retrieving the post", "details": str(e)}, 500

@auth_ns.route("/add_comments")
class AddComments(Resource):
    @auth_ns.expect(add_post_comment_request_model)
    def put(self):
        try:
            token = request.json.get("x-access-token")
            current_user = token_required(token)
            if "error" in current_user:
                return current_user
        except:
            return {"error": "Error in getting token"}

        try:
            data = request.json
            post_id = data.get("id")
            comments = data.get("comment")
            if not post_id or not comments:
                return {"error": "Invalid id or comments"}, 400
        except:
            return {"error": "Error in processing input data"}, 400

        try:
            post = posts_collection.find_one({'_id': ObjectId(post_id), 'author_id': current_user['_id']})
            if post:
                if "comments" not in post:
                    posts_collection.update_one({"_id": ObjectId(post_id)}, {"$set": {"comments": []}})
                try:
                    result = posts_collection.update_one({"_id": ObjectId(post_id)}, {"$push": {"comments": comments}})
                    return {"message": "Comments added successfully"}, 200
                except Exception as e:
                    return {"error": "Failed to add comments", "details": str(e)}, 500
            else:
                return {"error": "Post not found or you are not the author"}, 404
        except Exception as e:
            return {"error": str(e)}, 500

@auth_ns.route("/delete_comments")
class deleteComments(Resource):
    @auth_ns.expect(delete_post_comment_request_model)
    def put(self):
        data = request.json
        current_user = {"error": ""}
        try:
            token = data.get("x-access-token")
            current_user = token_required(token)
        except:
            return {"error": "Invalid token"}, 400

        if "error" in current_user:
            return current_user, 400

        post_id = data.get("id")
        comment = data.get("comment")
        if not post_id:
            return {"error": "Invalid id"}, 400

        try:
            result = posts_collection.update_one(
                {'_id': ObjectId(post_id), 'author_id': current_user['_id']},
                {"$pull": {"comments": comment}}
            )

            if result.matched_count == 0:
                return {'error': 'Post not found or you are not the author'}, 404

            return {'message': 'Comment deleted successfully'}, 200
        except Exception as e:
            return {"error": str(e)}, 500

@auth_ns.route("/update_comments")
class UpdateComments(Resource):
    @auth_ns.expect(Update_post_comment_request_model)
    def put(self):
        try:
            token = request.json.get("x-access-token")
            if not token:
                return {"error": "Token is missing"}, 400

            current_user = token_required(token)
            if "error" in current_user:
                return current_user
        except Exception as e:
            return {"error": f"Error in processing token: {str(e)}"}, 400

        try:
            data = request.json
            post_id = data.get("id")
            pre_comment = data.get("pre_comment")
            new_comment = data.get("new_comment")

            if not post_id or not pre_comment or not new_comment:
                return {"error": "Invalid input"}, 400

            result = posts_collection.update_one(
                {"_id": ObjectId(post_id), "comments": pre_comment},
                {"$set": {"comments.$": new_comment}}
            )

            if result.modified_count > 0:
                return {"message": "Comment updated successfully"}, 200
            else:
                return {"error": "Comment not found or not updated"}, 404
        except Exception as e:
            return {"error": f"An error occurred: {str(e)}"}, 500

@auth_ns.route("/like_dislike")
class LikeDislike(Resource):
    @auth_ns.expect(likeDislike_post_request_model)
    def put(self):
        data = request.json
        id = data.get("id")
        reaction = data.get("reaction")

        if not id or not reaction or reaction not in ["like", "dislike"]:
            return {"error": "Invalid input id or reaction"}, 400

        try:

            if reaction == 'like':
                result = posts_collection.update_one(
                    {"_id": ObjectId(id)},
                    {"$inc": {"likes": 1}}
                )
                if result.modified_count > 0:
                    return {"message": "Like added successfully"}, 200
                else:
                    return {"error": "Like not added"}, 404
            elif reaction == 'dislike':
                result = posts_collection.update_one(
                    {"_id": ObjectId(id)},
                    {"$inc": {"dislikes": 1}}
                )
                if result.modified_count > 0:
                    return {"message": "Dislike added successfully"}, 200
                else:
                    return {"error": "Dislike not added"}, 404
        except Exception as e:
            return {"error": str(e)}, 500

@auth_ns.route("/register")
class Register(Resource):
    @auth_ns.expect(register_model)
    def post(self):
        data = request.json
        username = data.get('username')
        password = data.get('password')
        name = data.get("name")
        email = data.get('email')
        phone_no = data.get('phone_no')

        if not username or not password or not name or not email or not phone_no:
            return {"error": "Missing data"}, 404

        hashed_pwd = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        user_data = {
            "name": name,
            "username": username,
            "password": hashed_pwd,
            "phone_no": phone_no,
            "email": email
        }

        try:
            collection.insert_one(user_data)
            return {"message": "SignUp successfully"}, 200
        except Exception as e:
            return {"error": "SignUp Unsuccessful", "details": str(e)}, 500

@auth_ns.route("/login")
class Login(Resource):
    @auth_ns.expect(login_model)
    def post(self):
        data = request.json
        username = data.get('username')
        password = data.get('password')

        try:
            document = collection.find_one({"username": username})
            if not document:
                return {"message": "User not found"}, 404

            if bcrypt.checkpw(password.encode("utf-8"), document['password']):
                access_token = jwt.encode({
                    "_id": str(document['_id']),
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
                }, app.config['SECRET_KEY'], algorithm="HS256")

                refresh_token = jwt.encode({
                    "_id": str(document['_id']),
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)
                }, app.config['SECRET_KEY'], algorithm="HS256")

                return {"access_token": access_token, "refresh_token": refresh_token}, 200
            else:
                return {"error": "Login Unsuccessful"}, 401
        except Exception as e:
            return {"error": "Login Unsuccessful", "details": str(e)}, 500
@auth_ns.route('/update_post')
class UpdatePost(Resource):
    @auth_ns.expect(update_post_request_model1)
    def put(self):
        try:
            token = request.json.get("x-access-token")
            if not token:
                return {"error": "Token is missing"}, 400

            current_user = token_required(token)
            if "error" in current_user:
                return current_user
        except Exception as e:
            return {"error": f"Error in processing token: {str(e)}"}, 400

        try:
            data = request.json
            post_id = data.get("id")
            if not post_id:
                return {"error": "Post ID is required"}, 400

            update_fields = {}
            if "title" in data:
                update_fields["title"] = data["title"]
            if "text" in data:
                update_fields["text"] = data["text"]
            if "tags" in data:
                update_fields["tags"] = data["tags"]
            if "thumbnail" in data:
                update_fields["thumbnail"] = data["thumbnail"]
            if "comments" in data:
                update_fields["comments"] = data["comments"]

            if not update_fields:
                return {"error": "No fields to update"}, 400

            result = posts_collection.update_one(
                {"_id": ObjectId(post_id), "author_id": current_user['_id']},
                {"$set": update_fields}
            )

            if result.modified_count > 0:
                return {"message": "Post updated successfully"}, 200
            else:
                return {"error": "Post not found or you are not the author"}, 404
        except Exception as e:
            return {"error": "An error occurred while updating the post", "details": str(e)}, 500

@auth_ns.route("/delete_post")
class DeletePost(Resource):
    @auth_ns.expect(get_post_model_request)
    def delete(self):
        try:
            token = request.json.get("x-access-token")
            if not token:
                return {"error": "Token is missing"}, 400

            current_user = token_required(token)
            if "error" in current_user:
                return current_user
        except Exception as e:
            return {"error": f"Error in processing token: {str(e)}"}, 400

        try:
            data = request.json
            post_id = data.get("id")
            if not post_id:
                return {"error": "Post ID is required"}, 400

            post = posts_collection.find_one({"_id": ObjectId(post_id), "author_id": current_user['_id']})
            if not post:
                return {"error": "Post not found or you are not the author"}, 404

            posts_collection.delete_one({"_id": ObjectId(post_id)})

            if not posts_collection.find_one({"_id": ObjectId(post_id)}):
                return {"message": "Post deleted successfully"}, 200
            else:
                return {"error": "Post not deleted"}, 400
        except Exception as e:
            return {"error": "An error occurred during post deletion", "details": str(e)}, 500


api.add_namespace(auth_ns, path='/auth')
if __name__ == "__main__":
    app.run(debug=True)
