from .models import Booking, Ticket
from screening.models import Showtime, Seat, Hall, Movie
from payment.models import Payment
from identity.models import User
from datetime import timedelta
from django.utils.dateparse import parse_date

from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Count, Avg, Max, Min, Sum, Q, F
from decimal import Decimal # best for money calculation (because it's exact)


# "What stops this Booking from being allowed?" 
# why dont need to create another service? a customer doesn't "make a ticket" then "make a lock." They just "Book a Movie." 
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
        showtime = showtime if showtime else (booking.showtime if booking else None) # use showtime if indeed exist, otherwise take from db if indeed exist in db, if not return None
        if not showtime:
            raise ValidationError("Showtime is required.") # if none happens
        
        if seat_ids is None: # Check if we have IDs from API, if not, try to get them from the booking object
            if booking and booking.id: 
                # # If the booking already exists (Update by Admin), 
                seat_ids = list(booking.seats.values_list('id', flat=True)) # get the IDs from the M2M field
            else: 
                # If it's a new booking, we get the list from the user
                seat_ids = []
        
        quantity = quantity if quantity else (booking.quantity if booking else len(seat_ids)) # when admin didnt put quantity, count all selected seats
        if not quantity:
            raise ValidationError("Quantity is required")
        
        if not user:
            raise ValidationError("User information is missing")


        # Since the action is one single event, keep these 3 different logics together makes it Atomic
        # 1. Check if movie is already over or started
        if showtime.end_at < timezone.now(): #if current time is after ending time
            raise ValidationError("The movie is already finished")
        
        if showtime.start_at < timezone.now(): #if current time is more than starting line time
            raise ValidationError("The movie is already started")
        
        
        # 2. Check if the quantity is equal to how much seat selected
        if quantity != len(seat_ids):
            raise ValidationError(f"Quantity ({quantity}) must match seat count ({len(seat_ids)})")
        

        # 3. check if inputted seatid(by user) is indeed belong to that spesific hall
        # (if showtime 1 plays in hall "IMAX 1" and range seat is 1-50, means if user choose beside ID 1-50, return error)
        seat_found = Seat.objects.filter(id__in=seat_ids, hall=showtime.hall)
        if seat_found.count() != len(seat_ids):
            raise ValidationError("One or more seats do not belong to the hall for this showtime")
        

        # 4. find out if the spesific hall is already full
        ticket_counts = Ticket.objects.filter(
            booking__showtime__hall = showtime.hall, # cant do "hall=hall" bcoz Ticket table has no hall column
            booking__showtime__movie = showtime.movie
        ).count()
        #count all seats for this spesific hall
        hall_capacity = showtime.hall.seats_per_row * showtime.hall.seats_per_column

        if (ticket_counts + len(seat_ids)) > hall_capacity: # case: if seats already sold 49/50, then a person buy 2 tickets
            raise ValidationError(f"Not enough seats available. Only {hall_capacity - ticket_counts} seats left")
        

        # 5. Check if the seat is already taken 
        taken_ticket = Ticket.objects.filter( #"Find me any Ticket that matches This Showtime AND is in This List of Seats"
            booking__showtime = showtime, # sql way of doing "booking.showtime" (to access showtime from Ticket)
            seat_id__in = seat_ids, # "__in" is for accessing list
        ).exists()

        if taken_ticket:
            raise ValidationError("One or more seats are already sold")
        

        # 6. check if selected seat is broken
        # 7. Fallback: ensure all IDs numbers entered is exist in the DB
        selected_seats = Seat.objects.filter(id__in=seat_ids) # out of these (___) selected seat IDs by user..

        if selected_seats.filter(is_broken=True).exists(): #.. we filter if any of these selected seat flagged by broken is exist
            raise ValidationError("This seat is currently under maintenance")
        
        if selected_seats.count() != len(seat_ids): #.. we .count() to see how many valid records, if retured valid record is not equal to how many user ids picked ...
            raise ValidationError("one or more seats is not available")
        
        
        # 8. Check if seat is locked by someone also prevent duplicate (with REDIS)
        for s_id in seat_ids:
            lock_key = f"lock:{showtime.id}:{s_id}" # "Name Tag" for the specific seat and showtime to be locked ; separate by `:` semantically 
            locked_by_user = cache.get(lock_key) # "The action" to find out if a certain "name tag" is already locked (Return None or Id)

            if locked_by_user:
                if locked_by_user == user.id:
                    raise ValidationError(f"You already have a pending booking for these seats. Please pay for the existing one")
                else:
                    raise ValidationError(f"Seat {s_id} is on hold by someone else.")
        
        # we lock it after checking all (Check All-then-Act All)
        # ORDER MATTER !!! THIS MUST BE AFTER ALL VALIDATIONS
        for s_id in seat_ids:
            lock_key = f"lock:{showtime.id}:{s_id}"
            cache.set(lock_key, user.id, timeout=600) # Auto-delete in 600 seconds (10 mins)


        #patch for admin
        if booking:
            with transaction.atomic():
                # delete prev data
                Ticket.objects.filter(booking=booking).delete() #delete ticket for this booking (delete from Ticket where booking=...)

                #update existing booking (what admin input)
                booking.quantity = quantity
                booking.showtime = showtime
                booking.final_price = booking.showtime.price * booking.quantity # price sync
                
                booking.save()

                # Sync M2M: This ensures the 'seats' table(M2M) matches the new 'seat_ids'(temp write field)
                booking.seats.set(seat_ids)

                for s_id in seat_ids: # bcoz prev ticket is deleted, so admin recreate new ticket
                    Ticket.objects.create(booking = booking, seat_id = s_id)
                # Admin is manually confirming booking, so no need SeatLock
                
            return booking
        
        
        # Booking and seatlock is created at same time, while ticket is created after payment
        with transaction.atomic():
            # 1. makes a row in Booking table. Let's say it gets ID: 100
            new_booking = Booking.objects.create(
                user = user,
                showtime = showtime,
                quantity = quantity,
                final_price = showtime.price * quantity, # whatever user pays on this day is recorded
                status = "PENDING"
            )

            # 2. Then `.set()` looks at that hidden bridge table (seats to booking)
            # It says: "Make a new connection: Booking 100 <-> Seat 5 and Booking 100 <-> Seat 6"
            new_booking.seats.set(seat_ids)
   
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

            # Every time this loop runs, it creates ONE separate row in the Ticket table (now each person gets his own ticket)
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

 

class BookingAnalytic:
    @staticmethod
    def booking_report(): #no need param, bcoz we fetch below
        """ Showing real-time booking report of the whole system (for upcoming show) """
        future_report = Booking.objects.filter(showtime__start_at__gt=timezone.now()) \
        .select_related("showtime__movie", "showtime__hall", "user") \
        .prefetch_related("seats") \
        .order_by("-created_at")

        reports = []

        for fr in future_report:
            reports.append({
                "movie": fr.showtime.movie.title,
                "hall": fr.showtime.hall.name,
                "show_start": fr.showtime.start_at.strftime("%d %b, %H:%M"),
                "quantity": fr.quantity,
                "seats": [f"{s.row_label}-{s.column_number}" for s in fr.seats.all()], #prefetch m2m
                "final_price": f"{int(fr.final_price)}$",
                "status": fr.status,
                "email": fr.user.email,
                "created_at": fr.created_at.strftime("%d %b %Y, %H:%M") # result: "04 May 2026, 18:34"
            })
        return reports


    @staticmethod
    def financial_report(period=None, startdate_input=None, enddate_input=None):
        """ Showing all report related to financial """ 

        booking_qs = Booking.objects.filter(status="CONFIRMED")
        showtime_qs = Showtime.objects.select_related("hall", "movie")
        
        if period == "day":
            starting_time = timezone.now() - timedelta(days=1)
            booking_qs = booking_qs.filter(created_at__gte=starting_time)
            showtime_qs = showtime_qs.filter(start_at__gte=starting_time)
        elif period == "week":
            starting_time = timezone.now() - timedelta(weeks=1)
            booking_qs = booking_qs.filter(created_at__gte=starting_time)
            showtime_qs = showtime_qs.filter(start_at__gte=starting_time)
        elif period == "month":
            starting_time = timezone.now() - timedelta(days=30)
            booking_qs = booking_qs.filter(created_at__gte=starting_time)
            showtime_qs = showtime_qs.filter(start_at__gte=starting_time)

        # Manual period input by user
        elif startdate_input or enddate_input:
            if startdate_input: #check if user send it
                start_date = parse_date(startdate_input) # take string like "2026-05-18" and turn it into real Python date object(for DB)
                if start_date: #check if parse_date actually success
                    booking_qs = booking_qs.filter(created_at__date__gte=start_date) # need __date__ because created_at has hours and minutes, but the input start_date and end_date do not. Adding it cuts off the hours and minutes so they can match up
                    showtime_qs = showtime_qs.filter(start_at__date__gte=start_date)
            
            if enddate_input:
                end_date = parse_date(enddate_input)
                if end_date:
                    booking_qs = booking_qs.filter(created_at__date__lte=end_date)
                    showtime_qs = showtime_qs.filter(start_at__date__lte=end_date) #shows what are start before inputted "end_date"


        # to show the total gross profit
        gross_profit =  booking_qs.aggregate(gp=Sum("final_price")) ["gp"] or Decimal('0')

        # to show gross profit each movie
        gp_each_movie = booking_qs.values("showtime__movie__title") \
        .annotate(gp=Sum("final_price")) \
        .order_by("-gp")
        
        # to show net profit (after calculating movie_licencing_fee(40%), tax(10%), maintenance & salary(30%) 
        expenses = (gross_profit * Decimal("0.4")) + (gross_profit * Decimal("0.1")) + (gross_profit * Decimal("0.3"))
        expected_net_profit = gross_profit - expenses


        # To show potential loss of unsold seats
        showtimes = showtime_qs.annotate(
            capacity = F("hall__seats_per_row") * F("hall__seats_per_column"), # calculate directly in DB before giving result
            # reverse relation: count how many booking(that already confirmed) in that showtime table
            sold_pershow = Count("booking", filter=Q(booking__status="CONFIRMED", booking__in=booking_qs)) # says "Is it confirmed? AND Is it part of this day/week/moths's filtered bookings?"
        )
        
        show = []
        for s in showtimes:
            unsold_seats = s.capacity - s.sold_pershow #why pylance complains? these attibute only exist for a split second while the query is running #type:ignore
            potential_loss = unsold_seats * s.price 

            show.append({
                "id": s.id,
                "movie": s.movie.title,
                "hall": s.hall.name,
                "price": s.price,
                "occupancy": f"{s.sold_pershow}/{s.capacity}", #type:ignore 
                "unsold_seats": unsold_seats,
                "potential_loss": f"{potential_loss}$",
                "max_revenue": f"{s.price * s.capacity}$" #type:ignore
            })
            

        #wrap in Dictionary (to know which number belong to which)
        return{
            "expected_net_profit": f"{expected_net_profit}$" or 0,
            "gross_profit": f"{gross_profit}$" or 0,
            "gross_profit_movie": [
                {
                    "movie": mov["showtime__movie__title"], # customize return here, instead of new serializer field
                    "profit": f"{mov["gp"]}$"
                } for mov in gp_each_movie
            ],
            "expenses": f"{expenses}$",
            "potential_loss": show
        } 
