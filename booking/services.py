from .models import Booking, Ticket
from screening.models import Showtime, Seat
from identity.models import User

from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from datetime import timedelta 
from django.core.cache import cache


# "What stops this Booking from being allowed?" 
class BookingService:
    @staticmethod # no need to assign `self`
    def make_booking(
        booking: Booking | None = None, 
        user: User | None = None, 
        showtime: Showtime | None = None, 
        quantity: int | None = None, 
        seat_ids: list[int] | None = None,
        **kwargs # will recognize auto-add field
        # default all to None, so in PATCH, we can just update 1 thing and left other
    ):

        # ---Setup processed input data---
        input_showtime = showtime if showtime else (booking.showtime if booking else None) # use showtime if indeed exist, otherwise take from db if indeed exist in db, if not return None
        if not input_showtime:
            raise ValidationError("Showtime is required.") # if none happens
        
        if seat_ids is None and booking: # if seat_ids not provided, but booking field in Ticket is exist
            # If we are UPDATING (Admin), look at existing tickets
            input_seat_ids = list(Ticket.objects.filter(user=booking.user, showtime=booking.showtime).values_list("seat_id", flat=True)) 
        else: 
            # If it's a new booking, we get the list from the user
            input_seat_ids = seat_ids or []
        
        input_quantity = quantity if quantity else (booking.quantity if booking else len(input_seat_ids)) # when admin didnt put quantity, count all selected seats
        if not input_quantity:
            raise ValidationError("Quantity is required")
        
        if not user:
            raise ValidationError("User information is missing")


        # Since the action is one single event, keep these 3 different logics together makes it Atomic
        # 1. Check if movie is already over or started
        if input_showtime.end_at < timezone.now(): #if current time is after ending time
            raise ValidationError("The movie is already finished")
        
        if input_showtime.start_at < timezone.now(): #if current time is more than starting line time
            raise ValidationError("The movie is already started")
        

        # 2. Check if the seat is already taken 
        if input_quantity != len(input_seat_ids):
            raise ValidationError(f"Quantity ({input_quantity}) must match seat count ({len(input_seat_ids)})")
        
        taken_ticket = Ticket.objects.filter( #"Find me any Ticket that matches This Showtime AND is in This List of Seats"
            booking__showtime = input_showtime, # sql way of doing "booking.showtime" (to access showtime from Ticket)
            seat_id__in = input_seat_ids, # "__in" is for accessing list
        ).exists()

        if taken_ticket:
            raise ValidationError("One or more seats are already sold")
        
        existing_seats_count = Seat.objects.filter(id__in=input_seat_ids).count()
        if existing_seats_count != len(input_seat_ids):
            raise ValidationError("one or more seats is not available")
        

        # 3. Check if seat is locked by someone also prevent duplicate (with REDIS)
        for s_id in input_seat_ids:
            lock_key = f"lock:{input_showtime.id}:{s_id}" # "Name Tag" for the specific seat and showtime to be locked ; separate by `:` semantically 
            locked_by_user = cache.get(lock_key) # "The action" to find out if a certain "name tag" is already locked (Return None or Id)

            if locked_by_user:
                if locked_by_user == user.id:
                    raise ValidationError(f"You already have a pending booking for these seats. Please pay for the existing one")
                else:
                    raise ValidationError(f"Seat {s_id} is on hold by someone else.")
        
        # we lock it after checking all (Check All-then-Act All)
        for s_id in input_seat_ids:
            lock_key = f"lock:{input_showtime.id}:{s_id}"
            cache.set(lock_key, user.id, timeout=600) # Auto-delete in 600 seconds (10 mins)


        #patch for admin
        if booking:
            with transaction.atomic():
                # delete prev data
                Ticket.objects.filter(booking=booking).delete() #delete ticket for this booking (delete from Ticket where booking=...)

                #update existing booking (what admin input)
                booking.quantity = input_quantity
                booking.showtime = input_showtime
                booking.final_price = booking.showtime.price * booking.quantity # price sync
                
                booking.save()

                for s_id in input_seat_ids: # bcoz prev ticket is deleted, so admin recreate new ticket
                    Ticket.objects.create(booking = booking, seat_id = s_id)
                # Admin is manually confirming booking, so no need SeatLock
                
            return booking
        
        
        # Booking and seatlock is created at same time, while ticket is created after payment
        with transaction.atomic():
            # 1. makes a row in Booking table. Let's say it gets ID: 100
            new_booking = Booking.objects.create(
                user = user,
                showtime = input_showtime,
                quantity = input_quantity,
                final_price = input_showtime.price * input_quantity, # whatever user pays on this day is recorded
                status = "PENDING"
            )

            # 2. Then `.set()` looks at that hidden bridge table
            # It says: "Make a new connection: Booking 100 <-> Seat 5 and Booking 100 <-> Seat 6"
            new_booking.seats.set(input_seat_ids)
   
        return new_booking


    @staticmethod
    def confirm_booking(booking: Booking):
    # moving from Seatlock(waiting room) to Ticket(sacred room)

        if booking.status != "PENDING":
            raise ValidationError(f"This booking is already {booking.status}") # stops if already expired/booked
        
        # 1. list all seats found in Booking table
        reserved_seats = booking.seats.all() # "gimme all seats for this spesific booking"

        # 2. Check Redis for EVERY seat
        for each_seat in reserved_seats:
            lock_key = f"lock:{booking.showtime.id}:{each_seat.id}"

            # This is how you "access the db of redis" to check
            if not cache.get(lock_key):
                # Apply these to db when 10 minutes is up
                booking.status = "EXPIRED"
                booking.save()
                raise ValidationError("10 minutes payment time exceeded, please make the new one")

        # 3. If user make payment within 10 minutes, we make sacred Ticket table
        with transaction.atomic():
            booking.status = "CONFIRMED"
            booking.save()

            # # Mass create the tickets
            for each_seat in reserved_seats:
                Ticket.objects.create(booking=booking, seat=each_seat)

        # 4. Clear Redis now since the seat is already sold
        for seat in reserved_seats:
            cache.delete(f"lock:{booking.showtime.id}:{seat.id}")

        return booking # give back the result once function finished
    
    
    @staticmethod
    def cancel_booking(booking: Booking):  

        # if user intendedly cancel the ticket (that already bought) and ask for refund, set CANCELLED
        if booking.status == "CONFIRMED":
            if booking.showtime.start_at < timezone.now():
                raise ValidationError("Movie is already started, you can't cancel the ticket now")
            
            if booking.showtime.end_at < timezone.now():
                raise ValidationError("The showtime has finished")
            
            Ticket.objects.filter(booking=booking).delete() # only delete ticket for this booking
            booking.status = "CANCELLED"


        # if within 10 mins seatlock: user cancel the payment, so delete seatlock, and set status to CANCELLED
        elif booking.status == "PENDING": # use elif bcoz it's completely different situation
            reserved_seats = booking.seats.all() # "gimme all seats for this spesific booking"
            for seat in reserved_seats:
                cache.delete(f"lock:{booking.showtime.id}:{seat.id}")
            
            booking.status = "CANCELLED" 

        booking.save()
        return booking


# why dont need to create another service?
# a customer doesn't "make a ticket" then "make a lock." They just "Book a Movie." 
