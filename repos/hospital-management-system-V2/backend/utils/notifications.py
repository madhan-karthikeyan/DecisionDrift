"""
Notification utilities for email (SMTP), Google Chat (webhook), and SMS (Twilio).

All functions fail gracefully and log errors rather than raising,
so a misconfigured channel never breaks a Celery task.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from flask import current_app

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Email (SMTP)
# ---------------------------------------------------------------------------

def send_email(to, subject, html_body, attachments=None):
    """Send an HTML email via SMTP.

    Parameters
    ----------
    to : str
        Recipient email address.
    subject : str
        Email subject line.
    html_body : str
        HTML content of the email body.
    attachments : list[tuple[str, bytes]] | None
        Optional list of (filename, file_bytes) tuples to attach.

    Returns
    -------
    bool
        True if the email was sent successfully, False otherwise.
    """
    cfg = current_app.config

    server_host = cfg.get("MAIL_SERVER", "smtp.gmail.com")
    port = cfg.get("MAIL_PORT", 587)
    use_tls = cfg.get("MAIL_USE_TLS", True)
    username = cfg.get("MAIL_USERNAME", "")
    password = cfg.get("MAIL_PASSWORD", "")
    sender = cfg.get("MAIL_DEFAULT_SENDER", "noreply@hospital.local")

    if not username or not password:
        logger.warning(
            "SMTP credentials not configured; skipping email to %s (subject: %s)",
            to, subject,
        )
        return False

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    if attachments:
        for filename, data in attachments:
            part = MIMEApplication(data, Name=filename)
            part["Content-Disposition"] = f'attachment; filename="{filename}"'
            msg.attach(part)

    try:
        with smtplib.SMTP(server_host, port, timeout=30) as smtp:
            if use_tls:
                smtp.starttls()
            smtp.login(username, password)
            smtp.sendmail(sender, [to], msg.as_string())
        logger.info("Email sent to %s (subject: %s)", to, subject)
        return True
    except Exception:
        logger.exception("Failed to send email to %s (subject: %s)", to, subject)
        return False


# ---------------------------------------------------------------------------
# Google Chat (webhook)
# ---------------------------------------------------------------------------

def send_gchat_message(text):
    """Post a text message to the configured Google Chat webhook.

    Parameters
    ----------
    text : str
        The message text to send.

    Returns
    -------
    bool
        True if the message was posted successfully, False otherwise.
    """
    import requests  # imported here to keep module importable without requests

    webhook_url = current_app.config.get("GCHAT_WEBHOOK_URL", "")

    if not webhook_url:
        logger.warning("GCHAT_WEBHOOK_URL not configured; skipping message")
        return False

    try:
        resp = requests.post(
            webhook_url,
            json={"text": text},
            timeout=10,
        )
        resp.raise_for_status()
        logger.info("Google Chat message sent successfully")
        return True
    except Exception:
        logger.exception("Failed to send Google Chat message")
        return False


# ---------------------------------------------------------------------------
# SMS (Twilio)
# ---------------------------------------------------------------------------

def send_sms(to, body):
    """Send an SMS via Twilio.

    Parameters
    ----------
    to : str
        Recipient phone number (E.164 format recommended, e.g. +1234567890).
    body : str
        SMS message body (max ~1600 chars for Twilio).

    Returns
    -------
    bool
        True if the SMS was sent successfully, False otherwise.
    """
    cfg = current_app.config

    account_sid = cfg.get("SMS_ACCOUNT_SID", "")
    auth_token = cfg.get("SMS_AUTH_TOKEN", "")
    from_number = cfg.get("SMS_FROM_NUMBER", "")

    if not all([account_sid, auth_token, from_number]):
        logger.warning(
            "Twilio SMS credentials not configured; skipping SMS to %s", to
        )
        return False

    try:
        import requests  # imported here to keep module importable without requests

        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        resp = requests.post(
            url,
            data={"To": to, "From": from_number, "Body": body},
            auth=(account_sid, auth_token),
            timeout=15,
        )
        resp.raise_for_status()
        logger.info("SMS sent to %s (sid: %s)", to, resp.json().get("sid"))
        return True
    except Exception:
        logger.exception("Failed to send SMS to %s", to)
        return False
