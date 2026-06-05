from django.urls import path
from . import views

urlpatterns = [
    # Page
    path("settings/", views.SettingsPageView.as_view()),

    # API
    path("api/v1/users/me/", views.UserMeView.as_view()),
    path("api/v1/users/change-password/", views.ChangePasswordView.as_view()),
]