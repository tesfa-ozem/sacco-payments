import requests

from gateway.mpesa_credentials import MpesaAccessToken, LipanaMpesaPpassword


class SafMethods:

    def __init__(self):
        self.access_token = MpesaAccessToken.validated_mpesa_access_token

    def send_push(self, args):
        api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        headers = {"Authorization": "Bearer %s" % self.access_token}
        response = requests.post(api_url, json=args, headers=headers)
        return response

    def send_money(self, args):
        pass

    def reverse(self, args):
        pass

    def transaction_status(self, args):
        pass

    def get_token(self):
        pass
