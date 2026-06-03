from rest_framework import serializers
from .models import Chat, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Message
        fields = ["message_id", "role", "content", "creation_date", "emotional_state", "safety_flag"]


class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Chat
        fields = ["chat_id", "title", "creation_date", "modify_date"]


class ChatDetailSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()

    class Meta:
        model  = Chat
        fields = ["chat_id", "title", "creation_date", "modify_date", "messages"]

    def get_messages(self, obj):
        messages = obj.message_set.filter(is_active=True).order_by("creation_date")
        return MessageSerializer(messages, many=True).data
    
class MessageRequestSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=1000, required=True)
    model   = serializers.ChoiceField(
        choices=["1", "2"],
        default="2",
        required=False,
    )
    
    