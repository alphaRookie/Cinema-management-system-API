# In this domain, admin is for monitoring and manage the business
# Good for troubleshooting, manual override, doing refund

from django.contrib import admin
from .models import Booking, Ticket
from .services import BookingService

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """ To manage money and status """
    list_display = ("id", "showtime", "user", "status", "quantity", "created_at", "final_price")
    list_filter = ("status", "created_at")
    readonly_fields = ("created_at", "final_price")
    search_fields = ("user__email",)

    # make admin smart
    def save_model(self, request, obj, form, change):
        BookingService.make_booking(booking=obj if change else None, **form.cleaned_data)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """ To see who is sitting where """
    list_display = ("id", "booking", "seat")
    search_fields = ("booking__id", )

