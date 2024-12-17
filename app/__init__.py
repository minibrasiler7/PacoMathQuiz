# app/__init__.py
from flask import Flask
from flask_socketio import SocketIO
from .extensions import db, login_manager
from .models import User  # Importer les modèles ici
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv()

socketio = SocketIO()

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///local.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialisation des extensions
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, async_mode='eventlet')
    migrate = Migrate(app, db)

    # Enregistrement des Blueprints
    from .routes import main, auth
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')

    # Définir le loader utilisateur après que les modèles sont importés
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
