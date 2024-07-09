from flask import Blueprint, request, jsonify
from flask_restful import Resource, Api
from bson import ObjectId
from app.utils import generate_tokens, token_required, hash_password, verify_password
import jwt

auth_bp = Blueprint('auth', __name__)
api = Api(auth_bp)

class Register(Resource):
    def post(self):
        data = request.json
        username = data.get('username')
        password = data.get('password')
        name = data.get("name")
        email = data.get('email')
        phone_no = data.get('phone_no')

        if not username or not password or not name or not email or not phone_no:
            return jsonify({"error": "Missing data"}), 400

        hashed_pwd = hash_password(password)

        user_data = {
            "name": name,
            "username": username,
            "password": hashed_pwd,
            "phone_no": phone_no,
            "email": email
        }

        try:
            request.app.db['users'].insert_one(user_data)
            return jsonify({"message": "SignUp successfully"}), 200
        except Exception as e:
            return jsonify({"error": "SignUp Unsuccessful"}), 500

class Login(Resource):
    def post(self):
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"error": "Missing username or password"}), 400

        try:
            document = request.app.db['users'].find_one({"username": username})
            if not document:
                return jsonify({"error": "User not found"}), 404

            if verify_password(password, document.get('password')):
                user_id_str = str(document['_id'])
                refresh_token, access_token = generate_tokens(user_id_str)
                return jsonify({"refresh_token": refresh_token, "access_token": access_token}), 200
            else:
                return jsonify({"error": "Invalid credentials"}), 401
        except Exception as e:
            return jsonify({"error": f"Exception: {str(e)}"}), 500

api.add_resource(Register, '/register')
api.add_resource(Login, '/login')
