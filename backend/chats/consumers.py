import json, logging, asyncio, time
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from django.contrib.auth.models import AnonymousUser
from agent.runner import run_agent
from chats.models import Chat

logger = logging.getLogger(__name__)

# Global state to track active generations across the server
# Structure: {chat_id: {"message_id": "...", "content": "..."}}
ACTIVE_GENERATIONS = {}

async def background_run_agent(user_id, chat_id, message, model_preference, channel_layer, ai_msg_id, user_msg_id=None):
    group_name = f"chat_{chat_id}"
    user_group = f"user_{user_id}"
    
    # Broadcast start of generation
    try:
        await channel_layer.group_send(
            user_group,
            {
                "type": "generation_status",
                "chat_id": str(chat_id),
                "is_generating": True
            }
        )
    except Exception as e:
        logger.error(f"Failed to broadcast generation start: {e}")
    
    try:
        async for payload in run_agent(str(user_id), chat_id, message, model_preference, "normal", ai_msg_id=ai_msg_id, user_msg_id=user_msg_id):
            final_payload = payload if isinstance(payload, dict) else {"chunk": payload}
            
            # Update global state
            if "chunk" in final_payload:
                ACTIVE_GENERATIONS[chat_id]["content"] += final_payload["chunk"]
            elif "replace_all" in final_payload:
                ACTIVE_GENERATIONS[chat_id]["content"] = final_payload["replace_all"]
            elif "clear" in final_payload:
                ACTIVE_GENERATIONS[chat_id]["content"] = ""
                
            final_payload["message_id"] = ai_msg_id
            await channel_layer.group_send(group_name, {"type": "chat.message", "payload": final_payload})
            
        await channel_layer.group_send(group_name, {"type": "chat.message", "payload": {"done": True, "message_id": ai_msg_id}})
    except asyncio.CancelledError:
        logger.info(f"Agent task cancelled for chat {chat_id}")
        await channel_layer.group_send(group_name, {"type": "chat.message", "payload": {"done": True, "aborted": True, "message_id": ai_msg_id}})
    except Exception as e:
        logger.error(f"Error in background agent: {e}")
        await channel_layer.group_send(group_name, {"type": "chat.message", "payload": {"error": "An error occurred while generating the response."}})
    finally:
        ACTIVE_GENERATIONS.pop(chat_id, None)
        try:
            await channel_layer.group_send(
                user_group,
                {
                    "type": "generation_status",
                    "chat_id": str(chat_id),
                    "is_generating": False
                }
            )
        except Exception as e:
            logger.error(f"Failed to broadcast generation end: {e}")

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]

        if isinstance(self.user, AnonymousUser):
            await self.close(code=4003)
            return

        chat_exists = await self.check_chat_exists(self.chat_id, self.user)
        if not chat_exists:
            await self.close(code=4004)
            return

        self.chat_group = f"chat_{self.chat_id}"
        self.user_group = f"user_{self.user.id}"

        # Join chat group
        await self.channel_layer.group_add(self.chat_group, self.channel_name)
        # Join user group (for global events like title updates)
        await self.channel_layer.group_add(self.user_group, self.channel_name)

        await self.accept()
        logger.info(f"WebSocket connected for chat {self.chat_id}")

        # Send catchup if this chat is actively generating
        if self.chat_id in ACTIVE_GENERATIONS:
            active_data = ACTIVE_GENERATIONS[self.chat_id]
            await self.send(text_data=json.dumps({
                "catchup": True,
                "message_id": active_data["message_id"],
                "content": active_data["content"]
            }))
        else:
            await self.send(text_data=json.dumps({
                "generation_status": {"chat_id": str(self.chat_id), "is_generating": False}
            }))

    async def disconnect(self, close_code):
        if hasattr(self, 'chat_group'):
            await self.channel_layer.group_discard(self.chat_group, self.channel_name)
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)
        logger.info(f"WebSocket disconnected with code {close_code}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"error": "Invalid JSON"}))
            return

        if data.get("action") == "stop":
            if self.chat_id in ACTIVE_GENERATIONS:
                task = ACTIVE_GENERATIONS[self.chat_id].get("task")
                if task:
                    task.cancel()
            return

        message = data.get("message", "").strip()
        model_preference = data.get("model_preference", "2")

        if not message:
            await self.send(text_data=json.dumps({"error": "Empty message"}))
            return

        if self.chat_id in ACTIVE_GENERATIONS:
            await self.send(text_data=json.dumps({"error": "A response is already generating."}))
            return

        import uuid
        client_message_id = data.get("client_message_id")
        user_msg_id = client_message_id if client_message_id else str(uuid.uuid4())

        # Broadcast the user message to the chat group
        await self.channel_layer.group_send(
            self.chat_group,
            {
                "type": "chat.message",
                "payload": {
                    "user_message": {
                        "message_id": user_msg_id,
                        "client_message_id": client_message_id,
                        "role": "user",
                        "content": message
                    }
                }
            }
        )

        ai_message_id = data.get("ai_message_id")
        ai_msg_id = ai_message_id if ai_message_id else str(uuid.uuid4())
        ACTIVE_GENERATIONS[self.chat_id] = {"message_id": ai_msg_id, "content": ""}
        
        # Spawn decoupled task
        task = asyncio.create_task(background_run_agent(self.user.id, self.chat_id, message, model_preference, self.channel_layer, ai_msg_id, user_msg_id))
        ACTIVE_GENERATIONS[self.chat_id]["task"] = task

    async def chat_message(self, event):
        # Called when a message is sent to the chat group
        await self.send(text_data=json.dumps(event["payload"]))
        
    async def title_update(self, event):
        # Called when a title update is sent to the user group
        await self.send(text_data=json.dumps({"title_update": event}))

    async def generation_status(self, event):
        # Called when a generation status update is sent to the user group
        await self.send(text_data=json.dumps({"generation_status": event}))

    async def chat_deleted(self, event):
        # Called when the chat is deleted from another view
        if self.chat_id in ACTIVE_GENERATIONS:
            task = ACTIVE_GENERATIONS[self.chat_id].get("task")
            if task:
                task.cancel()
        await self.send(text_data=json.dumps({"error": "Chat deleted"}))
        await self.close(code=4004)

    @database_sync_to_async
    def check_chat_exists(self, chat_id, user):
        return Chat.objects.filter(chat_id=chat_id, user=user).exists()
