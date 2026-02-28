# Translator to convert the data into JSON
# Serializer reads the Model's fields (like PositiveSmallIntegerField) and automatically creates rules based on them

from rest_framework import serializers
from rest_framework.serializers import ValidationError
from .models import Movie, Hall, Showtime, Seat
from django.utils import timezone


# we dont need read_only & write_only here, bcoz the field identity is clear, unlike when there is `join`
class MovieSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = Movie
        fields = ["id", "title", "genre", "duration", "rating", "release_date"]
        read_only_fields = ["id"]

    def validate_title(self, title):
        if not title.strip():
            raise ValidationError("Please dont leave the title empty")
        return title.strip()



class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ["id", "row_label", "column_number", "hall", "is_broken"] 
        read_only_fields = ["id", "row_label", "column_number", "hall"]



class HallBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hall
        fields = ["id", "name", "seats_per_row", "seats_per_column", "screen_type"] 
        read_only_fields = ["id"]
    

class HallReadonlySerializer(HallBaseSerializer):
    total_seats = serializers.SerializerMethodField()

    class Meta(HallBaseSerializer.Meta):
        fields = HallBaseSerializer.Meta.fields + ["total_seats"] # add what needed or dont add at all

    def get_total_seats(self, obj): # looping through halls, calling each one 'obj'
        return Seat.objects.filter(hall=obj).count() # when at halls A, return the count from hall "A". and so on..
    

class HallSerializer(HallBaseSerializer):
    class Meta(HallBaseSerializer.Meta):
        fields = HallBaseSerializer.Meta.fields 

    def validate_name(self, input_name):
        input_name = input_name.strip() # dont count the spaces
        if not input_name:
            raise ValidationError("Please don't leave name empty")
        return input_name
        
    def validate_seats_per_row(self, input_row): #layered constraint design (15 as max here, but in default is 26 by model)
        if input_row > 15 or input_row < 1:
            raise ValidationError("row: minimum is 1 and maximum is 15")
        return input_row
        
    def validate_seats_per_column(self, input_column):
        if input_column > 15 or input_column < 1:
            raise ValidationError("column: minimum is 1 and maximum is 15")
        return input_column



class ShowtimeBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Showtime
        fields = ["id", "start_at", "price", "end_at"]
        read_only_fields = ["id", "end_at"]


class ShowtimeReadonlySerializer(ShowtimeBaseSerializer):
    #get(shown in ShowtimeListAPIView)
    movie_info = serializers.SerializerMethodField() # this pattern is good for customing what return (show readable text)
    hall_info = serializers.SerializerMethodField()
    #get(shown in ShowtimeDetailAPIView)
    movie_detail = MovieSerializer(source="movie", read_only=True) # this pattern best for showing full data
    hall_detail = HallSerializer(source="hall", read_only=True) # Points to `hall`, but `hall_info` shows entire data ("hall": {...})

    class Meta(ShowtimeBaseSerializer.Meta):
        fields = ShowtimeBaseSerializer.Meta.fields + ["movie_info", "hall_info", "movie_detail", "hall_detail"]

    def get_movie_info(self, obj):
        return { "title": obj.movie.title }
    
    def get_hall_info(self, obj):
        return {
            "name": obj.hall.name, 
            "screen_type": obj.hall.screen_type
        }
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)# 1. Get the normal data first
        request = self.context.get('request')# 2. Check the request context
        
        # 3. If the URL has a "pk" (ID), it means we are in the Detail View
        # If not, it's the List View.
        is_detail_view = request and 'pk' in request.parser_context.get('kwargs', {})

        if not is_detail_view: # If it's NOT the detail view: Show Detail, Hide Info
            representation.pop('movie_detail', None)
            representation.pop('hall_detail', None)
        else: # If it IS the detail view: Show Info, Hide Detail
            representation.pop('movie_info', None)
            representation.pop('hall_info', None)

        return representation

        
class ShowtimeSerializer(ShowtimeBaseSerializer):
    #post/patch
    movie = serializers.PrimaryKeyRelatedField(queryset=Movie.objects.all(), write_only=True)
    hall = serializers.PrimaryKeyRelatedField(queryset=Hall.objects.all(), write_only=True)

    class Meta(ShowtimeBaseSerializer.Meta):
        fields = ShowtimeBaseSerializer.Meta.fields + ["movie", "hall"]

    def validate_start_at(self, starting): # it's format validation, not business rule
        if starting < timezone.now():
            raise ValidationError("Cant schedule movie in the past") 
        return starting
    

# POST (Trip In): The user sends {"movie": 5}. The serializer accepts it because movie is write_only.
# GET (Trip Out): The user receives the JSON. They don't see "movie": 5 (because it's hidden). Instead, they see "movie_detail": {...} which contains the Title, Genre, and Rating.


