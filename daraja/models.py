from django.db import models

# Create your models here.


class DarajaAcessToken(models.Model):
    """
    Store the Access Token Instead of hitting Safaricom per Every Request
    """
    code = models.CharField(default="DARAJA_ACCESS_TOKEN", max_length=255)
    token = models.TextField(null=True)
    expires_in = models.DateTimeField(null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.token} {self.expires_in} --> {self.date_created}"
