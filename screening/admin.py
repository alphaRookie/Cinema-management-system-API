# Register database models here. so we can see in admin panel

from django.contrib import admin
from .models import Movie, Hall, Showtime, Seat
from .services import MovieService, HallService, ShowtimeService, SeatService

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "genre", "duration", "rating", "release_date")
    list_filter = ("genre",) # grouping by ..
    search_fields = ("title",) # search by title
    
    # This part makes admin "smart" bcoz it connects to service
    def save_model(self, request, obj, form, change):
        MovieService.save_movie(movie=obj if change else None, **form.cleaned_data)

@admin.register(Hall)
class HallAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "seats_per_row", "seats_per_column", "screen_type")
    list_filter = ("screen_type",)# Comma needed, bcoz it's Tuple (a list of items) not string
    search_fields = ("name",)

    def save_model(self, request, obj, form, change):
        # Call Service to handle the 'if hall' logic and the seat generation
        HallService.save_hall(hall=obj if change else None, **form.cleaned_data)


@admin.register(Showtime)
class ShowtimeAdmin(admin.ModelAdmin):
    list_display = ("id", "start_at", "price", "movie", "hall")
    list_filter = ("hall", "movie")
    date_hierarchy = "start_at" # admin can jump by year → month → day

    def save_model(self, request, obj, form, change):
        ShowtimeService.save_showtime(showtime=obj if change else None, **form.cleaned_data)
   

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("row_label", "column_number", "hall") # we dont define `id` here btw
    list_filter = ("hall",)

    def save_model(self, request, obj, form, change):
        SeatService.update_seat(seat=obj, **form.cleaned_data)
