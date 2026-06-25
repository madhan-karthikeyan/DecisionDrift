from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from ...models import db, Doctor, Department
import json
from backend.config import Config


def _get_redis():
    """Lazily get redis_client from the current app to avoid stale None reference."""
    return getattr(current_app, 'redis_client', None)

public_bp = Blueprint('api_public', __name__)


@public_bp.route('/departments', methods=['GET'])
def get_public_departments():
    cache_key = "public:departments:all"
    redis = _get_redis()

    if redis:
        cached = redis.get(cache_key)
        if cached:
            return jsonify(json.loads(cached)), 200

    departments = Department.query.all()

    result = [{
        'id': d.id,
        'name': d.name
    } for d in departments]

    if redis:
        redis.setex(cache_key, 600, json.dumps(result))

    return jsonify(result), 200


@public_bp.route('/specializations', methods=['GET'])
def get_public_specializations():
    department_id = request.args.get('department_id', 'all')
    cache_key = f"public:specializations:{department_id}"
    redis = _get_redis()

    if redis:
        cached = redis.get(cache_key)
        if cached:
            return jsonify(json.loads(cached)), 200

    query = db.session.query(Doctor.specialization).filter(Doctor.is_blacklisted == False)

    if department_id != 'all':
        query = query.filter(Doctor.department_id == department_id)

    specializations = [s[0] for s in query.distinct().all() if s[0]]

    if redis:
        redis.setex(cache_key, 600, json.dumps(specializations))

    return jsonify(specializations), 200


@public_bp.route('/doctors', methods=['GET'])
def get_public_doctors():
    department_id = request.args.get('department_id', 'all')
    cache_key = f"public:doctors:{department_id}"
    redis = _get_redis()

    if redis:
        cached = redis.get(cache_key)
        if cached:
            return jsonify(json.loads(cached)), 200

    query = Doctor.query.filter(Doctor.is_blacklisted == False)

    if department_id != 'all':
        query = query.filter(Doctor.department_id == department_id)

    doctors = query.all()

    result = [{
        'id': d.id,
        'name': d.name,
        'specialization': d.specialization,
        'department_id': d.department_id,
        'experience_years': d.experience,
        'consultation_fee': d.consultation_fee
    } for d in doctors]

    if redis:
        redis.setex(cache_key, Config.REDIS_CACHE_EXPIRE, json.dumps(result))

    return jsonify(result), 200