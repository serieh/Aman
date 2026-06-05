from django.contrib import admin
from .models import Chat, Message

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'user', 'title', 'creation_date', 'modify_date')
    search_fields = ('title', 'user__email')
    list_filter = ('creation_date',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('message_id', 'chat', 'role', 'creation_date')
    search_fields = ('content', 'chat__chat_id')
    list_filter = ('role', 'creation_date')
