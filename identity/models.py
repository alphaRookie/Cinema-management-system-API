from django.db import models
from django.contrib.auth.models import AbstractUser # add custom field


# it comes up with many built-in what normally user have, these 3 new field we added are for additional
class User(AbstractUser): 
    """ Represents a user in the cinema system """
    email = models.EmailField(unique=True) # We "Override" email to make it unique for login
    phone_number = models.CharField(max_length=15) 
    #while field like username, fname, lname, password is from built-in AbstractUser
    
    # business flag (It doesn't give 'Power' over the site, it just tells the system to treat a person by special calculation)
    is_cinema_vip = models.BooleanField(default=False) 

    USERNAME_FIELD = "email" #by default it uses username for login, we force to use Email 
    REQUIRED_FIELDS = ["username"] #When create a user in the terminal (CMD), you must ask to type username too (DB demand it)


    def __str__(self):
        return self.email

