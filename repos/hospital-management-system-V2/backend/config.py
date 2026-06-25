import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///hospital.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=21600)
    
    REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
    REDIS_DB = int(os.environ.get("REDIS_DB", 1))
    REDIS_CACHE_EXPIRE = 300  # 5 minutes

    # Celery
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

    # ── Email (SMTP) ─────────────────────────────────────────────────────
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ("true", "1", "yes")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@hospital.local")

    # ── Google Chat webhook ──────────────────────────────────────────────
    GCHAT_WEBHOOK_URL = os.environ.get("GCHAT_WEBHOOK_URL", "")

    # ── SMS / Twilio ─────────────────────────────────────────────────────
    SMS_ACCOUNT_SID = os.environ.get("SMS_ACCOUNT_SID", "")
    SMS_AUTH_TOKEN = os.environ.get("SMS_AUTH_TOKEN", "")
    SMS_FROM_NUMBER = os.environ.get("SMS_FROM_NUMBER", "")

    # ── File export / report directories ─────────────────────────────────
    EXPORT_DIR = os.environ.get("EXPORT_DIR", os.path.join("instance", "exports"))
    REPORT_DIR = os.environ.get("REPORT_DIR", os.path.join("instance", "reports"))