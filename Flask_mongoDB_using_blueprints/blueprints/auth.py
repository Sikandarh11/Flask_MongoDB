from flask import Blueprint, request, jsonify, current_app
import jwt
import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from extensions import db
auth_bp = Blueprint('auth', __name__)
users_collection = db['users']


@auth_bp.route('/register', methods=['POST'])
def register():

    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    hashed_password = generate_password_hash(password)

    user_data = {
        'username': username,
        'password': hashed_password
    }

    users_collection.insert_one(user_data)
    return jsonify({'message': 'User registered successfully'}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    user = users_collection.find_one({'username': username})
    if user and check_password_hash(user['password'], password):
        access_token = generate_access_token(user['_id'])
        refresh_token = generate_refresh_token(user['_id'])
        return jsonify({'access_token': str(access_token), 'refresh_token': str(refresh_token)}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = users_collection.find_one({'_id': ObjectId(data['_id'])})
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token is expired!'}), 403
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 403
        return f(current_user, *args, **kwargs)
    return decorated


def generate_access_token(user_id):
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
            'iat': datetime.datetime.utcnow(),
            '_id': str(user_id)
        }
        return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    except Exception as e:
        return e


def generate_refresh_token(user_id):
    try:
        print("generate_refresh_token called" )
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30),
            'iat': datetime.datetime.utcnow(),
            '_id': str(user_id)
        }
        refresh_token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
        print("refresh token generated")
        return refresh_token
    except Exception as e:
        return e



@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    refresh_token = request.form.get('refresh_token')

    if not refresh_token:
        return jsonify({'error': 'Refresh token is missing!'}), 400

    try:
        data = jwt.decode(refresh_token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = data.get('sub')
        if user_id:
            user = users_collection.find_one({'_id': ObjectId(user_id)})
            if user:
                access_token = generate_access_token(user['_id'])
                return jsonify({'access_token': access_token}), 200
            else:
                return jsonify({'error': 'User not found'}), 404
        else:
            return jsonify({'error': 'Invalid refresh token format!'}), 400
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Refresh token is expired!'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid refresh token!'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500
