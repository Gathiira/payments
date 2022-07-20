from django.contrib import admin

from daraja.models import DarajaAcessToken

# Register your models here.


@admin.register(DarajaAcessToken)
class TokenAdmin(admin.ModelAdmin):
    list_display = ("token", "expires_in", "date_created", "date_updated")
