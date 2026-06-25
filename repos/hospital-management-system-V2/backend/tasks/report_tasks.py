"""
Monthly doctor report Celery tasks.

Scheduled via Celery Beat on the 1st of every month at 6:00 AM (Asia/Kolkata).
A parent task fans out per-doctor subtasks that each generate an HTML + PDF
report summarising the previous month's appointments, treatments, and diagnoses,
then emails the PDF to the doctor and saves it to disk.
"""

import io
import logging
import os
from datetime import date, timedelta

from backend.extensions import celery

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# HTML report template
# ---------------------------------------------------------------------------

def _render_report_html(doctor_name, specialization, month_label,
                        total_appointments, completed, cancelled,
                        rescheduled, booked, treatments, diagnosis_summary,
                        medication_summary):
    """Return a full HTML document for the monthly doctor report."""

    treatment_rows = ""
    for t in treatments:
        meds = ", ".join(t["medications"]) if t["medications"] else "&mdash;"
        treatment_rows += f"""\
        <tr>
          <td>{t["date"]}</td>
          <td>{t["patient"]}</td>
          <td>{t["diagnosis"]}</td>
          <td>{t["severity"]}</td>
          <td>{t["treatment_plan"]}</td>
          <td>{meds}</td>
          <td>{t["follow_up"] or "&mdash;"}</td>
        </tr>
"""

    diagnosis_rows = ""
    for diag, count in sorted(diagnosis_summary.items(), key=lambda x: -x[1]):
        diagnosis_rows += f"        <tr><td>{diag}</td><td>{count}</td></tr>\n"

    medication_rows = ""
    for med, count in sorted(medication_summary.items(), key=lambda x: -x[1]):
        medication_rows += f"        <tr><td>{med}</td><td>{count}</td></tr>\n"

    return f"""\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: Arial, sans-serif; margin: 30px; color: #333; font-size: 12px; }}
    h1 {{ color: #2563eb; margin-bottom: 4px; }}
    h2 {{ color: #1e40af; border-bottom: 2px solid #dbeafe; padding-bottom: 4px; margin-top: 28px; }}
    .meta {{ color: #666; margin-bottom: 20px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    th, td {{ border: 1px solid #ddd; padding: 6px 8px; text-align: left; }}
    th {{ background: #2563eb; color: #fff; font-size: 11px; }}
    tr:nth-child(even) {{ background: #f9fafb; }}
    .summary-grid {{ display: flex; gap: 16px; flex-wrap: wrap; margin-top: 12px; }}
    .summary-card {{ background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 6px;
                     padding: 12px 18px; min-width: 120px; text-align: center; }}
    .summary-card .number {{ font-size: 28px; font-weight: bold; color: #2563eb; }}
    .summary-card .label {{ font-size: 11px; color: #666; }}
    .footer {{ margin-top: 40px; font-size: 10px; color: #aaa; text-align: center;
               border-top: 1px solid #eee; padding-top: 10px; }}
  </style>
</head>
<body>
  <h1>Monthly Report &mdash; Dr. {doctor_name}</h1>
  <p class="meta">{specialization} &bull; {month_label}</p>

  <h2>Appointment Summary</h2>
  <div class="summary-grid">
    <div class="summary-card"><div class="number">{total_appointments}</div><div class="label">Total</div></div>
    <div class="summary-card"><div class="number">{completed}</div><div class="label">Completed</div></div>
    <div class="summary-card"><div class="number">{cancelled}</div><div class="label">Cancelled</div></div>
    <div class="summary-card"><div class="number">{rescheduled}</div><div class="label">Rescheduled</div></div>
    <div class="summary-card"><div class="number">{booked}</div><div class="label">Booked</div></div>
  </div>

  <h2>Treatment Details</h2>
  <table>
    <thead>
      <tr>
        <th>Date</th><th>Patient</th><th>Diagnosis</th><th>Severity</th>
        <th>Treatment Plan</th><th>Medications</th><th>Follow-up</th>
      </tr>
    </thead>
    <tbody>
      {treatment_rows if treatment_rows else '<tr><td colspan="7" style="text-align:center;">No treatments recorded</td></tr>'}
    </tbody>
  </table>

  <h2>Diagnosis Summary</h2>
  <table>
    <thead><tr><th>Diagnosis</th><th>Count</th></tr></thead>
    <tbody>
      {diagnosis_rows if diagnosis_rows else '<tr><td colspan="2" style="text-align:center;">No data</td></tr>'}
    </tbody>
  </table>

  <h2>Medication Summary</h2>
  <table>
    <thead><tr><th>Medication</th><th>Times Prescribed</th></tr></thead>
    <tbody>
      {medication_rows if medication_rows else '<tr><td colspan="2" style="text-align:center;">No data</td></tr>'}
    </tbody>
  </table>

  <div class="footer">
    Hospital Management System &mdash; Auto-generated Monthly Report
  </div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Parent task: fan-out
# ---------------------------------------------------------------------------

@celery.task(
    name="backend.tasks.report_tasks.generate_monthly_reports",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def generate_monthly_reports():
    """Dispatch per-doctor report generation for the previous month.

    Returns
    -------
    dict
        {"dispatched": int} — number of subtasks dispatched.
    """
    from celery import group
    from backend.models import Doctor

    doctors = Doctor.query.filter_by(is_blacklisted=False).all()
    logger.info("Monthly reports: dispatching for %d doctors", len(doctors))

    if not doctors:
        return {"dispatched": 0}

    job = group(
        generate_doctor_monthly_report.s(doctor.id)
        for doctor in doctors
    )
    result = job.apply_async()

    return {"dispatched": len(doctors), "group_id": str(result.id)}


# ---------------------------------------------------------------------------
# Per-doctor subtask
# ---------------------------------------------------------------------------

@celery.task(
    name="backend.tasks.report_tasks.generate_doctor_monthly_report",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
)
def generate_doctor_monthly_report(doctor_id):
    """Generate and email the monthly report for a single doctor.

    Parameters
    ----------
    doctor_id : str
        The Doctor primary key (UUID string).

    Returns
    -------
    dict
        Summary including file path and email status.
    """
    from collections import Counter
    from flask import current_app
    from sqlalchemy.orm import joinedload
    from backend.models import Doctor, Appointment
    from backend.utils.notifications import send_email

    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        logger.error("Doctor %s not found; skipping report", doctor_id)
        return {"error": "doctor_not_found"}

    # Determine previous month date range
    today = date.today()
    first_of_this_month = today.replace(day=1)
    last_of_prev_month = first_of_this_month - timedelta(days=1)
    first_of_prev_month = last_of_prev_month.replace(day=1)
    month_label = first_of_prev_month.strftime("%B %Y")

    # Query all appointments for the doctor in the previous month
    appointments = (
        Appointment.query
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.date >= first_of_prev_month,
            Appointment.date <= last_of_prev_month,
        )
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.treatment),
        )
        .all()
    )

    # Aggregate stats
    total = len(appointments)
    completed = sum(1 for a in appointments if a.status == "completed")
    cancelled = sum(1 for a in appointments if a.status == "cancelled")
    rescheduled = sum(1 for a in appointments if a.status == "rescheduled")
    booked = sum(1 for a in appointments if a.status == "booked")

    # Treatment details, diagnosis & medication summaries
    treatments = []
    diagnosis_counter = Counter()
    medication_counter = Counter()

    for appt in appointments:
        treatment = appt.treatment
        if not treatment:
            continue

        patient_name = appt.patient.name if appt.patient else "Unknown"
        meds = [m.medicine for m in treatment.medications] if treatment.medications else []

        treatments.append({
            "date": appt.date.strftime("%Y-%m-%d"),
            "patient": patient_name,
            "diagnosis": treatment.diagnosis or "N/A",
            "severity": treatment.severity or "N/A",
            "treatment_plan": treatment.treatment_plan or "N/A",
            "medications": meds,
            "follow_up": treatment.follow_up,
        })

        if treatment.diagnosis:
            diagnosis_counter[treatment.diagnosis] += 1
        for med in meds:
            medication_counter[med] += 1

    # Render HTML report
    html = _render_report_html(
        doctor_name=doctor.name,
        specialization=doctor.specialization or "General",
        month_label=month_label,
        total_appointments=total,
        completed=completed,
        cancelled=cancelled,
        rescheduled=rescheduled,
        booked=booked,
        treatments=treatments,
        diagnosis_summary=dict(diagnosis_counter),
        medication_summary=dict(medication_counter),
    )

    # Convert to PDF
    pdf_bytes = _html_to_pdf(html)

    # Save to disk
    report_dir = current_app.config.get("REPORT_DIR", os.path.join("instance", "reports"))
    os.makedirs(report_dir, exist_ok=True)

    safe_name = doctor.name.replace(" ", "_").lower()
    filename = f"report_{safe_name}_{first_of_prev_month.strftime('%Y_%m')}.pdf"
    filepath = os.path.join(report_dir, filename)

    with open(filepath, "wb") as f:
        f.write(pdf_bytes)

    logger.info("Report saved: %s (%d bytes)", filepath, len(pdf_bytes))

    # Email to doctor
    email_ok = False
    if doctor.email:
        email_ok = send_email(
            to=doctor.email,
            subject=f"Monthly Report — {month_label}",
            html_body=(
                f"<p>Dear Dr. {doctor.name},</p>"
                f"<p>Please find attached your monthly report for <strong>{month_label}</strong>.</p>"
                f"<p>Total appointments: {total} | Completed: {completed} | "
                f"Cancelled: {cancelled}</p>"
                f"<p>Best regards,<br>Hospital Management System</p>"
            ),
            attachments=[(filename, pdf_bytes)],
        )

    return {
        "doctor_id": doctor_id,
        "doctor_name": doctor.name,
        "month": month_label,
        "total_appointments": total,
        "file": filepath,
        "email_sent": email_ok,
    }


# ---------------------------------------------------------------------------
# PDF helper
# ---------------------------------------------------------------------------

def _html_to_pdf(html_string):
    """Convert an HTML string to PDF bytes using xhtml2pdf.

    Falls back to raw HTML bytes if xhtml2pdf is unavailable.
    """
    try:
        from xhtml2pdf import pisa

        buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.StringIO(html_string), dest=buffer)

        if pisa_status.err:
            logger.warning("xhtml2pdf reported errors; using raw HTML fallback")
            return html_string.encode("utf-8")

        return buffer.getvalue()
    except ImportError:
        logger.warning("xhtml2pdf not installed; saving raw HTML as PDF fallback")
        return html_string.encode("utf-8")
    except Exception:
        logger.exception("PDF conversion failed; using raw HTML fallback")
        return html_string.encode("utf-8")
