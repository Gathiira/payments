import logging
import time
from threading import Thread

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction as db_transaction
from django.db.models import F
from django.urls import reverse
from django.utils.crypto import get_random_string

from rest_framework import status, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from daraja.facade import MpesaTransaction
from daraja.serializers import StkPushSerializer
from payments.slack import send_slack_message
from payments.utils import PaymentProcessor
from utils.core import validate_phone_number
from utils.loading import get_model

PaymentMethod = get_model("payments", "PaymentMethod")
Transaction = get_model("payments", "Transaction")
TransactionLog = get_model("payments", "TransactionLog")

logger = logging.getLogger(__name__)


def generate_account_number():
    """
    generate sample account number for a transaction
    """
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
    data = {
        "amount": amount,
        "provider": method.code,
        "islog": method.islog,
        "method": method.id,
        "payment_method_name": method.name,
        "phone_number": "",
        "transaction_type": Transaction.MOBILE,
        "payment_method": Transaction.PAYBILL,
        "payment_code": Transaction.MMO,
        "customer": None,
        "target": "",
    }

    return data


def get_data_from_mpesa_items(items):
    """
    reformat payload data from daraja
    """
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
    """
    update transaction with callback data from daraja
    """
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
        items = get_data_from_mpesa_items(stkcallbackdata["CallbackMetadata"]["Item"])
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
    method = PaymentMethod.objects.filter(type=PaymentMethod.MOBILE, islog=True).first()
    data = get_transaction_payload(amount=kwargs["amount"], method=method)
    with db_transaction.atomic():
        transaction = PaymentProcessor.create_transaction_model(
            data, account_number=kwargs["account_number"]
        )
    return transaction


class InitiateStkPushView(views.APIView):
    def post(self, request, account_number, format=None):
        """
        initiates mpesa stk push for riders
        Args:
            request:

        Returns:
            200: if success
            400: in case of error or fails
        """
        payload = request.data
        serializer = StkPushSerializer(data=payload, many=False)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        payment_category = "Checkout"
        try:
            payment_method = PaymentMethod.objects.get(code="101MX")
        except Exception as e:
            logger.error(e)
            return Response(
                {"detail": "Invalid payment method. Kindly load payment method data"},
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )

        pay_amount = data["amount"]
        narration = f"Payment for  a transaction {account_number}"
        phone_number = data["phone_number"]
        # create an instance of Transaction
        transaction_payload = {
            "account_number": account_number,
            "provider": "702",
            "phone_number": phone_number,
            "currency": "KES",
            "country": "KE",
            "method": payment_method,
            "narration": narration,
            "amount": round(float(pay_amount)),
            "transaction_is_log": False,
            "payment_category": payment_category,
        }
        with db_transaction.atomic():
            logger.info(transaction_payload)
            transaction = Transaction(**transaction_payload)
            transaction.save()

            # build callback url
            base_url = settings.API_HOST_NAME
            transaction_url = reverse(
                "transaction-stkpush-callback",
                kwargs={"account_number": account_number},
            )
            callback_url = base_url + transaction_url

            logger.info(callback_url)

            query_url = reverse(
                "transaction-stkpush-query-status",
                kwargs={"account_number": account_number},
            )
            status_url = base_url + query_url

            accountref = account_number
            desc = data.get("description") or narration
            stk_data = {
                "callbackurl": callback_url,
                "accountref": accountref,
                "transaction_desc": desc,
                "amount": pay_amount,
                "phone_number": phone_number[1:],
            }
            mpesa_transaction = MpesaTransaction()
            mpesa_request = mpesa_transaction.lipa_na_mpesa_online(**stk_data)
            response_data = mpesa_request.json()
            print(response_data)
            logger.info(response_data)
            if mpesa_request.status_code != 200:
                db_transaction.set_rollback(True)
                return Response(
                    {"message": "Failed to initiate stk push. Try again later"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
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

        # send slack message
        send_slack_message(transaction)

        if transaction.status not in ["Successful"]:
            # check status from safaricom
            checkout_request_id = transaction.checkout_request_id
            mpesa_request = mpesa_transaction.query_mpesa_express_transaction_status(
                checkout_request_id
            )
            response = mpesa_request.json()
            logger.info(response)
            if mpesa_request.status_code != 200:
                error_msg = response["errorMessage"]
                status_code = 400
            else:
                error_msg = response["ResultDesc"]
                status_code = response["ResultCode"]
                # if status_code == 0:
                #     # process payments
                #     transaction.amount_paid = transaction.amount
                #     transaction.last_payment = transaction.amount
                #     transaction.status = Transaction.SUCCESSFUL
                #     transaction.save(
                #         update_fields=['last_payment', 'amount_paid', 'status'])

            return Response(
                {
                    "status": status_code,
                    "message": error_msg,
                    "query_status_url": status_url,
                }
            )
        resp = {
            "status": 200,
            "message": "Transaction successful",
            "query_status_url": status_url,
            "amount_paid": transaction.amount_paid,
        }
        return Response(resp)


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
        # if self.request.method in ["GET"]:
        #     self.permission_classes = [
        #         IsAuthenticated,
        #     ]
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
            transaction = Transaction.objects.get(account_number=account_number)
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

    # permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        # _payload = request.data
        server_url = settings.API_HOST_NAME
        validation_url = server_url + reverse("c2b-validation-url")
        confirmation_url = server_url + reverse("c2b-confirmation-url")
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
