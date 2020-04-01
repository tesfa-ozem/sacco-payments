from flask import current_app as app
from gateway import db
from gateway import ma
import datetime
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)


class MpesaPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    time_stamp = db.Column(db.DateTime, default=datetime.datetime.now)
    amount = db.Column(db.String)
    phone_number = db.Column(db.String)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(128))
    odoo_app_id = db.Column(db.String(10))
    odoo_member_id = db.Column(db.String(10))
    odoo_member_number = db.Column(db.String(20))
    odoo_registered = db.Column(db.Boolean)
    odoo_member = db.Column(db.Boolean)

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=60000):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})


    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        user = User.query.get(data['id'])
        return user


class OnlineTransactionsSchema(ma.ModelSchema):
    class Meta:
        model = MpesaPayment
