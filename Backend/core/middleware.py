import os
import django
from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from logger import log_context

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token):
    try:
        access_token = AccessToken(token)
        user = User.objects.get(id=access_token['user_id'])
        return user
    except Exception:
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]

        if token:
            scope["user"] = await get_user_from_token(token)
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)

class LoggingContextMiddleware:
    """Injects user authentication details and request chat IDs into logging context."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_id = "-"
        if request.user and request.user.is_authenticated:
            user_id = str(request.user.id)
            
        chat_id = "-"
        # Parse chat_id from URL resolver kwargs if available
        resolver_match = getattr(request, "resolver_match", None)
        if resolver_match and "chat_id" in resolver_match.kwargs:
            chat_id = str(resolver_match.kwargs["chat_id"])
        elif "chat_id" in request.GET:
            chat_id = request.GET["chat_id"]
            
        with log_context(chat_id=chat_id, user_id=user_id):
            return self.get_response(request)
