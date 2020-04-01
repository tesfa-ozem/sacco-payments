import os

basedir = os.path.abspath(os.path.dirname(__file__))


# load_dotenv(os.path.join(basedir, '.env'))


class Config:
    ADMINS = ['your-email@example.com']
    PROJECT_HOME = os.path.dirname(os.path.realpath(__file__))
    UPLOAD_FOLDER = '{}/uploads/'.format(PROJECT_HOME)
    SECRET_KEY = 'a - really - long - and -unique - key - that - nobody - knows'
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    JSON_AS_ASCII = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


# class DevelopementConfig(BaseConfig):
#     DEBUG = True
#     SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
#                               'sqlite:///' + os.path.join(basedir, 'app.db')
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#
#
# class TestingConfig(BaseConfig):
#     DEBUG = True
#     SQLALCHEMY_DATABASE_URI = os.environ.get('TESTING_DATABASE_URI') or \
#                               'mysql+pymysql://root:pass@localhost/flask_app_db'
#
#
# class ProductionConfig(BaseConfig):
#     DEBUG = False
#     SQLALCHEMY_DATABASE_URI = os.environ.get('PRODUCTION_DATABASE_URI') or \
#                               'mysql+pymysql://root:pass@localhost/flask_app_db'
