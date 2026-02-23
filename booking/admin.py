# In this domain, admin is for monitoring and manage the business
# Good for troubleshooting, manual override, doing refund

from django.contrib import admin
from .models import Booking, Ticket, SeatLock

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """ To manage money and status """
    list_display = ("id", "showtime", "user", "status", "quantity", "created_at", "final_price")
    list_filter = ("status", "created_at")
    readonly_fields = ("created_at", "final_price")
    #search_fields = ("user__email",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """ To see who is sitting where """
    list_display = ("id", "booking", "seat")
    search_fields = ("booking__id", )


@admin.register(SeatLock)
class SeatLockAdmin(admin.ModelAdmin):
    """ To monitor temporary lock """
    list_display = ("id", "showtime", "seat", "user", "locked_at", "expires_at")
    list_filter = ("locked_at",) # see which seats were locked in last hours, etc
    readonly_fields = ("locked_at", "expires_at")
    #search_fields = ("user__email",)
