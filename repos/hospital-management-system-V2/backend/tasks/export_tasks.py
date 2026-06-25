"""
Patient treatment-history CSV export Celery task.

Triggered by the patient via API (not scheduled). Uses ``bind=True``
so the task can report progress via ``self.update_state()``.  The
result backend (Redis DB 1) stores status so the frontend can poll.
"""

import csv
import io
import logging
import os
from datetime import datetime

from backend.extensions import celery

logger = logging.getLogger(__name__)


@celery.task(
    name="backend.tasks.export_tasks.export_patient_treatment_history",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def export_patient_treatment_history(self, patient_id):
    """Export a patient's full treatment history to CSV.

    Parameters
    ----------
    patient_id : str
        The Patient primary key (UUID string).

    State updates (visible via AsyncResult)
    ----------------------------------------
    - PROGRESS  {"current": n, "total": total, "percent": int}
    - SUCCESS   {"file": filename, "rows": int}

    Returns
    -------
    dict
        {"file": filename, "rows": int}
    """
    from flask import current_app
    from sqlalchemy.orm import joinedload
    from backend.models import Patient, Appointment
    from backend.utils.notifications import send_email

    patient = Patient.query.get(patient_id)
    if not patient:
        logger.error("Patient %s not found; aborting export", patient_id)
        return {"error": "patient_not_found"}

    # Fetch all appointments with treatments (and nested medications)
    appointments = (
        Appointment.query
        .filter_by(patient_id=patient_id)
        .options(
            joinedload(Appointment.doctor),
            joinedload(Appointment.treatment),
        )
        .order_by(Appointment.date.desc())
        .all()
    )

    total = len(appointments)
    self.update_state(state="PROGRESS", meta={"current": 0, "total": total, "percent": 0})

    # Build CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Date", "Doctor", "Specialization", "Status", "Reason",
        "Diagnosis", "Symptoms", "Severity", "Treatment Plan",
        "Medications", "Follow-up", "Notes",
    ])

    rows_written = 0
    for idx, appt in enumerate(appointments, 1):
        doctor_name = appt.doctor.name if appt.doctor else "Unknown"
        specialization = appt.doctor.specialization if appt.doctor else ""

        treatment = appt.treatment
        if treatment:
            # Eagerly load medications (already joined via relationship)
            meds = "; ".join(
                f"{m.medicine} ({m.dosage}, {m.frequency}, {m.duration})"
                for m in (treatment.medications or [])
            )
            diagnosis = treatment.diagnosis or ""
            symptoms = treatment.symptoms or ""
            severity = treatment.severity or ""
            treatment_plan = treatment.treatment_plan or ""
            follow_up = treatment.follow_up or ""
            notes = treatment.notes or ""
        else:
            diagnosis = symptoms = severity = treatment_plan = ""
            meds = follow_up = notes = ""

        writer.writerow([
            appt.date.strftime("%Y-%m-%d") if appt.date else "",
            doctor_name,
            specialization,
            appt.status or "",
            appt.reason or "",
            diagnosis,
            symptoms,
            severity,
            treatment_plan,
            meds,
            follow_up,
            notes,
        ])
        rows_written += 1

        # Report progress every 10 rows or on the last row
        if idx % 10 == 0 or idx == total:
            percent = int((idx / total) * 100) if total else 100
            self.update_state(
                state="PROGRESS",
                meta={"current": idx, "total": total, "percent": percent},
            )

    # Write file to disk
    export_dir = current_app.config.get("EXPORT_DIR", os.path.join("instance", "exports"))
    os.makedirs(export_dir, exist_ok=True)

    safe_name = patient.name.replace(" ", "_").lower()
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"treatment_history_{safe_name}_{timestamp}.csv"
    filepath = os.path.join(export_dir, filename)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        f.write(output.getvalue())

    logger.info("Export saved: %s (%d rows)", filepath, rows_written)

    # Notify patient via email
    if patient.email:
        send_email(
            to=patient.email,
            subject="Your Treatment History Export is Ready",
            html_body=(
                f"<p>Dear {patient.name},</p>"
                f"<p>Your treatment history export is complete.</p>"
                f"<ul>"
                f"  <li><strong>Records:</strong> {rows_written} appointments</li>"
                f"  <li><strong>File:</strong> {filename}</li>"
                f"</ul>"
                f"<p>You can download the file from the patient portal.</p>"
                f"<p>Best regards,<br>Hospital Management System</p>"
            ),
        )

    return {"file": filename, "rows": rows_written}
