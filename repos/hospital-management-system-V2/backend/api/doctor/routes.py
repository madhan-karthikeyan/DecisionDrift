from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta, time
from flask_jwt_extended import jwt_required
from ...models import db, Patient, Doctor, Appointment, Treatment, Medication, DoctorAvailability
from ...utils.decorators import get_current_user
import uuid

doctor_bp = Blueprint('api_doctor', __name__)


# ── GET endpoints ─────────────────────────────────────────────────────────

@doctor_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def doctor_dashboard():
    user = get_current_user()
    if not user or user.role != 'doctor':
        return jsonify({'error': 'Doctor access required'}), 403

    doctor = Doctor.query.filter_by(uuid=user.id).first()
    if not doctor:
        return jsonify({'error': 'Doctor profile not found'}), 404

    if doctor.is_blacklisted:
        return jsonify({'error': 'Your account has been blacklisted. Contact admin.'}), 403

    today = datetime.today().date()
    next_week = today + timedelta(days=7)
    appts = Appointment.query.filter_by(doctor_id=doctor.id).all()

    today_appointments = [a for a in appts if a.date == today]
    upcoming = [a for a in appts if a.date is not None and today < a.date <= next_week and a.status in {'scheduled', 'booked', 'rescheduled'}]
    completed_today = [a for a in appts if a.status == 'completed' and a.date == today]
    pending = [a for a in appts if a.status in {'scheduled', 'booked', 'rescheduled'}]

    # Count unique patients for this doctor
    total_patients = db.session.query(Patient.id).join(
        Appointment, Appointment.patient_id == Patient.id
    ).filter(Appointment.doctor_id == doctor.id).distinct().count()

    preview = [{
        'id': a.id,
        'patient_name': a.patient.name if a.patient else 'N/A',
        'date': a.date.strftime("%Y-%m-%d") if a.date else None,
        'time': a.start_time.strftime("%H:%M") if a.start_time else None,
        'status': a.status,
    } for a in sorted(upcoming, key=lambda a: (a.date or today, a.start_time or time.min))]

    result = {
        'doctor': {
            'id': doctor.id,
            'name': doctor.name,
            'specialization': doctor.specialization,
            'department': doctor.department.name if doctor.department else None
        },
        'todayAppointments': len(today_appointments),
        'totalPatients': total_patients,
        'pendingAppointments': len(pending),
        'completedToday': len(completed_today),
        'preview': preview
    }

    return jsonify(result), 200


@doctor_bp.route('/appointments', methods=['GET'])
@jwt_required()
def doctor_appointments():
    user = get_current_user()
    if not user or user.role != 'doctor':
        return jsonify({'error': 'Doctor access required'}), 403

    doctor = Doctor.query.filter_by(uuid=user.id).first()
    if not doctor:
        return jsonify({'error': 'Doctor profile not found'}), 404

    appointments = Appointment.query.filter_by(doctor_id=doctor.id).order_by(Appointment.date.desc(), Appointment.start_time.desc()).all()

    result = [{
        'id': a.id,
        'patient_name': a.patient.name if a.patient else 'N/A',
        'patient_id': a.patient.id if a.patient else None,
        'date': a.date.strftime('%Y-%m-%d') if a.date else None,
        'time_range': f"{a.start_time.strftime('%H:%M')} - {a.end_time.strftime('%H:%M')}" if a.start_time and a.end_time else None,
        'status': a.status
    } for a in appointments]

    return jsonify(result), 200


@doctor_bp.route('/patients', methods=['GET'])
@jwt_required()
def doctor_patients():
    user = get_current_user()
    if not user or user.role != 'doctor':
        return jsonify({'error': 'Doctor access required'}), 403

    doctor = Doctor.query.filter_by(uuid=user.id).first()
    if not doctor:
        return jsonify({'error': 'Doctor profile not found'}), 404

    patients = db.session.query(Patient).join(Appointment, Appointment.patient_id == Patient.id).filter(Appointment.doctor_id == doctor.id).distinct().all()

    result = [{
        'id': p.id,
        'name': p.name,
        'email': p.email,
        'phone': p.phone,
        'gender': p.gender,
        'dob': p.dob.isoformat() if p.dob else None,
        'age': p.age
    } for p in patients]

    return jsonify(result), 200


# ── Mutation endpoints (with cache invalidation + lowercase status) ───────

@doctor_bp.route('/appointments/<string:appointment_id>/complete', methods=['POST'])
@jwt_required()
def complete_appointment(appointment_id):
    user = get_current_user()
    if not user or user.role != 'doctor':
        return jsonify({'error': 'Doctor access required'}), 403

    doctor = Doctor.query.filter_by(uuid=user.id).first()
    if not doctor:
        return jsonify({'error': 'Doctor profile not found'}), 404

    appointment = db.session.get(Appointment, appointment_id)
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404

    if appointment.doctor_id != doctor.id:
        return jsonify({'error': 'Unauthorized access to this appointment'}), 403

    appointment.status = 'completed'
    db.session.commit()

    return jsonify({'success': True})


@doctor_bp.route('/appointments/<string:appointment_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_doctor_appointment(appointment_id):
    user = get_current_user()
    if not user or user.role != 'doctor':
        return jsonify({'error': 'Doctor access required'}), 403

    doctor = Doctor.query.filter_by(uuid=user.id).first()
    if not doctor:
        return jsonify({'error': 'Doctor profile not found'}), 404

    appointment = db.session.get(Appointment, appointment_id)
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404

    if appointment.doctor_id != doctor.id:
        return jsonify({'error': 'Unauthorized access to this appointment'}), 403

    appointment.status = 'cancelled'
    db.session.commit()

    return jsonify({'success': True})


# ── Diagnosis (not cached — low frequency detail views) ───────────────────

@doctor_bp.route('/appointments/<string:appointment_id>/diagnosis', methods=['GET'])
@jwt_required()
def get_diagnosis_form(appointment_id):
    user = get_current_user()
    if not user or user.role != 'doctor':
        return jsonify({'error': 'Doctor access required'}), 403

    doctor = Doctor.query.filter_by(uuid=user.id).first()
    if not doctor:
        return jsonify({'error': 'Doctor profile not found'}), 404

    appointment = db.session.get(Appointment, appointment_id)
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404

    if appointment.doctor_id != doctor.id:
        return jsonify({'error': 'Unauthorized access'}), 403

    prescription_list = []
    if appointment.treatment:
        for med in appointment.treatment.medications:
            prescription_list.append({
                "medicine": med.medicine,
                "dosage": med.dosage,
                "frequency": med.frequency,
                "duration": med.duration,
            })

    return jsonify({
        'appointment': {
            'id': appointment.id,
            'patient': {
                'id': appointment.patient.id if appointment.patient else None,
                'name': appointment.patient.name if appointment.patient else None,
                'dob': appointment.patient.dob.isoformat() if appointment.patient and appointment.patient.dob else None,
                'gender': appointment.patient.gender if appointment.patient else None,
            },
            'date': appointment.date.strftime('%Y-%m-%d') if appointment.date else None,
            'time': appointment.start_time.strftime('%H:%M') if appointment.start_time else None,
            'status': appointment.status
        },
        'diagnosis': appointment.treatment.diagnosis if appointment.treatment else None,
        'symptoms': appointment.treatment.symptoms if appointment.treatment else None,
        'severity': appointment.treatment.severity if appointment.treatment else None,
        'treatment_plan': appointment.treatment.treatment_plan if appointment.treatment else None,
        'follow_up': appointment.treatment.follow_up if appointment.treatment else None,
        'notes': appointment.treatment.notes if appointment.treatment else None,
        'prescription': prescription_list
    }), 200


@doctor_bp.route('/appointments/<string:appointment_id>/diagnosis', methods=['POST'])
@jwt_required()
def save_diagnosis(appointment_id):
    user = get_current_user()
    if not user or user.role != 'doctor':
        return jsonify({'error': 'Doctor access required'}), 403

    doctor = Doctor.query.filter_by(uuid=user.id).first()
    if not doctor:
        return jsonify({'error': 'Doctor profile not found'}), 404

    appointment = db.session.get(Appointment, appointment_id)
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404

    if appointment.doctor_id != doctor.id:
        return jsonify({'error': 'Unauthorized access'}), 403

    data = request.get_json()
    diagnosis = data.get('diagnosis')
    symptoms = data.get('symptoms')
    severity = data.get('severity')
    treatment_plan = data.get('treatment_plan')
    follow_up = data.get('follow_up')
    notes = data.get('notes')
    medicines = data.get('medicines', [])

    treatment_obj = appointment.treatment
    if not treatment_obj:
        treatment_obj = Treatment(appointment_id=appointment.id)
        db.session.add(treatment_obj)

    treatment_obj.diagnosis = diagnosis
    treatment_obj.symptoms = symptoms
    treatment_obj.severity = severity
    treatment_obj.treatment_plan = treatment_plan
    treatment_obj.follow_up = follow_up
    treatment_obj.notes = notes

    treatment_obj.medications.clear()
    for med in medicines:
        medication = Medication(
            medicine=med.get('medicine'),
            dosage=med.get('dosage'),
            frequency=med.get('frequency'),
            duration=med.get('duration')
        )
        treatment_obj.medications.append(medication)

    appointment.status = 'completed'
    db.session.commit()

    return jsonify({'message': 'Diagnosis and treatment saved successfully!'}), 200


# ── Patient history (not cached) ──────────────────────────────────────────

@doctor_bp.route('/patients/<string:patient_id>/history', methods=['GET'])
@jwt_required()
def patient_history(patient_id):
    user = get_current_user()
    if not user or user.role != 'doctor':
        return jsonify({'error': 'Doctor access required'}), 403

    doctor = Doctor.query.filter_by(uuid=user.id).first()
    if not doctor:
        return jsonify({'error': 'Doctor profile not found'}), 404

    patient = db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404

    appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.patient_id == patient.id
    ).order_by(Appointment.date.desc(), Appointment.start_time.desc()).all()

    visits = []
    diagnoses = []
    prescriptions = []

    for appt in appointments:
        visits.append({
            "date": appt.date.strftime("%Y-%m-%d") if appt.date else "",
            "time": appt.start_time.strftime("%H:%M") if appt.start_time else "",
            "type": "Consultation",
            "diagnosis": appt.treatment.diagnosis if appt.treatment else "",
            "status": appt.status or ""
        })

        if appt.treatment and appt.treatment.diagnosis:
            diagnoses.append({
                "date": appt.date.strftime("%Y-%m-%d") if appt.date else "",
                "diagnosis": appt.treatment.diagnosis,
                "severity": appt.treatment.severity or ""
            })

        if appt.treatment:
            for med in appt.treatment.medications:
                prescriptions.append({
                    "date": appt.date.strftime("%Y-%m-%d") if appt.date else "",
                    "medicine": med.medicine or "",
                    "dosage": med.dosage or "",
                    "frequency": med.frequency or "",
                    "duration": med.duration or "",
                })

    return jsonify({
        "patient_id": patient.id,
        "patient_name": patient.name,
        "patient": {
            "name": patient.name,
            "age": patient.age,
            "blood_type": patient.blood_type,
            "gender": patient.gender
        },
        "visits": visits,
        "diagnoses": diagnoses,
        "prescriptions": prescriptions,
    })


# ── Availability (not cached — mutated on same page) ─────────────────────

@doctor_bp.route('/availability', methods=['GET'])
@jwt_required()
def get_availability():
    user = get_current_user()
    if not user or user.role != 'doctor':
        return jsonify({'error': 'Doctor access required'}), 403

    doctor = Doctor.query.filter_by(uuid=user.id).first()
    if not doctor:
        return jsonify({'error': 'Doctor profile not found'}), 404

    existing_availability = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor.id,
        DoctorAvailability.date >= date.today()
    ).all()

    availability_data = []
    for a in existing_availability:
        d_label = a.date.strftime("%b %d") if isinstance(a.date, date) else str(a.date)

        availability_data.append({
            "day_of_week": a.day_of_week,
            "date_label": d_label,
            "start_time": a.start_time.strftime("%H:%M") if a.start_time else None,
            "end_time": a.end_time.strftime("%H:%M") if a.end_time else None,
            "slot_duration": a.slot_duration,
            "break_start": a.break_start.strftime("%H:%M") if a.break_start else None,
            "break_end": a.break_end.strftime("%H:%M") if a.break_end else None,
        })

    return jsonify(availability_data), 200


@doctor_bp.route('/availability', methods=['POST'])
@jwt_required()
def save_availability():
    user = get_current_user()
    if not user or user.role != 'doctor':
        return jsonify({'error': 'Doctor access required'}), 403

    doctor = Doctor.query.filter_by(uuid=user.id).first()
    if not doctor:
        return jsonify({'error': 'Doctor profile not found'}), 404

    data = request.get_json()
    today_date = date.today()
    today_index = today_date.weekday()
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor.id,
        DoctorAvailability.date >= today_date
    ).delete()

    skipped_days = []

    for i, day_name in enumerate(days_of_week):
        if not data.get(f'available_{i}'):
            continue

        start_time_str = data.get(f'start_time_{i}')
        end_time_str = data.get(f'end_time_{i}')
        slot_dur = data.get(f'slot_duration_{i}')
        break_start_str = data.get(f'break_start_{i}')
        break_end_str = data.get(f'break_end_{i}')

        def parse_time(value):
            if not value:
                return None
            try:
                return datetime.strptime(value, "%H:%M").time()
            except ValueError:
                return None

        start_time = parse_time(start_time_str)
        end_time = parse_time(end_time_str)

        if not start_time or not end_time:
            skipped_days.append(day_name)
            continue

        days_from_today = (i - today_index + 7) % 7
        target_date = today_date + timedelta(days=days_from_today)

        new_availability = DoctorAvailability(
            id=str(uuid.uuid4()),
            doctor_id=doctor.id,
            day_of_week=day_name,
            date=target_date,
            start_time=start_time,
            end_time=end_time,
            slot_duration=int(slot_dur) if slot_dur else 30,
            break_start=parse_time(break_start_str),
            break_end=parse_time(break_end_str),
        )
        db.session.add(new_availability)

    db.session.commit()
    msg = 'Availability updated successfully!'
    if skipped_days:
        msg += f' Note: {", ".join(skipped_days)} skipped due to invalid time format.'
    return jsonify({'message': msg}), 200

@doctor_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_doctor_profile():
    user = get_current_user()

    if not user or user.role != 'doctor':
        return jsonify({'error': 'Doctor access required'}), 403

    doctor = Doctor.query.filter_by(uuid=user.id).first()

    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404

    return jsonify({
        "id": doctor.id,
        "name": doctor.name,
        "email": doctor.email,
        "phone": doctor.phone,
        "specialization": doctor.specialization,
        "experience": doctor.experience,
        "department": doctor.department.name if doctor.department else None,

        # department default fee
        "department_fee": doctor.department.consultation_price if doctor.department else None,

        # doctor override fee
        "dr_consultation_fee": doctor.dr_consultation_fee,
    }), 200


@doctor_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_doctor_profile():
    user = get_current_user()

    if not user or user.role != 'doctor':
        return jsonify({'error': 'Doctor access required'}), 403

    doctor = Doctor.query.filter_by(uuid=user.id).first()

    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404

    data = request.get_json()

    doctor.name = data.get('name', doctor.name)
    doctor.phone = data.get('phone', doctor.phone)
    doctor.specialization = data.get('specialization', doctor.specialization)
    doctor.experience = data.get('experience', doctor.experience)

    # doctor override fee
    doctor.dr_consultation_fee = data.get(
        'dr_consultation_fee',
        doctor.dr_consultation_fee
    )

    db.session.commit()

    return jsonify({"message": "Profile updated successfully"})