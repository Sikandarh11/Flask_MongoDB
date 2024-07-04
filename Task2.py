from flask import Flask, redirect, url_for, render_template, request
from pymongo import MongoClient

connection_string = 'mongodb+srv://sikandarnust1140:ZBXI5No3tsTeKb0u@cluster0.mo69b0z.mongodb.net/myDB?retryWrites=true&w=majority'
client = MongoClient(connection_string)
database = client['users']
collection = database['UserAuthentication']

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/Login", methods=['POST'])
def login():
    user_name = request.form.get('UserName')
    email = request.form.get('email')
    password = request.form.get('Password')
    query = {
        "UserName": user_name,
        "Email": email,
        "Password": password
    }

    print("Query:", query)  # Debugging step

    document = collection.find_one(query)

    print("Document:", document)  # Debugging step

    if document:
        print("Login successful")
        return "Login successful"
    else:
        print("Login unsuccessful")
        return "Login unsuccessful"


@app.route("/SignUp", methods=['POST'])
def sign_up():
    user_name = request.form.get('UserName')
    email = request.form.get('email')
    password = request.form.get('Password')
    data = {
        "UserName": user_name,
        "Email": email,
        "Password": password
    }
    try:
        collection.insert_one(data)
    except Exception as e:
        print(f"An error occurred: {e}")
        return "An error occurred while saving to the database."
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
