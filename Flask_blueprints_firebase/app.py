from extensions import app
from blueprints.auth import auth_bp
from blueprints.storage_management import storage_management

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(storage_management)

if __name__ == '__main__':
    app.run(debug=True)
