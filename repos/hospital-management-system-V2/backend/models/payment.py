from backend.extensions import db
import uuid as uuid_lib

class PaymentIntent(db.Model):
    __tablename__ = "payment"

    id = db.Column(db.Integer, primary_key=True)
    intent_uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid_lib.uuid4()))

    patient_id = db.Column(db.String(36), nullable=False)
    doctor_id = db.Column(db.String(36), nullable=False)

    appointment_date = db.Column(db.Date, nullable=False)
    slot_time = db.Column(db.String, nullable=False)

    order_id = db.Column(db.String, unique=True)
    payment_id = db.Column(db.String)

    amount = db.Column(db.Integer)  # amount in paise

    reason = db.Column(db.Text, nullable=True)

    status = db.Column(db.String, default="pending")  
    # pending | paid | failed | expired

    created_at = db.Column(db.DateTime, server_default=db.func.now())