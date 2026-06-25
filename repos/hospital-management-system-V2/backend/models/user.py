from backend.extensions import db
import uuid as uuid_lib
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.String(36), primary_key=True, unique=True, nullable=False, default=lambda: str(uuid_lib.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)  

    # relationships
    patient = db.relationship('Patient', backref='user', uselist=False)
    doctor = db.relationship('Doctor', backref='user', uselist=False)
    admin = db.relationship('Admin', backref='user', uselist=False)
