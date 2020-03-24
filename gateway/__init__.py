from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from config import Config


db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()


def create_app(config_class=Config):
    # create application instance
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)

    with app.app_context():
        db.create_all()

    from gateway.api.routes import mod as mod
    app.register_blueprint(mod)

    from gateway.dashboard.dashboard_routes import mod as mod
    app.register_blueprint(mod)

    return app


from gateway import models
