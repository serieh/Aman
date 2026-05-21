from django.apps import AppConfig


class ChatsConfig(AppConfig):
    name = 'chats'
    
    def ready(self):
        from agent.apps import preload_models
        preload_models()
