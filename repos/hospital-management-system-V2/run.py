import os
from dotenv import load_dotenv

load_dotenv()

from backend import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() in ('1', 'true'))