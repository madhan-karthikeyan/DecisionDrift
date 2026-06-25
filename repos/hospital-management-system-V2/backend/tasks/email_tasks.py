"""
Low-level Celery task for sending emails asynchronously.

This wraps the notification utility so any part of the application
can dispatch an email without blocking the request:

    from backend.tasks.email_tasks import send_email_async
    send_email_async.delay(to, subject, html_body)
"""

import logging
from backend.extensions import celery

logger = logging.getLogger(__name__)


@celery.task(
    name="backend.tasks.email_tasks.send_email_async",
    bind=True,
    max_retries=5,
    default_retry_delay=60,
    rate_limit="100/m",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def send_email_async(self, to, subject, html_body, attachments=None):
    """Send an email in a Celery worker.

    Parameters
    ----------
    to : str
        Recipient email address.
    subject : str
        Email subject line.
    html_body : str
        HTML content of the email body.
    attachments : list[list[str, str]] | None
        Optional list of [filename, base64_encoded_bytes] pairs.
        Base64 encoding is used because Celery serialises to JSON.

    Returns
    -------
    dict
        {"status": "sent"} or {"status": "failed", "error": str}.
    """
    import base64
    from backend.utils.notifications import send_email

    decoded_attachments = None
    if attachments:
        decoded_attachments = [
            (name, base64.b64decode(data)) for name, data in attachments
        ]

    try:
        ok = send_email(to, subject, html_body, attachments=decoded_attachments)
        if ok:
            return {"status": "sent", "to": to}
        # send_email already logged the warning; retry on transient failures
        raise RuntimeError(f"send_email returned False for {to}")
    except Exception as exc:
        logger.warning("Email task failed (attempt %s/%s): %s",
                        self.request.retries + 1, self.max_retries + 1, exc)
        raise self.retry(exc=exc)
