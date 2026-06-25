from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from celery import Celery
from celery.schedules import crontab
import redis
from backend.config import Config
import razorpay
import os

# Core extensions
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
razorpay_client = razorpay.Client(
    auth=(
        os.getenv("RAZORPAY_KEY_ID"),
        os.getenv("RAZORPAY_KEY_SECRET")
    )
)
# Redis client
redis_client = None

# Celery instance (created but not configured yet)
celery = Celery(__name__)

def init_celery(app):
    celery.conf.update(
        broker=app.config.get("CELERY_BROKER_URL", "redis://localhost:6379/1"),
        result_backend=app.config.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="Asia/Kolkata",
        enable_utc=True,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        task_soft_time_limit=300,
        task_time_limit=600,
        task_track_started=True,
        task_default_retry_delay=60,
        task_max_retries=3,
        beat_schedule={
            "daily-appointment-reminders": {
                "task": "backend.tasks.reminder_tasks.send_daily_reminders",
                "schedule": crontab(hour=7, minute=0),
            },
            "monthly-doctor-reports": {
                "task": "backend.tasks.report_tasks.generate_monthly_reports",
                "schedule": crontab(day_of_month=1, hour=6, minute=0),
            },
        },
        worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
        worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s",
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask