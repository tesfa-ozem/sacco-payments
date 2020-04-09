import json

import requests

from gateway.mpesa_credentials import MpesaAccessToken, LipanaMpesaPpassword


class SafMethods:

    def __init__(self):
        self.access_token = MpesaAccessToken.validated_mpesa_access_token

    def send_push(self, args, phone_number):
        amount = 0
        for line in args:
            amount += line['amount']
            print LipanaMpesaPpassword.decode_password
        request_body = {
            "BusinessShortCode": LipanaMpesaPpassword.Business_short_code,
            "Password": LipanaMpesaPpassword.decode_password,
            "Timestamp": LipanaMpesaPpassword.lipa_time,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,  # replace with your phone number to get stk push
            "PartyB": LipanaMpesaPpassword.Business_short_code,
            # replace with your phone number to get stk push
            "PhoneNumber": phone_number,
            "CallBackURL": "https://f9a33a70.ngrok.io/api/v1/c2b/callback",
            "AccountReference": "Test Loans",
            "TransactionDesc": "Loans"
        }
        api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        headers = {"Authorization": "Bearer %s" % self.access_token}
        response = requests.post(api_url, json=request_body, headers=headers)
        return response

    def send_money(self, args):
        pass

    def reverse(self, args):
        pass

    def transaction_status(self, args):
        pass

    def get_token(self):
        pass

    def register_url(self):
        args = {
            "ShortCode": LipanaMpesaPpassword.Test_c2b_shortcode,
            "ResponseType": "Canceled",
            "ConfirmationURL": "https://1c817d39.ngrok.io/c2b/v1//api/confirmationCallback",
            "ValidationURL": "https://1c817d39.ngrok.io/c2b/v1/api/validationResponse"
        }
        api_url = "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl"
        headers = {"Authorization": "Bearer %s" % self.access_token}
        response = requests.post(api_url, json=args, headers=headers)
        return json.dumps(response.json(), ensure_ascii=False)

    def make_payment(self):
        args = {
            "ShortCode": LipanaMpesaPpassword.Test_c2b_shortcode,
            "CommandID": "CustomerPayBillOnline",
            "Amount": 1,
            "Msisdn": 254727292911,
            "BillRefNumber": "C2B working"
        }
        api_url = "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/simulate"
        headers = {"Authorization": "Bearer %s" % self.access_token}
        response = requests.post(api_url, json=args, headers=headers)
        return response
