# app.py
from datetime import datetime
import os
from flask import Flask
from dotenv import load_dotenv
from extensions import db, login_manager
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialiser les extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager.init_app(app)
bcrypt = Bcrypt(app)


# Importer les routes après l'initialisation des extensions
from routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.utcnow().year}

