
import bcrypt
from flask_uploads import UploadSet, configure_uploads, IMAGES
import jwt
from bson.objectid import ObjectId
from flask import Flask, request, url_for, send_from_directory, current_app
from pymongo import MongoClient
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
import os
import datetime
from flask_restx import Api, Resource, fields, reqparse


app = Flask(__name__)
app.config['SECRET_KEY'] = "your_secret_key_here"
app.config['UPLOAD_FOLDER'] = 'uploads'  # Directory to save uploaded files
app.config['MAX_CONTENT_PATH'] = 16 * 1024 * 1024  # 16 MB max upload size

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.config['SECRET_KEY'] = "your_secret_key_here"
authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'x-access-token'
    }
}
api = Api(app, authorizations=authorizations, security='apikey')
auth_ns = api.namespace('post_management', description='Post Management')


photos = UploadSet('photos', IMAGES)
app.config['UPLOADED_PHOTOS_DEST'] = 'uploads/photos'
configure_uploads(app, photos)

connection_string = 'mongodb+srv://sikandarnust1140:ZBXI5No3tsTeKb0u@cluster0.mo69b0z.mongodb.net/newDB?retryWrites=true&w=majority'
client = MongoClient(connection_string)
database = client['Authentication']
database2 = client['userCollection']
collection = database2['user']
posts_collection= database['posts_collection']



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
    'id': fields.String(required=True, description='The post ID'),
})
add_post_comment_request_model = api.model('Add Comments Request', {
    'id': fields.String(required=True, description='The post ID'),
    'comment': fields.String(required=True, description='The comment to add'),
})
delete_post_comment_request_model = api.model('Delete Comment Request', {
    "id": fields.String(required=True, description="Post ID"),
    "comment": fields.String(required=True, description="Delete post comment")
})
delete_post_request_model = api.model('Post Request', {
     "id": fields.String(required=True, description="Post ID")
})
Update_post_comment_request_model = api.model('Update Comments Request', {
    'id': fields.String(required=True, description='The post ID'),
    'new_comment': fields.String(required=True, description='New comment text'),
    'pre_comment': fields.String(required=True, description='Previous comment text'),
})
likeDislike_post_request_model = api.model('Post Request', {
    'id': fields.String(required=True, description='The post ID'),
    'reaction': fields.String(required=True, description='Post reaction (like/dislike)')
})
get_post_model_request = auth_ns.model("Get Post", {
    "id": fields.String(required=True, description="Post ID")
})
refresh_model = auth_ns.model('Refresh', {
    'refresh_token': fields.String(required=True, description='The refresh token')
})


post_request = reqparse.RequestParser()
post_request.add_argument('file', location='files', type=FileStorage, required=True)
post_request.add_argument('title', type=str, required=True)
post_request.add_argument('text', type=str, required=True)
post_request.add_argument('tags', type=str, required=True)

update_post_request = reqparse.RequestParser()
update_post_request.add_argument('id', type=str, required=True)
update_post_request.add_argument('file', location='files', type=FileStorage)
update_post_request.add_argument('title', type=str)
update_post_request.add_argument('text', type=str)
update_post_request.add_argument('tags', type=str)
update_post_request.add_argument('comments', type=str)



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
def token_required():
    try:
        token = request.headers.get('x-access-token')
        if not token:
            return {'message': 'Token is missing!'}, 401, None
    except Exception as e:
        return {"error": "Token not found"}, 400, None

    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        current_user = collection.find_one({"_id": ObjectId(data['_id'])})
        if not current_user:
            return {'message': 'yser not found'}, 404, None
    except jwt.ExpiredSignatureError:
        return {'message': 'token has expired!'}, 401, None
    except jwt.InvalidTokenError:
        return {'message': 'invalid token!'}, 401, None
    except Exception as e:
        return {'message': f'Error in token decoding: {str(e)}'}, 500, None

    return current_user



@auth_ns.route('/create_post')
class PostCreation(Resource):
    @api.expect(post_request)
    def post(self):
        current_user = token_required()
        args = post_request.parse_args()
        try:
            title = args["title"]
            text = args["text"]
            tags = args["tags"]
            uploaded_file = args['file']
            if not title or not text or not tags or not uploaded_file:
                return {"error": "Invalid input"}, 400

        except Exception as e:
            return {"error": f"Error parsing input: {str(e)}"}, 400

        try:
            # Secure the filename
            filename = secure_filename(uploaded_file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

            # Save the uploaded file
            uploaded_file.save(file_path)
        except Exception as e:
            return {"message": f"File upload error: {str(e)}"}, 400

        try:
            # Create post data
            post_data = {
                'title': title,
                'text': text,
                'tags': tags,
                'thumbnail_url': url_for('get_file', filename=filename, _external=True),
                'comments': [],
                'likes': 0,
                'dislikes': 0,
                'author_id': str(current_user['_id']),
                'created_at': datetime.datetime.utcnow().isoformat()
            }

            # Insert the post data into the database
            post = posts_collection.insert_one(post_data)

            return {"message": "Post created successfully",
                    "Post ID": str(post.inserted_id),
                    "Post Title": post_data['title'],
                    "Post Data" : post_data['text'],
                    "Post Tags" : post_data['tags'],
                    "Thumbnails" : post_data['thumbnail_url']
                    }, 201
        except Exception as e:
            return {"error": f"Error in creating post data: {str(e)}"}, 400


@auth_ns.route("/get_post/<id>")
class PostDetails(Resource):
    def get(self, id):
        post_id = id
        if not post_id:
            return {"error": "Post ID is required"}, 400
        current_user = token_required()
        try:
            post = posts_collection.find_one(
                {"_id": ObjectId(post_id)}
            )
        except:
            return {"error": "Post not found"}, 404
        try:
            if post:
                if str(current_user['_id']) != post['author_id']:
                    return {"error": "You are not the author"}, 403
                post_data = {
                    "Title": post['title'],
                    "Text": str(post['text']),
                    "Thumbnail_url": str(post['thumbnail_url']),
                    "Tags": str(post['tags']),
                    "Comments": str(post['comments']),
                    "Likes": str(post['likes']),
                    "Dislikes": str(post['dislikes']),
                    'Author Id': str(post['author_id']),
                    'Created at': str(post['created_at'])
                }
                return {"message": post_data}, 200
            else:
                return {"error": "Post not found"}, 404
        except Exception as e:
            return {"error": "An error occurred while retrieving the post", "details": str(e)}, 500

@app.route('/uploads/<filename>')
def get_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@auth_ns.route("/add_comments")
class AddComments(Resource):
    @auth_ns.expect(add_post_comment_request_model)
    def put(self):
        try:
            data = request.json
            post_id = data.get("id")
            comments = data.get("comment")
            if not post_id or not comments:
                return {"error": "Invalid id or comments"}, 400
        except:
            return {"error": "Error in processing input data"}, 400

        try:
            current_user = token_required()
            result = posts_collection.update_one({"_id": ObjectId(post_id), 'author_id': str(current_user['_id'])},
                                                         {"$push": {"comments": comments}})
            if result.matched_count == 0:
                return {'error': 'Post not found or you are not the author'}, 404

            return {'message': 'Comment added successfully'}, 200

        except Exception as e:
            return {"error": str(e)}, 500



@auth_ns.route("/delete_comments")
class deleteComments(Resource):
    @auth_ns.expect(delete_post_comment_request_model)
    def put(self):
        data = request.json

        post_id = data.get("id")
        comment = data.get("comment")
        if not post_id:
            return {"error": "Invalid id"}, 400

        try:
            current_user = token_required()
            result = posts_collection.update_one(
                {'_id': ObjectId(post_id), 'author_id': str(current_user['_id'])},
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
            data = request.json
            post_id = data.get("id")
            pre_comment = data.get("pre_comment")
            new_comment = data.get("new_comment")
            current_user = token_required()

            if not post_id or not pre_comment or not new_comment:
                return {"error": "Invalid input"}, 400

            result = posts_collection.update_one(
                {"_id": ObjectId(post_id), "comments": pre_comment, "author_id" : str(current_user['_id'])},
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

update_post_model = api.model('Post Request', {
    'id': fields.String(required=True, description='The post ID'),
    'title': fields.String(required=False, description='The post title'),
    'text': fields.String(required=False, description='The post text'),
    'tags': fields.String(required=False, description='The post tags'),
    'thumbnail': fields.String(required=False, description='The post thumbnail'),
    'comments': fields.String(required=False, description='The post comments'),
})



@auth_ns.route('/update_post')
class UpdatePost(Resource):
    @auth_ns.expect(update_post_request)
    def put(self):
        update_fields = {}
        post_id = ""
        args = update_post_request.parse_args()
        try:
            post_id = args["id"]
            if not post_id:
                return {"error": "Post ID is required"}, 400
        except KeyError as e:
            return {"error": f"Missing key: {str(e)}"}, 400
        except Exception as e:
            return {"error": f"An error occurred before title: {str(e)}"}, 500
        try:
            uploaded_file = args['file']
            filename = secure_filename(uploaded_file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        # Save the uploaded file
            uploaded_file.save(file_path)
            update_fields['thumbnail_url'] = url_for('get_file', filename=filename, _external=True)
        except Exception as e:
            return {"message": f"File upload error: {str(e)}"}, 400
        try:
            if args["title"]:
                update_fields["title"] = args["title"]
            if args['text']:
                update_fields['text'] = args['text']
            if args['tags']:
                update_fields['tags'] = args['tags']

            if not update_fields:
                print("update fields", update_fields)
                return {"error": "No fields to update"}, 400

        except KeyError as e:
            return {"error": f"Missing key: {str(e)}"}, 400
        except Exception as e:
            return {"error": f"An error occurred in input: {str(e)}"}, 500

        try:
            current_user = token_required()
            # Debugging print statement
            print(f"Current User: {current_user}")

            result = posts_collection.update_one(
                {"_id": ObjectId(post_id), "author_id" : str(current_user['_id'])},
                {"$set": update_fields}
            )

            if result.modified_count > 0:
                return {"message": "Post updated successfully"}, 200
            else:
                return {"error": "Post not found111"}, 404
        except Exception as e:
            return {"error": "An error occurred while updating the post", "details": str(e)}, 500

@auth_ns.route("/delete_post")
class DeletePost(Resource):
    @auth_ns.expect(get_post_model_request)
    def delete(self):
        try:
            data = request.json
            post_id = data.get("id")
            if not post_id:
                return {"error": "Post ID is required"}, 400
            current_user = token_required()
            post = posts_collection.find_one({"_id": ObjectId(post_id)})
            if not post:
                return {"error": "Post not found "}, 404
            elif post["author_id"] ==  str(current_user['_id']):
                posts_collection.delete_one({"_id": ObjectId(post_id)})
            else:
                return "you are not the author"
            return {"message": "Post deleted successfully"}, 200

        except Exception as e:
            return {"error": "An error occurred during post deletion", "details": str(e)}, 500


api.add_namespace(auth_ns, path='/auth')
if __name__ == "__main__":
    app.run(debug=True, port=8000)
