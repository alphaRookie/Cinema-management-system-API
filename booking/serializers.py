from rest_framework import serializers
from rest_framework.serializers import ValidationError
from .models import Booking, Ticket, SeatLock

class BookingBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["id", "showtime", "user", "quantity", "status", "created_at", "final_price"]
        read_only_fields = ["id", "user", "status", "created_at", "final_price"]


class BookingReadonlySerializer(BookingBaseSerializer):
    seats = serializers.SerializerMethodField() # We add a way to see the seats actually saved in the Ticket table
    class Meta(BookingBaseSerializer.Meta):
        fields = BookingBaseSerializer.Meta.fields + ["seats"]

    def get_seats(self, obj):
        # If the booking is already CONFIRMED, look in the Ticket table (sacred)
        if obj.status == "CONFIRMED":
            return Ticket.objects.filter(booking=obj).values_list("seat_id", flat=True) # This shows the list of seat IDs for the user to see
        
        # otherwise (if still pending) look at Seatlock table
        return SeatLock.objects.filter(user=obj.user, showtime=obj.showtime).values_list("seat_id", flat=True)


class BookingSerializer(BookingBaseSerializer):
    seat_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True)
    class Meta(BookingBaseSerializer.Meta):
        fields = BookingBaseSerializer.Meta.fields + ["seat_ids"]

    def validate_seat_ids(self, value):
        if not value:
            raise ValidationError("You must select at least one seat")
        return value

