import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction as db_transaction
from django.urls import reverse
from django.utils.crypto import get_random_string

from utils.loading import get_model
from rest_framework import status, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from daraja.facade import MpesaTransaction
from utils.core import validate_phone_number
from payments.utils import PaymentProcessor


PaymentMethod = get_model("interswitch", "PaymentMethod")
Transaction = get_model("interswitch", "Transaction")
TransactionLog = get_model("interswitch", "TransactionLog")

logger = logging.getLogger("sky.log")


def generate_account_number():
    seed = "".join(str(x) for x in range(10))
    while True:
        account_number = get_random_string(6, seed)
        try:
            Transaction.objects.get(account_number=account_number)
            logger.warning(
                "{} not unique account number generated".format(account_number)
            )
        except ObjectDoesNotExist:
            break
    return account_number


def get_transaction_payload(amount, method, number=None):
    """

    Args:
        number:
        amount:
        method:

    Returns:

    """
    generated_number = random_available_order_number()
    data = {
        "amount": amount,
        "provider": method.code,
        "islog": method.islog,
        "method": method.id,
        "payment_method_name": method.name,
        "order_number": number or generated_number,
        "phone_number": "",
        "transaction_type": Transaction.MOBILE,
        "payment_method": Transaction.PAYBILL,
        "payment_code": Transaction.MMO,
        "customer": None,
        "target": "",
    }

    return data


def get_data_from_mpesa_items(items):
    results = {}
    for item in items:
        if item["Name"] == "Amount":
            results["Amount"] = item["Value"]
        elif item["Name"] == "MpesaReceiptNumber":
            results["MpesaReceiptNumber"] = item["Value"]
        else:
            continue
    return results


def update_transaction_details(account_number, payload):
    try:
        transaction = Transaction.objects.get(account_number=account_number)
    except ObjectDoesNotExist:
        return False, "Invalid Transaction"

    callback_body = payload["Body"]
    stkcallbackdata = callback_body["stkCallback"]

    transaction_success = (
        stkcallbackdata["ResultCode"] == 0
        if callback_body.get("stkCallback")
        else False
    )

    if transaction_success:
        pay_status = Transaction.SUCCESSFUL
        items = get_data_from_mpesa_items(
            stkcallbackdata["CallbackMetadata"]["Item"])
        paid_amount = items["Amount"]
        provider_ref = items["MpesaReceiptNumber"]
        error_msg = stkcallbackdata["ResultDesc"]
    else:
        pay_status = Transaction.FAILED
        paid_amount = 0
        provider_ref = ""
        error_msg = stkcallbackdata["ResultDesc"] if stkcallbackdata else ""

    # if transaction_success and settings.SERVER != "production":
    #     try:
    #         order = Order.objects.get(number=transaction.order_number)
    #         paid_amount = int(order.total_incl_tax)
    #     except ObjectDoesNotExist:
    #         pass

    transaction.status = pay_status
    transaction.provider_reference = provider_ref
    transaction.error_message = error_msg
    transaction.amount_paid += paid_amount
    transaction.last_payment = paid_amount
    transaction.save(
        update_fields=[
            "amount_paid",
            "status",
            "provider_reference",
            "error_message",
            "last_payment",
        ]
    )
    return True, transaction


def create_transaction_instance(**kwargs):
    method = PaymentMethod.objects.filter(
        type=PaymentMethod.MOBILE, islog=True).first()
    data = get_transaction_payload(amount=kwargs["amount"], method=method)
    with db_transaction.atomic():
        transaction = PaymentProcessor.create_transaction_model(
            data, account_number=kwargs["account_number"]
        )
    return transaction


class MpesaStkPushCallbackView(views.APIView):
    """
    mpesa transaction urls
    """

    lookup_url_kwarg = "account_number"
    lookup_field = "account_number"
    permission_classes = [
        AllowAny,
    ]

    def get_permissions(self):
        if self.request.method in ["GET"]:
            self.permission_classes = [
                IsAuthenticated,
            ]
        return super(MpesaStkPushCallbackView, self).get_permissions()

    def post(self, request, account_number, *args, **kwargs):
        """
          - callback url for mpesa stk push
          payload

          {
          "Body": {
            "stkCallback": {
              "CallbackMetadata": {
                "Item": [
                  {
                    "Name": "Amount",
                    "Value": 1
                  },
                  {
                    "Name": "MpesaReceiptNumber",
                    "Value": "QDK8NK9HV8"
                  },
                  {
                    "Name": "Balance"
                  },
                  {
                    "Name": "TransactionDate",
                    "Value": 20220420003234
                  },
                  {
                    "Name": "PhoneNumber",
                    "Value": 254720600705
                  }
                ]
              },
              "CheckoutRequestID": "ws_CO_20042022003225112720600705",
              "ResultCode": 0,
              "MerchantRequestID": "43064-193905133-1",
              "ResultDesc": "The service request is processed successfully."
            }
          }
        }
        Args:
            request:

        Returns:

        """
        payload = request.data
        logger.info(payload)
        log = TransactionLog(json_data=payload)
        log.save()

        updated, resp = update_transaction_details(account_number, payload)
        if not updated:
            return Response(resp)
        return Response("Safaricom: The better option")

    def get(self, request, account_number, *args, **kwargs):
        """
         - status query for a stk push
        Args:
            request:

        Returns:

        """
        try:
            transaction = Transaction.objects.get(
                account_number=account_number)
        except ObjectDoesNotExist:
            return Response(
                {"message": "Invalid Transaction", "amount": 0},
                status=status.HTTP_200_OK,
            )

        if transaction.status in ["Successful"]:
            return Response(
                {
                    "message": "Transaction successful",
                    "amount": transaction.amount_paid,
                },
                status=status.HTTP_200_OK,
            )

        elif transaction.status not in ["Initiated"]:
            error_msg = transaction.error_message or "Transaction Failed!!"
            return Response(
                {"message": error_msg, "amount": transaction.amount_paid},
                status=status.HTTP_200_OK,
            )
        else:
            mpesa_transaction = MpesaTransaction()
            checkout_request_id = transaction.checkout_request_id
            mpesa_request = mpesa_transaction.query_mpesa_express_transaction_status(
                checkout_request_id
            )
            response = mpesa_request.json()
            logger.info(response)
            if mpesa_request.status_code != 200:
                return Response(
                    {"message": response["errorMessage"], "amount": 0},
                    status=status.HTTP_200_OK,
                )
            msg = response["ResultDesc"]
            return Response(
                {"message": msg, "amount": transaction.amount_paid},
                status=status.HTTP_200_OK,
            )


class MpesaRegisterUrlView(views.APIView):
    """
    mpesa register urls i.e validation url and confirmation url
    """

    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        # _payload = request.data
        server_url = settings.SKYGARDEN_API_HOST_NAME
        validation_url = server_url[:-1] + \
            reverse("transaction-validate-mpesa-payment")
        confirmation_url = server_url[:-1] + reverse(
            "transaction-confirm-mpesa-payment"
        )
        mpesa_transaction = MpesaTransaction()
        mpesa_request = mpesa_transaction.register_c2b_urls(
            confirmation_url, validation_url
        )
        response = mpesa_request.json()
        logger.info(response)
        return Response(response)


class MpesaValidationUrlView(views.APIView):
    """
    mpesa validate payment
    """

    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        payload = request.data
        logger.info(payload)
        # create a transaction against the account number (account number)
        # check if transaction exists else create
        bill_ref = payload.get("BillRefNumber")
        amount_paid = payload.get("TransAmount")
        txn_q = Transaction.objects.filter(account_number=bill_ref)
        if not txn_q.exists():
            data = {"account_number": bill_ref, "amount": amount_paid}
            create_transaction_instance(**data)

        context = {"ResultCode": 0, "ResultDesc": "Accepted"}
        return Response(context)


class MpesaConfirmationUrlView(views.APIView):
    """
    mpesa confirm payment
    payload:
        {
          "LastName": "SONGOK",
          "FirstName": "NICHOLAS",
          "TransAmount": "1.00",
          "MiddleName": "Nicholas",
          "BillRefNumber": "1234",
          "TransID": "QD681KVE8O",
          "TransactionType": "Pay Bill",
          "BusinessShortCode": "600986",
          "OrgAccountBalance": "20027361.00",
          "TransTime": "20220406231607",
          "InvoiceNumber": "",
          "MSISDN": "254705912645",
          "ThirdPartyTransID": ""
        }
    """

    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        payload = request.data
        logger.info(payload)
        log = TransactionLog(json_data=payload)
        log.save()

        bill_ref = payload.get("BillRefNumber")
        amount_paid = int(float(payload.get("TransAmount")))
        try:
            transaction = Transaction.objects.get(account_number=bill_ref)
        except ObjectDoesNotExist:
            data = {"account_number": bill_ref, "amount": amount_paid}
            transaction = create_transaction_instance(**data)

        # get phone number from logs
        phone_number = payload.get("MSISDN", "")
        phone_number = validate_phone_number(phone_number)
        if not bool(phone_number):
            phone_number = ""

        # update transaction model.
        transaction.amount_paid += amount_paid
        transaction.last_payment = amount_paid
        transaction.status = Transaction.SUCCESSFUL
        transaction.phone_number = phone_number
        transaction.first_name = payload.get("FirstName", "")
        transaction.provider_reference = payload.get("TransID", "")
        transaction.save()

        context = {"ResultCode": 0, "ResultDesc": "Accepted"}
        return Response(context)
