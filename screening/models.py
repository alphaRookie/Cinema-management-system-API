# A module named "model" with a class "Model" ; for storing, retrieve etc obj model

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _ # Translation is delayed until the string is displayed (so django know user's preference)


class Movie(models.Model): # django creates Id (PK) automatically
    class Genre(models.TextChoices):
        UNSPECIFIED = "UNSPECIFIED", _("Unspecified")
        ACTION = "ACTION", _("Action")
        COMEDY = "COMEDY", _("Comedy")
        DRAMA = "DRAMA", _("Drama")
        HORROR = "HORROR", _("Horror")
        SCIFI = "SCI-FI", _("Sci-Fi")
        ROMANCE = "ROMANCE", _("Romance")

    title = models.CharField(max_length=250) # auto not null 
    genre = models.CharField(max_length=50, choices=Genre.choices, default=Genre.UNSPECIFIED)
    duration = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(240)])
    rating = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)]) # DECIMAL(4,2)
    release_date = models.DateField() 

    def __str__(self): # make few to show identity (just identity, not much data)
        return self.title


class Hall(models.Model):
    class ScreenType(models.TextChoices):
        STANDARD = "STANDARD", _("Standard")
        IMAX = "IMAX", _("IMAX")
    
    name = models.CharField(max_length=100, unique=True)
    seats_per_row = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(26)]) #layered constraint design (we can set policy max to 15 in serializer, but system default max still 26)
    seats_per_column = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(50)])
    screen_type = models.CharField(
            max_length=50, choices=ScreenType.choices, default= ScreenType.STANDARD
        )
    
    def __str__(self):
        return self.name
    
    
class Showtime(models.Model):
    start_at = models.DateTimeField(db_index=True) #  helps searching faster when data grow bigger (but takes more space and abit slower)
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)]) # always decimal for exact count !
    movie = models.ForeignKey(Movie, on_delete=models.PROTECT) # dont let it to be deleted, bcoz showtime is where all data gathers (historical data depends)
    hall = models.ForeignKey(Hall, on_delete=models.PROTECT) 
    end_at = models.DateTimeField(blank=True, null=True) # autofill field (by service)

    def __str__(self):
        return self.movie.title
    
    def total_price(self, quantity): # By putting it in the Model, you make "calculator" that available everywhere in your app without writing it twice.
        return self.price * quantity


class Seat(models.Model):
    row_label = models.CharField(max_length=1) #, choices=[(chr(i), chr(i)) for i in range(ord("A"), ord("Z")+1)]
    column_number = models.PositiveSmallIntegerField()
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)

    def __str__(self): 
        return f"{self.row_label}-{self.column_number}" # makes sure the list says "A-1" (instead of: Seat object(1))

    class Meta: # This is about behavior and rules, not for showing text
        ordering = ["row_label", "column_number"] # make sure it's sorted (A1, A2, A3). 
        constraints = [
            models.UniqueConstraint(
                fields=["hall", "row_label", "column_number"], # can't have the same Hall, Row, and Seatnum more than once
                name="unique_seat_per_hall",
            ),
        ] 

    def save(self, *args, **kwargs): 
        self.row_label = self.row_label.upper() #force row label to be saved as uppercase (just to make sure)
        super().save(*args, **kwargs) # Save to DB without re-running all the heavy logic

# so all of data entered that gate datas are all consistent
