from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

prefix ="api/v1/auth/"

urlpatterns = [
    path("login/",    views.LoginPageView.as_view()),

    # API
    path(f"{prefix}register/", views.RegisterView.as_view()),
    path(f"{prefix}login/",    views.LoginView.as_view()),
    path(f"{prefix}refresh/",  TokenRefreshView.as_view()),  # built-in, no need to write it
    path(f"{prefix}logout/",   views.LogoutView.as_view()),
]