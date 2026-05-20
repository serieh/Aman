from django.urls import path
from . import views

urlpatterns = [
    # Pages
    path("dashboard/",views.DashboardPageView.as_view()),
    path("",views.DashboardPageView.as_view()),
    path("chat/",views.DashboardPageView.as_view()),
    path("chat/<uuid:chat_id>/", views.ChatRoomPageView.as_view()),

    # API
    path("api/v1/chats/",                        views.ChatListView.as_view()),
    path("api/v1/chats/<uuid:chat_id>/",          views.ChatDetailView.as_view()),
    path("api/v1/chats/<uuid:chat_id>/message/",  views.MessageView.as_view()),
]