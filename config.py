import os
basedir = os.path.abspath(os.path.dirname(__file__))
from helper.helper_functions import generate_secret_key

class Config:
    """
    Default configurations.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or generate_secret_key()
    SSL_DISABLE = False
    # Number of messages shown on each page in pagination.
    MESSAGES_PER_PAGE = 20

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """
    Configuration for development phase.
    MongoDB must be running on same machine, or else the configuration should
    be updated accordingly
    """
    DEBUG = True
    MONGODB_DB = 'development_db'
    MONGODB_HOST = '127.0.0.1'
    MONGODB_PORT = 27017
    PRESERVE_CONTEXT_ON_EXCEPTION = False


class TestingConfig(Config):
    """
    Configuration for testing phase.
    MongoDB must be running on same machine, or else the configuration should
    be updated accordingly.
    """
    DEBUG = False
    TESTING = True
    WTF_CSRF_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    MONGODB_DB = 'testing_db'
    MONGODB_HOST = '127.0.0.1'
    MONGODB_PORT = 27017
    PRESERVE_CONTEXT_ON_EXCEPTION = False


class ProductionConfig(Config):
    """
    Configuration for production.
    MongoDB settings should be updated accordingly.
    """
    MONGODB_SETTINGS = {
        'db': 'production_db',
        'host': 'server_ip',
        'port': 27017,  # default =27017
        'username': os.environ.get('MONGODB_USERNAME') or 'username',
        'password': os.environ.get('MONGODB_PASSWORD') or 'password'
    }
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
