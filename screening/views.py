# views return JSON in DRF
# In here, we see Response more often than raise bcoz we're dealing with user. so

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Movie, Hall, Showtime, Seat
from .serializers import MovieSerializer, HallSerializer, HallReadonlySerializer, ShowtimeSerializer, ShowtimeReadonlySerializer, SeatSerializer
from .services import MovieService, HallService, ShowtimeService, SeatService

from django.shortcuts import get_object_or_404



class MovieListAPIView(APIView):  # Request handler(HTTP) ; frontend called HTTP to ask the data from here
    def get(self, request): # when someone send a GET request from here....
        movies = Movie.objects.all() # this is like: SELECT * FROM Movie and turn into obj
        serializer = MovieSerializer(movies, many=True) # return Queryset (list of many models rows) to JSON
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = MovieSerializer(data = request.data) # JSON to Model
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        movie = MovieService.save_movie(None, **serializer.validated_data) # we dont pass movie bcoz initially this wasnt created
        # without **, we have to type `name=data['name']` one by one
        return Response(MovieSerializer(movie).data, status=status.HTTP_201_CREATED)
    

class MovieDetailAPIView(APIView):
    def get(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk) 
        serializer = MovieSerializer(movie) # no need `many=True` bcoz return single obj (Model to JSON)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # A POST request creates something new. 
    # You can't "create" a new movie inside Movie #5. It is already exists. If you wanna create a new one, you need to go back to main folder (/movies/)

    def patch(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk)
        serializer = MovieSerializer(movie, data = request.data, partial=True) # enable PATCH (update some instead all)
        serializer.is_valid(raise_exception=True) # shortcut
        updated_movie = MovieService.save_movie(movie, **serializer.validated_data) # pass movie if it exist
        return Response(MovieSerializer(updated_movie).data, status=status.HTTP_200_OK) # patch return OK, not 201
        
    def delete(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk)
        movie.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class HallListAPIView(APIView):
    def get(self, request):
        halls = Hall.objects.all()
        serializer = HallReadonlySerializer(halls, many=True) 
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = HallSerializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        hall = HallService.save_hall(None, **serializer.validated_data)
        return Response(HallSerializer(hall).data, status=status.HTTP_201_CREATED)
    

class HallDetailAPIView(APIView):
    def get(self, request, pk):
        hall = get_object_or_404(Hall, pk=pk)
        serializer = HallReadonlySerializer(hall)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, pk):
        hall = get_object_or_404(Hall, pk=pk) # this is like: SELECT * FROM Hall WHERE id=pk from db
        serializer = HallSerializer(hall, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_hall = HallService.save_hall(hall, **serializer.validated_data)
        return Response(HallSerializer(updated_hall).data, status=status.HTTP_200_OK)
    
    def delete(self, request, pk):
        hall = get_object_or_404(Hall, pk=pk)
        hall.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class ShowtimeListAPIView(APIView):
    # Trip out: Get list of showtimes
    def get(self, request):
        showtimes = Showtime.objects.all()
        serializer = ShowtimeReadonlySerializer(showtimes, many=True, context={"request":request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # Trip in: Create new showtimes
    def post(self, request):
        # 1.check format (serializer)
        serializer = ShowtimeSerializer(data = request.data, context={"request":request}) #takes raw material(JSON) from user and holds
        serializer.is_valid(raise_exception=True)
        showtime = ShowtimeService.save_showtime(None, **serializer.validated_data)
        return Response(ShowtimeSerializer(showtime).data, status=status.HTTP_201_CREATED)# If everything succeeded, you turn the new 'showtime' object back into JSON to (show the user what was created)
    
    
class ShowtimeDetailAPIView(APIView):
    def get(self, request, pk):
        showtime = get_object_or_404(Showtime, pk=pk)
        serializer = ShowtimeReadonlySerializer(showtime, context={"request":request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, pk):
        showtime = get_object_or_404(Showtime, pk=pk)
        serializer = ShowtimeSerializer(showtime, data=request.data, partial=True, context={"request":request})
        serializer.is_valid(raise_exception=True)
        updated_showtime = ShowtimeService.save_showtime(showtime, **serializer.validated_data)
        return Response(ShowtimeSerializer(updated_showtime).data, status=status.HTTP_200_OK)
    
    def delete(self, request, pk):
        showtime = get_object_or_404(Showtime, pk=pk)
        showtime.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class SeatDetailAPIView(APIView):
    def get(self, request, r, c, h_id):
        seats = get_object_or_404(Seat, row_label=r, column_number=c, hall_id=h_id) # MUST match the field name
        serializer = SeatSerializer(seats)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, r, c, h_id):
        seat = get_object_or_404(Seat, row_label=r, column_number=c, hall_id=h_id)
        serializer = SeatSerializer(seat, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_seat = SeatService.update_seat(seat, **serializer.validated_data)
        
        return Response(SeatSerializer(updated_seat).data, status=status.HTTP_200_OK)

