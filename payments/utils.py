from django.utils.crypto import get_random_string

from utils.loading import get_model

Transaction = get_model("payments", "Transaction")


class PaymentProcessor:
    @staticmethod
    def create_transaction_model(data):
        txn = Transaction()
        txn.provider = data["provider"]
        txn.phone_number = data["phone_number"]
        txn.method_id = data["method"]
        txn.amount = round(float(data["amount"]))
        txn.currency = "KES"
        txn.country = "KE"
        txn.city = "NBI"
        txn.narration = f"Payment for {data['account_number']}"
        txn.nonce = get_random_string(16)
        txn.transaction_type = data["transaction_type"]
        txn.payment_method = data["payment_method"]
        txn.payment_code = data["payment_code"]
        txn.transaction_is_log = data["islog"]
        txn.payment_method_name = data["payment_method_name"]
        txn.account_number = data["account_number"]

        if data["transaction_type"] == Transaction.CARDS:
            txn.first_name = data["first_name"]
            txn.last_name = data["last_name"]
            txn.email = data["email"]
            txn.postal_code = data["postal_code"]
            txn.street_address = data["line1"]

        txn.save()
        return txn
