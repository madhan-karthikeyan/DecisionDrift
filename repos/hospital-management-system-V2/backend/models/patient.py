from backend.extensions import db
import uuid as uuid_lib
from datetime import date  

class Patient(db.Model):
    __tablename__ = "patient"

    id = db.Column(db.String(36), primary_key=True, unique=True, nullable=False, default=lambda: str(uuid_lib.uuid4()))
    uuid = db.Column(db.String(36), db.ForeignKey('user.id'), unique=True, nullable=False)

    name = db.Column(db.String(100), nullable=False, default="Unnamed Patient")
    gender = db.Column(db.String(10))
    dob = db.Column(db.Date) 

    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    zipcode = db.Column(db.String(20))

    blood_type = db.Column(db.String(5))
    allergies = db.Column(db.Text)
    medical_summary = db.Column(db.Text)

    avatar_url = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)

    appointments = db.relationship('Appointment', back_populates='patient', lazy=True)

    @property
    def age(self):
        """Calculates the patient's age from their date of birth."""
        if not self.dob:
            return None
        today = date.today()
        # Calculate age
        years = today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
        return years

    def full_name(self):
        """If you ever want to split stored name into first/last dynamically."""
        parts = self.name.split(" ", 1)
        first = parts[0]
        last = parts[1] if len(parts) > 1 else ""
        return f"{first} {last}".strip()