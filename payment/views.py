# This acts as the Receptionist. it receives the request, asks the Serializer if the data is okay, and then hands the work to the Service

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Payment
from .serializers import PaymentSerializer
from .services import PaymentService
from booking.models import Booking
from django.shortcuts import get_object_or_404
from .permissions import IsManager, IsPaymentOwner


class PaymentAPIView(APIView):
    permission_classes = [IsAuthenticated, IsPaymentOwner]

    def get(self, request, pk=None):
        if pk:
            payment = get_object_or_404(Payment, pk=pk) # dont put `user=request.user`, bcoz we dont have the field
            self.check_object_permissions(request, payment) # This triggers IsPaymentOwner to check if payment.booking.user == request.user
            serializer = PaymentSerializer(payment)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        list_payments = Payment.objects.filter(
            booking__user=request.user, # payment dont have user field, so we connect user via booking
            status = "SUCCESS", # This will hide the FAILED part
        ).order_by("-created_at") # minus is reverse, put the newest at top
        serializer = PaymentSerializer(list_payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PaymentPostAPIView(APIView):
    permission_classes = [IsAuthenticated] # no need to include owner, bcoz payment not exist yet

    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Normally we use `pk=pk` to know which booking or sth, which accessible by typing number in url
        # But here we access it from JSON package
        # The user sends a new request to /payments/. Inside that "JSON Package," they include "booking": 21
        booking = get_object_or_404(Booking, id=serializer.validated_data.get("booking").id, user=request.user)

        payment = PaymentService.process_payment( #pass the actual object and the token string
            booking=booking, 
            payment_token=serializer.validated_data.get("payment_token")
        ) 
        return Response({
            "message": "Payment Successful!",
            "payment": PaymentSerializer(payment).data
        }, status=status.HTTP_201_CREATED)


class AdminPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request, pk=None):
        if pk:
            # detail of a customer's digital receipt
            payment = get_object_or_404(Payment, pk=pk)
            serializer = PaymentSerializer(payment)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        # Manager can see all of the payments happened
        list_payments = Payment.objects.all().order_by("-created_at")
        serializer = PaymentSerializer(list_payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
