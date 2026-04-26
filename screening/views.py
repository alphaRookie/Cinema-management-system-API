# views return JSON in DRF
# In here, we see Response more often than raise bcoz we're dealing with user. so

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Movie, Hall, Showtime, Seat
from .serializers import MovieSerializer, HallWriteSerializer, HallReadSerializer, ShowtimeWriteSerializer, ShowtimeReadListSerializer, ShowtimeReadItemSerializer, SeatSerializer, MessageSerializer, MovieResponseSerializer, HallResponseSerializer, ShowtimeResponseSerializer, SeatResponseSerializer
from .services import MovieService, HallService, ShowtimeService, SeatService
from .permissions import IsManager, IsWorker, IsManagerOrReadonly
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view


@extend_schema_view(
    get=extend_schema(summary="List all Movies", responses={200: MovieSerializer(many=True)}),
    post=extend_schema(summary="Adds a New Movie", request=MovieSerializer, responses={201: MovieResponseSerializer})
)
class MovieAPIView(APIView):
    permission_classes = [IsManagerOrReadonly]

    def get(self, request):
        movies = Movie.objects.all() # this is like: SELECT * FROM Movie and turn into obj
        serializer = MovieSerializer(movies, many=True) # return Queryset (list of many models rows) to JSON
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = MovieSerializer(data = request.data) # JSON to Model
        serializer.is_valid(raise_exception=True)
        movie = MovieService.save_movie(
            movie=None,
            title=serializer.validated_data.get("title"),
            genre=serializer.validated_data.get("genre"),
            duration=serializer.validated_data.get("duration"),
            rating=serializer.validated_data.get("rating"),
            release_date=serializer.validated_data.get("release_date"),
        ) 
        return Response({
            "message": "New movie added",
            "movie": MovieSerializer(movie).data #input shape is same as output shape, so we use the same serializer
        }, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(summary="Returns the details of a specific movie by ID", responses={200: MovieSerializer}),
    patch=extend_schema(summary="Updates an existing movie", request=MovieSerializer, responses={200: MovieResponseSerializer}),
    delete=extend_schema(summary="Deletes a movie by ID",responses={200: MessageSerializer})
)
class MovieItemAPIView(APIView):
    permission_classes = [IsManagerOrReadonly] # anyone can GET, and only logged-in admin can POST, PATCH, DELETE

    def get(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk) 
        serializer = MovieSerializer(movie) # no need `many=True` bcoz return single obj (Model to JSON)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk)
        serializer = MovieSerializer(movie, data = request.data, partial=True) # enable PATCH (update some instead all)
        serializer.is_valid(raise_exception=True) # shortcut
        updated_movie = MovieService.save_movie(
            movie=movie, 
            title=serializer.validated_data.get("title"),
            genre=serializer.validated_data.get("genre"),
            duration=serializer.validated_data.get("duration"),
            rating=serializer.validated_data.get("rating"),
            release_date=serializer.validated_data.get("release_date"),
        ) 
        return Response({
            "message": "Movie updated",
            "movie": MovieSerializer(updated_movie).data
        }, status=status.HTTP_200_OK) # patch return OK, not 201

    def delete(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk)
        movie.delete()
        return Response({"message": f"{movie.title} deleted"},status=status.HTTP_200_OK)



@extend_schema_view(
    get=extend_schema(summary="List all Halls", responses={200: HallReadSerializer(many=True)}),
    post=extend_schema(summary="Adds a New Hall", request=HallWriteSerializer, responses={201: HallResponseSerializer})
)
class HallAPIView(APIView):
    permission_classes = [IsManagerOrReadonly]

    def get(self, request):
        halls = Hall.objects.all()
        serializer = HallReadSerializer(halls, many=True) 
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    def post(self, request):
        serializer = HallWriteSerializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        hall = HallService.save_hall(
            hall=None,
            name=serializer.validated_data.get("name"),
            seats_per_row=serializer.validated_data.get("seats_per_row"),
            seats_per_column=serializer.validated_data.get("seats_per_column"),
            screen_type=serializer.validated_data.get("screen_type"),
        )
        return Response({
            "message": "New Hall created",
            "hall": HallReadSerializer(hall).data # desired output is different to what we input 
        }, status=status.HTTP_201_CREATED)
    
    
@extend_schema_view(
    get=extend_schema(summary="Retrieve the details of a specific hall by ID", responses={200: HallReadSerializer}),
    patch=extend_schema(summary="Updates an existing Hall by ID", request=HallWriteSerializer, responses={200: HallResponseSerializer}),
    delete=extend_schema(summary="Deletes a Hall by ID", responses={200: MessageSerializer})
)
class HallItemAPIView(APIView):
    permission_classes = [IsManagerOrReadonly]

    def get(self, request, pk):
        hall = get_object_or_404(Hall, pk=pk)
        serializer = HallReadSerializer(hall)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        hall = get_object_or_404(Hall, pk=pk) # this is like: SELECT * FROM Hall WHERE id=pk from db
        serializer = HallWriteSerializer(hall, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_hall = HallService.save_hall(
            hall=hall, 
            name=serializer.validated_data.get("name"),
            seats_per_row=serializer.validated_data.get("seats_per_row"),
            seats_per_column=serializer.validated_data.get("seats_per_column"),
            screen_type=serializer.validated_data.get("screen_type"),
        )
        return Response({
            "message": "Hall updated",
            "hall": HallReadSerializer(updated_hall).data
        }, status=status.HTTP_200_OK)
    
    def delete(self, request, pk):
        hall = get_object_or_404(Hall, pk=pk)
        hall.delete()
        return Response({"message": f"{hall.name} deleted"}, status=status.HTTP_200_OK)



@extend_schema_view(
    get=extend_schema(summary="List all Showtimes",responses={200: ShowtimeReadListSerializer(many=True)}),
    post=extend_schema(summary="Adds a New Showtime", request=ShowtimeWriteSerializer, responses={201: ShowtimeResponseSerializer})
)
class ShowtimeAPIView(APIView):
    permission_classes = [IsManagerOrReadonly]

    # Trip out: Get list of showtimes
    def get(self, request):
        showtimes = Showtime.objects.all()
        serializer = ShowtimeReadListSerializer(showtimes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    # Trip in: Create new showtimes
    def post(self, request):
        # 1.check format (serializer)
        serializer = ShowtimeWriteSerializer(data = request.data) #takes raw material(JSON) from user and holds
        serializer.is_valid(raise_exception=True)
        showtime = ShowtimeService.save_showtime(
            showtime=None,
            movie=serializer.validated_data.get("movie"),
            hall=serializer.validated_data.get("hall"),
            start_at=serializer.validated_data.get("start_at"),
            price=serializer.validated_data.get("price"),
        )
        return Response({
            "message": "New Showtime added",
            "showtime": ShowtimeReadListSerializer(showtime).data
        }, status=status.HTTP_201_CREATED)# If everything succeeded, you turn the new 'showtime' object back into JSON to (show the user what was created)


@extend_schema_view(
    get=extend_schema(summary="Retrieve details of a specific showtime by ID", responses={200: ShowtimeReadItemSerializer}),
    patch=extend_schema(summary="Updates an existing Showtime by ID", request=ShowtimeWriteSerializer, responses={200: ShowtimeResponseSerializer}),
    delete=extend_schema(summary="Deletes a Showtime by ID", responses={200: MessageSerializer})
)
class ShowtimeItemAPIView(APIView):
    permission_classes = [IsManagerOrReadonly]

    def get(self, request, pk):
        showtime = get_object_or_404(Showtime, pk=pk)
        serializer = ShowtimeReadItemSerializer(showtime)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, pk):
        showtime = get_object_or_404(Showtime, pk=pk)
        serializer = ShowtimeWriteSerializer(showtime, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_showtime = ShowtimeService.save_showtime(
            showtime=showtime, 
            movie=serializer.validated_data.get("movie"),
            hall=serializer.validated_data.get("hall"),
            start_at=serializer.validated_data.get("start_at"),
            price=serializer.validated_data.get("price"),
        )
        return Response({
            "message": "Showtime updated",
            "showtime": ShowtimeReadItemSerializer(updated_showtime).data
        }, status=status.HTTP_200_OK)
    
    def delete(self, request, pk):
        showtime = get_object_or_404(Showtime, pk=pk)
        showtime.delete()
        return Response({"message": f"{showtime.movie.title} at {showtime.start_at} cancelled"}, status=status.HTTP_200_OK)



@extend_schema_view(
    get=extend_schema(summary="Retrieve the details of a specific seat by ID", responses={200: SeatSerializer}),
    patch=extend_schema(summary="Updates an existing Seat", request=SeatSerializer, responses={200: SeatResponseSerializer}),
)
class SeatAPIView(APIView):
    permission_classes = [IsAuthenticated, IsManager | IsWorker]

    def get(self, request, r, c, h_id):
        seat = get_object_or_404(Seat, row_label=r, column_number=c, hall_id=h_id) # MUST match the field name
        serializer = SeatSerializer(seat)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, r, c, h_id):
        seat = get_object_or_404(Seat, row_label=r, column_number=c, hall_id=h_id)
        serializer = SeatSerializer(seat, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_seat = SeatService.update_seat(
            seat=seat,
            is_broken=serializer.validated_data.get("is_broken"),
        )
        
        return Response({
            "message": "Seat updated",
            "seat": SeatSerializer(updated_seat).data
        }, status=status.HTTP_200_OK)
