from backend.extensions import db
import uuid as uuid_lib

class Department(db.Model):
    __tablename__ = "department"

    id = db.Column(db.String(36), primary_key=True, unique=True, nullable=False,
                   default=lambda: str(uuid_lib.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False)

    description = db.Column(db.Text, nullable=True)
    phone_number = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

    consultation_price = db.Column(db.Integer, nullable=False, default=500, server_default="500")
    
    doctors = db.relationship(
        "Doctor",
        back_populates="department",
        foreign_keys="Doctor.department_id",
        lazy=True
    )
