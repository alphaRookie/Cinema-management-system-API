# In this domain, admin is for monitoring and manage the business
# Good for troubleshooting, manual override, doing refund

from django.contrib import admin
from .models import Booking, Ticket
from screening.models import Seat
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
        # Saves the Booking fields (user, showtime, quantity, etc) to generate the PK (bcoz M2M require both sides(booking and seat) to have IDs before they can be connected.)
        super().save_model(request, obj, form, change)

        # Extract seat_ids from the form because Admin uses 'seats' ManyToMany
        seat_ids = [seat.id for seat in form.cleaned_data.get('seats', [])]


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "seats":
            # If we are looking at a specific ticket already
            resolved = request.resolver_match
            if resolved and 'object_id' in resolved.kwargs:
                ticket = self.get_object(request, resolved.kwargs['object_id'])
                
                if ticket and ticket.booking:
                    # RULE: Only show seats that belong to the Hall of this booking's showtime
                    kwargs["queryset"] = Seat.objects.filter(hall=ticket.booking.showtime.hall)
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """ To see who is sitting where """
    list_display = ("id", "booking", "seat")
    search_fields = ("booking__id", )

