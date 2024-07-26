from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, storage
import json
from io import BytesIO
import datetime
import uuid

app = Flask(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("D:\\influential-kit-430506-m-45094-firebase-adminsdk-3gh5f-706e5664b9.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'influential-kit-430506-m-45094.appspot.com'
})

bucket = storage.bucket()

@app.route('/create_post', methods=['POST'])
def create_post():
    token = request.headers.get('x-access-token')
    if not token:
        return {"error": "Authorization token is missing"}, 401

    data = request.json
    try:
        title = data.get("title")
        text = data.get("text")
        tags = data.get("tags")
        if not title or not text or not tags:
            return {"error": "Invalid input"}, 400
    except Exception as e:
        return {"error": f"Error parsing input: {str(e)}"}, 400

    try:
        post_id = str(uuid.uuid4())
        post_data = {
            'id': post_id,
            'title': title,
            'text': text,
            'tags': tags,
            'comments': [],
            'likes': 0,
            'dislikes': 0,
            'created_at': datetime.datetime.utcnow().isoformat()
        }

        json_data = json.dumps(post_data)
        json_bytes = BytesIO(json_data.encode('utf-8'))

        blob = bucket.blob(f'{post_id}.json')
        blob.upload_from_file(json_bytes, content_type='application/json')

        return jsonify({'message': 'Post created successfully', 'post_id': post_id, 'content': post_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_post/<post_id>', methods=['GET'])
def get_post(post_id):
    token = request.headers.get('x-access-token')
    if not token:
        return {"error": "Authorization token is missing"}, 401

    try:
        blob = bucket.blob(f'{post_id}.json')
        if blob.exists():
            json_data = blob.download_as_string()
            post_data = json.loads(json_data)
            return jsonify({'message': 'Post retrieved successfully', 'post_id': post_id, 'content': post_data})
        else:
            return jsonify({'error': 'Post not found'}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update_post/<post_id>', methods=['PUT'])
def update_post(post_id):
    token = request.headers.get('x-access-token')
    if not token:
        return {"error": "Authorization token is missing"}, 401

    data = request.json
    try:
        title = data.get("title")
        text = data.get("text")
        tags = data.get("tags")

        if not title and not text and not tags:
            return {"error": "No fields to update"}, 400

        blob = bucket.blob(f'{post_id}.json')
        if blob.exists():
            json_data = blob.download_as_string()
            post_data = json.loads(json_data)

            if title:
                post_data['title'] = title
            if text:
                post_data['text'] = text
            if tags:
                post_data['tags'] = tags

            post_data['updated_at'] = datetime.datetime.utcnow().isoformat()

            json_data = json.dumps(post_data)
            json_bytes = BytesIO(json_data.encode('utf-8'))

            blob.upload_from_file(json_bytes, content_type='application/json')

            return jsonify({'message': 'Post updated successfully', 'post_id': post_id, 'content': post_data})
        else:
            return jsonify({'error': 'Post not found'}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete_post/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    token = request.headers.get('x-access-token')
    if not token:
        return {"error": "Authorization token is missing"}, 401

    try:
        blob = bucket.blob(f'{post_id}.json')
        if blob.exists():
            blob.delete()
            return jsonify({'message': f'Post {post_id} deleted successfully'})
        else:
            return jsonify({'error': 'Post not found'}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/add_comment/<post_id>', methods=['POST'])
def add_comment(post_id):
    token = request.headers.get('x-access-token')
    if not token:
        return {"error": "Authorization token is missing"}, 401

    data = request.json
    comment = data.get("comment")

    if not comment:
        return {"error": "Comment cannot be empty"}, 400

    try:
        blob = bucket.blob(f'{post_id}.json')
        if blob.exists():
            json_data = blob.download_as_string()
            post_data = json.loads(json_data)

            # Add comment
            post_data['comments'].append({
                'comment': comment,
                'created_at': datetime.datetime.utcnow().isoformat()
            })


            json_data = json.dumps(post_data)
            json_bytes = BytesIO(json_data.encode('utf-8'))

            blob.upload_from_file(json_bytes, content_type='application/json')

            return jsonify({'message': 'Comment added successfully', 'post_id': post_id, 'content': post_data})
        else:
            return jsonify({'error': 'Post not found'}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/react_to_post/<post_id>', methods=['POST'])
def react_to_post(post_id):
    token = request.headers.get('x-access-token')
    if not token:
        return {"error": "Authorization token is missing"}, 401

    data = request.json
    reaction = data.get('reaction')

    if reaction not in ['like', 'dislike']:
        return {"error": "Invalid reaction type. Must be 'like' or 'dislike'"}, 400

    try:
        blob = bucket.blob(f'{post_id}.json')
        if blob.exists():
            json_data = blob.download_as_string()
            post_data = json.loads(json_data)

            if reaction == 'like':
                post_data['likes'] += 1
            elif reaction == 'dislike':
                post_data['dislikes'] += 1

            json_data = json.dumps(post_data)
            json_bytes = BytesIO(json_data.encode('utf-8'))

            blob.upload_from_file(json_bytes, content_type='application/json')

            return jsonify({'message': f'Post {reaction}d successfully', 'post_id': post_id, 'content': post_data})
        else:
            return jsonify({'error': 'Post not found'}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)
