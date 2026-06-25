from backend.extensions import db
import uuid as uuid_lib

class Appointment(db.Model):
    __tablename__ = "appointment"

    id = db.Column(db.String(36), primary_key=True, unique=True, default=lambda: str(uuid_lib.uuid4()))
    doctor_id = db.Column(db.String(36), db.ForeignKey('doctor.id'), nullable=False, index=True)
    patient_id = db.Column(db.String(36), db.ForeignKey('patient.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='booked', index=True)  # booked / completed / cancelled / rescheduled
    reason = db.Column(db.Text, nullable=True)  # Reason for appointment

    consultation_fee = db.Column(db.Integer)

    doctor = db.relationship('Doctor', back_populates='appointments')
    patient = db.relationship('Patient', back_populates='appointments')

    treatment = db.relationship('Treatment', back_populates='appointment', uselist=False)