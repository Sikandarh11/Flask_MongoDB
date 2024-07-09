from flask import Blueprint, request, jsonify
from flask_restful import Resource, Api
from bson import ObjectId
from app.utils import token_required

posts_bp = Blueprint('posts', __name__)
api = Api(posts_bp)

class Post(Resource):
    @token_required
    def post(self, current_user):
        data = request.form
        title = data.get("title")
        text = data.get("text")
        tags = data.getlist("tags")
        thumbnail = request.files.get("thumbnail")
        comments = data.getlist("comments")

        if not title or not text or not tags or not thumbnail:
            return jsonify({"error": "Invalid input"}), 400

        post_data = {
            "title": title,
            "text": text,
            "tags": tags,
            "thumbnail": thumbnail.read(),
            "comments": comments,
            "likes": 0,
            "dislikes": 0,
            "created_at": datetime.datetime.utcnow()
        }

        try:
            request.app.db['posts'].insert_one(post_data)
            return jsonify({"message": "Post created successfully"}), 201
        except Exception as e:
            return jsonify({"error": "Post creation failed"}), 500

    @token_required
    def get(self, current_user):
        post_id = request.args.get("id")
        try:
            post = request.app.db['posts'].find_one({'_id': ObjectId(post_id)})
            if post:
                post['_id'] = str(post['_id'])
                return jsonify(post), 200
            else:
                return jsonify({'error': 'Post not found'}), 404
        except Exception as e:
            return jsonify({'Error': str(e)}), 500

api.add_resource(Post, '/')
