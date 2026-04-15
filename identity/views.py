from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny # only logged-in users can book or see bookings
from typing import cast
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404

from .models import User
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .services import UserService
from .permissions import IsOwner, IsManager


# allow spesific logged-in user to see 'his own' profile, also update it
class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated, IsOwner] 
    
    def get(self, request):
        serializer = UserSerializer(request.user) #we use `request.user` bcoz they already logged-in
        return Response(serializer.data, status=status.HTTP_200_OK) # let frontend handle the message for `GET`
    
    def patch(self, request):
        # We use RegisterSerializer for the INPUT (it has the validation rules)
        # But we use UserSerializer for the OUTPUT (the response)
        serializer = RegisterSerializer(request.user, data=request.data, partial=True) #compare
        serializer.is_valid(raise_exception=True)

        update_user = UserService.save_user(
            user=request.user,
            email=serializer.validated_data.get("email"),
            phone_number=serializer.validated_data.get("phone_number"),
            username=serializer.validated_data.get("username"),
            password=serializer.validated_data.get("password")
        )

        # Why there's no access & refresh token?
        # Changing a username or phone_number doesn't change "who" the user is, the token is still valid
        return Response({
            "message": "Profile updated",
            "user": UserSerializer(update_user).data 
        }, status=status.HTTP_200_OK)
        
    
#for register
class RegisterUserAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        register_user = UserService.save_user(
            user=None,
            email=serializer.validated_data.get("email"),
            phone_number=serializer.validated_data.get("phone_number"),
            username=serializer.validated_data.get("username"),
            password=serializer.validated_data.get("password")
        )

        refresh = RefreshToken.for_user(register_user)

        return Response({
            "message": "Register successful",
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(register_user).data,
            }, status=status.HTTP_201_CREATED
        )


#for login
class LoginUserAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        login_user = cast(User, UserService.authenticate_user(# cast will catch typo error like "print(login_user.is_cinema_vp)"
            email=serializer.validated_data.get("email"),
            password=serializer.validated_data.get("password")
        ))

        refresh = RefreshToken.for_user(login_user)

        return Response({
            "message": "Login successful",
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(login_user).data,
        }, status=status.HTTP_200_OK)


# This logs out the refresh_token, not access_token
class LogoutUserAPIView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    def post(self, request):
        try:
            # The Frontend must send the "refresh" token in the body
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            
            token.blacklist() # This is where the 'token_blacklist' app does its job

            return Response({
                "message": "Logout successful. Token is now invalid."
            }, status=status.HTTP_205_RESET_CONTENT)
            
        except Exception as e:
            return Response({
                "error": "Invalid token or already logged out."
            }, status=status.HTTP_400_BAD_REQUEST)

