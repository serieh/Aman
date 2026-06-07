from django.shortcuts import render
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Chat, Message
from .serializers import ChatSerializer, ChatDetailSerializer, MessageRequestSerializer
from agent.runner import run_agent
from logger import get_logger

logger = get_logger(__name__)

# ── Pages ─────────────────────────────────────────────────────

class DashboardPageView(View):
    def get(self, request):
        return render(request, "dashboard.html")


class ChatRoomPageView(View):
    def get(self, request, chat_id):
        return render(request, "chat.html")


# ── API ───────────────────────────────────────────────────────

class ChatListView(APIView):

    def get(self, request):
        chats = Chat.objects.select_related("user").filter(user=request.user).order_by("-modify_date")
        return Response(ChatSerializer(chats, many=True).data)

    def post(self, request):
        chat = Chat.objects.create(user=request.user)
        return Response(ChatSerializer(chat).data, status=status.HTTP_201_CREATED)


class ChatDetailView(APIView):

    def get_chat(self, request, chat_id):
        try:
            return Chat.objects.get(chat_id=chat_id, user=request.user)
        except Chat.DoesNotExist:
            return None

    def get(self, request, chat_id):
        chat = self.get_chat(request, chat_id)
        if not chat:
            return Response({"error": "Chat not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(ChatDetailSerializer(chat).data)

    def delete(self, request, chat_id):
        chat = self.get_chat(request, chat_id)
        if not chat:
            return Response({"error": "Chat not found"}, status=status.HTTP_404_NOT_FOUND)
        chat.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, chat_id):
        chat = self.get_chat(request, chat_id)
        if not chat:
            return Response({"error": "Chat not found"}, status=status.HTTP_404_NOT_FOUND)
        
        title = request.data.get("title")
        if title is not None:
            chat.title = title
            chat.save()
            return Response(ChatSerializer(chat).data)
        return Response({"error": "No title provided"}, status=status.HTTP_400_BAD_REQUEST)

class DeleteHistoryView(APIView):
    def delete(self, request):
        user = request.user
        # Delete all chats
        Chat.objects.filter(user=user).delete()
        # Delete from Qdrant Memory
        try:
            from agent.memory.long_term_memory import clear_user_facts
            clear_user_facts(str(user.id))
        except Exception as e:
            logger.error(f"Failed to clear Qdrant memory for user {user.id}: {e}")
        
        return Response(status=status.HTTP_204_NO_CONTENT)

class DeleteMemoryView(APIView):
    def delete(self, request):
        user = request.user
        # Only delete from Qdrant Memory
        try:
            from agent.memory.long_term_memory import clear_user_facts
            clear_user_facts(str(user.id))
        except Exception as e:
            logger.error(f"Failed to clear Qdrant memory for user {user.id}: {e}")
        
        return Response(status=status.HTTP_204_NO_CONTENT)

class MessageView(APIView):
    def post(self, request, chat_id):
        # Validate the chat exists and belongs to the user
        try:
            chat = Chat.objects.get(chat_id=chat_id, user=request.user)
        except Chat.DoesNotExist:
            return Response(
                {"error": "Chat not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = MessageRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_message = serializer.validated_data["content"]
        model_preference = serializer.validated_data.get("model", "2")
        user_id = str(request.user.id)
        chat_id_str = str(chat_id)

        logger.info(
            f"MessageView dispatching to agent | chat_id: {chat_id_str} "
            f"| user_id: {user_id} | model: {model_preference}"
        )

        from django.http import StreamingHttpResponse
        try:
            generator = run_agent(
                user_id=user_id,
                chat_id=chat_id_str,
                user_message=user_message,
                model_preference=model_preference,
            )
            return StreamingHttpResponse(generator, content_type='text/plain')
        except Exception as e:
            logger.error(f"Agent call failed | chat_id: {chat_id_str} | error: {e}")
            return Response(
                {"error": "Something went wrong processing your message."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
