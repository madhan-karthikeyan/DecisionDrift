from backend.extensions import db
import uuid as uuid_lib
from flask_login import UserMixin


class Doctor(UserMixin, db.Model):
    __tablename__ = "doctor"

    uuid = db.Column(db.String(36), db.ForeignKey("user.id"), unique=True, nullable=False)

    id = db.Column(
        db.String(36),
        primary_key=True,
        unique=True,
        nullable=False,
        default=lambda: str(uuid_lib.uuid4())
    )

    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)

    department_id = db.Column(
        db.String(36),
        db.ForeignKey("department.id"),
        nullable=False
    )

    dr_consultation_fee = db.Column(db.Integer, nullable=True)

    experience = db.Column(db.Integer, nullable=True, default=0)

    avatar_url = db.Column(
        db.String(255),
        nullable=True,
        default="/static/img/default_doctor.png"
    )

    is_available = db.Column(db.Boolean, nullable=False, default=True)

    is_blacklisted = db.Column(
        db.Boolean,
        nullable=False,
        server_default=db.text("0"),
        index=True
    )

    # Relationships
    department = db.relationship(
        "Department",
        back_populates="doctors",
        foreign_keys=[department_id],
        primaryjoin="Doctor.department_id == Department.id",
        lazy=True
    )

    appointments = db.relationship(
        "Appointment",
        back_populates="doctor",
        lazy=True
    )

    @property
    def consultation_fee(self):
        if self.dr_consultation_fee is not None:
            return self.dr_consultation_fee
        return self.department.consultation_price