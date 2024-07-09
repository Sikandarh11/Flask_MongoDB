from flask import Blueprint, request, jsonify
from flask_restful import Resource, Api
from bson import ObjectId
from app.utils import token_required

users_bp = Blueprint('users', __name__)
api = Api(users_bp)

class UserProfile(Resource):
    @token_required
    def get(self, current_user):
        user_id = request.args.get("id")
        try:
            user = request.app.db['users'].find_one({'_id': ObjectId(user_id)})
            if user:
                user['_id'] = str(user['_id'])
                return jsonify(user), 200
            else:
                return jsonify({'error': 'user not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

api.add_resource(UserProfile, '/profile')
