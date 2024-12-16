# app.py
from datetime import datetime
import os
from flask import Flask
from dotenv import load_dotenv
from extensions import db, login_manager
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')
DATABASE_URL = os.getenv('DATABASE_URL')

# Remplacer 'postgres://' par 'postgresql://' si nécessaire
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///local.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialiser les extensions
db.init_app(app)
migrate = Migrate(app, db)
socketio = SocketIO(app, async_mode='eventlet')
login_manager.init_app(app)
bcrypt = Bcrypt(app)

@app.context_processor
def inject_current_year():
    from datetime import datetime
    return {'current_year': datetime.utcnow().year}
# Importer les routes après l'initialisation des extensions
from routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Utilisez socketio.run au lieu de app.run si vous souhaitez tester les WebSockets localement
    socketio.run(app, debug=True)


