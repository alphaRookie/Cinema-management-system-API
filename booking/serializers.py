from rest_framework import serializers
from rest_framework.serializers import ValidationError
from .models import Booking, Ticket

class BookingBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["id", "showtime", "user", "seats", "quantity", "status", "created_at", "final_price"]
        read_only_fields = ["id", "user", "seats","status", "created_at", "final_price"]


class BookingReadSerializer(BookingBaseSerializer):
    choosen_seats = serializers.SerializerMethodField() # We add a way to see the seats actually saved in the Ticket table
    class Meta(BookingBaseSerializer.Meta):
        fields = BookingBaseSerializer.Meta.fields + ["choosen_seats"]

    def get_choosen_seats(self, obj):
        # If the booking is already CONFIRMED, look in the Ticket table (sacred)
        if obj.status == "CONFIRMED":
            return Ticket.objects.filter(booking=obj).values_list("seat_id", flat=True) # This shows the list of seat IDs for the user to see
        
        # If it's PENDING or EXPIRED, show what was saved in the "waiting room"
        # "Look at those rows in the bridge table(join) and just give me a list of the Seat IDs."
        return obj.seats.values_list("id", flat=True)    


class BookingWriteSerializer(BookingBaseSerializer):
    seat_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True)
    class Meta(BookingBaseSerializer.Meta):
        fields = BookingBaseSerializer.Meta.fields + ["seat_ids"]

    def validate_seat_ids(self, value):
        if not value:
            raise ValidationError("You must select at least one seat")
        return value


#Swagger
class MessageSerializer(serializers.Serializer):
    message = serializers.CharField

class BookingResponseSerializer(MessageSerializer):
    booking = BookingWriteSerializer()
    