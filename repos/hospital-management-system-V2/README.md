# MediCore — Hospital Management System

A full-stack hospital management system with role-based dashboards for administrators, doctors, and patients. Built with Flask (REST API) and Vue 3 (SPA), backed by SQLite, Redis, and Celery for background jobs.

## Features

### Role-Based Access

- **Admin** — Manage doctors, patients, departments, and appointments. Dashboard with system-wide statistics.
- **Doctor** — View appointments, record diagnoses and prescriptions, manage weekly availability slots, review patient history.
- **Patient** — Search doctors by department/specialization, book appointments, view treatment history, export records to CSV, manage profile.

### Background Jobs (Celery)

- **Daily Reminders** — Email, Google Chat, and SMS notifications for patients with same-day appointments (7:00 AM IST).
- **Monthly Reports** — Auto-generated PDF reports per doctor with appointment summaries, treatment details, and diagnosis/medication breakdowns (1st of each month, 6:00 AM IST).
- **CSV Export** — Patients trigger an async export of their full treatment history. Progress is tracked in real-time via polling, and an email is sent on completion.

### Other

- JWT authentication with role-based route guards
- Redis caching with event-based invalidation
- Swagger UI at `/api/docs`
- SMTP email, Google Chat webhooks, Twilio SMS (all optional, fail gracefully)
- PDF generation via xhtml2pdf

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3, Vue Router 4, Axios, Vite 5 |
| Backend | Flask, Flask-JWT-Extended, SQLAlchemy, Flask-Migrate |
| Database | SQLite (default), supports PostgreSQL/MySQL via `DATABASE_URL` |
| Cache | Redis (DB 0) |
| Task Queue | Celery with Redis broker (DB 1) |
| PDF | xhtml2pdf |
| API Docs | Flasgger (Swagger 2.0) |

---

## Project Structure

```
hospital-management-system-V2/
├── run.py                    # Flask entry point
├── manage.py                 # Flask-Migrate CLI
├── seed_doctors.py           # Seed script (1 doctor per department)
├── requirements.txt
├── api.yaml                  # Swagger spec (needs update)
│
├── backend/
│   ├── __init__.py           # App factory (create_app)
│   ├── config.py             # All configuration
│   ├── extensions.py         # SQLAlchemy, JWT, Celery, Redis
│   ├── celery_worker.py      # Celery worker entry point
│   ├── api/
│   │   ├── auth/routes.py    # Login, register, current user
│   │   ├── admin/routes.py   # CRUD doctors/patients/departments/appointments
│   │   ├── doctor/routes.py  # Appointments, diagnosis, availability
│   │   ├── patient/routes.py # Dashboard, booking, profile, CSV export
│   │   └── public/routes.py  # Public endpoints (no auth)
│   ├── models/               # 9 SQLAlchemy models
│   ├── tasks/                # Celery tasks (email, reminders, reports, export)
│   └── utils/                # Cache, decorators, notifications
│
├── frontend/
│   ├── src/
│   │   ├── api/              # Axios instance + API modules
│   │   ├── components/       # Layout, auth forms, modals, dialogs
│   │   ├── composables/      # useDialog
│   │   ├── router/           # Vue Router with auth guards
│   │   └── views/            # Admin, Doctor, Patient dashboards
│   ├── vite.config.js        # Dev server (port 3000), proxy to Flask
│   └── dist/                 # Production build
│
├── migrations/               # Alembic migration versions
└── instance/                 # SQLite DB, seed outputs, exports, reports
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Redis server running on localhost:6379

### Backend Setup

```bash
# Create and activate virtual environment
python -m venv hms
source hms/bin/activate   # Linux/macOS
# hms\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Initialize the database
flask --app run:app db upgrade

# (Optional) Seed doctors — creates 20 doctors, one per department
python seed_doctors.py

# Start the Flask server
python run.py
```

The API will be available at `http://localhost:5000`. Swagger UI is at `http://localhost:5000/api/docs`.

A default admin account is created automatically on first run:
- **Username:** `admin`
- **Password:** `Admin@123` (override with `ADMIN_DEFAULT_PASSWORD` env var)

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The frontend will be available at `http://localhost:3000`. API requests are proxied to the Flask backend.

### Celery (Optional — for background jobs)

```bash
# Start the worker (processes tasks)
celery -A backend.celery_worker:celery worker --loglevel=info

# Start the beat scheduler (dispatches scheduled tasks)
celery -A backend.celery_worker:celery beat --loglevel=info
```

---

## API Overview

~40 endpoints across 6 blueprints. All endpoints except `/api/public/*` and `/api/auth/login|register` require a JWT Bearer token.

| Blueprint | Prefix | Auth | Description |
|-----------|--------|------|-------------|
| **auth** | `/api/auth` | No | Login, register, get current user |
| **public** | `/api/public` | No | List departments, specializations, doctors |
| **admin** | `/api/admin` | Admin | CRUD for doctors, patients, departments; appointments list; dashboard stats |
| **doctor** | `/api/doctor` | Doctor | Appointments, diagnosis, patient history, availability management |
| **patient** | `/api/patient` | Patient | Dashboard, book/cancel/reschedule appointments, search doctors, profile, CSV export |

### Patient Export Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/patient/export/treatment-history` | Trigger async CSV export (returns `task_id`, HTTP 202) |
| `GET` | `/api/patient/export/status/<task_id>` | Poll export progress (`PROGRESS`, `SUCCESS`, `FAILURE`) |
| `GET` | `/api/patient/export/download/<filename>` | Download completed CSV file |

---

## Data Models

```
User ──────── Admin (1:1)
  │
  ├───────── Doctor (1:1) ──── Department (M:1)
  │              │
  │              └──── DoctorAvailability (1:M)
  │
  └───────── Patient (1:1)
                 │
                 └──── Appointment (1:M) ──── Doctor (M:1)
                            │
                            └──── Treatment (1:1)
                                      │
                                      └──── Medication (1:M)
```

- All primary keys are UUID strings except `Medication.id` (integer autoincrement).
- Appointment statuses: `booked`, `completed`, `cancelled`, `rescheduled`.

---

## Environment Variables

All variables have sensible defaults and are optional for local development. Only `MAIL_USERNAME` and `MAIL_PASSWORD` are needed if you want email notifications to work.

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | Random | Flask secret key |
| `JWT_SECRET_KEY` | Random | JWT signing key |
| `DATABASE_URL` | `sqlite:///hospital.db` | Database connection string |
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_DB` | `0` | Redis DB for cache |
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Celery broker |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/1` | Celery result store |
| `MAIL_SERVER` | `smtp.gmail.com` | SMTP server |
| `MAIL_PORT` | `587` | SMTP port |
| `MAIL_USE_TLS` | `true` | Use STARTTLS |
| `MAIL_USERNAME` | — | SMTP username |
| `MAIL_PASSWORD` | — | SMTP password |
| `MAIL_DEFAULT_SENDER` | `noreply@hospital.local` | From address |
| `GCHAT_WEBHOOK_URL` | — | Google Chat webhook URL |
| `SMS_ACCOUNT_SID` | — | Twilio account SID |
| `SMS_AUTH_TOKEN` | — | Twilio auth token |
| `SMS_FROM_NUMBER` | — | Twilio sender number |
| `EXPORT_DIR` | `instance/exports` | CSV export directory |
| `REPORT_DIR` | `instance/reports` | PDF report directory |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:5000` | Allowed CORS origins |
| `FLASK_DEBUG` | `false` | Enable debug mode |
| `ADMIN_DEFAULT_PASSWORD` | `Admin@123` | Default admin password |

---

## Production Build

```bash
# Build the frontend
cd frontend
npm run build

# The dist/ output is served by Flask's static file handler
# Run the Flask app in production with a WSGI server:
gunicorn -w 4 -b 0.0.0.0:5000 "backend:create_app()"
```

Set `SECRET_KEY` and `JWT_SECRET_KEY` to fixed values in production (the defaults regenerate on restart, which invalidates all sessions).

---

## License

This project is for educational purposes.
