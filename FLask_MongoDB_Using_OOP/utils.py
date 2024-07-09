import datetime
import jwt
import bcrypt
from flask import jsonify, request, current_app
from functools import wraps
from bson import ObjectId


def generate_tokens(user_id):
    access_token = jwt.encode({
        "_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    }, current_app.config['SECRET_KEY'], algorithm='HS256')

    refresh_token = jwt.encode({
        "_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, current_app.config['SECRET_KEY'], algorithm='HS256')

    return refresh_token, access_token


def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password)


def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.headers.get("x-access-token")
        if not token:
            return jsonify({"message": "token not found"}), 400
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = current_app.db['users'].find_one({"_id": ObjectId(data['_id'])})
            if not current_user:
                return jsonify({"message": "Invalid token"}), 401
            return func(current_user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "invalid token"}), 401
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return decorated
