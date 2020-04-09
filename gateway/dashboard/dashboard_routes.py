
from flask import Flask, jsonify, request, Blueprint, json, abort, url_for, g
from gateway.models import MpesaPayment, OnlineTransactionsSchema, User
from flask_httpauth import HTTPTokenAuth


auth = HTTPTokenAuth(scheme='Token')

mod = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@mod.route('/mpesaTransactions', methods=['GET'])
@auth.login_required
def get_transactions():
    transactions = MpesaPayment.query.order_by(MpesaPayment.id).all()
    transaction_schema = OnlineTransactionsSchema(many=True)
    resp = jsonify({'message': 'Record successfully retried',
                    "data": transaction_schema.dump(transactions),
                    'bar': get_barchart_data()})
    resp.status_code = 200
    return resp


# @mod.route('/barChartData')
def get_barchart_data():
    transactions = MpesaPayment.query.order_by(MpesaPayment.id).all()
    amount_data = []
    category = []
    listLength = len(transactions)
    count = 0
    amount = 0.0
    day = lambda t: t.strftime("%A")
    for payment in transactions:
        if payment.time_stamp.strftime("%A") == day(transactions[count].time_stamp):
            amount = amount + float(payment.amount)

            if transactions.index(payment) == listLength - 1:
                print "end"
                count = transactions.index(payment)
                amount_data.append(amount)
        else:
            print "entered"

            count = transactions.index(payment)
            amount_data.append(amount)
            amount = 0
            amount = amount + float(payment.amount)
        print amount
    return amount_data




# @auth.verify_password
# def verify_password(username, password):
#     user = User.query.filter_by(username=username).first()
#     if not user or not user.verify_password(password):
#         return False
#     g.user = user
#     return True
