import base64
import uuid
import requests
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, auth, storage
from google.cloud import storage as gcs
from google.oauth2 import service_account
app = Flask(__name__)


# Initialize Firebase Admin SDK
cred = credentials.Certificate("D:\\influential-kit-430506-m-45094-firebase-adminsdk-3gh5f-4781881dca.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'influential-kit-430506-m-45094.appspot.com'
})
gcs_credentials = service_account.Credentials.from_service_account_file("D:\\influential-kit-430506-m-45094-firebase-adminsdk-3gh5f-4781881dca.json")
gcs_client = gcs.Client(credentials=gcs_credentials)
bucket = storage.bucket()

def verify_token(token):
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token['uid']
    except Exception as e:
        print(f"Token verification error: {str(e)}")
        return None

@app.route('/register', methods=['POST'])
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

@app.route('/login', methods=['POST'])
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

@app.route('/list_buckets', methods=['GET'])
def list_buckets():
    token = request.headers.get('x-access-token')
    if not token:
        return jsonify({"error": "Authorization token is missing"}), 401
    uid = verify_token(token)
    if not uid:
        return jsonify({"error": "Invalid or expired token"}), 401

    try:
        buckets = list(gcs_client.list_buckets())
        bucket_names = [bucket_i.name for bucket_i in buckets]
        return jsonify({'buckets': bucket_names})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/rename_file', methods=['POST'])
def rename_file():
    token = request.headers.get('x-access-token')
    if not token:
        return {"error": "Authorization token is missing"}, 401

    decoded_token = auth.verify_id_token(token)
    uid = decoded_token['uid']
    if not uid:
        return {"error": "Invalid or expired token"}, 401

    data = request.get_json()
    orignal_name = data.get('orignal_name')
    new_name = data.get('new_name')

    try:
        source_blob = bucket.blob(orignal_name)
        if not source_blob.exists():
            return jsonify({'error': 'Source file not found'}), 404

        bucket.copy_blob(source_blob, bucket, new_name)
        source_blob.delete()
        return jsonify({'message': 'File renamed successfully'})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/list_objects', methods=['GET'])
def list_objects():

    token = request.headers.get('x-access-token')
    if not token:
        return {"error": "Authorization token is missing"}, 401

    decoded_token = auth.verify_id_token(token)
    uid = decoded_token['uid']
    if not uid:
        return {"error": "Invalid or expired token"}, 401

    try:
        blobs = bucket.list_blobs()
        blob_names = [blob.name for blob in blobs]
        return jsonify({'blob names': blob_names})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/delete_file/<id>', methods=['DELETE'])
def delete_file(id):
    token = request.headers.get('x-access-token')
    if not token:
        return {"error": "Authorization token is missing"}, 401

    decoded_token = auth.verify_id_token(token)
    uid = decoded_token['uid']
    if not uid:
        return {"error": "Invalid or expired token"}, 401
    print(uid)
    try:
        blob = bucket.blob(id)
        if blob.exists():
            blob.delete()
            return jsonify({'message': 'File deleted successfully'})
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({"error1": str(e)}), 500

@app.route('/get_file/<id>', methods=['GET'])
def get_file(id):
    token = request.headers.get('x-access-token')
    if not token:
        return {"error": "Authorization token is missing"}, 401

    decoded_token = auth.verify_id_token(token)
    uid = decoded_token['uid']
    if not uid:
        return {"error": "Invalid or expired token"}, 401
    print(uid)
    try:
        blob = bucket.blob(id)
        if blob.exists():
            file_data = blob.download_as_bytes()  # Use download_as_bytes to handle both text and binary data
            encoded_file_data = base64.b64encode(file_data).decode('utf-8')
            return jsonify({'message': 'File found successfully', 'file_data': encoded_file_data})
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({"error1": str(e)}), 500

@app.route('/upload_file', methods=['POST'])
def upload_file():
    token = request.headers.get('x-access-token')
    if not token:
        return {"error": "Authorization token is missing"}, 401

    uid = verify_token(token)
    if not uid:
        return {"error": "Invalid or expired token"}, 401

    file = request.files.get('file')
    if not file:
        return {"error": "No file provided"}, 400

    try:
        file_id = str(uuid.uuid4())
        blob = bucket.blob(file_id)
        blob.upload_from_file(file, content_type=file.content_type)

        return jsonify({'message': 'File uploaded successfully', 'file_id': file_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
