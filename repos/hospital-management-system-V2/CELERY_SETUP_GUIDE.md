# Flask + Celery + Redis — Setup & Testing Guide

A complete developer guide for running the Hospital Management System's async task infrastructure.

---

## 1. Environment Setup

### 1.1 Copy the environment template

```bash
cp .env.example .env
```

Then open `.env` and fill in the values for your environment.

### 1.2 All environment variables explained

```bash
# =============================================================================
# Flask
# =============================================================================

# A random secret key used by Flask to sign session cookies.
# Generate with: python -c "import secrets; print(secrets.token_hex(64))"
SECRET_KEY=change-me-to-a-random-64-char-string-in-production

# Database connection string.
# Dev (SQLite):  sqlite:///hospital.db
# Prod (Postgres): postgresql://user:password@localhost:5432/hospital
# Prod (MySQL):   mysql+pymysql://user:password@localhost:3306/hospital
DATABASE_URL=sqlite:///hospital.db

# =============================================================================
# JWT Authentication
# =============================================================================

# Secret key for signing JWT tokens. Must be different from SECRET_KEY.
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=change-me-to-another-random-string-in-production

# =============================================================================
# Redis
# =============================================================================

REDIS_HOST=localhost
REDIS_PORT=6379
# IMPORTANT: Celery uses DB 1. Keep this consistent to avoid collisions.
#   DB 0 = your cache (application)
#   DB 1 = Celery broker + result backend
REDIS_DB=1

# =============================================================================
# Celery
# =============================================================================

# Redis DB 1 is the broker (message queue) AND result backend (task results).
# Both must use the same Redis instance and database.
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# =============================================================================
# Email (SMTP)
# =============================================================================

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password
MAIL_DEFAULT_SENDER=noreply@hospital.local

# =============================================================================
# Google Chat webhook (optional)
# =============================================================================

# Leave empty to disable Google Chat notifications.
GCHAT_WEBHOOK_URL=

# =============================================================================
# SMS / Twilio (optional)
# =============================================================================

# Leave all empty to disable SMS notifications.
SMS_ACCOUNT_SID=
SMS_AUTH_TOKEN=
SMS_FROM_NUMBER=

# =============================================================================
# File Storage
# =============================================================================

EXPORT_DIR=instance/exports
REPORT_DIR=instance/reports

# =============================================================================
# Razorpay (optional)
# =============================================================================

RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
```

---

### 1.3 How to generate a Gmail App Password

Gmail **requires** an App Password, not your regular account password.

**Steps:**

1. Enable Two-Factor Authentication (2FA) on your Google account:
   → https://myaccount.google.com/security

2. Go to App Passwords:
   → https://myaccount.google.com/apppasswords

3. Select app: **Mail**
   Select device: **Other (Custom name)** → type `HospitalManagement`

4. Google will generate a **16-character password** (with spaces), e.g.:
   `abcd efgh ijkl mnop`

5. Copy it into your `.env` as `MAIL_PASSWORD`.

**Why not use my regular password?**
Google disabled "Less Secure Apps" in May 2022. Regular passwords are rejected. App passwords are scoped, revocable, and tied to your 2FA — much safer.

---

### 1.4 Where to get Twilio credentials

1. Sign up at https://www.twilio.com/ (free trial includes $15 credit)

2. Get your **Account SID** and **Auth Token** from the Twilio Console:
   → https://console.twilio.com/?frameUrl=/console

3. Buy a phone number (or use the trial number) from:
   → https://console.twilio.com/?frameUrl=/console/phone-numbers/search

4. Set `SMS_FROM_NUMBER` to your Twilio phone number in **E.164 format**, e.g. `+12025551234`

---

### 1.5 What is a Google Chat webhook?

A webhook lets Celery post notifications directly into a Google Chat space (room).

**Steps to create one:**

1. Open Google Chat in your browser: https://chat.google.com

2. Go to the space (room) you want notifications posted to

3. Click the space name → **Integrations** → **Manage webhooks**

4. Click **Add webhook**, give it a name (e.g. "Hospital Bot"), click **Save**

5. Copy the **Webhook URL** — paste it into your `.env` as `GCHAT_WEBHOOK_URL`

**Leave it empty** if you don't need Google Chat notifications. The code handles this gracefully.

---

## 2. How to Run the System

### 2.1 Prerequisites

```bash
# Install all dependencies
pip install -r requirements.txt

# Verify Redis is installed
redis-server --version
```

### 2.2 Start Redis

```bash
# macOS (Homebrew)
brew services start redis

# Ubuntu/Debian
sudo systemctl start redis-server

# or start manually in background
redis-server --daemonize yes
```

Verify Redis is running:

```bash
redis-cli ping
# Expected: PONG
```

### 2.3 Start the Flask application

```bash
# From the project root (where run.py lives)
python run.py
# or
flask --app backend run --debug
```

You should see:

```
* Running on http://127.0.0.1:5000
```

### 2.4 Start Celery Worker

In a **new terminal window**:

```bash
celery -A backend.celery_worker.celery worker \
  --loglevel=INFO \
  --concurrency=4 \
  --pool=prefork
```

Expected output:

```
[celery@your-machine v5.x.x@0.1.x]
local -> celery@your-machine: OK
```

### 2.5 Start Celery Beat (for scheduled tasks)

In a **third terminal window** (optional — only needed for periodic tasks):

```bash
celery -A backend.celery_worker.celery beat \
  --loglevel=INFO
```

**Note:** You can also run Beat embedded inside the worker (simpler):

```bash
celery -A backend.celery_worker.celery worker \
  --loglevel=INFO \
  --concurrency=4 \
  --pool=prefork \
  --beat
```

### 2.6 Quick startup script

Save as `scripts/start.sh`:

```bash
#!/bin/bash
set -e

echo "Starting Redis..."
redis-server --daemonize yes

echo "Starting Celery worker..."
celery -A backend.celery_worker.celery worker \
  --loglevel=INFO \
  --concurrency=4 \
  --pool=prefork &

echo "Starting Celery Beat..."
celery -A backend.celery_worker.celery beat \
  --loglevel=INFO &

echo "Starting Flask app..."
cd "$(dirname "$0")" && python run.py
```

---

## 3. How to Test Celery Tasks

### 3A. Basic task test — send_email_async

```python
# Open a Python shell with the Flask app context
python -c "
from backend import create_app
from backend.tasks.email_tasks import send_email_async

app = create_app()
with app.app_context():
    result = send_email_async.delay(
        to='test@example.com',
        subject='Test Email from Celery',
        html_body='<h1>Hello!</h1><p>This is a test.</p>'
    )
    print(f'Task ID: {result.id}')
    print(f'Task state: {result.state}')
"
```

**Expected worker output:**

```
[celery@machine] backend.tasks.email_tasks.send_email_async
[celery@machine] Task accepted: ...
[celery@machine] Task succeeded: ...
```

**Check task status:**

```python
from celery.result import AsyncResult
from backend.extensions import celery

result = AsyncResult('your-task-id-here', app=celery)
print(result.state)      # PENDING / STARTED / SUCCESS / FAILURE
print(result.get())      # Get return value (blocks)
```

---

### 3B. Email test — verify it actually sends

```python
# Verify email credentials are loaded
python -c "
from backend import create_app
app = create_app()
with app.app_context():
    print('MAIL_USERNAME:', app.config.get('MAIL_USERNAME'))
    print('MAIL_PASSWORD set:', bool(app.config.get('MAIL_PASSWORD')))
    print('MAIL_SERVER:', app.config.get('MAIL_SERVER'))
    print('MAIL_PORT:', app.config.get('MAIL_PORT'))
"
```

Then trigger a task:

```python
from backend import create_app
from backend.tasks.email_tasks import send_email_async

app = create_app()
with app.app_context():
    # Use your real email to test
    task = send_email_async.delay(
        to='your-real-email@gmail.com',
        subject='Celery Test',
        html_body='<p>Did you get this?</p>'
    )
    print(f'Task: {task.id}')
```

Check your inbox. If you get a `SMTPAuthenticationError`, your App Password is wrong.

---

### 3C. Redis test — inspect Celery's data

```bash
# List all keys in Redis DB 1 (Celery's database)
redis-cli -n 1 KEYS '*'

# Watch task results in real-time
redis-cli -n 1 SUBSCRIBE celery

# Check Celery's result backend for a specific task
redis-cli -n 1 GET 'celery-task-meta-<your-task-id>'

# Check the Celery message queue (unacked messages)
redis-cli -n 1 LRANGE celery 0 -1

# Check scheduled tasks (Beat)
redis-cli -n 1 KEYS 'celerybeat*'

# Clear all Celery data (use with caution!)
redis-cli -n 1 FLUSHDB
```

---

### 3D. Failure test — observe retry behavior

```python
# Trigger a task with an invalid email to force a failure
from backend import create_app
from backend.tasks.email_tasks import send_email_async

app = create_app()
with app.app_context():
    # This will fail because MAIL_USERNAME/PASSWORD are empty in .env
    # (or use a deliberately wrong value)
    task = send_email_async.delay(
        to='nobody@example.com',
        subject='Test Failure',
        html_body='<p>Testing retries...</p>'
    )
    print(f'Task ID: {task.id}')
```

**Expected worker output:**

```
[celery@machine] Task backend.tasks.email_tasks.send_email_async[...] retry:
  'SMTP authentication error' in 60s (60/1800s).
[celery@machine] Task backend.tasks.email_tasks.send_email_async[...] retry:
  'SMTP authentication error' in 120s (120/1800s).
[celery@machine] Task backend.tasks.email_tasks.send_email_async[...] failed: ...
```

The **exponential backoff** kicks in: 60s → 120s → 240s, etc. (with jitter).

---

### 3E. Database task test — ensure Flask app context works

```python
from backend import create_app
from backend.tasks.reminder_tasks import send_daily_reminders
from backend.tasks.export_tasks import export_patient_treatment_history

app = create_app()

# Test 1: Daily reminders task (queries DB)
with app.app_context():
    result = send_daily_reminders.delay()
    print(f'Reminder task: {result.id}')

# Test 2: Export task (queries DB + writes file)
# First get a valid patient ID from your database
with app.app_context():
    from backend.models import Patient
    patient = Patient.query.first()
    if patient:
        result = export_patient_treatment_history.delay(patient.id)
        print(f'Export task: {result.id}')
        # Monitor progress
        import time
        while result.state == 'PROGRESS':
            print(f'Progress: {result.info}')
            time.sleep(2)
        print(f'Final state: {result.state}')
        print(f'Result: {result.get()}')
```

**Expected worker output:**

```
[celery@machine] Task accepted: ...
[celery@machine] Task backend.tasks.reminder_tasks.send_daily_reminders[...]: ...
  Daily reminders: found N appointments for 2026-03-21
[celery@machine] Task succeeded: ...
```

If you see `RuntimeError: Working outside of request context` or `RuntimeError: Working outside of application context` — the `ContextTask` wrapper isn't being used. With the fixes applied, this should **not** happen.

---

### 3F. Check task registration

```python
from backend import create_app
from backend.extensions import celery

app = create_app()
with app.app_context():
    registered = [name for name in celery.tasks.keys()
                 if name.startswith('backend.tasks')]
    for name in sorted(registered):
        print(name)
```

Expected output:

```
backend.tasks.email_tasks.send_email_async
backend.tasks.export_tasks.export_patient_treatment_history
backend.tasks.report_tasks.generate_doctor_monthly_report
backend.tasks.report_tasks.generate_monthly_reports
backend.tasks.reminder_tasks.send_daily_reminders
```

---

## 4. Common Errors & Fixes

### Error: `ModuleNotFoundError: No module named 'backend'`

**Cause:** Running from the wrong directory or missing `PYTHONPATH`.

**Fix:**

```bash
# Option 1: Set PYTHONPATH explicitly
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Option 2: Run from project root with -m
python -m backend.celery_worker

# Option 3: Run using celery directly from project root
cd /path/to/project-root
celery -A backend.celery_worker.celery worker --loglevel=INFO
```

---

### Error: `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379`

**Cause:** Redis is not running.

**Fix:**

```bash
# Start Redis
redis-server --daemonize yes

# Verify
redis-cli ping
# Should return: PONG
```

---

### Error: `SMTPAuthenticationError: 535-5.7.8 Username and Password not accepted`

**Cause:** Using a regular Gmail password instead of an App Password.

**Fix:** Follow the Gmail App Password steps in Section 1.3 above. Make sure:
- 2FA is enabled on your Google account
- You're using the 16-char App Password (not your real password)
- `MAIL_USERNAME` is your full Gmail address

---

### Error: `RuntimeError: Working outside of application context`

**Cause:** Tasks are accessing Flask `current_app` or SQLAlchemy models **before** the app context is set up.

**Fix:** With the fixes applied, this is handled by the `ContextTask` wrapper in `extensions.py`. If you still see it:

1. Verify `init_celery(app)` is called **before** any task imports:
   ```python
   # backend/__init__.py — correct order:
   db.init_app(app)
   migrate.init_app(app, db)
   init_celery(app)   # ← must be here
   ```

2. Always import tasks AFTER the app is created:
   ```python
   # celery_worker.py — correct order:
   app = create_app()       # app context is set up here
   init_celery(app)          # context is bound here
   celery.autodiscover_tasks(...)
   ```

---

### Error: `celery.exceptions.NotRegistered: 'backend.tasks...'`

**Cause:** Tasks were not discovered. This happens if:
- `autodiscover_tasks` is missing
- Task modules were not imported

**Fix:** With the fixes applied, `celery_worker.py` now uses:

```python
celery.autodiscover_tasks(["backend.tasks"])
```

Make sure task modules are imported. The `backend/tasks/__init__.py` handles this.

---

### Error: `Connection refused: amqp://guest:guest@localhost:5672//`

**Cause:** Celery is defaulting to RabbitMQ instead of Redis.

**Fix:** Ensure `CELERY_BROKER_URL` is set in `.env` and loaded by Flask:

```bash
# Verify it loads correctly
python -c "
from backend import create_app
app = create_app()
print('CELERY_BROKER_URL:', app.config.get('CELERY_BROKER_URL'))
"
```

Also verify your `.env` file exists in the project root and is named exactly `.env` (not `.env.local` or similar).

---

### Error: Tasks fail silently with `SUCCESS` but nothing happens

**Cause:** The task ran but caught all exceptions internally (e.g. `send_email` returns `False` but doesn't raise).

**Fix:** Check the task's return value and logs:

```python
from celery.result import AsyncResult
from backend.extensions import celery

result = AsyncResult('your-task-id', app=celery)
print('State:', result.state)
print('Info:', result.info)   # Return value or error details
```

Look at worker logs for `logger.warning` or `logger.error` messages.

---

### Error: `BROKER_URL must be set before accessing this property`

**Cause:** Celery config accessed before `init_celery(app)` was called.

**Fix:** Ensure `celery_worker.py` creates the app first:

```python
# ❌ Wrong — accesses celery before app exists
from backend.extensions import celery
app = create_app()

# ✅ Correct — app exists before celery is configured
app = create_app()
celery.autodiscover_tasks(["backend.tasks"])
```

---

## 5. Production Best Practices

### 5.1 Retries & Exponential Backoff

All tasks now use `autoretry_for`, `retry_backoff`, and `retry_jitter`:

```python
@celery.task(
    autoretry_for=(Exception,),
    retry_backoff=True,          # Exponential backoff
    retry_backoff_max=600,       # Max 10 minutes between retries
    retry_jitter=True,           # Randomize delay to prevent thundering herd
    max_retries=3,
)
def my_task():
    ...
```

**Retry schedule** with `retry_backoff=True`:
- Attempt 1 fails → retry in ~60s
- Attempt 2 fails → retry in ~120s
- Attempt 3 fails → retry in ~240s
- Attempt 4 fails → give up, mark as `FAILURE`

`retry_jitter=True` adds randomness (±25%) to prevent all workers retrying simultaneously.

---

### 5.2 Rate Limiting

The email task has a rate limit of **100 emails per minute**:

```python
@celery.task(
    rate_limit="100/m",   # 100 messages per minute
    ...
)
def send_email_async(...):
```

Change it in `backend/tasks/email_tasks.py`. Other rate limit formats:
- `"10/s"` — 10 per second
- `"200/h"` — 200 per hour
- `"50/m"` — 50 per minute

---

### 5.3 Monitoring with Flower

Flower provides a web UI for monitoring Celery workers.

**Install:**

```bash
pip install flower
```

**Run:**

```bash
celery -A backend.celery_worker.celery flower --port=5555
```

**Open:** http://localhost:5555

Features:
- Real-time worker status
- Task history and results
- Task graphs and statistics
- Rate limit monitoring

---

### 5.4 Structured Logging

Worker logs are now structured with timestamps and process info:

```
[2026-03-21 10:30:00, INFO/MainProcess] celery@machine ready
[2026-03-21 10:31:05, INFO/Worker-1] [backend.tasks.reminder_tasks.send_daily_reminders(...)] 
  Daily reminders: found 5 appointments for 2026-03-21
[2026-03-21 10:31:06, INFO/Worker-1] [backend.tasks.reminder_tasks.send_daily_reminders(...)] 
  Daily reminders complete: {'total': 5, 'email_ok': 4, 'gchat_ok': 5, 'sms_ok': 3}
[2026-03-21 10:31:06, INFO/Worker-1] Task succeeded in 1.234s
```

For production, integrate with structured logging (JSON format):

```python
import logging
import json
import sys

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "task_id"):
            log_data["task_id"] = record.task_id
        return json.dumps(log_data)
```

---

### 5.5 Idempotency

Tasks that generate files or send emails should be idempotent (safe to retry).

**Current state:** The export task can be safely retried because it re-generates the CSV each time.

**For stronger idempotency** (prevent duplicate execution):

```python
from celery import current_task

@celery.task(
    name="backend.tasks.export_tasks.export_patient_treatment_history",
    bind=True,
    idempotency_key="{task.request.id}",  # Unique per task invocation
)
def export_patient_treatment_history(self, patient_id):
    ...
```

Celery doesn't have built-in idempotency. For production, consider:
- Store a lock in Redis with `SETNX` + TTL
- Use a database flag on the patient record

---

### 5.6 Production Checklist

```
[ ] Use PostgreSQL/MySQL instead of SQLite
[ ] Set strong random SECRET_KEY and JWT_SECRET_KEY
[ ] Use Redis AUTH password or TLS for Redis
[ ] Use a real SMTP service (SendGrid, Mailgun, SES) instead of Gmail
[ ] Set task_soft_time_limit and task_time_limit appropriate for your tasks
[ ] Run multiple Celery workers across machines for redundancy
[ ] Monitor with Flower or Prometheus + Grafana
[ ] Set up alerts for failed tasks (email/Slack on FAILURE)
[ ] Use Celery's result_expires to auto-clean old results
[ ] Set up Redis persistence (AOF or RDB) to prevent message loss
[ ] Consider RabbitMQ or Amazon SQS as broker for critical production workloads
```

---

## Quick Reference: One-Command Start

```bash
# Terminal 1: Redis
redis-server --daemonize yes

# Terminal 2: Celery Worker
celery -A backend.celery_worker.celery worker --loglevel=INFO --concurrency=4

# Terminal 3: Celery Beat (optional)
celery -A backend.celery_worker.celery beat --loglevel=INFO

# Terminal 4: Flask
python run.py
```
