from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.utils.crypto import get_random_string

# Create your models here.


class PaymentMethod(models.Model):
    """Payment methods for collecting funds
            name = 'Equitel'
            code = '703'
            type = 'mobile'
            islog = False
            description = "Customer will pay offline to Equitel"
            target = settings.PAYBILL_NUMBER

    Arguments:
        models {[type]} -- [description]
    """

    MOBILE, CARD = "mobile", "card"
    METHOD_TYPE = (
        (MOBILE, _("Mobile Payment")),
        (CARD, _("Card Payment")),
    )
    name = models.CharField(
        max_length=50, help_text="Name of the payment method")
    code = models.CharField(
        max_length=10, help_text="Code to id this method")
    type = models.CharField(
        max_length=24,
        help_text="Type of payment method being used",
        choices=METHOD_TYPE,
        default=MOBILE,
    )
    islog = models.BooleanField(
        default=True, help_text="If true payment will be completed later"
    )
    description = models.TextField(default="")
    target = models.CharField(max_length=24, blank=True, null=True)
    is_active = models.BooleanField(
        default=True,
        help_text="We can use this to activate or deactivate a payment method",
    )
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Transaction(models.Model):

    """Record all payments collections whether successful or failed.

    Arguments:
        models {[type]} -- [description]
    """
    INITIATED, PENDING, FAILED = "Initiated", "Pending", "Failed"
    SUCCESSFUL, CANCELLED, REVERSED = "Successful", "Cancelled", "Reversed"
    FAILEDCOMPLETELY, RETRYING = "Failed Completely", "Retrying"

    PAYMENT_STATUSES = (
        (INITIATED, _("Initiated")),
        (PENDING, _("Pending")),
        (FAILED, _("Failed")),
        (SUCCESSFUL, _("Successful")),
        (CANCELLED, _("Cancelled")),
        (REVERSED, _("Reversed")),
        (FAILEDCOMPLETELY, _("Failed Completely")),
        (RETRYING, _("Retrying")),
    )

    MPESA, TELKOM, EQUITEL, AIRTELL, MASTERCARD, VISA = (
        "702",
        "700",
        "703",
        "710",
        "MCK",
        "VCK",
    )

    PAYMENT_PROVIDERS = (
        (MPESA, _("MPESA")),
        (TELKOM, _("Telkom cash")),
        (AIRTELL, "Airtell Money"),
        (MASTERCARD, _("Mastercard Kenya")),
        (VISA, _("Visa Kenya")),
    )
    CHECKOUT, TOPUP, DELIVERY = "Checkout", "Topup", "Delivery"
    PAYMENT_CATEGORIES = [
        (CHECKOUT, "Checkout"),
        (TOPUP, "Topup"),
        (DELIVERY, "Delivery"),
    ]
    provider = models.CharField(
        null=True,
        blank=True,
        max_length=50,
        choices=PAYMENT_PROVIDERS,
        help_text="Provider of payment services",
    )
    account_number = models.CharField(max_length=28, unique=True)
    phone_number = models.CharField(max_length=28, blank=True, null=True)
    transaction_ref = models.CharField(
        max_length=40,
        db_index=True,
        editable=False,
        help_text="Unique transaction reference",
    )
    currency = models.CharField(max_length=12, default="KES")
    country = models.CharField(max_length=10, blank=True, null=True)
    city = models.CharField(max_length=10, blank=True, null=True)
    narration = models.CharField(max_length=100)
    method = models.ForeignKey(
        PaymentMethod,
        blank=True,
        null=True,
        related_name="payments",
        on_delete=models.SET_NULL,
    )
    status = models.CharField(
        choices=PAYMENT_STATUSES, max_length=15, default=INITIATED
    )
    amount = models.PositiveIntegerField()
    error_message = models.TextField(default="")
    instruction_to_customer = models.TextField(default="")
    transaction_is_log = models.BooleanField(
        default=True, help_text="True means the payment is to be me made later"
    )
    provider_reference = models.CharField(
        max_length=30, blank=True, null=True
    )  # For mpesa save the uniqe ref here
    amount_paid = models.PositiveIntegerField(default=0)
    last_payment = models.PositiveIntegerField(default=0)
    first_name = models.CharField(
        max_length=40, null=True, blank=True, help_text="first name on card"
    )
    last_name = models.CharField(
        max_length=40, null=True, blank=True, help_text="last name on card"
    )
    email = models.EmailField(
        max_length=70, null=True, blank=True, help_text="Card holder email"
    )
    postal_code = models.CharField(max_length=15, null=True, blank=True)
    street_address = models.CharField(max_length=200, null=True, blank=True)
    initiator_account = models.CharField(
        max_length=70,
        null=True,
        blank=True,
        help_text="sometimes the payment can come from a different account",
    )
    payment_category = models.CharField(
        max_length=100, null=True, blank=True, choices=PAYMENT_CATEGORIES
    )
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    last_edited = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.narration

    def _get_unique_ref(self):
        while True:
            length = 20
            ref = get_random_string(length)
            try:
                txn = Transaction.objects.get(transaction_ref=ref)
            except ObjectDoesNotExist:
                break
        return ref

    def save(self, *args, **kwargs):
        if not self.transaction_ref:
            self.transaction_ref = self._get_unique_ref()
        return super(Transaction, self).save(*args, **kwargs)


class TransactionLog(models.Model):
    """
    Logs
    """
    json_data = models.JSONField()
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.recieved_on)
