# This handles the input from the user (like the payment "Token" from the frontend) and validates that the data is correct

from rest_framework import serializers
from .models import Payment

class PaymentBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["booking", "stripe_charge_id", "amount", "status", "created_at"]
        read_only_fields = ["created_at", "status", "amount", "stripe_charge_id"]

class PaymentReadSerializer(PaymentBaseSerializer):
    class Meta(PaymentBaseSerializer.Meta):
        pass #use the same field

class PaymentWriteSerializer(PaymentBaseSerializer):
    payment_token = serializers.CharField(write_only=True) #"temporary" field for the Stripe card token (we dont want to show this to user)
    class Meta(PaymentBaseSerializer.Meta):
        fields = PaymentBaseSerializer.Meta.fields + ["payment_token"]


#Swagger
class MessageSerializer(serializers.Serializer):
    serializer = serializers.CharField()

class PaymentResponseSerializer(MessageSerializer):
    payment = PaymentReadSerializer() #show the read
