from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny # only logged-in users can book or see bookings
from typing import cast
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import User
from .serializers import WriteModelSerializer, WriteNonModelSerializer, ReadUserSerializer, MessageSerializer, IdentityResponseSerializer
from .services import UserService
from .permissions import IsOwner, IsManager


@extend_schema_view(
    get=extend_schema(summary="For user to access his Profile", responses={200: ReadUserSerializer}),
    patch=extend_schema(summary="To change User's Profile", request=WriteModelSerializer, responses={201: IdentityResponseSerializer})
)
# allow spesific logged-in user to see 'his own' profile, also update it
class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated, IsOwner] 
    
    def get(self, request):
        serializer = ReadUserSerializer(request.user) #we use `request.user` bcoz they already logged-in
        return Response(serializer.data, status=status.HTTP_200_OK) # let frontend handle the message for `GET`
    
    def patch(self, request):
        # We use WriteModelSerializer for the INPUT (it has the validation rules)
        # But we use ReadUserSerializer for the OUTPUT (the response)
        serializer = WriteModelSerializer(request.user, data=request.data, partial=True) #compare
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
            "user": ReadUserSerializer(update_user).data 
        }, status=status.HTTP_200_OK)
        

@extend_schema_view(
    post=extend_schema(summary="To register an Account", request=WriteModelSerializer, responses={201: IdentityResponseSerializer})
)
class RegisterUserAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = WriteModelSerializer(data=request.data)
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
            "user": ReadUserSerializer(register_user).data,
            }, status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    post=extend_schema(summary="Login to a Registered Account", description="Authenticate a user with email and password to receive Bearer tokens.", request=WriteNonModelSerializer, responses={200: IdentityResponseSerializer})
)
class LoginUserAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = WriteNonModelSerializer(data=request.data)
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
            "user": ReadUserSerializer(login_user).data,
        }, status=status.HTTP_200_OK)


@extend_schema_view(
    post=extend_schema(summary="Log-out from an Account", responses={200: MessageSerializer})
)
class LogoutUserAPIView(APIView): # This logs out the refresh_token, not access_token
    permission_classes = [IsAuthenticated, IsOwner]

    def post(self, request):
        try:
            # The Frontend must send the "refresh" token in the body
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            
            token.blacklist() # This is where the 'token_blacklist' app does its job

            return Response({
                "message": "Logout successful. Token is now invalid."
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "error": "Invalid token or already logged out."
            }, status=status.HTTP_400_BAD_REQUEST)


#-------------------- ADMIN --------------------

@extend_schema_view(
    get=extend_schema(summary="Admin: List all Users", responses={200: ReadUserSerializer(many=True)}) #bcoz it returns list
)
class AdminUserAPIView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        users = User.objects.all().order_by("-date_joined")
        serializer = ReadUserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(summary="Admin: Retrieve the detail of an Account by ID", responses={200: ReadUserSerializer}),
    delete=extend_schema(summary="Admin: Deletes an Account by ID", responses={200: MessageSerializer})
)
class AdminUserItemAPIView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        serializer = ReadUserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.delete()
        return Response({"message": f"User {user.email} has been removed"})
