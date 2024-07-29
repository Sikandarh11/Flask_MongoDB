from flask import Blueprint, request, jsonify, Flask
import requests
from firebase_admin import auth
app = Flask(__name__)

auth_bp = Blueprint('auth', __name__)

def verify_token(token):
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token['uid']
    except Exception as e:
        print(f"Token verification error: {str(e)}")
        return None

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return {"error": "Email and password are required"}, 400

    try:
        user = auth.create_user(email=email, password=password)
        return jsonify({'message': 'User registered successfully', 'uid': user.uid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return {"error": "Email and password are required"}, 400

    try:
        api_key = 'AIzaSyDXjfjQntf7TBke7mQix7gs5eTaogm3kJg'
        url = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}'
        payload = {
            'email': email,
            'password': password,
            'returnSecureToken': True
        }
        response = requests.post(url, json=payload)
        response_data = response.json()

        if 'idToken' in response_data:
            id_token = response_data['idToken']
            return jsonify({'message': 'Login successful', 'id_token': id_token}), 200
        else:
            return jsonify({'error': response_data.get('error', 'Login failed')}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
