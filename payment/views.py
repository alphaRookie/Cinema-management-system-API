# This acts as the Receptionist. it receives the request, asks the Serializer if the data is okay, and then hands the work to the Service

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Payment
from .serializers import PaymentReadSerializer, PaymentWriteSerializer, PaymentResponseSerializer
from .services import PaymentService
from booking.models import Booking
from django.shortcuts import get_object_or_404
from .permissions import IsManager, IsPaymentOwner
from drf_spectacular.utils import extend_schema, extend_schema_view


@extend_schema_view(
    get=extend_schema(summary="For user to see all of his payment receipts collection", responses={200: PaymentReadSerializer(many=True)}),
)
class PaymentAPIView(APIView):
    permission_classes = [IsAuthenticated, IsPaymentOwner]

    def get(self, request):
        list_payments = Payment.objects.filter(
            booking__user=request.user, # payment dont have user field, so we connect user via booking
            status = "SUCCESS", # This will hide the FAILED part
        ).order_by("-created_at") # minus is reverse, put the newest at top
        serializer = PaymentReadSerializer(list_payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

@extend_schema_view(
    get=extend_schema(summary="For user to see the detail of his payment receipts", responses={200: PaymentReadSerializer}),
)
class PaymentItemAPIView(APIView):
    permission_classes = [IsAuthenticated, IsPaymentOwner]

    def get(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk) # dont put `user=request.user`, bcoz we dont have the field
        self.check_object_permissions(request, payment) # This triggers IsPaymentOwner to check if payment.booking.user == request.user
        serializer = PaymentReadSerializer(payment)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    post=extend_schema(summary="Proceed the Payment process", request=PaymentWriteSerializer, responses={201: PaymentResponseSerializer})
)
class PaymentPostAPIView(APIView):
    permission_classes = [IsAuthenticated] # no need to include owner, bcoz payment not exist yet

    def post(self, request):
        serializer = PaymentWriteSerializer(data=request.data)
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
            "payment": PaymentReadSerializer(payment).data
        }, status=status.HTTP_201_CREATED)


#-------------------- ADMIN --------------------

@extend_schema_view(
    get=extend_schema(summary="Admin: to see all of the payments happened", responses={200: PaymentReadSerializer(many=True)}),
)
class AdminPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        list_payments = Payment.objects.all().order_by("-created_at")
        serializer = PaymentReadSerializer(list_payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(summary="Admin: to see the detail of a payment receipts", responses={200: PaymentReadSerializer}),
)
class AdminPaymentItemAPIView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request, pk):
        # detail of a customer's digital receipt
        payment = get_object_or_404(Payment, pk=pk)
        serializer = PaymentReadSerializer(payment)
        return Response(serializer.data, status=status.HTTP_200_OK)
