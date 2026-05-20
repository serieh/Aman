from django.shortcuts import render
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Chat, Message
from .serializers import ChatSerializer, ChatDetailSerializer, MessageRequestSerializer


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
        chats = Chat.objects.filter(user=request.user).order_by("-modify_date")
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


class MessageView(APIView):

    def post(self, request, chat_id):
        try:
            chat = Chat.objects.get(chat_id=chat_id, user=request.user)
        except Chat.DoesNotExist:
            return Response({"error": "Chat not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = MessageRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user_message = serializer.validated_data["content"]
        model_preference = serializer.validated_data["model"]
        messages = ChatDetailSerializer().get_messages(chat)

        # ── AI goes here later ──────────────────────────────
        # reply = await run_agent(chat_id, user_message, messages, model_preference)
        response = {
            "content": "This is a placeholder response from the AI.",
            "emotional_state": {"note": "This is a placeholder emotional state.", "emotion": "neutral", "confidence": 0.8}
        }
        # ───────────────────────────────────────────────────

        # save user message
        Message.objects.create(chat=chat, role="user", content=user_message, emotional_state=response.get("emotional_state", dict()), safety_flag=None)

        # save AI reply
        cleaned_response = (response.get("content", "")).replace("\n", "")
        ai_message = Message.objects.create(chat=chat, role="assistant", content=cleaned_response, emotional_state=response.get("emotional_state", dict()), safety_flag=None)

        # update chat's modify_date
        chat.save()

        return Response({"reply": cleaned_response})