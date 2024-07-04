from flask import Flask, redirect, url_for, render_template, request
from pymongo import MongoClient
connection_string = 'mongodb+srv://sikandarnust1140:ZBXI5No3tsTeKb0u@cluster0.mo69b0z.mongodb.net/myDB?retryWrites=true&w=majority'
client = MongoClient(connection_string)
database = client['users']
collection = database['info']

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=['POST'])
def submit():
    name = email= phone= address = "NONE"
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    address = request.form.get('address')
    data = {
        "Name" : name,
        "Email" : email,
        "Phone no:":phone,
        "Address":address
    }
    try:
        collection.insert_one(data)
    except Exception   as e:
        print(e)


    # Here, you can add logic to handle the form data, like saving it to a database
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
