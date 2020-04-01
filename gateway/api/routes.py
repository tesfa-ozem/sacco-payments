import flask
import requests
from flask import jsonify, request, Blueprint, json, g, abort, url_for
from requests.auth import HTTPBasicAuth
import yaml
from gateway.dashboard.dashboard_routes import auth
from gateway.models import MpesaPayment, User
from gateway.mpesa_credentials import MpesaAccessToken, LipanaMpesaPpassword, PaymentTypes
from gateway import db
from gateway.odoo_methods.logic import Logic
import datetime

from gateway.saf_end_points.saf_methods import SafMethods

mod = Blueprint('api', __name__, url_prefix='/api')

logic = Logic()
payments = SafMethods()


@mod.route('/signUp', methods=['POST'])
def new_user():
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        abort(400)  # missing arguments
    if User.query.filter_by(username=username).first() is not None:
        abort(400)  # existing user
    user = User(username=username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'username': user.username}), 201, {
        'Location': url_for('api.get_member', id=user.id, _external=True)}


@mod.route('/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})


@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    print password
    print username_or_token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@mod.route('/api/v1/access/token')
def get_access_token():
    consumer_key = 'cHnkwYIgBbrxlgBoneczmIJFXVm0oHky'
    consumer_secret = '2nHEyWSD4VjpNh2g'
    api_URL = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    r = requests.get(api_URL, auth=HTTPBasicAuth(
        consumer_key, consumer_secret))
    mpesa_access_token = json.loads(r.text)
    validated_mpesa_access_token = mpesa_access_token['access_token']
    return jsonify(validated_mpesa_access_token)


@mod.route('/getMember', methods=['POST'])
@auth.login_required
def get_member():
    try:
        member = logic.get_reg_status()
        return jsonify(member)
    except Exception as e:
        print(str(e))
        return jsonify(str(e))


@mod.route('/registerMember', methods=['POST'])
@auth.login_required
def add_member():
    try:
        args = {
            'name': request.json['name'],
            'address': request.json['address'],
            'phone_no': request.json['phone_no'],
            'mobile_no': request.json['mobile_no'],
            'email': request.json['email'],
            'registration_date': datetime.datetime.now().strftime("%Y-%m-%d"),
            'state': 'draft',
            'date_of_birth': request.json['dob'],
            'home_address': request.json['home_address'],
            'location': request.json['location'],

        }
        return str(logic.register_member(args))
    except Exception as e:
        return str(e)


# Sacco process


@mod.route("/MakePayment", methods=['POST'])
@auth.login_required
def lipa_na_mpesa_online():
    global trans_type
    global odoo_app_id
    user = g.user
    status = logic.get_reg_status()
    if status['state'] == 'complete' and user.odoo_member is not True:
        trans_type = request.json['trans_type']
        user.odoo_member_number = status['member_id'][1]
        user.odoo_member_id = status['member_id'][0]
        user.odoo_member = True
        db.session.add(user)
        db.session.commit()
        odoo_app_id = status['member_id'][0]
        amount = request.json['amount']
        request_body = {
            "BusinessShortCode": LipanaMpesaPpassword.Business_short_code,
            "Password": LipanaMpesaPpassword.decode_password,
            "Timestamp": LipanaMpesaPpassword.lipa_time,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": 254727292911,  # replace with your phone number to get stk push
            "PartyB": LipanaMpesaPpassword.Business_short_code,
            # replace with your phone number to get stk push
            "PhoneNumber": 254727292911,
            "CallBackURL": "https://b23a417d.ngrok.io/api/v1/c2b/callback",
            "AccountReference": "Test Loans",
            "TransactionDesc": "Loans"
        }
        response = payments.send_push(args=request_body)
        return json.dumps(response.text, ensure_ascii=False)
    elif status['state'] != 'complete':
        trans_type = request.json['trans_type']
        amount = request.json['amount']
        odoo_app_id = g.user.odoo_app_id
        request_body = {
            "BusinessShortCode": LipanaMpesaPpassword.Business_short_code,
            "Password": LipanaMpesaPpassword.decode_password,
            "Timestamp": LipanaMpesaPpassword.lipa_time,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": 254727292911,  # replace with your phone number to get stk push
            "PartyB": LipanaMpesaPpassword.Business_short_code,
            # replace with your phone number to get stk push
            "PhoneNumber": 254727292911,
            "CallBackURL": "https://b23a417d.ngrok.io/api/v1/c2b/callback",
            "AccountReference": "Test Loans",
            "TransactionDesc": "Loans"
        }
        response = payments.send_push(args=request_body)
        return json.dumps(response.text, ensure_ascii=False)
    else:
        trans_type = request.json['trans_type']
        amount = request.json['amount']
        odoo_app_id = g.user.odoo_member_id
        request_body = {
            "BusinessShortCode": LipanaMpesaPpassword.Business_short_code,
            "Password": LipanaMpesaPpassword.decode_password,
            "Timestamp": LipanaMpesaPpassword.lipa_time,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": 254727292911,  # replace with your phone number to get stk push
            "PartyB": LipanaMpesaPpassword.Business_short_code,
            # replace with your phone number to get stk push
            "PhoneNumber": 254727292911,
            "CallBackURL": "https://b23a417d.ngrok.io/api/v1/c2b/callback",
            "AccountReference": "Test Loans",
            "TransactionDesc": "Loans"
        }
        response = payments.send_push(args=request_body)
        return json.dumps(response.json(), ensure_ascii=False)


# Loan process

@mod.route('/ApplyLoan')
def apply_loan():
    try:
        user_logged = g.user

        args = {
            "application_date": "2020-04-04",
            "loan_product_type": 1,
            "requested_amount": 20000.0,
            "loan_purpose": "Housing",
            "guarantor": "MEMBER0012",
            "member_no": user_logged.odoo_id
            # "loan_type": "online"
        }
        guarantor_id = request.json['guarantor']
        return str(logic.apply_loan(args, guarantor_id))
    except Exception as e:
        return str(e)


@mod.route('/LoanLimit')
def loan_limit():
    pass


@mod.route('/RepayLoan')
def repay_loan():
    pass


@mod.route('/LoanPaymentSchedule')
def loan_repayment_schedule():
    pass


# Mpesa Call back method


@mod.route('/v1/c2b/callback', methods=['POST'])
def call_back():
    try:
        payment_body = yaml.load(json.dumps(
            request.json['Body']['stkCallback']['CallbackMetadata']['Item']))
        name = payment_body[1]['Value']
        amount = str(payment_body[0]['Value'])
        phone_number = str(payment_body[3]['Value'])
        payment = MpesaPayment(name=name, amount=amount,
                               phone_number=phone_number)
        bank_code = logic.get_bank_code()
        db.session.add(payment)
        db.session.commit()
        if trans_type == 1:

            args = {
                'bank_code': bank_code,
                'member_application_id': odoo_app_id,
                'transaction_type': 'registration',
                'receipt_type': 'auto',
                'amount': 2.0,
            }
            amounts = {
                'reg_fee': 1,
                'min_share': 2
            }
            print logic.pay_reg_fee(args, amounts)
        if trans_type == 2:
            args = {
                'bank_code': bank_code,
                'received_from': odoo_app_id,
                'transaction_type': 'normal',
                'receipt_type': 'auto'
            }

            logic.deposit(args, amount)
        if trans_type == 3:
            args = {
                'bank_code': bank_code,
                'received_from': odoo_app_id,
                'transaction_type': 'normal',
                'receipt_type': 'auto'
            }

            logic.buy_share(args, amount)
        if trans_type == 4:
            print 'pay loan'
        if trans_type == 5:
            pass
        # print trans_type
        # payment_body = yaml.load(json.dumps(
        #     request.json['Body']['stkCallback']['CallbackMetadata']['Item']))
        # print yaml.load(json.dumps(
        #     request.json['Body']))
        #
        # name = payment_body[1]['Value']
        # amount = str(payment_body[0]['Value'])
        # phone_number = str(payment_body[3]['Value'])
        # payment = MpesaPayment(name=name, amount=amount,
        #                        phone_number=phone_number)

        # db.session.add(payment)
        # db.session.commit()

        # args = {
        #     'bank_code': bank_code,
        #     'member_name': 'tesfa',
        #     'member_application_id': odoo_id,
        #     'transaction_type': 'registration',
        #     'receipt_type': 'auto',
        #     'amount': amount
        # }

        # if trans_type is 'reg':
        #     logic.pay_reg_fee(args)
        # elif trans_type is 'share_contribution':
        #     logic.deposit(args)

        # logic = Logic()
        # bank_code = logic.get_bank_code()

        # print odoo_id
        # logic = Logic()
        # logic.pay_reg_fee(args)
        return request.json
    except Exception as e:
        print(str(e))
        return jsonify()


# Apply for Loan

@mod.route('/ApplyLoan',methods=['POST'])
@auth.login_required
def loan_application():
    amount = request.json['amount']
    user_logged = g.user
    args = {
        "loan_product_type": 3,
        "requested_amount": amount,
        "loan_purpose": "Housing",
        "member_no": user_logged.odoo_member_id,
        "loan_type": "online"
    }
    return str(logic.apply_loan(args))


@mod.route('/getMemberStatus')
@auth.login_required
def get_status():
    return jsonify(logic.get_reg_status())
