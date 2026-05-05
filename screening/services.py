# where we put logic business rules
from .models import Movie, Hall, Showtime, Seat
from identity.models import User
from booking.models import Booking, Ticket
from rest_framework.exceptions import ValidationError # in normal django we import from "django.core.exceptions"
from datetime import timedelta, date, datetime
from decimal import Decimal
from django.db import transaction
from django.db.models import Count, Avg, Max, Min, Sum
from django.utils import timezone
from django.core.cache import cache
from django_redis.cache import RedisCache


class MovieService:
    @staticmethod # because the service doesn't need to "know" about itself. It only cares about the data you give it
    def save_movie(
        movie: Movie | None=None, 
        title:str | None=None,
        genre:str | None=None,
        duration:int | None=None,
        rating:Decimal | None=None,
        release_date:date | None=None,
    ): 
        if movie:
            # We apply those new values to the old movie object and save it
            movie.title = title if title else movie.title
            movie.genre = genre if genre else movie.genre
            movie.duration = duration if duration else movie.duration
            movie.rating = rating if rating is not None else movie.rating # accept falsy value (new movie might have 0 rating)
            movie.release_date = release_date if release_date else movie.release_date

            movie.save()
            return movie
        
        else:
            return Movie.objects.create(
                title=title, # take exactly what the user typed. We don't need a fallback because this is new movie
                genre=genre,
                duration=duration,
                rating=rating,
                release_date=release_date
            ) # make a completely new record in the database with that data



class HallService:
    @staticmethod
    def _generate_seats(hall: Hall): # private method, views can't call it
        # LOGIC: Usually, we don't POST seats one by one. We write a Service that generates all 100 seats automatically when a Hall is created.
        seats_to_bulk = [] 
        for r in range(hall.seats_per_row): # if user type 10, result: `range(10)`
            row_label = chr(ord("A") + r) # why`+r`? bcoz r starts from 0, we need it to get "A"

            for c in range(1, hall.seats_per_column + 1): # if user type 10, result: `range(1, 11)`
                column_number = c # seat numbers starts from 1 (until what typed)

                seat = Seat( #create new seat object in memory (not `.save()` yet)
                    hall=hall,
                    row_label=row_label,
                    column_number=column_number,
                )
                seats_to_bulk.append(seat)

        # This sends all 100 seats to the database in one command
        Seat.objects.bulk_create(seats_to_bulk)


    @staticmethod
    def save_hall(
        hall: Hall | None=None,
        name: str | None=None,
        seats_per_row:int | None=None,
        seats_per_column:int | None=None,
        screen_type:str | None=None,
    ):
        # LOGIC: want to resize the Hall to smaller/bigger, but the hall is already filled.. so we need to delete previous and recreate them all
        if hall:
            with transaction.atomic():

                # check if the new-old version are diff (from user and from DB)
                row_diff = seats_per_row and (seats_per_row != hall.seats_per_row)
                col_diff = seats_per_column and (seats_per_column != hall.seats_per_column) # access spesific data early; here set fallback so when left empty it return false 

                # If I change the name, the Hall is saved, seats ignored. If I change the size, Hall is saved AND seats are updated
                hall.name = name if name else hall.name
                hall.seats_per_row = seats_per_row if seats_per_row else hall.seats_per_row
                hall.seats_per_column = seats_per_column if seats_per_column else hall.seats_per_column
                hall.save()

                if row_diff or col_diff: # only run when changing seats number
                    Seat.objects.filter(hall=hall).delete() # this is like delete seats in 1 spesific room instead of whole Hall obj
                    HallService._generate_seats(hall) # generate new seat using updated hall
            
            return hall # after trans.atomic closed (no error found), we send the finished 'hall' object back to the View

        # otherwise, create new hall object and store to DB
        with transaction.atomic():
            new_hall = Hall.objects.create(
                name=name,
                seats_per_row=seats_per_row,
                seats_per_column=seats_per_column,
                screen_type=screen_type,
            )
            HallService._generate_seats(new_hall)
        return new_hall 



# Use HallService style when the steps for "Create" and "Update" are totally different
# Use ShowtimeService style when the "Math" and "Validation" are the same for both (update and create not so diff)
class ShowtimeService:
    @staticmethod
    def save_showtime(
        showtime: Showtime | None=None,
        movie: Movie | None=None,
        hall: Hall | None=None,
        start_at: datetime | None=None,
        price: int | None=None,
       **kwargs # will recognize auto-add field
    ):
        # prevent showtime in the same hall overlapping (DDD logic)
        # when we want to insert movie A to hall_1 at 9-11, but its overlap with movie C. so we do empty checkup to find an empty hall at that spesific time to give options to move

        # --- Preparation and Validation phase (shared the same logic) ---
        get_hall = hall if hall else (showtime.hall if showtime else None)
        get_movie = movie if movie else (showtime.movie if showtime else None) 
        start_time = start_at if start_at else (showtime.start_at if showtime else None)
        
        if not get_movie or not get_hall or not start_time: # to handle None, incase user forgot to input
            raise ValidationError("Movie, Hall, Start time are required")
        
        show_duration_plus_cleaning = get_movie.duration + 30 #duration of showtime is derived(turunan) from movie
        end_time = start_time + timedelta(minutes=show_duration_plus_cleaning) 
        if showtime:
            showtime.end_at = end_time # auto-add end_at
        
        # overlap check(shared)
        overlap = Showtime.objects.filter( 
            hall = get_hall, # Is there a Prev Movie in the same hall?
            start_at__lt = end_time, # An overlap exists if the existing show starts BEFORE our show ends...
            end_at__gt = start_time # ...and the existing show ends AFTER our show starts.
        )
        if showtime: #make sure only run in PATCH, no need in POST(bcoz its new)
            overlap = overlap.exclude(id=showtime.id) #type:ignore # This part makes sure doesnt compare to himself

        if overlap.exists():
            # Instead of just returning error, we give user the available alternative halls
            busy_showtimes = Showtime.objects.filter(start_at__lt=end_time, end_at__gt=start_time) # "Show me every movie playing anywhere in the building during this time"
            busy_halls = busy_showtimes.values_list("hall_id", flat=True).distinct() #grab IDs, turn into list, remove duplicate
            available_hall = Hall.objects.all().exclude(id__in=busy_halls) # `id__in=...` to tell the exclude function which column to compare

            list_hall = [hall.name for hall in available_hall]

            if list_hall:
                message = f"This hall is busy. Available halls at this time: {list_hall}"
            else:
                message = "All halls are currently busy at this time"

            raise ValidationError(message)

        
        # --- Saving phase (different logic) ---
        if showtime:
            showtime.movie = movie if movie else showtime.movie
            showtime.hall = hall if hall else showtime.hall
            showtime.start_at = start_at if start_at else showtime.start_at
            showtime.price = price if price is not None else showtime.price # accpet falsy (might be free)

            showtime.save()
            return showtime
        
        return Showtime.objects.create(
            movie=movie,
            hall=hall,
            start_at=start_at,
            price=price,
            end_at=end_time,
        )



class SeatService:
    @staticmethod
    def update_seat(
        seat: Seat,
        is_broken: bool | None = None,
        **kwargs
    ):
        # We only update 'is_broken'. Row and Column are locked.
        if is_broken is not None:
            seat.is_broken = is_broken
        
        seat.save()
        return seat



# The output is focused on analyze instead of just CRUD
class ScreeningAnalytic():
    @staticmethod
    def top_movies():
        """ Showing the most picked movies by customer """
        # Use 'values' to group by the Movie Title (via Showtime) ; JOIN the spesific target column only (what we want to show)
        # Use 'annotate' to Sum the quantity for "each group" of Title
        return Booking.objects.filter(status="CONFIRMED") \
            .values("showtime__movie__title") \
            .annotate(total_sold=Sum("quantity")) \
            .order_by("-total_sold") # from highest
    
    # later add dynamic filter by day, week, month
    # also maybe add way to take only top 5 for admin? bcoz rn i meant making this for both everyone
    

    @staticmethod
    def showtime_occupancy(): # dont need to give a specific showtime; it finds them itself using '.objects.filter'
        """ Showing Real-time upcoming Showtime(alongside movie and hall info) """
        
        # use select_related to avoid slow "N+1" queries
        upcoming_shows = Showtime.objects.filter(start_at__gt=timezone.now()) \
        .select_related("movie", "hall") \
        .order_by("-start_at")

        showtime_report = [] #empty tray to store collections

        for show in upcoming_shows: 
            capacity = show.hall.seats_per_row * show.hall.seats_per_column # use 'show.' to calculate the math for each individual movie slot
            ticket_counts = show.booking_set.filter(status="CONFIRMED").aggregate(total_seat=Sum("quantity")) ["total_seat"] or 0 #get "all confirmed booking/ticket for this showtime", then sum it --backward logic #type:ignore
            occupancy_rate = (ticket_counts/capacity)*100 if capacity>0 else 0

            time_str = show.start_at.strftime("%d %b %Y, %H:%M") #convert to readable time
            display_text = f"[{time_str}] {show.movie.title} - {show.hall.name} ({int(occupancy_rate)}% Full)" # not use class name (showtime)

            showtime_report.append({
                "id": show.id,
                "screening": display_text
            })
        return showtime_report


    @staticmethod
    def hall_seats_layout(showtime_id): #enough to pass showtime id only
        """ Triggered when admin clicks a spesific showtime_occupancy --to see detail seats layout of a Hall. """

        # 1. Get the specific showtime(and the Hall it belongs to) --when user click a spesific showtime
        selected_showtime = Showtime.objects.select_related("hall").get(id=showtime_id) #use get bcoz we click on a spesific choice
        all_seats = selected_showtime.hall.seat_set.all() #Get all seats in of that specific Hall

        # 2. Get 'Confirmed' seat IDs from Postgres (look for tickets linked to this specific showtime)
        confirmed_seats = Ticket.objects.filter(
            booking__showtime_id = showtime_id,
            booking__status = "CONFIRMED"
        ).values_list("seat_id", flat=True) # list all seat_id from this showtime that are already confirmed

        # 3. Get 'Pending' seat IDs from Redis
        # Use the '*' to find all locked seats for this showtime
        locked_keys = cache.keys(f"lock:{showtime_id}:*") #type:ignore # This "lock:" name must be same everywhere
        locked_seats = [int(k.split(':')[-1]) for k in locked_keys] # Turn "seatlock:5:102" into just the ID 102

        # 4. Get info of which seat belong to who
        taker = Ticket.objects.filter(
            booking__showtime_id = showtime_id,
            booking__status = "CONFIRMED"
        ).select_related("booking__user") #grab user from this showtime that are already confirmed

        # use Dictionary map --each occupied seat(key) has value(email)
        # Turn the Queryset from "taker" to simple dictionary --ex: {101: "manager1@gmail.com", 105: "student@uni.edu"}
        map_taker = {t.seat.id: t.booking.user.email for t in taker} 


        seat_layout = []
        for seat in all_seats:
            if seat.is_broken:
                status = "Grey"
            elif seat.id in confirmed_seats:
                status = "Red"
            elif seat.id in locked_seats: 
                status = "Yellow"
            else:
                status = "Green"

            seat_layout.append({
                "seat_id": seat.id,
                "seat_label": f"{seat.row_label}-{seat.column_number}",
                "status": status,
                "taken_by": map_taker.get(seat.id, "None") # asks: "Do we have a record for Seat ID 101, 102, 109?" --if yes show the email otherwise "None"
            })
        return seat_layout
