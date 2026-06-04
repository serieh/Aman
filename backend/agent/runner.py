import threading
from datetime import date
from django.db import close_old_connections
from langchain_core.messages import SystemMessage, HumanMessage
from chats.models import Chat
from users.models import User
from logger import get_logger
from agent.memory.history import load_history, save_message, update_chat_modify_date
from agent.graph import GRAPH
from agent.llm import title_generator
from agent.prompts.builder import build_system_prompt
from agent.emotion_estimator import estimate_emotion
from agent.safety.safety_runner import run_input_safety, run_output_safety
from agent.config import SAFETY_MAX_OUTPUT_RETRIES


logger = get_logger(__name__)
logger.info("Agent runner initialized")


def _generate_title_background(user_message: str, chat_id: str):
    """
    Background thread target: generates a chat title via LLM and saves it.
    Uses Django ORM (thread-safe) for the DB update.
    """
    logger.debug(f"Chat title generation requested | chat_id: {chat_id}")
    try:
        title = title_generator(user_message)
        logger.info(f"Chat title generation completed successfully | chat_id: {chat_id}")
        Chat.objects.filter(chat_id=chat_id).update(title=title)
    except Exception as e:
        logger.error(f"Title generation failed, defaulting to 'Untitled Chat' | chat_id: {chat_id} | error: {e}")
        try:
            Chat.objects.filter(chat_id=chat_id).update(title="Untitled Chat")
        except Exception as inner:
            logger.error(f"Fallback title update also failed | error: {inner}")
    finally:
        close_old_connections()


def run_agent(user_id: str,chat_id: str,user_message: str,model_preference: str = "2" ) -> str:
    logger.info(f"Agent runner started | chat_id: {chat_id} | id: {user_id}")

    try:
        history = load_history(chat_id)

        if not history:
            chat = Chat.objects.filter(chat_id=chat_id).values_list("title", flat=True).first()
            
            # Check if it's None, empty, or default fallback
            if not chat or chat == "Untitled Chat":
                logger.info(f"No history or title found, generating title | chat_id: {chat_id}")
                threading.Thread(
                    target=_generate_title_background,
                    args=(user_message, chat_id),
                    daemon=True,
                ).start()
            else:
                logger.info(f"No history found but title exists, skipping title generation | chat_id: {chat_id}")
        else:
            logger.debug(f"History exists, skipping title generation | chat_id: {chat_id}")
        
        # ── Emotion Estimation ─────────────────────────────────────
        emotion = estimate_emotion(user_message)
        logger.debug(f"Emotion estimation completed | chat_id: {chat_id} | emotion: {emotion}")

        # ── Input Safety Gate ──────────────────────────────────────
        safety = run_input_safety(user_message)
        safety_tier = safety.get("safety_tier")
        crisis_flag = safety.get("crisis_flag", False)
        grey_area_flag = safety.get("grey_area_flag", False)
        category_hints = safety.get("category_hints", "")

        if safety_tier:
            logger.info(f"Safety gate triggered | tier: {safety_tier} | chat_id: {chat_id}")

        # ── Fetch User Context ─────────────────────────────────────
        try:
            user = User.objects.get(id=user_id)
            age = (date.today() - user.birthdate).days // 365 if user.birthdate else "unknown"
            user_context = (
                f"--------------------------------------------------\n"
                f"USER PROFILE\n"
                f"--------------------------------------------------\n"
                f"Name: {user.name}\n"
                f"Age: {age}\n"
                f"Gender: {user.gender}\n"
                f"Country Code: {user.country}\n"
            )
        except Exception as e:
            logger.error(f"Failed to fetch user {user_id} | error: {e}")
            user_context = ""

        # ── Dynamic System Prompt (safety + emotion combined) ──────
        system_prompt = build_system_prompt(
            emotion=emotion,
            safety_flag=safety_tier,
            grey_area_categories=category_hints,
            user_context=user_context,
        )

        messages = [
            SystemMessage(content=system_prompt), 
            *history,                               
            HumanMessage(content=user_message),
        ]
    
        logger.debug(f"Invoking LangGraph | chat_id: {chat_id} | context_messages: {len(messages)}")

        result = GRAPH.invoke({
            "messages": messages,
            "user_id": user_id,
            "chat_id": chat_id,
            "model_preference": model_preference,
        })
        response = result.get("response") or {}
        cleaned_response = (response.get("content", "")).replace("\n", "")

        # ── Output Safety Gate (with retry) ────────────────────────
        for attempt in range(1, SAFETY_MAX_OUTPUT_RETRIES + 1):
            validation = run_output_safety(cleaned_response, crisis_flag, grey_area_flag)
            if validation["safe"]:
                break

            logger.warning(
                f"Response blocked (attempt {attempt}/{SAFETY_MAX_OUTPUT_RETRIES}) "
                f"| reason: {validation['reason']} | chat_id: {chat_id}"
            )

            if attempt < SAFETY_MAX_OUTPUT_RETRIES:
                # Retry with an explanation of what was blocked
                retry_instruction = SystemMessage(content=(
                    f"Your previous response was blocked by the safety system.\n"
                    f"Reason: {validation['reason']}\n"
                    f"Please regenerate a response that avoids the blocked pattern. "
                    f"Stay empathetic and present with the user."
                ))
                messages_with_retry = messages + [retry_instruction]
                result = GRAPH.invoke({
                    "messages": messages_with_retry,
                    "user_id": user_id,
                    "chat_id": chat_id,
                    "model_preference": model_preference,
                })
                response = result.get("response") or {}
                cleaned_response = (response.get("content", "")).replace("\n", "")
            else:
                # All retries exhausted — use safe fallback
                logger.error(f"Output safety exhausted retries | chat_id: {chat_id}")
                cleaned_response = (
                    "I'm here with you. Could you tell me a little more "
                    "about what's on your mind?"
                )

        # ── Persist Messages ───────────────────────────────────────
        logger.debug(f"Persisting user and assistant messages | chat_id: {chat_id}")
        
        save_message(
            chat_id,
            role="user",
            content=user_message,
            emotional_state=emotion,
            safety_flag=safety_tier,
        )

        save_message(chat_id, role="assistant", content=cleaned_response)
        
        update_chat_modify_date(chat_id)
        
        logger.info(f"Agent runner completed successfully | chat_id: {chat_id}")
        return cleaned_response
        
    except Exception as e:
        logger.error(f"Agent runner failed | chat_id: {chat_id} | error: {str(e)}")
        return "Sorry, something went wrong while processing your message."
