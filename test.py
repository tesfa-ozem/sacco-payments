import unittest

from app import create_app, db
from app.models import User
from app.odoo_methods.logic import Logic
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username='susan')
        u.hash_password('cat')
        self.assertFalse(u.verify_password('dog'))
        self.assertTrue(u.verify_password('cat'))

    def test_member(self):
        logic = Logic()
        status = logic.get_reg_status()
        self.assertIsNotNone(status)


if __name__ == '__main__':
    unittest.main(verbosity=2)
