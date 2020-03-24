import functools
import flask
import requests
from flask import jsonify, request, Blueprint, json, g, abort, url_for
from requests.auth import HTTPBasicAuth
import yaml

from app.dashboard.dashboard_routes import auth
from app.models import MpesaPayment, User
from app.mpesa_credentials import MpesaAccessToken, LipanaMpesaPpassword
import xmlrpclib
from app import db
from app.odoo_methods.logic import Logic
import datetime

mod = Blueprint('api', __name__, url_prefix='/api')

HOST = 'localhost'
PORT = 8069
DB = 'test_sacco'
USER = 'admin'
PASS = '123'
ROOT = 'http://%s:%d/xmlrpc/' % (HOST, PORT)
logic = Logic()


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


@mod.route('/index', methods=['GET'])
@auth.login_required
def hello_world():
    logic.get_reg_status()
    return jsonify("Hello")


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


@mod.route("/custom_header")
def custom_header():
    resp = flask.make_response()
    resp.headers["custom-header"] = "custom"
    return resp


@mod.route("/v1/online/lipa")
@auth.login_required
def lipa_na_mpesa_online():
    global odoo_id
    odoo_id = int(g.user.odoo_id)
    access_token = MpesaAccessToken.validated_mpesa_access_token
    member_number = request.args.get('member_number')
    transaction_type = request.args.get('transaction_type')
    amount = request.args.get('amount')
    phone = request.args.get('phone_number')
    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": "Bearer %s" % access_token}

    request_body = {
        "BusinessShortCode": LipanaMpesaPpassword.Business_short_code,
        "Password": LipanaMpesaPpassword.decode_password,
        "Timestamp": LipanaMpesaPpassword.lipa_time,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": int(phone),  # replace with your phone number to get stk push
        "PartyB": LipanaMpesaPpassword.Business_short_code,
        # replace with your phone number to get stk push
        "PhoneNumber": int(phone),
        "CallBackURL": "https://ebded651.ngrok.io/api/v1/c2b/callback",
        "AccountReference": g.user.odoo_member_number,
        "TransactionDesc": "Testing stk push"
    }
    response = requests.post(api_url, json=request_body, headers=headers)
    return json.dumps(response.text, ensure_ascii=False)


@mod.route('/v1/c2b/register')
def register_urls():
    access_token = MpesaAccessToken.validated_mpesa_access_token
    api_url = "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl"
    headers = {"Authorization": "Bearer %s" % access_token}
    options = {"ShortCode": LipanaMpesaPpassword.Test_c2b_shortcode,
               "ResponseType": "Completed",
               "ConfirmationURL": "https://ebded651.ngrok.io/api/v1/c2b/confirmation",
               "ValidationURL": "https://ebded651.ngrok.io/api/v1/c2b/validation"}
    response = requests.post(api_url, json=options, headers=headers)
    return jsonify(response.text)


@mod.route('/v1/c2b/callback', methods=['POST'])
def call_back():
    trans_type = ''
    bank_code = logic.get_bank_code()
    try:
        global payment_body
        payment_body = yaml.load(json.dumps(
            request.json['Body']['stkCallback']['CallbackMetadata']['Item']))
        print yaml.load(json.dumps(
            request.json['Body']['stkCallback']['CallbackMetadata']['Item']))

        name = payment_body[1]['Value']
        amount = str(payment_body[0]['Value'])
        phone_number = str(payment_body[3]['Value'])
        payment = MpesaPayment(name=name, amount=amount,
                               phone_number=phone_number)
        db.session.add(payment)
        db.session.commit()

        args = {
            'bank_code': bank_code,
            'member_name': 'tesfa',
            'member_application_id': odoo_id,
            'transaction_type': 'registration',
            'receipt_type': 'auto',
            'amount': amount
        }

        if trans_type is 'reg':
            logic.pay_reg_fee(args)
        elif trans_type is 'share_contribution':
            logic.deposit(args)

        # logic = Logic()
        # bank_code = logic.get_bank_code()

        # print odoo_id
        # logic = Logic()
        # logic.pay_reg_fee(args)
        return request.json
    except Exception as e:
        print(str(e))
        return jsonify()


@mod.route('/getMember')
@auth.login_required
def get_member():
    try:
        uid = xmlrpclib.ServerProxy(ROOT + 'common').login(DB, USER, PASS)
        print "Logged in as %s (uid:%d)" % (USER, uid)

        call = functools.partial(
            xmlrpclib.ServerProxy(ROOT + 'object').execute,
            DB, uid, PASS)

        sessions = \
            call('sacco.member', 'search_read', [('no', '=', '%s' % (request.args.get('memberNo')))],
                 ['id', 'name', 'no'])[0]

        return jsonify(sessions)
    except Exception as e:
        print(str(e))
        return jsonify(str(e))


@mod.route('/paymentsToday')
def get_payments():
    pass


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


@mod.route('/applyLoan', methods=['POST'])
@auth.login_required
def apply_for_loan():
    try:
        user_logged = g.user
        args = {
            "application_date": request.json['application_date'],
            "loan_product_type": request.json['loan_product_type'],
            "requested_amount": request.json['requested_amount'],
            "loan_purpose": request.json['loan_purpose'],
            "member_no": user_logged.odoo_id
        }
        return str(logic.apply_loan(args))
    except Exception as e:
        return str(e)


@mod.route('/odoo/callback',methods=['POST'])
def disburse_loan():
    access_token = MpesaAccessToken.validated_mpesa_access_token
    api_url = "https://sandbox.safaricom.co.ke/mpesa/b2c/v1/paymentrequest"
    headers = { "Authorization": "Bearer %s" % access_token }
    request = {
    "InitiatorName": "tesfaromano",
    "SecurityCredential":"Safaricom3081# ",
    "CommandID": "BusinessPayment",
    "Amount": 1,
    "PartyA": LipanaMpesaPpassword.Test_c2b_shortcode,
    "PartyB": 254727222784,
    "Remarks": " remaks",
    "QueueTimeOutURL": "https://a55b330a.ngrok.io/api/your_timeout_url",
    "ResultURL": "https://a55b330a.ngrok.io/api/c2b/result",
    "Occasion": "test "
    }
  
    response = requests.post(api_url, json = request, headers=headers)
    return json.dumps(response.text, ensure_ascii=False)

@mod.route('/c2b/result', methods=['POST'])
def b2c_result():
    print request.json['Result']
    return("hello")

@mod.route('/your_timeout_url', methods=['POST'])
def b2c_timout():
    print request.json['Result']
    return("timed out")
