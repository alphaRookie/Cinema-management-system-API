from rest_framework import serializers
from .models import User
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.password_validation import validate_password # built-in password checker
import re

# DONT use ModelSerializer, because it passes the raw input to model to be checked by Model rules
# we defined unique email in model, so using it will always block it
class LoginSerializer(serializers.Serializer): 
    email = serializers.EmailField() # No need "Unique" check 
    password = serializers.CharField(write_only=True) 

    def validate_email(self, value):
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_regex, value): # re.match(pattern `email_regex`, string i input in form) ; `re` checks all with 1 move
            raise DRFValidationError("Please enter a valid email address")
        return value
    
    # We skip validate_password here because the Service/Authenticate will check if it's correct.


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True) # dont show it when display result to user

    class Meta:
        model = User
        fields = ["email", "password", "phone_number", "username", "is_cinema_vip"]
        read_only_fields = ["is_cinema_vip"]

    def validate_email(self, value):
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_regex, value):
            raise DRFValidationError("Please enter a valid email address")
        return value

    def validate_username(self, value):
        if len(value) < 5:
            raise DRFValidationError("Username must be atleast 5 character")
        if value.isdigit():
            raise DRFValidationError("Value cannot be only numbers")
        return value

    def validate_password(self, value):
        try:
            validate_password(value, user=self.instance) # `user=self.instance` checks if the pass has similarity with uname & email
        except DjangoValidationError as e: # catch django list of error and raise by DRF
            raise DRFValidationError(e.message) 
        return value
    

# Focuses on displaying data
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "username", "phone_number", "is_cinema_vip", "last_login"]
        read_only_fields = ["id", "is_cinema_vip"]

