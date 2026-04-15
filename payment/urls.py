from django.urls import path
from .views import PaymentAPIView, PaymentPostAPIView, AdminPaymentAPIView

urlpatterns = [
    path("/receipt", PaymentAPIView.as_view(), name="payment-list"),
    path("/receipt/<int:pk>", PaymentAPIView.as_view(), name="payment-detail"),
    
    path("", PaymentPostAPIView.as_view(), name="payment-post"), # Process a new payment via Stripe

    path("/admin", AdminPaymentAPIView.as_view(), name="adm-payment-list"),
    path("/admin/<int:pk>", AdminPaymentAPIView.as_view(), name="adm-payment-detail")
]
