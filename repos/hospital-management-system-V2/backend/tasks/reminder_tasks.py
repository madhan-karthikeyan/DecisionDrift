"""
Daily appointment reminder Celery task.

Scheduled via Celery Beat at 7:00 AM daily (Asia/Kolkata).
Queries all appointments for today with status 'booked' or 'rescheduled',
then sends email, Google Chat, and SMS reminders for each.
"""

import logging
from datetime import date

from backend.extensions import celery

logger = logging.getLogger(__name__)

ACTIVE_STATUSES = ("booked", "rescheduled")


# ---------------------------------------------------------------------------
# HTML email template
# ---------------------------------------------------------------------------

def _render_reminder_email(patient_name, doctor_name, specialization,
                           appointment_date, start_time, reason):
    """Return an HTML string for the appointment reminder email."""
    return f"""\
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: Arial, sans-serif; background: #f4f6f8; margin: 0; padding: 0; }}
    .container {{ max-width: 560px; margin: 30px auto; background: #fff;
                  border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,.08);
                  overflow: hidden; }}
    .header {{ background: #2563eb; color: #fff; padding: 24px 28px; }}
    .header h1 {{ margin: 0; font-size: 22px; }}
    .body {{ padding: 24px 28px; color: #333; line-height: 1.6; }}
    .detail {{ margin: 8px 0; }}
    .label {{ font-weight: bold; color: #555; }}
    .footer {{ padding: 16px 28px; font-size: 12px; color: #888;
               border-top: 1px solid #eee; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Appointment Reminder</h1>
    </div>
    <div class="body">
      <p>Dear <strong>{patient_name}</strong>,</p>
      <p>This is a friendly reminder about your upcoming appointment:</p>
      <div class="detail"><span class="label">Doctor:</span> Dr. {doctor_name} ({specialization})</div>
      <div class="detail"><span class="label">Date:</span> {appointment_date}</div>
      <div class="detail"><span class="label">Time:</span> {start_time}</div>
      <div class="detail"><span class="label">Reason:</span> {reason or "General consultation"}</div>
      <p>Please arrive 10 minutes early. If you need to reschedule,
         please do so through the patient portal or call us.</p>
      <p>We look forward to seeing you!</p>
    </div>
    <div class="footer">
      Hospital Management System &mdash; Automated Reminder
    </div>
  </div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------

@celery.task(
    name="backend.tasks.reminder_tasks.send_daily_reminders",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def send_daily_reminders():
    """Send reminders for all of today's active appointments.

    Returns
    -------
    dict
        Summary of how many reminders were attempted and succeeded per channel.
    """
    from sqlalchemy.orm import joinedload
    from backend.models import Appointment, Patient, Doctor
    from backend.utils.notifications import send_email, send_gchat_message, send_sms

    today = date.today()

    appointments = (
        Appointment.query
        .filter(
            Appointment.date == today,
            Appointment.status.in_(ACTIVE_STATUSES),
        )
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.doctor),
        )
        .all()
    )

    logger.info("Daily reminders: found %d appointments for %s", len(appointments), today)

    stats = {"total": len(appointments), "email_ok": 0, "gchat_ok": 0, "sms_ok": 0}

    for appt in appointments:
        patient = appt.patient
        doctor = appt.doctor

        if not patient or not doctor:
            logger.warning("Skipping appointment %s — missing patient or doctor", appt.id)
            continue

        # ── Email ────────────────────────────────────────────────────
        if patient.email:
            html = _render_reminder_email(
                patient_name=patient.name,
                doctor_name=doctor.name,
                specialization=doctor.specialization or "General",
                appointment_date=today.strftime("%A, %B %d, %Y"),
                start_time=appt.start_time.strftime("%I:%M %p") if appt.start_time else "TBD",
                reason=appt.reason,
            )
            if send_email(patient.email,
                          f"Appointment Reminder — {today.strftime('%b %d, %Y')}",
                          html):
                stats["email_ok"] += 1

        # ── Google Chat ──────────────────────────────────────────────
        msg = (
            f"Reminder: *{patient.name}* has an appointment with "
            f"Dr. {doctor.name} ({doctor.specialization}) today at "
            f"{appt.start_time.strftime('%I:%M %p') if appt.start_time else 'TBD'}."
        )
        if send_gchat_message(msg):
            stats["gchat_ok"] += 1

        # ── SMS ──────────────────────────────────────────────────────
        if patient.phone:
            sms_body = (
                f"Hi {patient.name}, reminder: you have an appointment with "
                f"Dr. {doctor.name} today at "
                f"{appt.start_time.strftime('%I:%M %p') if appt.start_time else 'TBD'}. "
                f"Please arrive 10 min early."
            )
            if send_sms(patient.phone, sms_body):
                stats["sms_ok"] += 1

    logger.info("Daily reminders complete: %s", stats)
    return stats
