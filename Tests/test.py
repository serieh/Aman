import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import User
from chats.models import Chat, Message

def add_mock_chats_to_user(email):
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        print(f"User with email {email} does not exist.")
        return

    # Create dummy chats
    chat1 = Chat.objects.create(user=user, title="Dealing with Anxiety")
    chat2 = Chat.objects.create(user=user, title="Relationship Advice")
    chat3 = Chat.objects.create(user=user, title="Work Stress Management")
    chat4 = Chat.objects.create(user=user, title="Nighttime Insomnia")
    chat5 = Chat.objects.create(user=user, title="Depression Coping Strategies")

    print(f"Successfully created 5 mock chats for {user.name} ({user.email})")

if __name__ == '__main__':
    target_email = input("Enter the email of the user to add mock chats to: ")
    add_mock_chats_to_user(target_email)