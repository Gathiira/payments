import logging
import json
from datetime import datetime, timedelta

import pytz
import requests
from requests.auth import HTTPBasicAuth

from daraja.models import DarajaAcessToken

logger = logging.getLogger(__name__)


class MpesaGateway(object):
    """
    a class to handle mpesa authentication/ getting access key
    """

    def __init__(self, vault):
        self.vault = vault

    def _get_access_headers(self):
        access_token = self.get_daraja_access_token()
        headers = {"Authorization": "Bearer %s" % access_token}
        return headers

    def get_daraja_access_token(self):
        """
        use this method to get mpesa access token
        Returns:

        """
        consumer_key = self.vault.DARAJA_CONSUMER_KEY
        consumer_secret = self.vault.DARAJA_CONSUMER_SECRET

        now = datetime.now(pytz.timezone("Africa/Nairobi"))
        token_q, _ = DarajaAcessToken.objects.get_or_create(
            code="DARAJA_ACCESS_TOKEN")
        if token_q and bool(token_q.expires_in) and token_q.expires_in > now:
            return token_q.token
        else:
            req = requests.get(
                self.vault.DARAJA_ACCESS_URL,
                auth=HTTPBasicAuth(consumer_key, consumer_secret),
            )
            try:
                mpesa_access_token = json.loads(req.text)
                validated_mpesa_token = mpesa_access_token["access_token"]
                expires_in = int(mpesa_access_token["expires_in"])
                token_q.token = validated_mpesa_token
                token_q.expires_in = now + timedelta(seconds=expires_in)
                token_q.save()
                return validated_mpesa_token
            except Exception as e:
                logger.error('response --> %s', req.text)
                logger.error(e)
                return ''

    def initiate_stk_push(self, payload):
        """
        sending request to safaricom api
        Args:
            payload: json with required key, values

        Returns:
            - mpesa stk push response
        """
        api_url = self.vault.DARAJA_STKPUSH_URL
        headers = self._get_access_headers()
        response = requests.post(api_url, json=payload, headers=headers)
        return response

    def mpesa_express_query(self, payload):
        """
        Headers
        Key: Authorization
        Value: Basic cFJZcjZ6anEwaThMMXp6d1FETUCDFx
        ​
        Body
          {
            "BusinessShortCode": 174379,
            "Password": "MTc0Mzc5YmZiMjc5ZjlhYTliZGJjZjE1OGU",
            "Timestamp": 20220407155444,
            "CheckoutRequestID": "ws_CO_070420221544074736"
          }
        Args:
            payload:

        Returns:

        """
        api_url = self.vault.DARAJA_STKPUSH_QUERY_URL
        headers = self._get_access_headers()
        response = requests.post(api_url, json=payload, headers=headers)
        return response

    def register_c2b_urls(self, payload):
        api_url = self.vault.DARAJA_C2B_REGISTER_URL
        headers = self._get_access_headers()
        response = requests.post(api_url, json=payload, headers=headers)
        return response
