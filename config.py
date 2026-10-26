import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'cpd-analytics-core-secret-key-2026')
    DEBUG = False
    TESTING = False
    DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
    STATIC_PATH = os.path.join(os.path.dirname(__file__), 'static')
    TEMPLATES_PATH = os.path.join(os.path.dirname(__file__), 'templates')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_by_name = {
    'dev': DevelopmentConfig,
    'prod': ProductionConfig,
    'default': DevelopmentConfig
}
