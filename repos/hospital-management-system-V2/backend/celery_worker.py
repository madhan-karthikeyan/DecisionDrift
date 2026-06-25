from backend import create_app
from backend.extensions import celery

app = create_app()

celery.autodiscover_tasks(["backend.tasks"])