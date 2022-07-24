from rest_framework import serializers

from payments.models import PaymentMethod, Transaction


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = '__all__'


class TransactionSerializer(serializers.ModelSerializer):
    method = PaymentMethodSerializer(many=False)

    class Meta:
        model = Transaction
        fields = '__all__'
