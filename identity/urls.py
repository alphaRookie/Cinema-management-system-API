from django.urls import path
from .views import UserProfileAPIView, LoginUserAPIView, RegisterUserAPIView

urlpatterns = [
    path("register/", RegisterUserAPIView.as_view(), name="register-user"),
    path("login/", LoginUserAPIView.as_view(), name="login-user"),
    path("profile/", UserProfileAPIView.as_view(), name="profile-user")
]
