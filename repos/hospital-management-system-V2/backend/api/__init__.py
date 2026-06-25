from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from .auth import auth_bp
from .admin import admin_bp
from .doctor import doctor_bp
from .patient import patient_bp
from .public import public_bp
from ..models import db, Department
from ..utils.cache import cache_get, cache_set

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Register sub-blueprints with their URL prefixes
api_bp.register_blueprint(auth_bp, url_prefix='/auth')
api_bp.register_blueprint(admin_bp, url_prefix='/admin')
api_bp.register_blueprint(doctor_bp, url_prefix='/doctor')
api_bp.register_blueprint(patient_bp, url_prefix='/patient')
api_bp.register_blueprint(public_bp, url_prefix='/public')


# Route registered directly on api_bp: /api/departments
@api_bp.route('/departments', methods=['GET'])
@jwt_required()
def get_all_departments():
    cache_key = "departments:all"
    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify(cached), 200

    departments = Department.query.all()
    result = [{
        'id': d.id,
        'name': d.name,
        'description': d.description,
        'phone_number': d.phone_number,
        'email': d.email
    } for d in departments]

    cache_set(cache_key, result)
    return jsonify(result), 200
