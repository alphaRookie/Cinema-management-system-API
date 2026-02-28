from django.urls import path
from .views import PaymentListAPIView, PaymentPostAPIView

urlpatterns = [
    # GET: List history for the current user
    path("", PaymentListAPIView.as_view(), name="payment-list"),
    
    # POST: Process a new payment via Stripe
    path("process/", PaymentPostAPIView.as_view(), name="payment-process"),
]
