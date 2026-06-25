from backend.extensions import db
import uuid as uuid_lib

class Admin(db.Model):
    __tablename__ = "admin"

    uuid = db.Column(db.String(36), db.ForeignKey('user.id'), unique=True, nullable=False)
    id = db.Column(db.String(36), primary_key=True, unique=True, nullable=False, default=lambda: str(uuid_lib.uuid4()))
    name = db.Column(db.String(100), nullable=False)
