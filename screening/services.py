# where we put logic business rules
from .models import Movie, Hall, Showtime, Seat
from rest_framework.exceptions import ValidationError # in normal django we import from "django.core.exceptions"
from datetime import timedelta
from django.db import transaction

class MovieService:
    @staticmethod # because the service doesn't need to "know" about itself. It only cares about the data you give it
    def save_movie(movie: Movie | None=None, **data): 
        if movie:
            # .get compare what the user type to change with what is currently in the database
            title = data.get("title", movie.title) 
            genre = data.get("genre", movie.genre)
            duration = data.get("duration", movie.duration)
            rating = data.get("rating", movie.rating)
            release_date = data.get("release_date", movie.release_date)
            
            # We apply those new values to the old movie object and save it
            movie.title = title 
            movie.genre = genre
            movie.duration = duration
            movie.rating = rating
            movie.release_date = release_date

            movie.save()
            return movie
        
        else:
            # manual extraction
            title = data.get("title") # take exactly what the user typed. We don't need a fallback because this is a brand new movie
            genre = data.get("genre")
            duration = data.get("duration")
            rating = data.get("rating")
            release_date = data.get("release_date")
            # manual pass
            return Movie.objects.create(
                title=title,
                genre=genre,
                duration=duration,
                rating=rating,
                release_date=release_date
            ) # tell Django to make a completely new record in the database with that data



class HallService:
    @staticmethod
    def _generate_seats(hall): # private method, views can't call it
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
    def save_hall(hall: Hall | None=None, **data):# flipping switch for post and patch (first arg when we call func in views)
        # LOGIC: want to resize the Hall to smaller/bigger, but the hall is already filled.. so we need to delete previous and recreate them all
        if hall:
            with transaction.atomic():

                # check if the new-old version are diff (from user and from DB)
                row_diff = data.get("seats_per_row", hall.seats_per_row)!=hall.seats_per_row 
                col_diff = data.get("seats_per_column", hall.seats_per_column)!=hall.seats_per_column # access spesific data early; here set fallback so when left empty it return false 

                # If I change the name, the Hall is saved, seats ignored. If I change the size, Hall is saved AND seats are updated
                for key, value in data.items():
                    setattr(hall, key, value)
                hall.save()

                if row_diff or col_diff: # only run when changing seats number
                    hall.seat_set.all().delete()#type:ignore # this is like delete seats in 1 spesific room instead of whole Hall obj
                    HallService._generate_seats(hall) # generate new seat using updated hall
            
            return hall # after trans.atomic closed (no error found), we send the finished 'hall' object back to the View

        # otherwise, create new hall object and store to DB
        with transaction.atomic():
            new_hall = Hall.objects.create(**data)
            HallService._generate_seats(new_hall)
        return new_hall 



class ShowtimeService:
    @staticmethod
    def save_showtime(showtime: Showtime | None=None, **data):
        # prevent showtime in the same hall overlapping (DDD logic)
        # when we want to insert movie A to hall_1 at 9-11, but its overlap with movie C. so we do empty checkup to find an empty hall at that spesific time to give options to move

        # --- Preparation and Validation phase (shared the same logic) ---
        get_hall = data.get("hall", showtime.hall if showtime else None)
        get_movie = data.get("movie", showtime.movie if showtime else None) 
        start_time = data.get("start_at", showtime.start_at if showtime else None)
        
        if not get_movie or not get_hall or not start_time: # to handle None, incase user forgot to input
            raise ValidationError("Movie, Hall, Start time are required")
        
        show_duration_plus_cleaning = get_movie.duration + 30 #duration of showtime is derived(turunan) from movie
        end_time = start_time + timedelta(minutes=show_duration_plus_cleaning) 
        data["end_at"] = end_time # auto-add
        
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
            for key, value in data.items():
                setattr(showtime, key, value)
            showtime.save()
            return showtime
        
        return Showtime.objects.create(**data)


# Use HallService style when the steps for "Create" and "Update" are totally different
# Use ShowtimeService style when the "Math" and "Validation" are the same for both (update and create not so diff)


class SeatService:
    @staticmethod
    def update_seat(seat: Seat, **data):
        # We DO NOT allow changing 'row_label' or 'column_number' here. Those are locked by the HallService.

        for key, value in data.items():
            setattr(seat, key, value)
        seat.save()
        return seat
