# This is the History. It stores the Stripe "Transaction ID" and the amount. Even if the booking is deleted later, we still have the record that money was taken

from django.db import models

class Payment(models.Model):
    """ To record every time someone tries to pay """
    booking = models.ForeignKey("booking.Booking", on_delete=models.PROTECT) # Cant delete booking if payment attached
    stripe_charge_id = models.CharField(max_length=100, blank=True) # Stripe ID (receipt).. Its Generated, We get this from Stripe (intent.id) after the bank says yes
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[("SUCCESS", "Success"), ("FAILED", "Failed")])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.booking.user} - {self.booking.showtime} - Status:{self.status}"
