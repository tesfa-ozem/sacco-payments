
from app import create_app
from flask_script import Manager


app = create_app()
manager = Manager(app)

