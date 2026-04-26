from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated # only logged-in users can book or see bookings
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Booking
from .serializers import BookingWriteSerializer, BookingReadSerializer, BookingResponseSerializer, MessageSerializer
from .services import BookingService
from .permissions import IsManager


@extend_schema_view(
    get=extend_schema(summary="List All Bookings", responses={200: BookingReadSerializer(many=True)}),
    post=extend_schema(summary="Create a New Booking", request=BookingWriteSerializer, responses={201: BookingResponseSerializer})
)
class BookingAPIView(APIView): 
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        bookings = Booking.objects.filter(user=request.user) # Make sure the owner ID matches this specific person's ID
        serializer = BookingReadSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BookingWriteSerializer(data=request.data)
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
            "booking": BookingReadSerializer(booking).data # returning read bcoz expected output is diff to the input
        },status=status.HTTP_201_CREATED)
    

@extend_schema_view(
    get=extend_schema(summary="Retrieve the details of a specific booking by ID", responses={200: BookingReadSerializer}),
    delete=extend_schema(summary="Deletes a Booking by ID", responses={200: MessageSerializer})
)
class BookingItemAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, user=request.user) # This returns 404 "Not Found" if the ID is wrong OR the User is wrong
        serializer = BookingReadSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, user=request.user)
        BookingService.cancel_booking(booking)
        return Response({"message": "Booking cancelled"}, status=status.HTTP_200_OK) # we change status not delete. so user can see it in their history later


#-------------------- ADMIN --------------------

@extend_schema_view(
    get=extend_schema(summary="Admin: To see the whole customer bookings", responses={200: BookingReadSerializer(many=True)}), 
)
# Advancing admin dashboard soon !!!
class AdminBookingAPIView(APIView):
    permission_classes = [IsAuthenticated, IsManager]
    # Admin dont need POST to keep data clean(let user do).

    def get(self, request):
        bookings = Booking.objects.all().order_by("-created_at")
        serializer = BookingReadSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(summary="Admin: To find customer bookings and check his history by ID", responses={200: BookingReadSerializer}),
    patch=extend_schema(summary="Admin: Updates an existing Booking by ID.", request=BookingWriteSerializer, responses={200: BookingResponseSerializer}),
    delete=extend_schema(summary="Admin: Deletes a Booking by ID", responses={200: MessageSerializer})
)
class AdminBookingItemAPIView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk) # Managers can see ANY booking, so no user=request.user filter
        serializer = BookingReadSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # To help customers change seats or showtimes
    def patch(self, request, pk): 
        booking = get_object_or_404(Booking, pk=pk)
        serializer = BookingWriteSerializer(booking, data=request.data, partial=True)
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
            "booking": BookingReadSerializer(updated_booking).data
        }, status=status.HTTP_200_OK)
    
    # To handle cancellations and refunds
    def delete(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        BookingService.cancel_booking(booking)
        return Response({"message": f"Booking for {booking.user.email} was cancelled by Admin"}, status=status.HTTP_200_OK)
