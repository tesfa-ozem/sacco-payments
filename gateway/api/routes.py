from flask import jsonify, request, Blueprint, json, g, abort, url_for
import yaml
from flask_httpauth import MultiAuth, HTTPTokenAuth, HTTPBasicAuth

from gateway.dashboard.dashboard_routes import auth
from gateway.models import MpesaPayment, User
from gateway.mpesa_credentials import LipanaMpesaPpassword
from gateway import db
from gateway.odoo_methods.logic import Logic
import datetime

from gateway.saf_end_points.saf_methods import SafMethods

token_auth = HTTPTokenAuth(scheme='Bearer')
basic_auth = HTTPBasicAuth()
multi_auth = MultiAuth(basic_auth, auth)
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


@mod.route('index', methods=['POST'])
@token_auth.login_required
def index():
    return "Hello world"


@mod.route('/token')
@basic_auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})


@basic_auth.verify_password
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


@token_auth.verify_token
def verify_token(token):
    print token
    user = User.verify_auth_token(token)
    if not user:
        return False
    g.user = user
    return True


@mod.route('/getMember', methods=['POST'])
@token_auth.login_required
def get_member():
    try:
        member = logic.get_reg_status()
        return jsonify(member)
    except Exception as e:
        print(str(e))
        return jsonify(str(e))


@mod.route('/registerMember', methods=['POST'])
@token_auth.login_required
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
@token_auth.login_required
def lipa_na_mpesa_online():
    global trans_type
    global odoo_app_id
    global odoo_member_id
    global lines
    global user
    user = g.user
    status = logic.get_reg_status()
    lines = request.json['lines']
    trans_type = request.json['header']['transaction_type']
    phone_number = request.json['phone']
    if status['state'] == 'complete' and user.odoo_member is not True:
        user.odoo_member_number = status['member_id'][1]
        user.odoo_member_id = status['member_id'][0]
        user.odoo_member = True
        db.session.add(user)
        db.session.commit()
        odoo_member_id = status['member_id'][0]

    elif status['state'] != 'complete':
        odoo_app_id = user.odoo_app_id

    else:
        odoo_member_id = user.odoo_member_id
        print odoo_member_id

    response = payments.send_push(args=lines, phone_number=phone_number)
    return json.dumps(response.json(), ensure_ascii=False)


# Loan process


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
        if trans_type == 'registration':
            print user.odoo_app_id
            args = {
                'bank_code': bank_code,
                'member_application_id': user.odoo_app_id,
                'transaction_type': trans_type,
                'receipt_type': 'auto'
            }
            logic.deposit(args, lines, user)
        else:
            args = {
                'bank_code': bank_code,
                'received_from': odoo_member_id,
                'transaction_type': trans_type,
                'receipt_type': 'auto'
            }
            logic.deposit(args, lines, user, odoo_member_id)

        return request.json
    except Exception as e:
        print(str(e))
        return jsonify()


# Apply for Loan

@mod.route('/ApplyLoan', methods=['POST'])
@token_auth.login_required
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
@token_auth.login_required
def get_status():
    return jsonify(logic.get_reg_status())


# C2b Api

@mod.route('/validationResponse')
def validation_response():
    return str('success')


@mod.route('/confirmationCallback')
def confirmation_callback():
    return str('confirmation_callback')
