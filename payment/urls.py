from django.urls import path
from .views import PaymentAPIView, PaymentItemAPIView, PaymentPostAPIView, AdminPaymentAPIView, AdminPaymentItemAPIView

urlpatterns = [
    path("/receipt", PaymentAPIView.as_view(), name="payment-list"),
    path("/receipt/<int:pk>", PaymentItemAPIView.as_view(), name="payment-detail"),
    
    path("", PaymentPostAPIView.as_view(), name="payment-post"), # Process a new payment via Stripe

    path("/adm", AdminPaymentAPIView.as_view(), name="adm-payment-list"),
    path("/adm/<int:pk>", AdminPaymentItemAPIView.as_view(), name="adm-payment-detail")
]
