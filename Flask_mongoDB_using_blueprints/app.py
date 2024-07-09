from extensions import app
from blueprints.auth import auth_bp
from blueprints.post import posts_bp

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(posts_bp)

if __name__ == '__main__':
    app.run(debug=True)
