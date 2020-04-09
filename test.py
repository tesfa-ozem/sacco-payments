import unittest

from config import Config
from gateway import create_app, db
from gateway.models import User
from gateway.mpesa_credentials import LipanaMpesaPpassword
from gateway.odoo_methods.logic import Logic
from gateway.saf_end_points.saf_methods import SafMethods


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

    def test_url_registration(self):
        end_points = SafMethods()
        status = end_points.register_url()
        print status

    def test_push(self):
        args = [
            {
                "transaction_type": " deposits",
                "amount": 200
            },
            {
                "transaction_type": " deposits",
                "amount": 200
            },

        ]
        end_points = SafMethods()
        status = end_points.send_push(args, 254727292911)
        print status


if __name__ == '__main__':
    unittest.main(verbosity=2)
