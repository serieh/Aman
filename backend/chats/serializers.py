from rest_framework import serializers
from .models import Chat, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Message
        fields = ["message_id", "role", "content", "creation_date", "emotional_state", "safety_flag"]


class ChatSerializer(serializers.ModelSerializer):
    is_generating = serializers.SerializerMethodField()

    class Meta:
        model  = Chat
        fields = ["chat_id", "title", "creation_date", "modify_date", "is_generating"]

    def get_is_generating(self, obj):
        from chats.consumers import ACTIVE_GENERATIONS
        return str(obj.chat_id) in ACTIVE_GENERATIONS


class ChatDetailSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()
    is_generating = serializers.SerializerMethodField()

    class Meta:
        model  = Chat
        fields = ["chat_id", "title", "creation_date", "modify_date", "messages", "is_generating"]

    def get_messages(self, obj):
        messages = obj.message_set.filter(is_active=True).order_by("creation_date")
        return MessageSerializer(messages, many=True).data

    def get_is_generating(self, obj):
        from chats.consumers import ACTIVE_GENERATIONS
        return str(obj.chat_id) in ACTIVE_GENERATIONS
    
class MessageRequestSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=1000, required=True)
    model   = serializers.ChoiceField(
        choices=["1", "2"],
        default="2",
        required=False,
    )
    
    