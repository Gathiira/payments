from django.contrib import admin

from payments.models import PaymentMethod, Transaction

# Register your models here.


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "type", "islog",
                    "is_active", "date_created")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("account_number", "status", "provider_reference",
                    "transaction_ref", "date_created")
