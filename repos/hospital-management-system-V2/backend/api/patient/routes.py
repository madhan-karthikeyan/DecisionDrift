import logging
import os
import razorpay
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from datetime import datetime, timedelta
from flask_jwt_extended import jwt_required
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from ...models import db, Patient, Doctor, Appointment, Department, Treatment, Medication, DoctorAvailability, PaymentIntent
from ...extensions import razorpay_client
from ...utils.decorators import get_current_user
from ...utils.cache import cache_get, cache_set

logger = logging.getLogger(__name__)

patient_bp = Blueprint('api_patient', __name__)

ACTIVE_STATUSES = {'scheduled', 'booked', 'rescheduled'}
CANCELLABLE_STATUSES = {'scheduled', 'booked', 'rescheduled'}


# ── GET endpoints ─────────────────────────────────────────────────────────

@patient_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def patient_dashboard():
    user = get_current_user()
    if not user or user.role != 'patient':
        return jsonify({'error': 'Patient access required'}), 403

    patient = Patient.query.filter_by(uuid=user.id).first()
    if not patient:
        return jsonify({'error': 'Patient profile not found'}), 404

    today = datetime.today().date()
    next_week = today + timedelta(days=7)
    base_filter = Appointment.patient_id == patient.id

    # Efficient count queries instead of loading all appointments into memory
    today_appointments_count = Appointment.query.filter(
        base_filter,
        Appointment.date == today
    ).count()

    pending_count = Appointment.query.filter(
        base_filter,
        Appointment.status.in_(ACTIVE_STATUSES)
    ).count()

    completed_count = Appointment.query.filter(
        base_filter,
        Appointment.status == 'completed'
    ).count()

    upcoming_appointments = Appointment.query.options(
        joinedload(Appointment.doctor)
    ).filter(
        base_filter,
        Appointment.date > today,
        Appointment.date <= next_week,
        Appointment.status.in_(ACTIVE_STATUSES)
    ).order_by(
        Appointment.date.asc(),
        Appointment.start_time.asc()
    ).all()

    appointments_preview = [{
        'id': appt.id,
        'doctor_name': appt.doctor.name if appt.doctor else 'N/A',
        'date': appt.date.strftime("%Y-%m-%d") if appt.date else None,
        'time': appt.start_time.strftime("%H:%M") if appt.start_time else None,
        'type': getattr(appt, 'type', None) or 'General',
        'status': appt.status
    } for appt in upcoming_appointments]

    result = {
        'patient': {
            'id': patient.id,
            'name': patient.name,
            'email': patient.email
        },
        'current_date': datetime.now().strftime("%A, %B %d, %Y"),
        'today_appointments_count': today_appointments_count,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'upcoming_count': len(upcoming_appointments),
        'appointments': appointments_preview
    }

    return jsonify(result), 200


@patient_bp.route('/appointments', methods=['GET'])
@jwt_required()
def patient_appointments():
    user = get_current_user()
    if not user or user.role != 'patient':
        return jsonify({'error': 'Patient access required'}), 403

    patient = Patient.query.filter_by(uuid=user.id).first()
    if not patient:
        return jsonify({'error': 'Patient profile not found'}), 404

    today = datetime.now().date()
    inactive_statuses = ['completed', 'cancelled']

    upcoming = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.date >= today,
        Appointment.status.in_(ACTIVE_STATUSES)
    ).order_by(Appointment.date.asc()).all()

    past = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        or_(
            Appointment.date < today,
            Appointment.status.in_(inactive_statuses)
        )
    ).order_by(Appointment.date.desc()).all()

    def format_appointment(a):
        treatment_obj = a.treatment
        prescription_list = []
        if treatment_obj:
            for med in treatment_obj.medications:
                prescription_list.append({
                    "medicine": med.medicine or "",
                    "dosage": med.dosage or "",
                    "frequency": med.frequency or "",
                    "duration": med.duration or "",
                })

        return {
            'id': a.id,
            'doctor_id': a.doctor_id,
            'doctor': {
                'name': a.doctor.name if a.doctor else None,
                'specialization': a.doctor.specialization if a.doctor else None,
            } if a.doctor else None,
            'date': a.date.strftime('%Y-%m-%d') if a.date else None,
            'time': a.start_time.strftime('%H:%M') if a.start_time else None,
            'status': a.status,
            'diagnosis': treatment_obj.diagnosis if treatment_obj else None,
            'prescription': prescription_list,
        }

    result = {
        'upcoming': [format_appointment(a) for a in upcoming],
        'past': [format_appointment(a) for a in past]
    }

    return jsonify(result), 200


@patient_bp.route('/doctors', methods=['GET'])
@jwt_required()
def search_doctors():
    user = get_current_user()
    if not user or user.role != 'patient':
        return jsonify({'error': 'Patient access required'}), 403

    search_query = request.args.get('search', '').strip()
    specialization_query = request.args.get('specialization', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    cache_key = (
        f"patient:doctors:search={search_query}:spec={specialization_query}"
        f":page={page}:per={per_page}"
    )

    # Try to serve from cache
    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify(cached), 200

    query = Doctor.query.options(
        db.joinedload(Doctor.department)
    ).filter(Doctor.is_blacklisted == False)

    if search_query:
        search_term = f'%{search_query}%'
        query = query.outerjoin(Department, Doctor.department_id == Department.id).filter(
            or_(
                Doctor.name.ilike(search_term),
                Doctor.specialization.ilike(search_term),
                Department.name.ilike(search_term)
            )
        )

    if specialization_query:
        query = query.filter(Doctor.specialization.ilike(f'%{specialization_query}%'))

    total = query.count()
    doctors = query.offset((page - 1) * per_page).limit(per_page).all()

    specializations_list = [
        spec[0]
        for spec in db.session.query(Doctor.specialization).filter(Doctor.is_blacklisted == False).distinct()
        if spec[0]
    ]

    result = {
        'doctors': [{
            'id': d.id,
            'name': d.name,
            'specialization': d.specialization,
            'email': d.email,
            'phone': d.phone,
            'department_name': d.department.name if d.department else None,
            'experience': d.experience,
            'dr_consultation_fee': d.dr_consultation_fee,
            'consultation_fee': d.consultation_fee
        } for d in doctors],
        'specializations': specializations_list,
        'total': total,
        'page': page,
        'per_page': per_page
    }

    cache_set(cache_key, result)
    return jsonify(result), 200



@patient_bp.route('/doctors/<string:doctor_id>/slots', methods=['GET'])
@jwt_required()
def get_doctor_slots(doctor_id):
    user = get_current_user()
    if not user or user.role != 'patient':
        return jsonify({'error': 'Patient access required'}), 403

    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'Missing date'}), 400

    try:
        appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # 1. Get availability blocks
    blocks = DoctorAvailability.query.filter_by(
        doctor_id=doctor_id,
        date=appt_date
    ).all()

    if not blocks:
        return jsonify({'slots': []}), 200

    # 2. Generate candidate slots
    candidate_slots = []
    for block in blocks:
        start = datetime.combine(appt_date, block.start_time)
        end = datetime.combine(appt_date, block.end_time)
        duration = block.slot_duration or 30

        current = start
        while current + timedelta(minutes=duration) <= end:
            # Skip break time
            if block.break_start and block.break_end:
                break_start = datetime.combine(appt_date, block.break_start)
                break_end = datetime.combine(appt_date, block.break_end)
                if break_start <= current < break_end:
                    current += timedelta(minutes=duration)
                    continue

            candidate_slots.append(current.time())
            current += timedelta(minutes=duration)

    # 3. Fetch already booked appointments
    existing_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.date == appt_date,
        Appointment.status.in_(ACTIVE_STATUSES)
    ).all()

    booked_times = {a.start_time for a in existing_appointments if a.start_time}

    # 4. Remove booked + past times
    now = datetime.now()
    valid_slots = []

    for slot_time in candidate_slots:
        slot_datetime = datetime.combine(appt_date, slot_time)

        if slot_time in booked_times:
            continue

        if slot_datetime <= now:
            continue

        valid_slots.append(slot_time.strftime('%H:%M'))

    return jsonify({'slots': sorted(valid_slots)}), 200


# ── Mutation endpoints (with cache invalidation) ──────────────────────────

@patient_bp.route('/appointments/create-payment-order', methods=['POST'])
@jwt_required()
def create_payment_order():
    user = get_current_user()
    if not user or user.role != 'patient':
        return jsonify({'error': 'Patient access required'}), 403

    patient = Patient.query.filter_by(uuid=user.id).first()
    if not patient:
        return jsonify({'error': 'Patient profile not found'}), 404

    data = request.get_json()
    doctor_id = data.get('doctor_id')
    date_str = data.get('appointment_date')
    time_str = data.get('appointment_time')
    reason = data.get('reason', '').strip()

    if not all([doctor_id, date_str, time_str]):
        return jsonify({'error': 'Doctor, date and time are required'}), 400

    doctor = db.session.get(Doctor, doctor_id)
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404

    try:
        appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        appt_time = datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        return jsonify({'error': 'Invalid date or time format'}), 400

    if datetime.combine(appt_date, appt_time) < datetime.now():
        return jsonify({'error': 'Cannot book an appointment in the past'}), 400

    # Find the availability block this slot belongs to
    block = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.date == appt_date,
        DoctorAvailability.start_time <= appt_time,
        DoctorAvailability.end_time > appt_time
    ).first()

    if not block:
        return jsonify({'error': 'Doctor is not available at this time'}), 400

    # Check if the slot falls during a break
    if block.break_start and block.break_end:
        if block.break_start <= appt_time < block.break_end:
            return jsonify({'error': 'This time falls during the doctor\'s break'}), 400

    # Check for existing bookings on this slot
    clash = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.date == appt_date,
        Appointment.start_time == appt_time,
        Appointment.status.in_(ACTIVE_STATUSES)
    ).first()

    if clash:
        return jsonify({'error': 'This slot has just been booked. Please choose another time'}), 409

    # Create PaymentIntent record
    amount = doctor.consultation_fee * 100  # Razorpay uses paise

    intent = PaymentIntent(
        patient_id=patient.id,
        doctor_id=doctor_id,
        appointment_date=appt_date,
        slot_time=appt_time.strftime('%H:%M'),
        amount=amount,
        reason=reason or None,
        status='pending'
    )

    try:
        db.session.add(intent)
        db.session.flush()  # Populate intent_uuid before Razorpay call

        # Create Razorpay order
        order = razorpay_client.order.create({
            'amount': intent.amount,
            'currency': 'INR',
            'receipt': intent.intent_uuid
        })

        intent.order_id = order['id']
        db.session.commit()

        return jsonify({
            'order_id': order['id'],
            'amount': intent.amount,
            'razorpay_key': os.getenv('RAZORPAY_KEY_ID'),
            'intent_uuid': intent.intent_uuid
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to create payment order")
        return jsonify({'error': 'Failed to create payment order. Please try again.'}), 500


@patient_bp.route('/appointments/verify-payment', methods=['POST'])
@jwt_required()
def verify_payment():
    user = get_current_user()
    if not user or user.role != 'patient':
        return jsonify({'error': 'Patient access required'}), 403

    patient = Patient.query.filter_by(uuid=user.id).first()
    if not patient:
        return jsonify({'error': 'Patient profile not found'}), 404

    data = request.get_json()
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature')

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return jsonify({'error': 'Payment verification details are required'}), 400

    # Find the PaymentIntent by order_id
    intent = PaymentIntent.query.filter_by(order_id=razorpay_order_id).first()
    if not intent:
        return jsonify({'error': 'Payment order not found'}), 404

    if intent.patient_id != patient.id:
        return jsonify({'error': 'Forbidden'}), 403

    if intent.status == 'paid':
        return jsonify({'error': 'Payment has already been processed'}), 409

    # Verify Razorpay signature
    try:
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })
    except razorpay.errors.SignatureVerificationError:
        intent.status = 'failed'
        db.session.commit()
        return jsonify({'error': 'Payment verification failed'}), 400

    # Re-check slot availability to prevent double booking
    try:
        appt_date = intent.appointment_date
        appt_time = datetime.strptime(intent.slot_time, '%H:%M').time()

        clash = Appointment.query.filter(
            Appointment.doctor_id == intent.doctor_id,
            Appointment.date == appt_date,
            Appointment.start_time == appt_time,
            Appointment.status.in_(ACTIVE_STATUSES)
        ).with_for_update().first()

        if clash:
            intent.status = 'failed'
            db.session.commit()
            return jsonify({'error': 'This slot has just been booked. Please choose another time. Payment will be refunded.'}), 409

        # Look up availability block for slot duration
        block = DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == intent.doctor_id,
            DoctorAvailability.date == appt_date,
            DoctorAvailability.start_time <= appt_time,
            DoctorAvailability.end_time > appt_time
        ).first()

        duration = (block.slot_duration or 30) if block else 30
        end_time = (datetime.combine(appt_date, appt_time) + timedelta(minutes=duration)).time()

        doctor = db.session.get(Doctor, intent.doctor_id)

        # Mark payment as paid and store payment_id
        intent.status = 'paid'
        intent.payment_id = razorpay_payment_id

        # Create the appointment
        appointment = Appointment(
            doctor_id=intent.doctor_id,
            patient_id=intent.patient_id,
            date=appt_date,
            start_time=appt_time,
            end_time=end_time,
            status='booked',
            reason=intent.reason,
            consultation_fee=doctor.consultation_fee if doctor else intent.amount // 100
        )

        db.session.add(appointment)
        db.session.commit()

        return jsonify({
            'message': 'Payment verified and appointment booked successfully!',
            'appointment_id': appointment.id
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to verify payment and book appointment")
        return jsonify({'error': 'Failed to process payment. Please try again.'}), 500


@patient_bp.route('/appointments/<string:appointment_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_patient_appointment(appointment_id):
    user = get_current_user()
    if not user or user.role != 'patient':
        return jsonify({'error': 'Patient access required'}), 403

    patient = Patient.query.filter_by(uuid=user.id).first()
    if not patient:
        return jsonify({'error': 'Patient profile not found'}), 404

    appointment = db.session.get(Appointment, appointment_id)
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404

    if appointment.patient_id != patient.id:
        return jsonify({'error': 'Forbidden'}), 403

    if appointment.status not in CANCELLABLE_STATUSES:
        return jsonify({'error': f'Cannot cancel an appointment with status \'{appointment.status}\''}), 400

    appointment.status = 'cancelled'

    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to cancel appointment")
        return jsonify({'error': 'Failed to cancel appointment. Please try again.'}), 500


@patient_bp.route('/appointments/reschedule', methods=['POST'])
@jwt_required()
def reschedule_appointment():
    user = get_current_user()
    if not user or user.role != 'patient':
        return jsonify({'error': 'Patient access required'}), 403

    patient = Patient.query.filter_by(uuid=user.id).first()
    if not patient:
        return jsonify({'error': 'Patient profile not found'}), 404

    data = request.get_json()
    appointment_id = data.get('appointment_id')
    new_date_str = data.get('new_date')
    new_time_str = data.get('new_time')

    if not all([appointment_id, new_date_str, new_time_str]):
        return jsonify({'error': 'Please select a date and time'}), 400

    appointment = db.session.get(Appointment, appointment_id)
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404

    if appointment.patient_id != patient.id:
        return jsonify({'error': 'Forbidden'}), 403

    try:
        new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
        new_start_time = datetime.strptime(new_time_str, '%H:%M').time()
    except ValueError:
        return jsonify({'error': 'Invalid date or time'}), 400

    new_start_dt = datetime.combine(new_date, new_start_time)
    if new_start_dt < datetime.now():
        return jsonify({'error': 'Cannot reschedule to a past time'}), 400

    # Validate doctor availability block exists for the new date/time
    block = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == appointment.doctor_id,
        DoctorAvailability.date == new_date,
        DoctorAvailability.start_time <= new_start_time,
        DoctorAvailability.end_time > new_start_time
    ).first()

    if not block:
        return jsonify({'error': 'Doctor is not available at this time'}), 400

    # Validate the slot does not fall during a break
    if block.break_start and block.break_end:
        if block.break_start <= new_start_time < block.break_end:
            return jsonify({'error': 'This time falls during the doctor\'s break'}), 400

    # Check for scheduling conflicts with other appointments
    clash = Appointment.query.filter(
        Appointment.doctor_id == appointment.doctor_id,
        Appointment.date == new_date,
        Appointment.start_time == new_start_time,
        Appointment.id != appointment.id,
        Appointment.status.in_(ACTIVE_STATUSES)
    ).first()

    if clash:
        return jsonify({'error': 'That slot is already booked. Please choose another time'}), 400

    duration = block.slot_duration or 30
    new_end_time = (new_start_dt + timedelta(minutes=duration)).time()

    appointment.date = new_date
    appointment.start_time = new_start_time
    appointment.end_time = new_end_time
    appointment.status = 'rescheduled'

    try:
        db.session.commit()
        return jsonify({'message': 'Appointment rescheduled successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to reschedule appointment")
        return jsonify({'error': 'Failed to reschedule appointment. Please try again.'}), 500


# ── Detail / profile endpoints (not cached) ──────────────────────────────

@patient_bp.route('/appointments/<string:appointment_id>', methods=['GET'])
@jwt_required()
def get_patient_appointment_detail(appointment_id):
    user = get_current_user()
    if not user or user.role != 'patient':
        return jsonify({'error': 'Patient access required'}), 403

    patient = Patient.query.filter_by(uuid=user.id).first()
    if not patient:
        return jsonify({'error': 'Patient profile not found'}), 404

    appointment = db.session.get(Appointment, appointment_id)
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404

    if appointment.patient_id != patient.id:
        return jsonify({'error': 'Forbidden'}), 403

    doctor = db.session.get(Doctor, appointment.doctor_id)
    treatment = Treatment.query.filter_by(appointment_id=appointment.id).first()
    medications = Medication.query.filter_by(treatment_id=treatment.id).all() if treatment else []

    result = {
        'id': appointment.id,
        'date': str(appointment.date),
        'start_time': str(appointment.start_time) if appointment.start_time else None,
        'end_time': str(appointment.end_time) if appointment.end_time else None,
        'status': appointment.status,
        'reason': appointment.reason,
        'doctor': {
            'name': doctor.name if doctor else 'N/A',
            'specialization': doctor.specialization if doctor else 'N/A',
            'department': doctor.department.name if doctor and doctor.department else 'N/A'
        },
        'treatment': None,
        'prescription': []
    }

    if treatment:
        result['treatment'] = {
            'diagnosis': treatment.diagnosis,
            'symptoms': treatment.symptoms,
            'severity': treatment.severity,
            'treatment_plan': treatment.treatment_plan,
            'notes': treatment.notes,
            'follow_up': treatment.follow_up
        }
        result['prescription'] = [
            {
                'medicine': med.medicine,
                'dosage': med.dosage,
                'frequency': med.frequency,
                'duration': med.duration
            }
            for med in medications
        ]

    return jsonify(result)


@patient_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_patient_profile():
    user = get_current_user()
    if not user or user.role != 'patient':
        return jsonify({'error': 'Patient access required'}), 403

    patient = Patient.query.filter_by(uuid=user.id).first()
    if not patient:
        return jsonify({'error': 'Patient profile not found'}), 404

    return jsonify({
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
    }), 200


@patient_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_patient_profile():
    user = get_current_user()
    if not user or user.role != 'patient':
        return jsonify({'error': 'Patient access required'}), 403

    patient = Patient.query.filter_by(uuid=user.id).first()
    if not patient:
        return jsonify({'error': 'Patient profile not found'}), 404

    data = request.get_json()
    name = data.get('name', '').strip()
    if name:
        patient.name = name

    new_email = data.get('email')
    if new_email and new_email != patient.email:
        existing = Patient.query.filter(
            Patient.email == new_email,
            Patient.id != patient.id
        ).first()
        if existing:
            return jsonify({'error': 'Email is already in use by another patient'}), 409
        patient.email = new_email

    patient.phone = data.get('phone', patient.phone)
    patient.gender = data.get('gender', patient.gender)
    patient.address = data.get('address', patient.address)
    patient.city = data.get('city', patient.city)
    patient.state = data.get('state', patient.state)
    patient.zipcode = data.get('zipcode', patient.zipcode)
    patient.blood_type = data.get('blood_type', patient.blood_type)
    patient.allergies = data.get('allergies', patient.allergies)
    patient.medical_summary = data.get('medical_summary', patient.medical_summary)

    dob_str = data.get('dob')
    if dob_str:
        try:
            patient.dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({'error': 'Invalid date format for DOB'}), 400

    try:
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to update patient profile")
        return jsonify({'error': 'Failed to update profile. Please try again.'}), 500


# ── Export endpoints ──────────────────────────────────────────────────────

@patient_bp.route('/export/treatment-history', methods=['POST'])
@jwt_required()
def export_treatment_history():
    """Trigger an async CSV export of the patient's treatment history.

    Returns 202 with {"task_id": ..., "message": ...}.
    """
    from backend.tasks.export_tasks import export_patient_treatment_history

    user = get_current_user()
    if not user or user.role != 'patient':
        return jsonify({'error': 'Patient access required'}), 403

    patient = Patient.query.filter_by(uuid=user.id).first()
    if not patient:
        return jsonify({'error': 'Patient profile not found'}), 404

    task = export_patient_treatment_history.delay(patient.id)

    return jsonify({
        'task_id': task.id,
        'message': 'Export started. You will be notified when it is ready.',
    }), 202


@patient_bp.route('/export/status/<task_id>', methods=['GET'])
@jwt_required()
def export_status(task_id):
    """Check the status of a running export task.

    Returns the Celery task state, progress metadata, and result (if done).
    """
    from backend.extensions import celery

    user = get_current_user()
    if not user or user.role != 'patient':
        return jsonify({'error': 'Patient access required'}), 403

    result = celery.AsyncResult(task_id)

    response = {'task_id': task_id, 'state': result.state}

    if result.state == 'PROGRESS':
        response['progress'] = result.info  # {"current", "total", "percent"}
    elif result.state == 'SUCCESS':
        response['result'] = result.result  # {"file", "rows"}
    elif result.state == 'FAILURE':
        response['error'] = str(result.info)

    return jsonify(response), 200


@patient_bp.route('/export/download/<filename>', methods=['GET'])
@jwt_required()
def export_download(filename):
    """Download a completed export file.

    Only allows downloading CSV files from the configured export directory.
    """
    import os

    user = get_current_user()
    if not user or user.role != 'patient':
        return jsonify({'error': 'Patient access required'}), 403

    # Basic filename sanitation — prevent path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        return jsonify({'error': 'Invalid filename'}), 400

    if not filename.endswith('.csv'):
        return jsonify({'error': 'Only CSV exports can be downloaded'}), 400

    export_dir = current_app.config.get('EXPORT_DIR', os.path.join('instance', 'exports'))
    filepath = os.path.join(export_dir, filename)

    if not os.path.isfile(filepath):
        return jsonify({'error': 'File not found'}), 404

    return send_from_directory(
        os.path.abspath(export_dir),
        filename,
        as_attachment=True,
        mimetype='text/csv',
    )
