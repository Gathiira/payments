import imp

from rest_framework import serializers

from utils.core import validate_phone_number


class StkPushSerializer(serializers.Serializer):
    amount = serializers.IntegerField(required=True, min_value=1)
    phone_number = serializers.CharField(required=True)
    description = serializers.CharField(required=False)

    def validate_phone_number(self, phone_number):
        # validate phone_number
        valid_number = validate_phone_number(phone_number)
        if not valid_number:
            raise serializers.ValidationError("Kindly add a valid phone number")
        return valid_number
