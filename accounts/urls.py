from django.urls import path
from .views import (
    RegisterView,
    VerifyEmailOTPView,
    LoginView,
    RefreshView,
    LogoutView,
    MyProfileView,
)
urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-otp/", VerifyEmailOTPView.as_view(), name="verify-otp"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MyProfileView.as_view(), name="my-profile"),
]