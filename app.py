# app.py
from datetime import datetime

from flask import Flask
from extensions import db, login_manager
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre_cle_secrete'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

# Initialiser les extensions
db.init_app(app)
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

