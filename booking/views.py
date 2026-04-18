from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated # only logged-in users can book or see bookings
from django.shortcuts import get_object_or_404

from .models import Booking
from .serializers import BookingSerializer, BookingReadonlySerializer
from .services import BookingService
from .permissions import IsManager


class BookingAPIView(APIView): 
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk=None): # MUST default to `None`, so it considered optional
        if pk:
            # if URL has ID, look at ONE specific booking
            booking = get_object_or_404(Booking, pk=pk, user=request.user) # This returns 404 "Not Found" if the ID is wrong OR the User is wrong
            serializer = BookingReadonlySerializer(booking)
            return Response(serializer.data, status=status.HTTP_200_OK)
    
        # if URL has no ID, look at the WHOLE list
        bookings = Booking.objects.filter(user=request.user) # Make sure the owner ID matches this specific person's ID
        serializer = BookingReadonlySerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # DRF already turned the ID into an Object
        booking = BookingService.make_booking(
            booking=None, 
            user=request.user,  # we pass the user from the request into our service (this prevents users from booking for someone else)
            showtime=serializer.validated_data.get("showtime"),
            quantity=serializer.validated_data.get("quantity"),
            seat_ids=serializer.validated_data.get("seat_ids"),
        )
        # We return the Readonly version because it shows the "seats" field
        return Response({
            "message": "Booking successfully created, you have 10 minutes to complete the Payment",
            "booking": BookingReadonlySerializer(booking).data
        },status=status.HTTP_201_CREATED)
    

    def delete(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, user=request.user)
        BookingService.cancel_booking(booking)
        return Response({"message": "Booking cancelled"}, status=status.HTTP_200_OK) # we change status not delete. so user can see it in their history later


# Advancing admin dashboard soon !!!
class AdminBookingAPIView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    # Admin dont need POST to keep data clean(let user do).

    # To find customer tickets and check history
    def get(self, request, pk=None):
        if pk:
            booking = get_object_or_404(Booking, pk=pk) # Managers can see ANY booking, so no user=request.user filter
            serializer = BookingReadonlySerializer(booking)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        # this is like seeing whole list of booking in djangoadmin
        bookings = Booking.objects.all().order_by("-created_at")
        serializer = BookingReadonlySerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    
    # To help customers change seats or showtimes
    def patch(self, request, pk): 
        booking = get_object_or_404(Booking, pk=pk)
        serializer = BookingSerializer(booking, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        updated_booking = BookingService.make_booking(
            booking=booking, # pass the existing booking object into our service 
            user=booking.user, # referring to the Owner of that booking, not request.user
            showtime=serializer.validated_data.get("showtime"),
            quantity=serializer.validated_data.get("quantity"),
            seat_ids=serializer.validated_data.get("seat_ids"),
        )
        return Response({
            "message": f"Booking for {booking.user.email} successfully updated by Admin",
            "booking": BookingReadonlySerializer(updated_booking).data
        }, status=status.HTTP_200_OK)
    
    
    # To handle cancellations and refunds
    def delete(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        BookingService.cancel_booking(booking)
        return Response({"message": f"Booking for {booking.user.email} was cancelled by Admin"}, status=status.HTTP_200_OK)
