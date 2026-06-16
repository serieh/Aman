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

    print(f"Successfully created 3 mock chats for {user.name} ({user.email})")

    # Optionally add messages to one of the chats
    Message.objects.create(
        chat=chat1,
        role="user",
        content="I have been feeling really anxious lately about my upcoming exams."
    )
    Message.objects.create(
        chat=chat1,
        role="assistant",
        content="It's completely normal to feel anxious before exams. Let's talk about some strategies to manage that stress."
    )
    print(f"Added mock messages to chat: {chat1.title}")

if __name__ == '__main__':
    # You can change the email to the user you want to add chats to
    target_email = input("Enter the email of the user to add mock chats to: ")
    add_mock_chats_to_user(target_email)
