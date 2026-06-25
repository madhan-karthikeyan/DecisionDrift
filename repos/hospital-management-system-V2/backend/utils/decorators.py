from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from ..models import db, User


def get_current_user():
    """Get the current user from JWT identity."""
    user_id = get_jwt_identity()
    if not user_id:
        return None
    return db.session.get(User, user_id)


def require_admin(fn):
    """Decorator to require admin role."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return fn(*args, **kwargs)
    return wrapper


def require_doctor(fn):
    """Decorator to require doctor role."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or user.role != 'doctor':
            return jsonify({'error': 'Doctor access required'}), 403
        return fn(*args, **kwargs)
    return wrapper


def require_patient(fn):
    """Decorator to require patient role."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or user.role != 'patient':
            return jsonify({'error': 'Patient access required'}), 403
        return fn(*args, **kwargs)
    return wrapper
