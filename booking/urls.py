from django.urls import path
from .views import BookingAPIView, BookingItemAPIView, AdminBookingAPIView, AdminBookingItemAPIView

urlpatterns = [
    path("", BookingAPIView.as_view(), name="booking-list"), # booking list and post handled here
    path("/<int:pk>", BookingItemAPIView.as_view(), name="booking-detail"), # booking detail and delete handled here

    path("/adm", AdminBookingAPIView.as_view(), name="adm-booking-list"),
    path("/adm/<int:pk>", AdminBookingItemAPIView.as_view(), name="adm-booking-detail")
]
