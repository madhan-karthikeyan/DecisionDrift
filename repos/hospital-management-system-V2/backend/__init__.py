import os
from flask import Flask, redirect, request, jsonify
from .models import User, Admin
from flasgger import Swagger
from backend.config import Config
from werkzeug.security import generate_password_hash
from backend.extensions import jwt, migrate, db, init_celery
import redis

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS handling -- restrict to configured allowed origins
    ALLOWED_ORIGINS = os.environ.get(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:3000,http://localhost:5000'
    ).split(',')

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin', '')
        if origin in ALLOWED_ORIGINS:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    @app.route('/api/<path:subpath>', methods=['OPTIONS'])
    def handle_options(subpath):
        return '', 204

    # Initialize JWT
    jwt.init_app(app)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    init_celery(app)
    import backend.extensions as extensions
    extensions.redis_client = redis.Redis(
        host=app.config["REDIS_HOST"],
        port=app.config["REDIS_PORT"],
        db=app.config["REDIS_DB"],
        decode_responses=True
    )

    app.redis_client = extensions.redis_client

    basedir = os.path.abspath(os.path.dirname(__file__))
    root_path = os.path.dirname(basedir)
    swagger_file_path = os.path.join(root_path, 'api.yaml')

    template = {
        "swagger": "2.0",
        "info": {
            "title": "Hospital Management System API",
            "version": "1.0.0",
            "description": "API documentation for the Hospital Management System"
        }
    }

    Swagger(app, template=template, template_file=swagger_file_path)

    with app.app_context():
        try:
            # Only create tables if not using migrations (e.g. testing).
            # In production, rely on Flask-Migrate / Alembic.
            if app.config.get('SQLALCHEMY_CREATE_TABLES', False):
                db.create_all()

            # Create default admin if not exists
            if not User.query.filter_by(role='admin').first():
                default_admin_password = os.environ.get('ADMIN_DEFAULT_PASSWORD', 'Admin@123')
                admin_user = User(
                    username='admin',
                    password=generate_password_hash(default_admin_password),
                    role='admin'
                )
                db.session.add(admin_user)
                db.session.flush()

                admin_profile = Admin(uuid=admin_user.id, name='Super Admin')
                db.session.add(admin_profile)
                db.session.commit()
                print("Default admin created successfully!")
        except Exception as e:
            print(f"DB Init note: {e}")

    # Import and register the API blueprint (contains all sub-blueprints)
    from .api import api_bp
    app.register_blueprint(api_bp)

    @app.route('/', methods=['GET', 'POST'])
    def home():
        return redirect('/api/docs')

    return app
