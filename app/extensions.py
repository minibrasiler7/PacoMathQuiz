# app/extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Adapter en fonction du Blueprint
login_manager.login_message_category = 'info'

bcrypt = Bcrypt()
socketio = SocketIO()
