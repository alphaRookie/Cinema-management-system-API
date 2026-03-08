from .models import User
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.db.models import Q
from django.contrib.auth import authenticate

# here is about protection rule layer, while in `admin.py` is about blocking visual
class UserService:
    @staticmethod
    def can_manage_target(actor: User, target: User|None=None): #same as `request` and `obj`
        if target is None:
            return False
        
        if target.is_superuser and not actor.is_superuser:
            raise PermissionDenied("Non-superuser can't access superuser")


    @staticmethod
    def can_access_field(actor: User, target: User|None=None):
        forbidden = []

        # no one can change himself except superuser
        if target == actor and not actor.is_superuser:
            forbidden.extend(["is_active", "is_staff", "is_superuser", "groups", "user_permissions", "is_cinema_vip"])

        # except superuser, none can assign these power to anyone
        if not actor.is_superuser:
            forbidden.extend(["is_superuser", "is_staff", "groups", "user_permissions"])

        # no staff can assign "vip badge" to staff
        if target:
            if actor.is_staff and target.is_staff:
                forbidden.extend(["is_cinema_vip"])
        
        return set(forbidden) #when giving back the list, make sure give no duplicates `set()`


    @staticmethod
    def save_user(
        user: User | None=None,
        email: str | None=None,
        phone_number: int | None=None,
        username: str | None=None,
        password: str | None=None,
    ):
        # 1. Search for any user that matches any of the unique fields
        # Perform a single database hit instead of three separated actions
        duplicate = User.objects.filter(
            Q (email=email) |
            Q (phone_number=phone_number) |
            Q (username=username) 
        )  
        
        # exclude current user, so we dont collide with ourself
        if user:
            duplicate = duplicate.exclude(pk=user.pk)

        # 2. If we found someone, identify the specific field
        existing_user = duplicate.first() # return the single actual object
        if existing_user:
            if existing_user.email == email:
                raise ValidationError({"email": "A user with this email already exists"})
            if existing_user.phone_number == phone_number:
                raise ValidationError({"Phone number": "This phone number is already registered"})
            if existing_user.username == username:
                raise ValidationError({"Username": "This username is already taken"})
        
        # 3. otherwise update if exist
        if user:
            user.email = email if email else user.email
            user.phone_number = phone_number if phone_number else user.phone_number
            user.username = username if username else user.username
            if password:
                user.set_password(password) #hash the new password
                
            user.save()
            return user
        
        # but before creating, make sure user indeed provide it
        if not username or not email or not password:
            raise ValidationError("Email, Username, and Password are required to create an account.")
        
        # 4. or create the new one
        return User.objects.create_user( # Use create_user so the password gets hashed automatically
            email=email,
            phone_number=phone_number,
            username=username,
            password=password,
        )
    
    
    @staticmethod
    def authenticate_user(
        email: str | None=None,
        password: str | None=None,
    ):
        if not email or not password:
            raise ValidationError("Email and Password are required")

        # use django built-in to verify hashed password
        user = authenticate(email=email, password=password)

        if not user:
            raise ValidationError("Invalid email or password")
        return user
    