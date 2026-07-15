from django.urls import re_path
from . import consumers
from . import voice_consumer

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<chat_id>[\w-]+)/$", consumers.ChatConsumer.as_asgi()),
    re_path(r"ws/voice/(?P<chat_id>[\w-]+)/$", voice_consumer.VoiceConsumer.as_asgi()),
]
