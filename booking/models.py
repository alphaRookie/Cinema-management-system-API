from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from rest_framework.exceptions import ValidationError

class Booking(models.Model):
    """ Represents a user's transaction for a specific showtime. It tracks the payment status and the number of tickets bought """
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        CONFIRMED = "CONFIRMED", _("Confirmed")
        CANCELLED = "CANCELLED", _("Cancelled")
        EXPIRED = "EXPIRED", _("Expired")

    id: int
    showtime = models.ForeignKey("screening.Showtime", on_delete=models.CASCADE)
    user = models.ForeignKey("identity.User", on_delete=models.CASCADE)
    # Use M2M so one booking can link to many seats (1 person can book for his friends and also do 1 payment instead of separated payment for each ticket)
    seats = models.ManyToManyField("screening.Seat", related_name="bookings") # this field is for Storage(after validated). while "seat_ids" in serializer is temp field that carries user input so we can do validation in service
    quantity = models.PositiveSmallIntegerField(
        choices=[(q, q) for q in range(1, 11)],
        default=1, 
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True) # auto grab the current time
    final_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) #in case the price will change someday, this will freeze the price 

    def __str__(self):
        return f"Booking {self.pk} for {self.user} : {self.showtime}" # pk refer to id as default

    def total_price(self): # By putting it in the Model, we make "calculator" that available everywhere in the app without writing it twice
        return self.showtime.price * self.quantity
    
    
    def clean(self):
        if self.pk and self.showtime:
            # Loop through every seat selected in this booking
            for seat in self.seats.all():
                if seat.hall != self.showtime.hall:
                    raise ValidationError(f"Wrong Hall! You selected Seat {seat.row_label}-{seat.column_number} in {seat.hall.name}, but the showtime is in {self.showtime.hall.name}.")

    
    
class Ticket(models.Model):
    """ Represents the Seat is already occupied """
    id: int
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    seat = models.ForeignKey("screening.Seat", on_delete=models.CASCADE)


# Seatlock table is deleted since we apply Redis
