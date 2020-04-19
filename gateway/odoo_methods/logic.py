import functools
import xmlrpclib

from flask import request, g, jsonify
import sys

var = sys.version

HOST = '127.0.0.1'
PORT = 8069
DB = 'test_sacco'
USER = 'admin'
PASS = '123'
ROOT = 'http://%s:%d/xmlrpc/' % (HOST, PORT)


class Logic:

    def __init__(self):

        self.common = xmlrpclib.ServerProxy(ROOT + 'common')
        self.version = self.common.version()
        self.uid = self.common.authenticate(DB, USER, PASS, {})
        self.models_class = xmlrpclib.ServerProxy(ROOT + 'object')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None or exc_value is None or traceback is not None:
            return exc_value

    def register_member(self, args):
        try:
            member_id = self.models_class.execute_kw(
                DB, self.uid, PASS, 'sacco.member.application', 'create', [args])
            self.models_class.exec_workflow(
                DB, self.uid, PASS, 'sacco.member.application', 'send_for_payment', member_id)
            return member_id
        except Exception as e:
            return str(e)

    def update_member(self, args):
        user_logged = g.user
        if user_logged.odoo_registered is not True:
            member = self.search_member()

            self.models_class.execute_kw(DB, self.uid, PASS, 'sacco.member.application', 'write',
                                         [[member['id']], args])
            self.models_class.exec_workflow(
                DB, self.uid, PASS, 'sacco.member.application', 'send_for_payment', member['id'])
            return "Updated"

    def search_member(self):
        try:
            user = g.user

            if user.odoo_registered:
                member = self.models_class.execute_kw(DB, self.uid, PASS, 'sacco.member', 'search_read',
                                                      [[['id', '=', user.odoo_member_id]]])[0]
                return member
            else:
                print "not here"
                member = self.models_class.execute_kw(DB, self.uid, PASS, 'sacco.member.application', 'search_read',
                                                      [[['id', '=', user.odoo_app_id]]])[0]

                return member
        except Exception as e:
            return str(e)

    # TODO: add  script for multiple guarantors
    def apply_loan(self, args):
        user_logged = g.user
        loan_id = self.models_class.execute_kw(DB, self.uid, PASS, 'sacco.loan', 'create', [args])
        self.models_class.exec_workflow(
            DB, self.uid, PASS, 'sacco.loan', 'send_for_appraisal', loan_id)
        print loan_id
        return loan_id

    def pay_loan(self, args):
        pass

    def check_balance(self, args):
        pass

    def check_loan_limit(self, args):
        pass

    def get_bank_code(self):
        setup = self.models_class.execute_kw(
            DB, self.uid, PASS, 'sacco.setup', 'search_read', [[['id', '=', 1]]])[0]
        return setup['mpesa_account'][0]

    def get_reg_status(self):
        user_logged = g.user
        self.models_class = xmlrpclib.ServerProxy(ROOT + 'object')
        member_status = \
            self.models_class.execute_kw(DB, self.uid, PASS, 'sacco.member.application', 'search_read',
                                         [[['id', '=', user_logged.odoo_app_id]]],
                                         {'fields': ['state', 'registration_fee_balance', 'share_capital_balance',
                                                     'member_id']})[0]

        return member_status

    # Deposits

    def deposit(self, args, lines, user, odoo_member_id=0):
        logged_user = user
        recipt_id = self.models_class.execute_kw(
            DB, self.uid, PASS, 'sacco.receipt.header', 'create', [args])
        print recipt_id
        if args['transaction_type'] == "normal":
            for l in lines:
                line = {
                    'no': recipt_id,
                    'transaction_type': l['transaction_type'],
                    'member_no': odoo_member_id,
                    'member_name': "USer",
                    'amount': l['amount']
                }
                self.models_class.execute_kw(DB, self.uid, PASS, 'sacco.receipt.line', 'create', [line])
        else:
            for l in lines:
                line = {
                    'no': recipt_id,
                    'transaction_type': l['transaction_type'],
                    'member_application_id': logged_user.odoo_app_id,
                    'member_name': logged_user.username,
                    'amount': l['amount']
                }
                self.models_class.execute_kw(DB, self.uid, PASS, 'sacco.receipt.line', 'create', [line])
        self.models_class.exec_workflow(
            DB, self.uid, PASS, 'sacco.receipt.header', 'send_for_posting', recipt_id)

    def disburse_loan(self, args):
        self.models_class.exec_workflow(
            DB, self.uid, PASS, 'sacco.loan', 'send_for_appraisal', args)
