from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

class Booking(models.Model):
    """ Represents a user's transaction for a specific showtime. It tracks the payment status and the number of tickets bought """
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        CONFIRMED = "CONFIRMED", _("Confirmed")
        CANCELLED = "CANCELLED", _("Cancelled")
        EXPIRED = "EXPIRED", _("Expired")

    showtime = models.ForeignKey("screening.Showtime", on_delete=models.CASCADE)
    #user = models.ForeignKey("account.blabla", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) # pake sementara sebelum buat account
    quantity = models.PositiveSmallIntegerField(
        choices=[(q, q) for q in range(1, 11)],
        default=1, 
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True) # auto grab the current time
    #in case the price will change someday, this will freeze the price 
    #I buy a shirt for $10 yesterday, today that shirt increase to $12, the receipt history now says: "You paid $12 yesterday" (`final_price` overcome the bug)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 

    def __str__(self):
        return f"Booking {self.pk} for {self.user}" # pk refer to id as default

    def total_price(self): # By putting it in the Model, we make "calculator" that available everywhere in the app without writing it twice
        return self.showtime.price * self.quantity


class Ticket(models.Model):
    """ Represents the Seat is already occupied """
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    seat = models.ForeignKey("screening.Seat", on_delete=models.CASCADE)


class SeatLock(models.Model):
    """ Represents the Seat is being "On hold" (Temporary) """
    showtime = models.ForeignKey("screening.Showtime", on_delete=models.CASCADE)
    seat = models.ForeignKey("screening.Seat", on_delete=models.CASCADE)
    #user = models.ForeignKey("account.blabla", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) 
    locked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField() # make logic that deletes seatlock after 10 minutes if not paid yet

