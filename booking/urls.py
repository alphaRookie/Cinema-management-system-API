from django.urls import path
from .views import BookingAPIView, AdminBookingAPIView

urlpatterns = [
    path("", BookingAPIView.as_view(), name="booking-list"), # booking list and post handled here
    path("/<int:pk>", BookingAPIView.as_view(), name="booking-detail"), # booking detail and delete handled here

    path("/admin", AdminBookingAPIView.as_view(), name="adm-booking-list"),
    path("/admin/<int:pk>", AdminBookingAPIView.as_view(), name="adm-booking-detail")
]
