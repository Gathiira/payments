import base64
import logging
import time
from datetime import datetime
from threading import Thread

from django.conf import settings
from django.urls import reverse

from daraja.configs import DarajaConfigs
from daraja.gateway import MpesaGateway
from utils.loading import get_model

Transaction = get_model("payments", "Transaction")
TransactionLog = get_model("payments", "TransactionLog")

logger = logging.getLogger(__name__)


class MpesaTransaction(object):
    """
    a class to handle mpesa operations
    """

    def __init__(self):
        self.vault = DarajaConfigs()
        self.lipa_time = datetime.now().strftime("%Y%m%d%H%M%S")
        self.business_short_code = self.vault.DARAJA_BUSINESS_SHORT_CODE
        self.c2b_bussiness_code = self.vault.DARAJA_C2B_BUSINESS_SHORT_CODE
        self.mpesa_gateway = MpesaGateway(self.vault)

    def get_password(self):
        passkey = self.vault.DARAJA_PASS_KEY
        data_to_encode = self.business_short_code + passkey + self.lipa_time
        online_password = base64.b64encode(data_to_encode.encode())
        decode_password = online_password.decode("utf-8")
        return decode_password

    def lipa_na_mpesa_online(
        self, amount, phone_number, callbackurl, accountref, transaction_desc=""
    ):
        """
        takes the arguments creates an mpesa payload
        and initiate an mpesa stk push with appropriate details passed
        Args:
            amount: 200
            phone_number: 254712345678
            callbackurl: https://......
            accountref: what you requesting payment for
            transaction_desc: a short narration of the transaction in progress, default=''

        Returns:
            - mpesa response
        """
        payload = {
            "BusinessShortCode": self.business_short_code,
            "Password": self.get_password(),
            "Timestamp": self.lipa_time,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,  # replace with your phone number to get stk push
            "PartyB": self.business_short_code,
            "PhoneNumber": phone_number,  # replace with your phone number to get stk push
            "CallBackURL": callbackurl,
            "AccountReference": accountref,
            "TransactionDesc": transaction_desc,
        }
        logging.info(payload)
        response = self.mpesa_gateway.initiate_stk_push(payload)
        return response

    def query_mpesa_express_transaction_status(self, checkout_request_id):
        payload = {
            "BusinessShortCode": self.business_short_code,
            "Password": self.get_password(),
            "Timestamp": self.lipa_time,
            "CheckoutRequestID": checkout_request_id,
        }
        logging.info(payload)
        response = self.mpesa_gateway.mpesa_express_query(payload)
        return response

    def process_mobile_transaction(self, transaction):
        """
        [create  mpesa txn]
        sample request
        POST
            Content-Type: application/json
            [Other HTTP headers]...
             {
                "callbackurl": 'sky garden callback',
                "accountref": 'order',
                "transaction_desc": 'order checkout',
                "amount": 10,
                "phone_number": 0712345678,
            }
        """
        # build callback url
        base_url = settings.SKYGARDEN_API_HOST_NAME
        transaction_url = reverse(
            "transaction-stkpush-callback",
            kwargs={"account_number": transaction.account_number},
        )[1:]
        callback_url = base_url + transaction_url

        logger.info(callback_url)
        # https://dev-api.sky.garden/api/v3/transaction-stkpush/872547/callback/

        stk_data = {
            "callbackurl": callback_url,
            "accountref": transaction.order_number,
            "transaction_desc": transaction.narration,
            "amount": int(transaction.amount),
            "phone_number": str(transaction.phone_number)[1:],
        }
        mpesa_request = self.lipa_na_mpesa_online(**stk_data)
        response_data = mpesa_request.json()
        logger.info(response_data)
        if mpesa_request.status_code != 200:
            transaction.status = Transaction.PENDING
            transaction.error_message = "Failed to initiate stk push!"
            transaction.instruction_to_customer = (
                "Payment Initiated. Please pay via {} to paybill number"
                " {} account number {}".format(
                    transaction.payment_method_name,
                    settings.SKYGARDEN_PAYBILL_NUMBER,
                    transaction.account_number,
                )
            )
            transaction.save(
                update_fields=["instruction_to_customer", "error_message", "status"]
            )
            return transaction
        else:
            transaction.merchant_id = response_data["MerchantRequestID"]
            transaction.checkout_request_id = response_data["CheckoutRequestID"]
            transaction.save(update_fields=["merchant_id", "checkout_request_id"])

            # wait for mpesa transactions to happen and return appropriate response
            # max wait is 90 sec with 10 loops. Then return a failed response

            def await_transaction(await_period):
                while await_period < 20:
                    time.sleep(await_period)
                    transaction.refresh_from_db()
                    if transaction.status in ["Successful"]:
                        break
                    elif transaction.status not in ["Initiated"]:
                        break
                    else:
                        await_period += 2
                return

            async_wait = Thread(target=await_transaction, args=(2,))
            async_wait.start()
            async_wait.join()

            transaction.refresh_from_db()

            if transaction.status not in ["Successful"]:
                transaction.status = Transaction.PENDING
                transaction.instruction_to_customer = "Payment failed. Try again"
            else:
                transaction.instruction_to_customer = "Thank you. Payment received"
            transaction.save()
            return transaction

    def register_c2b_urls(self, confirmation_url, validation_url):
        """
        ResponseType - This parameter specifies what is to happen if for any reason the validation URL is nor reachable.
                        Note that:
                        This is the default action value that determines what MPesa will do in the scenario
                        that your endpoint is unreachable or is unable to respond on time.
                        Only two values are allowed: Completed or Cancelled.
                        -> Completed means MPesa will automatically complete your transaction
                        -> Cancelled means MPesa will automatically cancel the transaction.


        ShortCode -     The short code of the organization.

        ConfirmationURL	- This is the URL that receives the confirmation request from API upon payment completion.

        ValidationURL	This is the URL that receives the validation request from API upon payment submission.
                        The validation URL is only called if the external validation on
                        the registered shortcode is enabled. (By default External Validation is disabled)
        Returns:
            mpesa response with

        """
        payload = {
            "ShortCode": self.c2b_bussiness_code,
            "ResponseType": "Completed",  # can be 'Cancelled', 'Completed'
            "ConfirmationURL": confirmation_url,
            "ValidationURL": validation_url,
        }
        logging.info(payload)
        response = self.mpesa_gateway.register_c2b_urls(payload)
        return response
