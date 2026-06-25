from backend.extensions import db
import uuid as uuid_lib
from datetime import datetime, timedelta  

class DoctorAvailability(db.Model):
    __tablename__ = "doctor_availability"

    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid_lib.uuid4()))
    doctor_id = db.Column(db.String(36),
                          db.ForeignKey('doctor.id'),
                          nullable=False,
                          index=True)
    day_of_week = db.Column(db.String(10), nullable=False)  
    date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    slot_duration = db.Column(db.Integer, nullable=False, default=30) 

    break_start = db.Column(db.Time, nullable=True)
    break_end = db.Column(db.Time, nullable=True)

    doctor = db.relationship('Doctor',
                             backref=db.backref('availabilities', lazy=True))

    def __repr__(self):
        return f"<Availability {self.doctor_id} {self.day_of_week} {self.start_time}-{self.end_time}>"

    def generate_slots(self):
        slots = []
        if not self.date or not self.start_time or not self.end_time:
            return slots

        duration = self.slot_duration or 30
        delta = timedelta(minutes=duration)

        start_dt = datetime.combine(self.date, self.start_time)
        end_dt = datetime.combine(self.date, self.end_time)

        break_start_dt = datetime.combine(self.date, self.break_start) if self.break_start else None
        break_end_dt = datetime.combine(self.date, self.break_end) if self.break_end else None

        cur = start_dt
        while cur + delta <= end_dt:
            if break_start_dt and break_end_dt and break_start_dt <= cur < break_end_dt:
                cur = break_end_dt
                continue

            slots.append(cur.time())
            cur += delta

        return slots