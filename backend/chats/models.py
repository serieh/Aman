import uuid
from django.db import models
from users.models import User


class Chat(models.Model):
    chat_id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user          = models.ForeignKey(User, on_delete=models.CASCADE, db_column="id")
    title         = models.CharField(max_length=255, blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    modify_date   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chats"


class Message(models.Model):
    message_id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat            = models.ForeignKey(Chat, on_delete=models.CASCADE, db_column="chat_id")
    role            = models.CharField(max_length=20)  # user / assistant
    content         = models.TextField()
    creation_date   = models.DateTimeField(auto_now_add=True)
    emotional_state = models.JSONField(null=True, blank=True)
    safety_flag     = models.CharField(max_length=10, null=True, blank=True)
    is_active       = models.BooleanField(default=True)

    class Meta:
        db_table = "messages"


class Summary(models.Model):
    SAFETY_CHOICES = [
        ("RED", "RED"),
        ("ORANGE", "ORANGE"),
        ("YELLOW", "YELLOW"),
        ("GRAY", "GRAY"),
    ]

    summary_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        db_column="chat_id",
        related_name="summaries"
    )

    content = models.TextField()

    emotional_state = models.JSONField(
        blank=True,
        null=True
    )

    safety_flag = models.CharField(
        max_length=10,
        choices=SAFETY_CHOICES,
        blank=True,
        null=True
    )

    version = models.IntegerField(default=1)

    creation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "summaries"
        # ordering = ["-version"]

    def __str__(self):
        return f"Summary v{self.version} - {self.chat.chat_id}"