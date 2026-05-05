# place different url routes and connect to views

from django.urls import path
from .views import MovieAPIView, MovieItemAPIView, HallAPIView, HallItemAPIView, ShowtimeAPIView, ShowtimeItemAPIView, SeatAPIView, TopMoviesAPIView, ShowtimeOccupancyListAPIView, ShowtimeOccupancyDetailAPIView

urlpatterns = [
    path("/movies", MovieAPIView.as_view(), name="movie-list"),
    path("/movies/<int:pk>", MovieItemAPIView.as_view(), name="movie-detail"),

    path("/halls", HallAPIView.as_view(), name="halls-list"),
    path("/halls/<int:pk>", HallItemAPIView.as_view(), name="halls-detail" ),
    
    path("/halls/seat/<int:pk>", SeatAPIView.as_view(), name="seats-detail"),

    path("/showtimes", ShowtimeAPIView.as_view(), name="showtimes-list"),
    path("/showtimes/<int:pk>", ShowtimeItemAPIView.as_view(), name="showtime-detail"),

    # Analytic
    path("/movies/top", TopMoviesAPIView.as_view(), name="top-movies"),

    path("/showtimes/occupancy", ShowtimeOccupancyListAPIView.as_view(), name="showtime-occupancy"),
    path("/showtimes/occupancy/<int:pk>", ShowtimeOccupancyDetailAPIView.as_view(), name="showtime-occupancy-detail"),
]

