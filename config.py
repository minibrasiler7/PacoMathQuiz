# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')  # Remplacez 'default_secret_key' par une valeur sécurisée
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
