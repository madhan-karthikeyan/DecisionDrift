from backend.extensions import db
from .medication import Medication
import uuid as uuid_lib

class Treatment(db.Model):
    __tablename__ = "treatment"

    id = db.Column(db.String(36), primary_key=True, unique=True, nullable=False, default=lambda: str(uuid_lib.uuid4()))
    appointment_id = db.Column(db.String(36), db.ForeignKey('appointment.id'), nullable=False)

    diagnosis = db.Column(db.Text, nullable=True)
    symptoms = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(50), nullable=True)
    treatment_plan = db.Column(db.Text, nullable=True)  
    follow_up = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    appointment = db.relationship('Appointment', back_populates='treatment')
    medications = db.relationship('Medication', back_populates='treatment', cascade='all, delete-orphan')
