from backend.extensions import db

class Medication(db.Model):
    __tablename__ = "treatment_medication"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    treatment_id = db.Column(
        db.String(36),
        db.ForeignKey('treatment.id'),
        nullable=False
    )

    medicine = db.Column(db.String(255), nullable=False)
    dosage = db.Column(db.String(255), nullable=True)
    frequency = db.Column(db.String(255), nullable=True)
    duration = db.Column(db.String(255), nullable=True)

    treatment = db.relationship('Treatment', back_populates='medications')
