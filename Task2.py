from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import datetime

# MongoDB connection
connection_string = 'mongodb+srv://sikandarnust1140:ZBXI5No3tsTeKb0u@cluster0.mo69b0z.mongodb.net/myDB?retryWrites=true&w=majority'
client = MongoClient(connection_string)
database = client['SocialMedia']
post_collection = database['post']
comments = database['comments']
user = database['user']

# Flask app
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/create_post", methods=['POST'])
def create_post():
    title = request.form.get('title')
    add_Description = request.form.get('add_Description')
    Tags = request.form.get('Tags').split(',') if request.form.get('Tags') else []
    Thumbnails = request.form.get('Thumbnails').split(',') if request.form.get('Thumbnails') else []

    data = {
        "title": title,
        "add_Description": add_Description,
        "Tags": Tags,
        "Thumbnails": Thumbnails,
        "likes": 0,
        "comments": 0,
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow()
    }

    try:
        post_collection.insert_one(data)
        return render_template("index.html")
    except Exception as e:
        return jsonify({'error': f"An error occurred: {e}"}), 500

@app.route('/get_Post', methods=['GET'])
def get_post():
    searchTerm = request.args.get('searchTerm')

    if searchTerm:
        search_results = list(post_collection.find({
            "$or": [
                {"title": {"$regex": searchTerm, "$options": "i"}},  # Case-insensitive search for title
                {"Tags": {"$regex": searchTerm, "$options": "i"}}    # Case-insensitive search for tags
            ]
        }))
        if search_results:
            for post in search_results:
                post['_id'] = str(post['_id'])  # Convert ObjectId to string for JSON serialization
            return jsonify({'posts': search_results})
        else:
            return jsonify({'message': 'No posts found for the given search term'}), 404
    else:
        return jsonify({'message': 'Please provide a search term in the query parameter'}), 400

@app.route('/Update_Post', methods=['POST'])
def update_post():
    title = request.form.get('title2')  # Get the title from the form field 'title2'
    new_title = request.form.get('new_title')
    new_description = request.form.get('new_description')
    new_tags = request.form.get('new_tags').split(',') if request.form.get('new_tags') else []
    new_thumbnails = request.form.get('new_thumbnails').split(',') if request.form.get('new_thumbnails') else []

    if title:
        update_fields = {}
        if new_title:
            update_fields['title'] = new_title
        if new_description:
            update_fields['add_Description'] = new_description
        if new_tags:
            update_fields['Tags'] = new_tags
        if new_thumbnails:
            update_fields['Thumbnails'] = new_thumbnails

        result = post_collection.update_one(
            {'title': title},
            {'$set': update_fields}
        )

        if result.matched_count:
            return jsonify({'message': 'Post updated successfully'})
        else:
            return jsonify({'message': 'Post not found'}), 404
    else:
        return jsonify({'message': 'Post name must be provided'}), 400

if __name__ == "__main__":
    app.run(debug=True)
