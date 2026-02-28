from .models import Booking, Ticket, SeatLock
from screening.models import Showtime, Seat

from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import timedelta 

from django.contrib.auth import get_user_model 
User = get_user_model() # fake user

# "What stops this Booking from being allowed?" 
class BookingService:
    @staticmethod # no need to assign `self`
    def make_booking(
        booking: Booking | None = None, 
        user: User | None = None, 
        showtime: Showtime | None = None, 
        quantity: int | None = None, 
        seat_ids: list[int] | None = None
        # default all to None, so in PATCH, we can just update 1 thing and left other
    ):

        # ---Setup processed input data---
        input_showtime = showtime if showtime else (booking.showtime if booking else None) # use showtime if indeed exist, otherwise take from db if indeed exist in db, if not return None
        if not input_showtime:
            raise ValidationError("Showtime is required.") # if none happens
        
        if seat_ids is None and booking: # if seat_ids not provided, but booking field in Ticket is exist
            #"In the Seatlock table, find all rows that belong to this specific user and showtime, then tell me which Seat IDs are inside those Seatlock" then list it
            input_seat_ids = list(SeatLock.objects.filter(user=booking.user, showtime=booking.showtime).values_list("seat_id", flat=True)) 
        else:
            input_seat_ids = seat_ids or [] #get the list

        input_quantity = quantity if quantity else (booking.quantity if booking else len(input_seat_ids)) # when admin didnt put quantity, count all selected seats
        if not input_quantity:
            raise ValidationError("Quantity is required")


        # Since the action is one single event, keep these 3 different logics together makes it Atomic
        # 1. Check if movie is already over or started
        if input_showtime.end_at < timezone.now():
            raise ValidationError("The movie is already finished")
        
        if input_showtime.start_at < timezone.now():
            raise ValidationError("The movie is already started")
        

        # before doing some business logic check, we need to make sure old data is clean and clear (Find PENDING bookings that made more than 10 minutes ago)
        expired_locks = SeatLock.objects.filter(expires_at__lt = timezone.now() - timedelta(minutes=10)) # Find all User IDs and Showtime IDs that have EXPIRED locks

        for lock in expired_locks:
            Booking.objects.filter(
                # as we dont have PK, we cant do `seatlock__expires_at__lt`. So we use user and showtime as the "common ground" to find expired locks
                # Find PENDING bookings for this specific person and show
                status = "PENDING",
                showtime = lock.showtime, # ganti ke created_at bisanya jirt...besok mungkin perlu cara undo commit ?
                user = lock.user
            ).update(status = "EXPIRED") # update the status
        
        expired_locks.delete() # Wipe out the old seatlock obj


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
        

        # 3. Check if seat is locked ("on hold" by someone)
        locked_seat = SeatLock.objects.filter(
            showtime = input_showtime,
            seat_id__in = input_seat_ids,
            expires_at__gt = timezone.now() #that expires in future (means it's still locked now)
        )

        if user: # if this lock belong to this user, ignore it
            locked_seat = locked_seat.exclude(user=user)

        if locked_seat.exists(): # exlude at the end, so the user check can happen, then we can block if other user try to
            raise ValidationError("One or more seats are on hold by someone else")
        

        # if the same user has duplicate booking but havent paid yet
        duplicate_booking = SeatLock.objects.filter(
            showtime = input_showtime,
            seat_id__in = input_seat_ids,
            user = user,
        ).exists()

        if duplicate_booking:
            raise ValidationError("You already have a pending booking for these seats. Please pay for the existing one.")


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
        
        
        # Booking and seatlock is created at same time, while ticket is created after user decide
        with transaction.atomic():
            new_booking = Booking.objects.create(
                user = user,
                showtime = input_showtime,
                quantity = input_quantity,
                final_price = input_showtime.price * input_quantity, # whatever user pays on this day is recorded
                status = "PENDING"
            )

            bulk_seatlock = []
            for s_id in input_seat_ids:
                seatlock = SeatLock( # in memory
                    showtime = input_showtime,
                    user = user,
                    seat_id = s_id,
                    expires_at = timezone.now() + timedelta(minutes=10) # seatlock has 10 mins timer
                )
                bulk_seatlock.append(seatlock)
            SeatLock.objects.bulk_create(bulk_seatlock)
   
        return new_booking

    # LOGIC:
    # if within 10 mins seatlock: user did payment, delete current seatlock, and change the status to CONFIRMED

    # if within 10 mins seatlock: user cancel the payment, so delete seatlock, and set status to CANCELLED
    # or if user intendedly cancel the ticket (that already bought) and ask for refund, set CANCELLED
    
    # if within 10 mins seatlock: user did nothing, set to EXPIRED
    # if ticket is already bought, and the show is now finished, change to EXPIRED (maybe delete?)



    @staticmethod
    def confirm_booking(booking: Booking):
    # moving from Seatlock(waiting room) to Ticket(sacred room)

        if booking.status == "PENDING":
            with transaction.atomic():
                # 1. list all seats found in Seatlock table
                seat_ids = list(SeatLock.objects.filter(
                    user=booking.user, 
                    showtime=booking.showtime,
                ).values_list("seat_id", flat=True)) 

                if not seat_ids:
                    raise ValidationError("No locked seats found in this booking")
        
                # 2. create the sacred Ticket table
                for s_id in seat_ids:
                    Ticket.objects.create(booking=booking, seat_id=s_id) # expect the ID; but if we pass `seat=` it expect object

                # 3. delete the temporary lock (so nobody else can take them) 
                SeatLock.objects.filter(
                    showtime = booking.showtime,
                    user = booking.user
                ).delete()

                booking.status = "CONFIRMED"
                booking.save()

        return booking
    
    

    @staticmethod
    def cancel_booking(booking: Booking):  

        # if user intendedly cancel the ticket (that already bought) and ask for refund, set CANCELLED
        if booking.status == "CONFIRMED":
            Ticket.objects.filter(booking=booking).delete() # only delete ticket for this booking
            booking.status = "CANCELLED"

        # if within 10 mins seatlock: user cancel the payment, so delete seatlock, and set status to CANCELLED
        elif booking.status == "PENDING":
            SeatLock.objects.filter(
                showtime = booking.showtime,
                user = booking.user,
            ).delete()
            booking.status = "CANCELLED" 

        booking.save()
        return booking


# why dont need to create another service?
# a customer doesn't "make a ticket" then "make a lock." They just "Book a Movie." 
