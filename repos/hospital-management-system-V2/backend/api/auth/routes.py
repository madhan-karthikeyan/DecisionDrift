from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from flask_jwt_extended import create_access_token, jwt_required
from ...models import db, User, Patient, Doctor
from ...utils.decorators import get_current_user
import logging
import re

auth_bp = Blueprint('api_auth', __name__)
logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# TODO: [L51] Add a password change/reset endpoint so users can update credentials
# TODO: [L57] Consider using httpOnly cookies for JWT instead of localStorage to mitigate XSS
# TODO: [L58] Add CSRF protection (e.g. Flask-WTF CSRFProtect or double-submit cookie pattern)


# TODO: Add rate limiting to prevent brute-force attacks (e.g. Flask-Limiter: 5 per minute)
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        # Check blacklist for doctors
        if user.role == 'doctor':
            doctor = Doctor.query.filter_by(uuid=user.id).first()
            if doctor and doctor.is_blacklisted:
                return jsonify({'error': 'Your account has been blacklisted. Contact admin.'}), 403

        # Create JWT token
        additional_claims = {'role': user.role}
        access_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims
        )

        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role
            }
        }), 200

    return jsonify({'error': 'Invalid username or password'}), 401


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    username = data.get('username', '').strip()
    password = data.get('password', '')
    name = data.get('name', '').strip()
    gender = data.get('gender')
    dob_str = data.get('dob')
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()
    address = data.get('address', '').strip() or None
    city = data.get('city', '').strip() or None
    state = data.get('state', '').strip() or None
    zipcode = data.get('zipcode', '').strip() or None
    blood_type = data.get('blood_type') or None
    allergies = data.get('allergies', '').strip() or None
    medical_summary = data.get('medical_summary', '').strip() or None

    errors = []

    # Required-field validation
    if not username:
        errors.append("Username is required.")
    elif len(username) < 3:
        errors.append("Username must be at least 3 characters long.")

    if not name:
        errors.append("Name is required.")

    if not email:
        errors.append("Email is required.")
    elif not EMAIL_RE.match(email):
        errors.append("Please provide a valid email address.")

    # Validation
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")

    dob = None
    if dob_str:
        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                errors.append("You must be at least 18 years old to register.")
        except ValueError:
            errors.append("Date of birth must be a valid date.")

    if User.query.filter_by(username=username).first():
        errors.append("Username already exists!")

    if Patient.query.filter_by(email=email).first():
        errors.append("Email already registered!")

    if errors:
        return jsonify({'errors': errors}), 400

    try:
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, role='patient')
        db.session.add(new_user)
        db.session.flush()

        new_patient = Patient(
            uuid=new_user.id,
            name=name,
            gender=gender,
            dob=dob,
            email=email,
            phone=phone,
            address=address,
            city=city,
            state=state,
            zipcode=zipcode,
            blood_type=blood_type,
            allergies=allergies,
            medical_summary=medical_summary
        )
        db.session.add(new_patient)
        db.session.commit()

        return jsonify({'message': 'Registration successful! Please login.'}), 201

    except Exception as e:
        db.session.rollback()
        logger.exception("Registration failed")
        return jsonify({'error': 'Registration failed. Please try again.'}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user_info():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    response = {
        'id': user.id,
        'username': user.username,
        'role': user.role
    }

    if user.role == 'patient':
        patient = Patient.query.filter_by(uuid=user.id).first()
        if patient:
            response['patient'] = {
                'id': patient.id,
                'name': patient.name,
                'email': patient.email,
                'phone': patient.phone,
                'gender': patient.gender,
                'dob': patient.dob.isoformat() if patient.dob else None,
                'age': patient.age,
                'address': patient.address,
                'city': patient.city,
                'state': patient.state,
                'zipcode': patient.zipcode,
                'blood_type': patient.blood_type,
                'allergies': patient.allergies,
                'medical_summary': patient.medical_summary
            }

    elif user.role == 'doctor':
        doctor = Doctor.query.filter_by(uuid=user.id).first()
        if doctor:
            response['doctor'] = {
                'id': doctor.id,
                'name': doctor.name,
                'email': doctor.email,
                'phone': doctor.phone,
                'specialization': doctor.specialization,
                'department_id': doctor.department_id,
                'is_blacklisted': doctor.is_blacklisted
            }

    elif user.role == 'admin':
        response['admin'] = {'username': user.username}

    return jsonify(response), 200
