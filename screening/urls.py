# place different url routes and connect to views

from django.urls import path
from .views import MovieListAPIView, MovieDetailAPIView, HallListAPIView, HallDetailAPIView , ShowtimeListAPIView, ShowtimeDetailAPIView, SeatDetailAPIView

urlpatterns = [
    path("movies/", MovieListAPIView.as_view(), name="movie-list"),
    path("movies/<int:pk>/", MovieDetailAPIView.as_view(), name="movie-detail"),

    path("halls/", HallListAPIView.as_view(), name="halls-list"),
    path("halls/<int:pk>/", HallDetailAPIView.as_view(), name="halls-detail" ),
    
    path("halls/<int:h_id>/<str:r><int:c>", SeatDetailAPIView.as_view(), name="seats-detail"),

    path("showtimes/", ShowtimeListAPIView.as_view(), name="showtimes-list"),
    path("showtimes/<int:pk>/", ShowtimeDetailAPIView.as_view(), name="showtime-detail")
]

