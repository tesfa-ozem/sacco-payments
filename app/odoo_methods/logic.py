import functools
import xmlrpclib

from flask import request, g

from app.models import User
from app import db

HOST = 'localhost'
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

    def register_member(self, args):
        try:
            user_logged = g.user
            print user_logged.odoo_registered
            if user_logged.odoo_registered is not True:
                models = xmlrpclib.ServerProxy(ROOT + 'object')
                member_id = models.execute_kw(DB, self.uid, PASS, 'sacco.member.application', 'create', [args])
                models.exec_workflow(
                    DB, self.uid, PASS, 'sacco.member.application', 'send_for_payment', member_id)
                member_number = \
                    models.execute_kw(DB, self.uid, PASS, 'sacco.member.application', 'search_read',
                                      [[['id', '=', member_id]]],
                                      {'fields': ['no']})[0]['no']
                print member_number

                user_logged.odoo_registered = True
                user_logged.odoo_id = str(member_id)
                user_logged.odoo_member_number = member_number
                db.session.add(user_logged)
                db.session.commit()
                return str(member_id)
            else:
                return "member registered"
        except Exception as e:
            return str(e)

    def search_member(self, args):
        pass

    # TODO: add  script for multiple guarantors
    def apply_loan(self, args, guarantor_id):
        user_logged = g.user
        if user_logged.odoo_member:
            models = xmlrpclib.ServerProxy(ROOT + 'object')
            loan_id = models.execute_kw(DB, self.uid, PASS, 'sacco.loan', 'create', [args])
            models.execute_kw(DB, self.uid, PASS, 'sacco.loan.guarantors', 'create', [{
                'loan_no': loan_id,
                'member_no': guarantor_id
            }])
            print loan_id

    def pay_loan(self, args):
        pass

    def deposit(self, args):
        pass

    def check_balance(self, args):
        pass

    def check_loan_limit(self, args):
        pass

    # TODO: add control for the amount
    def pay_reg_fee(self, args):
        reg_fee = self.get_reg_fee()
        models = xmlrpclib.ServerProxy(ROOT + 'object')
        recipt_id = models.execute_kw(DB, self.uid, PASS, 'sacco.receipt.header', 'create', [args])
        if reg_fee['reg_fee']:
            models.execute_kw(DB, self.uid, PASS, 'sacco.receipt.line', 'create', [{
                'no': recipt_id,
                'transaction_type': 'registration',
                'member_application_id': args['member_application_id'],
                'member_name': 'Tesfa',
                'amount': reg_fee['reg_fee'],

            }
            ])

        if reg_fee['min_share'] is not None:
            models.execute_kw(DB, self.uid, PASS, 'sacco.receipt.line', 'create', [{
                'no': recipt_id,
                'transaction_type': 'shares',
                'member_application_id': args['member_application_id'],
                'member_name': 'Tesfa',
                'amount': reg_fee['min_share']
            }
            ])
        models.execute_kw(DB, self.uid, PASS, 'sacco.receipt.header', 'action_post', [recipt_id])
        return self.get_reg_status()

    def get_bank_code(self):
        models = xmlrpclib.ServerProxy(ROOT + 'object')
        setup = models.execute_kw(DB, self.uid, PASS, 'sacco.setup', 'search_read', [[['id', '=', 1]]])[0]
        return setup['mpesa_account'][0]

    def get_reg_fee(self):
        try:

            models = xmlrpclib.ServerProxy(ROOT + 'object')
            setup = models.execute_kw(DB, self.uid, PASS, 'sacco.setup', 'search_read', [[['id', '=', 1]]])[0]
            rg_fee = setup['registration_fee']
            min_share_cap = setup['minimum_shares']
            return {'reg_fee': rg_fee,
                    'min_share': min_share_cap}
        except Exception as e:

            return str(e)

    def get_total_reg_fee(self):
        total_reg_fee = 0.0

        for i in self.get_reg_fee().values():
            total_reg_fee += i

        return total_reg_fee

    def get_reg_status(self):
        user_logged = g.user
        models = xmlrpclib.ServerProxy(ROOT + 'object')
        member_status = \
            models.execute_kw(DB, self.uid, PASS, 'sacco.member.application', 'search_read',
                              [[['id', '=', user_logged.odoo_id]]],
                              {'fields': ['state', 'registration_fee_balance', 'share_capital_balance']})[0]

        return member_status
