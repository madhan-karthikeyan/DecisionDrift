# manage.py
from backend import create_app
from backend.models import db
from flask_migrate import Migrate

app = create_app()

# Initialize migration
migrate_obj = Migrate(app, db)

if __name__ == "__main__":
    # You can call Flask-Migrate commands from here if needed
    # e.g., create migration folder
    # init()
    # migrate(message="Initial migration")
    # upgrade()
    pass
