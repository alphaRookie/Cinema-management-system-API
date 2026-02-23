from .models import Booking, Ticket, SeatLock
from screening.models import Showtime, Seat

from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import timedelta 

# "What stops this Booking from being allowed?" 
class BookingService:
    @staticmethod # no need to assign `self`
    def make_booking(booking: Booking | None=None, **data):

        # Since the action is one single event, keep these 3 different logics together makes it Atomic
        # 1. Check if movie is already over or started
        showtime = get_object_or_404(Showtime, id=data.get("showtime").id) #type:ignore #SELECT * FROM showtime WHERE id=[user_input] LIMIT 1;

        if showtime.end_at < timezone.now():
            raise ValidationError("The movie is already finished")
        
        if showtime.start_at < timezone.now():
            raise ValidationError("The movie is already started")
        

        # 2. Check if the seat is already taken 
        quantity = data.get("quantity", booking.quantity if booking else 0) # when user forgot input, default to 0. instead of None(can crash when comparing below)
        seat_ids = data.get("seat_ids", []) #get the list
        if quantity != len(seat_ids):
            raise ValidationError(f"Please choose {quantity} seats")
        
        taken_ticket = Ticket.objects.filter( #"Find me any Ticket that matches This Showtime AND is in This List of Seats"
            booking__showtime = showtime, # sql way of doing "booking.showtime" (to access showtime from Ticket)
            seat_id__in = seat_ids, # "__in" is for accessing list
        ).exists()

        if taken_ticket:
            raise ValidationError("One or more seats are already sold")
        
        existing_seats_count = Seat.objects.filter(id__in=seat_ids)
        if existing_seats_count != seat_ids:
            raise ValidationError("one or more seats is not available")
        

        # 3. Check if seat is locked ("on hold" by someone)
        locked_seat = SeatLock.objects.filter(
            showtime = showtime,
            seat_id__in = seat_ids,
            expires_at__gt = timezone.now() #that expires in future (means it's still locked now)
        ).exists()

        if locked_seat:
            raise ValidationError("One or more seats are on hold by someone else")
        
        # DEBUG TEST

        #patch for admin
        if booking:
            with transaction.atomic():
                # delete prev data
                booking.ticket_set.all().delete() #type:ignore

                for key, value in data.items():
                    setattr(booking, key, value) #update existing booking (what admin input)
                
                #these 2 rules to prevent that input mistake
                booking.quantity = len(seat_ids)
                booking.final_price = booking.showtime.price * booking.quantity # price sync

                booking.save()

                for s_id in seat_ids: 
                    Ticket.objects.create( # bcoz prev ticket is deleted, so admin recreate new ticket
                        booking = booking,
                        seat_id = s_id
                    )
                # Admin is manually confirming booking, so no need SeatLock
                
            return booking
        
        
        # Tickets and SeatLocks are linked to that specific booking in DB
        with transaction.atomic():
            booking = Booking.objects.create(
                user = data.get("user"),
                showtime = showtime,
                quantity = quantity,
                final_price = showtime.price * quantity, # whatever user pays on this day is recorded
                status = "PENDING"
            )

            bulk_seatlock = []
            for s_id in seat_ids:
                Ticket.objects.create(
                    booking = booking,
                    seat_id = s_id
                )
                
                seatlock = SeatLock( # in memory
                    showtime = showtime,
                    user = data.get("user"),
                    seat_id = s_id,
                    expires_at = timezone.now() + timedelta(minutes=10) # seatlock has 10 mins timer
                )
                bulk_seatlock.append(seatlock)
            SeatLock.objects.bulk_create(bulk_seatlock)
            
        return booking


# why dont need to create another service?
# a customer doesn't "make a ticket" then "make a lock." They just "Book a Movie." 
