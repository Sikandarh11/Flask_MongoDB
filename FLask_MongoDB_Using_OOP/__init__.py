from flask import Flask
from flask_restful import Api
from pymongo import MongoClient
from app.auth.routes import auth_bp
from app.users.routes import users_bp
from app.posts.routes import posts_bp


def create_app():
    app = Flask(__name__)
    api = Api(app)

    app.config['SECRET_KEY'] = "your_secret_key_here"
    connection_string = 'mongodb+srv://sikandarnust1140:ZBXI5No3tsTeKb0u@cluster0.mo69b0z.mongodb.net/newDB?retryWrites=true&w=majority'
    client = MongoClient(connection_string)

    # Initialize database collections
    app.db = {
        'users': client['userCollection']['user'],
        'posts': client['Authentication']['posts_collection']
    }

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(posts_bp, url_prefix='/posts')

    return app
