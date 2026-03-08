from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny # only logged-in users can book or see bookings
from django.shortcuts import get_object_or_404

from .models import User
from .serializers import RegisterSerializer, LoginSerializer
from .services import UserService


# allow spesific logged in user to see his profile, also update it
class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated] 
    
    def get(self, request):
        serializer = RegisterSerializer(request.user) #we use `request.user` bcoz they already logged-in
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request):
        serializer = RegisterSerializer(request.user, data=request.data, partial=True) #compare
        serializer.is_valid(raise_exception=True)

        update_user = UserService.save_user(
            user=request.user,
            email=serializer.validated_data.get("email"),
            phone_number=serializer.validated_data.get("phone_number"),
            username=serializer.validated_data.get("username"),
            password=serializer.validated_data.get("password")
        )
        return Response(RegisterSerializer(update_user).data, status=status.HTTP_200_OK)
        
    
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
        return Response(RegisterSerializer(register_user).data, status=status.HTTP_201_CREATED)


#for login
class LoginUserAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        login_user = UserService.authenticate_user(
            email=serializer.validated_data.get("email"),
            password=serializer.validated_data.get("password")
        )

        return Response(
            {f"message": "Login successful", "user": LoginSerializer(login_user).data}, 
            status=status.HTTP_200_OK
        )
