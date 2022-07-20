import os

SERVER = os.environ.get("SKY_ENV", "local")
# SERVER = "production"  # activate this field to test locally with prod configs


class DarajaConfigs:
    """
    Daraja configs access from env
    """

    def __init__(self):
        self.is_prod = SERVER == "production"

        self.DARAJA_ACCESS_URL = (
            os.environ.get("DARAJA_LIVE_ACCESS_URL")
            if self.is_prod
            else os.environ.get("DARAJA_SANDBOX_ACCESS_URL")
        )

        self.DARAJA_CONSUMER_KEY = (
            os.environ.get("DARAJA-LIVE-KEY")
            if self.is_prod
            else os.environ.get("DARAJA_SANDBOX_CONSUMER_KEY")
        )

        self.DARAJA_CONSUMER_SECRET = (
            os.environ.get("DARAJA-LIVE-SECRET")
            if self.is_prod
            else os.environ.get("DARAJA_SANDBOX_CONSUMER_SECRET")
        )

        self.DARAJA_PASS_KEY = (
            os.environ.get("DARAJA-LIVE-PASSKEY")
            if self.is_prod
            else os.environ.get("DARAJA_SANDBOX_PASS_KEY")
        )

        self.DARAJA_BUSINESS_SHORT_CODE = (
            os.environ.get("DARAJA_LIVE_BUSINESS_SHORT_CODE")
            if self.is_prod
            else os.environ.get("DARAJA_SANDBOX_BUSINESS_SHORT_CODE")
        )

        self.DARAJA_STKPUSH_URL = (
            os.environ.get("DARAJA_LIVE_STKPUSH_URL")
            if self.is_prod
            else os.environ.get("DARAJA_SANDBOX_STKPUSH_URL")
        )

        self.DARAJA_STKPUSH_QUERY_URL = (
            os.environ.get("DARAJA_LIVE_STKPUSH_QUERY_URL")
            if self.is_prod
            else os.environ.get("DARAJA_SANDBOX_STKPUSH_QUERY_URL")
        )

        self.DARAJA_C2B_REGISTER_URL = (
            os.environ.get("DARAJA_LIVE_C2B_REGISTER_URL")
            if self.is_prod
            else os.environ.get("DARAJA_SANDBOX_C2B_REGISTER_URL")
        )

        self.DARAJA_C2B_BUSINESS_SHORT_CODE = (
            os.environ.get("DARAJA_LIVE_BUSINESS_SHORT_CODE")
            if self.is_prod
            else "600996"
        )

        self.DARAJA_B2C_BUSINESS_SHORT_CODE = (
            os.environ.get("DARAJA_LIVE_BUSINESS_SHORT_CODE")
            if self.is_prod
            else "600996"
        )
