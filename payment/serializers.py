# This handles the input from the user (like the payment "Token" from the frontend) and validates that the data is correct

from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    payment_token = serializers.CharField(write_only=True) #"temporary" field for the Stripe card token
    
    class Meta:
        model = Payment
        fields = ["booking", "stripe_charge_id", "amount", "status", "created_at", "payment_token"]
        read_only_fields = ["created_at", "status", "amount"]
