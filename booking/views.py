
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated # only logged-in users can book or see bookings
from django.shortcuts import get_object_or_404

from .models import Booking
from .serializers import BookingSerializer, BookingReadonlySerializer
from .services import BookingService

class BookingListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = Booking.objects.filter(user=request.user) # We only show the bookings that belong to the logged-in user
        serializer = BookingReadonlySerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # we pass the user from the request into our service (this prevents users from booking for someone else)
        booking = BookingService.make_booking(None, user=request.user, **serializer.validated_data)
        
        # We return the Readonly version because it shows the "seats" field
        return Response(BookingReadonlySerializer(booking).data, status=status.HTTP_201_CREATED)
    

class BookingDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, user=request.user)
        serializer = BookingReadonlySerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk): # Admins usually use this, but we'll fetch the booking first
        booking = get_object_or_404(Booking, pk=pk)
        serializer = BookingSerializer(booking, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # We pass the existing booking object into our service
        updated_booking = BookingService.make_booking(booking, user=request.user, **serializer.validated_data)
        return Response(BookingReadonlySerializer(updated_booking).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, user=request.user)
        booking.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
