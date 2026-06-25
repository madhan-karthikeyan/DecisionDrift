from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
import secrets
import logging
from datetime import datetime
from flask_jwt_extended import jwt_required
from ...models import db, User, Patient, Doctor, Appointment, Department
from ...utils.decorators import get_current_user
from ...utils.cache import (
    invalidate_on_doctor_change,
    invalidate_on_department_change,
)

admin_bp = Blueprint('api_admin', __name__)
logger = logging.getLogger(__name__)


# ── GET endpoints ─────────────────────────────────────────────────────────

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def admin_dashboard():
    user = get_current_user()
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    total_doctors = Doctor.query.count()
    total_patients = Patient.query.count()
    total_appointments = Appointment.query.count()

    result = {
        'doctors': total_doctors,
        'patients': total_patients,
        'appointments': total_appointments
    }
    return jsonify(result), 200


@admin_bp.route('/departments', methods=['GET'])
@jwt_required()
def get_departments():
    user = get_current_user()
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    departments = Department.query.all()
    result = [{
        'id': d.id,
        'name': d.name,
        'description': d.description,
        'phone_number': d.phone_number,
        'email': d.email,
        'consultation_price': d.consultation_price,
        'doctor_count': len(d.doctors) if d.doctors else 0
    } for d in departments]

    return jsonify(result), 200


@admin_bp.route('/doctors', methods=['GET'])
@jwt_required()
def get_doctors():
    user = get_current_user()
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    doctors = Doctor.query.all()
    result = [{
        'id': d.id,
        'uuid': d.uuid,
        'name': d.name,
        'specialization': d.specialization,
        'email': d.email,
        'phone': d.phone,
        'department_id': d.department_id,
        'department_name': d.department.name if d.department else None,
        'is_blacklisted': d.is_blacklisted,
        'experience': d.experience,
        'dr_consultation_fee': d.dr_consultation_fee,
        'consultation_fee': d.consultation_fee
    } for d in doctors]

    return jsonify(result), 200


@admin_bp.route('/patients', methods=['GET'])
@jwt_required()
def get_patients():
    user = get_current_user()
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    patients = Patient.query.all()
    result = [{
        'id': p.id,
        'uuid': p.uuid,
        'name': p.name,
        'email': p.email,
        'phone': p.phone,
        'gender': p.gender,
        'dob': p.dob.isoformat() if p.dob else None,
        'age': p.age,
        'address': p.address,
        'city': p.city,
        'state': p.state,
        'zipcode': p.zipcode,
        'blood_type': p.blood_type,
        'allergies': p.allergies,
        'medical_summary': p.medical_summary
    } for p in patients]

    return jsonify(result), 200


@admin_bp.route('/appointments', methods=['GET'])
@jwt_required()
def get_all_appointments():
    user = get_current_user()
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    appointments_list = Appointment.query.order_by(
        Appointment.date.desc(), Appointment.start_time.desc()
    ).all()

    result = [{
        'id': a.id,
        'doctor_name': a.doctor.name if a.doctor else 'N/A',
        'patient_name': a.patient.name if a.patient else 'N/A',
        'date': a.date.strftime("%Y-%m-%d") if a.date else None,
        'time': a.start_time.strftime("%H:%M") if a.start_time else None,
        'status': a.status
    } for a in appointments_list]

    return jsonify(result), 200


# ── Single-resource GETs (not cached — low frequency) ─────────────────────

@admin_bp.route('/departments/<string:id>', methods=['GET'])
@jwt_required()
def get_department(id):
    user = get_current_user()
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    department = db.session.get(Department, id)
    if not department:
        return jsonify({'error': 'Department not found'}), 404

    return jsonify({
        'id': department.id,
        'name': department.name,
        'description': department.description,
        'phone_number': department.phone_number,
        'email': department.email,
        'consultation_price': department.consultation_price
    }), 200


@admin_bp.route('/doctors/<string:id>', methods=['GET'])
@jwt_required()
def get_doctor(id):
    user = get_current_user()
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    doctor = db.session.get(Doctor, id)
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404

    return jsonify({
        'id': doctor.id,
        'uuid': doctor.uuid,
        'name': doctor.name,
        'specialization': doctor.specialization,
        'email': doctor.email,
        'phone': doctor.phone,
        'department_id': doctor.department_id,
        'department_name': doctor.department.name if doctor.department else None,
        'is_blacklisted': doctor.is_blacklisted
    }), 200


@admin_bp.route('/patients/<string:id>', methods=['GET'])
@jwt_required()
def get_patient(id):
    user = get_current_user()
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    patient = db.session.get(Patient, id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404

    return jsonify({
        'id': patient.id,
        'uuid': patient.uuid,
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
    }), 200


# ── Mutation endpoints (with cache invalidation) ──────────────────────────

# -- Departments --

@admin_bp.route('/departments', methods=['POST'])
@jwt_required()
def create_department():
    user = get_current_user()
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    name = data.get('name', '').strip()
    phone_number = data.get('phone_number', '').strip()
    email = data.get('email', '').strip()
    description = data.get('description', '').strip()

    if not all([name, phone_number, email]):
        return jsonify({'error': 'All fields except description are required'}), 400

    if Department.query.filter_by(name=name).first():
        return jsonify({'error': 'Department already exists'}), 400

    department = Department(
        name=name,
        phone_number=phone_number,
        email=email,
        description=description
    )
    db.session.add(department)

    try:
        db.session.commit()
        invalidate_on_department_change()
        return jsonify({'message': f"Department '{name}' added successfully!"}), 201
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to create department")
        return jsonify({'error': 'Failed to create department. Please try again.'}), 500


@admin_bp.route('/departments/<string:id>', methods=['PUT'])
@jwt_required()
def update_department(id):
    user = get_current_user()
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    department = db.session.get(Department, id)
    if not department:
        return jsonify({'error': 'Department not found'}), 404

    data = request.get_json()
    department.name = data.get('name', department.name).strip()
    department.description = data.get('description', department.description)
    department.phone_number = data.get('phone_number', department.phone_number)
    department.email = data.get('email', department.email).strip()

    try:
        db.session.commit()
        invalidate_on_department_change()
        return jsonify({'message': 'Department updated successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to update department")
        return jsonify({'error': 'Failed to update department. Please try again.'}), 500


@admin_bp.route('/departments/<string:id>', methods=['DELETE'])
@jwt_required()
def delete_department(id):
    user = get_current_user()
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    department = db.session.get(Department, id)
    if not department:
        return jsonify({'error': 'Department not found'}), 404

    if department.doctors:
        return jsonify({'error': f"Cannot delete '{department.name}'. Reassign {len(department.doctors)} doctor(s) first."}), 400

    try:
        db.session.delete(department)
        db.session.commit()
        invalidate_on_department_change()
        return jsonify({'message': f"Department '{department.name}' deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to delete department")
        return jsonify({'error': 'Failed to delete department. Please try again.'}), 500


# -- Doctors --

@admin_bp.route('/doctors', methods=['POST'])
@jwt_required()
def create_doctor():
    user = get_current_user()
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    name = data.get('name', '').strip()
    specialization = data.get('specialization', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    department_id = data.get('department_id')
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not all([name, specialization, email, phone, department_id, username, password]):
        return jsonify({'error': 'All fields are required'}), 400

    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters long'}), 400

    dept = db.session.get(Department, department_id)
    if not dept:
        return jsonify({'error': 'Selected department not found'}), 400

    if Doctor.query.filter((Doctor.email == email) | (Doctor.phone == phone)).first():
        return jsonify({'error': 'Email or phone already exists for another doctor'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400

    try:
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, role='doctor')
        db.session.add(new_user)
        db.session.flush()

        doctor = Doctor(
            uuid=new_user.id,
            name=name,
            specialization=specialization,
            email=email,
            phone=phone,
            department_id=department_id
        )
        db.session.add(doctor)
        db.session.commit()

        invalidate_on_doctor_change()

        return jsonify({'message': f"Doctor '{name}' created successfully! Username: {username}"}), 201

    except Exception as exc:
        db.session.rollback()
        logger.exception("Failed to create doctor")
        return jsonify({'error': 'Failed to create doctor. Please try again.'}), 500


@admin_bp.route('/doctors/<string:id>', methods=['PUT'])
@jwt_required()
def update_doctor(id):
    user = get_current_user()
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    doctor = db.session.get(Doctor, id)
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404

    data = request.get_json()
    doctor.name = data.get('name', doctor.name).strip()
    doctor.specialization = data.get('specialization', doctor.specialization).strip()
    doctor.email = data.get('email', doctor.email).strip()
    doctor.phone = data.get('phone', doctor.phone).strip()

    new_dept_id = data.get('department_id', doctor.department_id)
    if new_dept_id != doctor.department_id:
        dept = db.session.get(Department, new_dept_id)
        if not dept:
            return jsonify({'error': 'Selected department not found'}), 400
    doctor.department_id = new_dept_id

    try:
        db.session.commit()
        invalidate_on_doctor_change()
        return jsonify({'message': f"Doctor '{doctor.name}' updated successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to update doctor")
        return jsonify({'error': 'Failed to update doctor. Please try again.'}), 500


@admin_bp.route('/doctors/<string:id>', methods=['DELETE'])
@jwt_required()
def delete_doctor(id):
    user = get_current_user()
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    doctor = db.session.get(Doctor, id)
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404

    user_acc = db.session.get(User, doctor.uuid)

    try:
        # Delete associated appointments first to avoid FK constraint errors
        Appointment.query.filter_by(doctor_id=doctor.id).delete()
        db.session.delete(doctor)
        if user_acc:
            db.session.delete(user_acc)
        db.session.commit()

        invalidate_on_doctor_change()

        return jsonify({'message': f"Doctor '{doctor.name}' and associated user account deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to delete doctor")
        return jsonify({'error': 'Failed to delete doctor. Please try again.'}), 500


@admin_bp.route('/doctors/<string:id>/blacklist', methods=['POST'])
@jwt_required()
def blacklist_doctor(id):
    user = get_current_user()
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    doctor = db.session.get(Doctor, id)
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404

    doctor.is_blacklisted = not doctor.is_blacklisted
    db.session.commit()

    invalidate_on_doctor_change()

    status = "blacklisted" if doctor.is_blacklisted else "removed from blacklist"
    return jsonify({'message': f"Doctor '{doctor.name}' has been {status}."}), 200


# -- Patients --

@admin_bp.route('/patients', methods=['POST'])
@jwt_required()
def create_patient():
    user = get_current_user()
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    dob_str = data.get('dob')

    username = email
    default_password = secrets.token_urlsafe(10)

    if not all([name, email, phone, dob_str]):
        return jsonify({'error': 'Name, Email, Phone, and DOB are required'}), 400

    if Patient.query.filter_by(email=email).first():
        return jsonify({'error': 'A patient with this email already exists'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': f"A user with username '{username}' already exists"}), 400

    try:
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        hashed_pw = generate_password_hash(default_password)
        new_user = User(username=username, password=hashed_pw, role='patient')
        db.session.add(new_user)
        db.session.flush()

        new_patient = Patient(
            uuid=new_user.id,
            name=name,
            dob=dob,
            email=email,
            phone=phone,
            gender=data.get('gender'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            zipcode=data.get('zipcode'),
            blood_type=data.get('blood_type'),
            allergies=data.get('allergies'),
            medical_summary=data.get('medical_summary')
        )
        db.session.add(new_patient)
        db.session.commit()

        return jsonify({
            'message': f"Patient '{name}' added! Username: {username}"
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to create patient")
        return jsonify({'error': 'Failed to create patient. Please try again.'}), 500


@admin_bp.route('/patients/<string:id>', methods=['PUT'])
@jwt_required()
def update_patient(id):
    user = get_current_user()
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    patient = db.session.get(Patient, id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404

    data = request.get_json()
    patient.name = data.get('name', patient.name)
    patient.gender = data.get('gender', patient.gender)
    patient.dob = datetime.strptime(data.get('dob'), '%Y-%m-%d').date() if data.get('dob') else patient.dob
    patient.email = data.get('email', patient.email)
    patient.phone = data.get('phone', patient.phone)
    patient.address = data.get('address', patient.address)
    patient.city = data.get('city', patient.city)
    patient.state = data.get('state', patient.state)
    patient.zipcode = data.get('zipcode', patient.zipcode)
    patient.blood_type = data.get('blood_type', patient.blood_type)
    patient.allergies = data.get('allergies', patient.allergies)
    patient.medical_summary = data.get('medical_summary', patient.medical_summary)

    try:
        db.session.commit()
        return jsonify({'message': f"Patient '{patient.name}' updated successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to update patient")
        return jsonify({'error': 'Failed to update patient. Please try again.'}), 500


@admin_bp.route('/patients/<string:id>', methods=['DELETE'])
@jwt_required()
def delete_patient(id):
    user = get_current_user()
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    patient = db.session.get(Patient, id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404

    user_acc = db.session.get(User, patient.uuid)

    try:
        # Delete associated appointments first to avoid FK constraint errors
        Appointment.query.filter_by(patient_id=patient.id).delete()
        db.session.delete(patient)
        if user_acc:
            db.session.delete(user_acc)
        db.session.commit()

        return jsonify({'message': f"Patient '{patient.name}' and associated user account deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to delete patient")
        return jsonify({'error': 'Failed to delete patient. Please try again.'}), 500
