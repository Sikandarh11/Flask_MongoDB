from flask import Flask, redirect, url_for, render_template, request, jsonify
from pymongo import MongoClient
import bcrypt
import jwt
import datetime

# MongoDB connection
connection_string = 'mongodb+srv://sikandarnust1140:ZBXI5No3tsTeKb0u@cluster0.mo69b0z.mongodb.net/myDB?retryWrites=true&w=majority'
client = MongoClient(connection_string)
database = client['users']
collection = database['UserAuthentication']

# Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/SignUp", methods=['POST'])
def sign_up():
    user_name = request.form.get('UserName')
    email = request.form.get('email')
    password = request.form.get('Password')

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    print(password)
    data = {
        "UserName": user_name,
        "Email": email,
        "Password": hashed_password
    }

    try:
        collection.insert_one(data)
    except Exception as e:
        print(f"An error occurred: {e}")
        return "An error occurred while saving to the database."

    return render_template("index.html")


@app.route("/Login", methods=['POST'])
def login():
    user_name = request.form.get('UserName1')
    password = request.form.get('Password1')

    query = {"UserName": user_name}

    user = collection.find_one(query)

    if user and bcrypt.checkpw(password.encode('utf-8'), user['Password']):
        token = jwt.encode({
            'user_id': str(user['_id']),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'])

        return jsonify({'token': token})
    else:
        return jsonify({'message': 'Login unsuccessful'}), 401


if __name__ == "__main__":
    app.run(debug=True)
