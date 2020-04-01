import functools
import xmlrpclib

from flask import request, g

from gateway.models import User
from gateway import db

HOST = '136.244.96.154'
PORT = 8069
DB = 'sacco'
USER = 'admin'
PASS = '123'
ROOT = 'http://%s:%d/xmlrpc/' % (HOST, PORT)


class Logic:

    def __init__(self):

        self.common = xmlrpclib.ServerProxy(ROOT + 'common')
        self.version = self.common.version()
        self.uid = self.common.authenticate(DB, USER, PASS, {})
        self.models_class = xmlrpclib.ServerProxy(ROOT + 'object')

    def register_member(self, args):
        try:
            user_logged = g.user
            print user_logged.odoo_registered
            if user_logged.odoo_registered is not True:
                member_id = self.models_class.execute_kw(
                    DB, self.uid, PASS, 'sacco.member.application', 'create', [args])
                self.models_class.exec_workflow(
                    DB, self.uid, PASS, 'sacco.member.application', 'send_for_payment', member_id)
                member_number = \
                    self.models_class.execute_kw(DB, self.uid, PASS, 'sacco.member.application', 'search_read',
                                                 [[['id', '=', member_id]]],
                                                 {'fields': ['no']})[0]['no']
                print member_number

                user_logged.odoo_registered = True
                user_logged.odoo_app_id = str(member_id)
                db.session.add(user_logged)
                db.session.commit()
                return str(member_id)
            else:
                return "member registered"
        except Exception as e:
            return str(e)

    def search_member(self):
        models = xmlrpclib.ServerProxy(ROOT + 'object')

        member = models.execute_kw(DB, self.uid, PASS, 'sacco.member.application', 'search_read',
                                   [[['id', '=', 40]]],
                                   {'fields': ['id', 'name', 'no', 'state']})[0]

        return member

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

    # TODO: add control for the amount
    def pay_reg_fee(self, args, amounts):
        reg_fee = self.get_reg_fee()
        recipt_id = self.models_class.execute_kw(
            DB, self.uid, PASS, 'sacco.receipt.header', 'create', [args])
        if reg_fee['reg_fee'] == amounts['reg_fee']:
            self.models_class.execute_kw(DB, self.uid, PASS, 'sacco.receipt.line', 'create', [{
                'no': recipt_id,
                'transaction_type': 'registration',
                'member_application_id': args['member_application_id'],
                'member_name': 'Tesfa',
                'amount': amounts['reg_fee'],

            }
            ])

        if amounts['min_share'] is not None:
            self.models_class.execute_kw(DB, self.uid, PASS, 'sacco.receipt.line', 'create', [{
                'no': recipt_id,
                'transaction_type': 'shares',
                'member_application_id': args['member_application_id'],
                'member_name': 'Tesfa',
                'amount': amounts['min_share']
            }
            ])
        self.models_class.execute_kw(DB, self.uid, PASS,
                                     'sacco.receipt.header', 'action_post', [recipt_id])

        return self.get_reg_status()

    def get_bank_code(self):
        setup = self.models_class.execute_kw(
            DB, self.uid, PASS, 'sacco.setup', 'search_read', [[['id', '=', 1]]])[0]
        return setup['mpesa_account'][0]

    def get_reg_fee(self):
        try:
            setup = self.models_class.execute_kw(
                DB, self.uid, PASS, 'sacco.setup', 'search_read', [[['id', '=', 1]]])[0]
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
        self.models_class = xmlrpclib.ServerProxy(ROOT + 'object')
        member_status = \
            self.models_class.execute_kw(DB, self.uid, PASS, 'sacco.member.application', 'search_read',
                                         [[['id', '=', user_logged.odoo_app_id]]],
                                         {'fields': ['state', 'registration_fee_balance', 'share_capital_balance',
                                                     'member_id']})[
                0]

        return member_status

    # Deposits

    def deposit(self, args, amount):
        recipt_id = self.models_class.execute_kw(
            DB, self.uid, PASS, 'sacco.receipt.header', 'create', [args])

        self.models_class.execute_kw(DB, self.uid, PASS, 'sacco.receipt.line', 'create', [{
            'no': recipt_id,
            'transaction_type': 'deposits',
            'member_no': args['received_from'],
            'member_name': 'Nezghi',
            'amount': amount
        }
        ])
        self.models_class.exec_workflow(
            DB, self.uid, PASS, 'sacco.receipt.header', 'send_for_posting', recipt_id)

    def buy_share(self, args, amount):

        recipt_id = self.models_class.execute_kw(
            DB, self.uid, PASS, 'sacco.receipt.header', 'create', [args])

        self.models_class.execute_kw(DB, self.uid, PASS, 'sacco.receipt.line', 'create', [{
            'no': recipt_id,
            'transaction_type': 'shares',
            'member_no': args['received_from'],
            'member_name': 'Nezghi',
            'amount': amount
        }
        ])
        self.models_class.exec_workflow(
            DB, self.uid, PASS, 'sacco.receipt.header', 'send_for_posting', recipt_id)

    def disburse_loan(self,args):
        self.models_class.exec_workflow(
            DB, self.uid, PASS, 'sacco.loan', 'send_for_appraisal', args)
