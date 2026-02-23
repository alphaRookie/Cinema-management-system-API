from django.urls import path
from .views import BookingListAPIView, BookingDetailAPIView

urlpatterns = [
    path("", BookingListAPIView.as_view(), name="booking-list"),
    
    path("<int:pk>/", BookingDetailAPIView.as_view(), name="booking-detail"),
]
