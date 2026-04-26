from django.urls import path
from .views import UserProfileAPIView, LoginUserAPIView, RegisterUserAPIView, LogoutUserAPIView, AdminUserAPIView, AdminUserItemAPIView

urlpatterns = [
    path("/register", RegisterUserAPIView.as_view(), name="register-user"),
    path("/login", LoginUserAPIView.as_view(), name="login-user"),
    path("/profile", UserProfileAPIView.as_view(), name="profile-user"),
    path("/logout", LogoutUserAPIView.as_view(), name="logout-user"),

    path("/adm", AdminUserAPIView.as_view(), name="list-users"),
    path("/adm/<int:pk>", AdminUserItemAPIView.as_view(), name="list-users-detail"),
]
