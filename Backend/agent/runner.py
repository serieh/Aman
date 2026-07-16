import threading, asyncio, json
from datetime import date
from django.db import close_old_connections
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from langchain_core.messages import SystemMessage, HumanMessage
from chats.models import Chat
from users.models import User
from logger import get_logger, chat_id_var, user_id_var
from timing_logger import timed_operation
from agent.memory.history import load_history, save_message, update_chat_modify_date
from agent.graph import GRAPH
from agent.llm import title_generator
from agent.prompts.builder import build_system_prompt
from agent.emotion_estimator import estimate_emotion
from agent.safety.safety_runner import run_input_safety, run_output_safety
from agent.config import SAFETY_MAX_OUTPUT_RETRIES
from agent.memory.long_term_memory import extract_and_save_facts
from chats.models import Message


logger = get_logger(__name__)
logger.info("Agent runner initialized")


def _generate_title_background(user_message: str, chat_id: str, user_id: str):
    close_old_connections()
    logger.debug(f"Chat title generation requested | chat_id: {chat_id}")
    
    # Pre-determine fallback language
    try:
        user_lang = Chat.objects.filter(chat_id=chat_id).values_list("user__language", flat=True).first() or "en"
    except Exception:
        user_lang = "en"
    
    fallback_title = "محادثة جديدة" if user_lang == "ar" else "New Chat"
    final_title = fallback_title
    
    try:
        title = title_generator(user_message, language=user_lang)
        logger.info(f"Chat title generation completed successfully | chat_id: {chat_id}")
        Chat.objects.filter(chat_id=chat_id).update(title=title)
        final_title = title
    except Exception as e:
        logger.error(f"Title generation failed, defaulting to localized fallback | chat_id: {chat_id} | error: {e}")
        try:
            Chat.objects.filter(chat_id=chat_id).update(title=fallback_title)
        except Exception as inner:
            logger.error(f"Fallback title update also failed | error: {inner}")
    finally:
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"user_{user_id}",
                    {
                        "type": "title_update",
                        "chat_id": str(chat_id),
                        "title": final_title
                    }
                )
        except Exception as e:
            logger.error(f"Failed to broadcast title update: {e}")
        close_old_connections()


def _fetch_emotion_and_flags_history(chat_id: str):
    close_old_connections()
    recent_msgs = Message.objects.filter(chat_id=chat_id, role="user").order_by("-creation_date")[:5]
    
    emotions = []
    flags = []
    for m in reversed(recent_msgs):
        if m.emotional_state:
            em_dict = m.emotional_state
            if isinstance(em_dict, str):
                try:
                    em_dict = json.loads(em_dict)
                except:
                    em_dict = {}

            if em_dict and isinstance(em_dict, dict):
                top = ", ".join(f"{k}={int(v * 100)}%" for k, v in list(em_dict.items())[:2])
                emotions.append(top)

        if m.safety_flag and m.safety_flag not in ["SAFE", "None", None]:
            flags.append(m.safety_flag)

    return emotions, flags


def _get_user_context(user_id: str):
    close_old_connections()
    try:
        user = User.objects.get(id=user_id)
        age = (date.today() - user.birthdate).days // 365 if user.birthdate else "unknown"
        lang_names = {"en": "English", "ar": "Arabic", "es": "Spanish"}
        pref_lang_name = lang_names.get(user.language, "English")
        
        context_str = (
            f"Name: {user.name}\n"
            f"Age: {age}\n"
            f"Gender: {user.gender}\n"
            f"Country: {user.country}\n"
            f"Preferred Language: {pref_lang_name}\n"
        )
        return context_str, user.language
    except Exception:
        return "", "en"

def _get_chat_persona(chat_id: str):
    close_old_connections()
    try:
        return Chat.objects.get(chat_id=chat_id).persona_id
    except Chat.DoesNotExist:
        return "aman"


def _check_chat_title(chat_id: str, user_message: str, user_id: str):
    close_old_connections()
    # Check if a title has ever been generated/attempted for this chat
    chat_title = Chat.objects.filter(chat_id=chat_id).values_list("title", flat=True).first()
    
    # Identify placeholder titles that can be overwritten by dynamic titles
    placeholders = {
        None, "", "Untitled Chat", "Voice Conversation", "New Chat",
        "محادثة غير معنونة", "محادثة صوتية", "محادثة جديدة"
    }
    
    if chat_title in placeholders:
        # Set a placeholder immediately to block subsequent messages from starting duplicate threads
        Chat.objects.filter(chat_id=chat_id).update(title="Updating title...")
        
        logger.debug(f"Starting background title generation | chat_id: {chat_id}")
        threading.Thread(
            target=_generate_title_background,
            args=(user_message, chat_id, user_id),
            daemon=True
        ).start()


async def run_agent(user_id: str, chat_id: str, user_message: str, model_preference: str = "2", mode: str = "normal", ai_msg_id: str | None = None, user_msg_id: str | None = None, persona_id: str | None = None):
    chat_id_var.set(str(chat_id))
    user_id_var.set(str(user_id))
    logger.info(f"Async Agent runner started | chat_id: {chat_id} | id: {user_id} | mode: {mode}")

    with timed_operation("total_request", chat_id=chat_id, user_id=user_id):
        try:
            # Sync wrapper functions for asyncio.to_thread with timing
            def _timed_load_history():
                with timed_operation("history_load", chat_id=chat_id):
                    return load_history(chat_id, mode=mode)

            def _timed_estimate_emotion():
                with timed_operation("emotion_estimation", chat_id=chat_id):
                    return estimate_emotion(user_message)

            def _timed_input_safety():
                with timed_operation("input_safety_check", chat_id=chat_id):
                    return run_input_safety(user_message)

            def _timed_user_context():
                with timed_operation("user_context_fetch", chat_id=chat_id):
                    return _get_user_context(user_id)

            def _timed_emotion_flag_history():
                with timed_operation("emotion_flag_history", chat_id=chat_id):
                    return _fetch_emotion_and_flags_history(chat_id)

            def _timed_get_persona():
                with timed_operation("persona_fetch", chat_id=chat_id):
                    return _get_chat_persona(chat_id)

            (
                history,
                emotion,
                safety,
                (user_context, user_language),
                (emotion_history, flag_history),
                db_persona_id
            ) = await asyncio.gather(
                asyncio.to_thread(_timed_load_history),
                asyncio.to_thread(_timed_estimate_emotion),
                asyncio.to_thread(_timed_input_safety),
                asyncio.to_thread(_timed_user_context),
                asyncio.to_thread(_timed_emotion_flag_history),
                asyncio.to_thread(_timed_get_persona)
            )

            if not persona_id:
                persona_id = db_persona_id  # use DB-fetched persona if none provided by caller

            safety_tier = safety.get("safety_tier")
            category_hints = safety.get("category_hints", "")

            await asyncio.to_thread(_check_chat_title, chat_id, user_message, user_id)

            system_prompt = build_system_prompt(
                emotion=emotion,
                safety_flag=safety_tier,
                grey_area_categories=category_hints,
                user_context=user_context,
                mode=mode,
                persona_id=persona_id,
                language=user_language,
                emotion_history=emotion_history,
                flag_history=flag_history,
            )

            messages = [
                SystemMessage(content=system_prompt),
                *history,
                HumanMessage(content=user_message),
            ]

            state_input = {
                "messages": messages,
                "user_id": user_id,
                "chat_id": chat_id,
                "model_preference": model_preference
            }

            await asyncio.to_thread(
                save_message,
                chat_id,
                role="user",
                content=user_message,
                emotional_state=emotion,
                safety_flag=safety_tier,
                message_id=user_msg_id,
            )

            is_safe = True
            assistant_content = ""
            assistant_flag = safety_tier
            safety_blocked = False

            for attempt in range(SAFETY_MAX_OUTPUT_RETRIES):
                with timed_operation("llm_inference", chat_id=chat_id, attempt=attempt):
                    final_text = ""
                    tools_called_in_attempt = False

                    # Run graph in streaming mode
                    async for event in GRAPH.astream_events(state_input, version="v2"):
                        kind = event["event"]
                        name = event["name"]

                        if kind == "on_chat_model_stream":
                            chunk = event["data"]["chunk"]
                            if chunk.content:
                                # Handle LangChain bug where with_fallbacks yields cumulative chunks
                                if final_text and chunk.content.startswith(final_text):
                                    new_text = chunk.content[len(final_text):]
                                    final_text = chunk.content
                                    if new_text:
                                        yield new_text
                                else:
                                    final_text += chunk.content
                                    yield chunk.content

                        elif kind == "on_chat_model_end":
                            output = event["data"].get("output")
                            if output and hasattr(output, "content") and output.content and not final_text.strip() and not tools_called_in_attempt:
                                # Fallback models might skip stream events when executed inside with_fallbacks
                                final_text = output.content
                                yield final_text

                        elif kind == "on_tool_start":
                            tools_called_in_attempt = True
                            yield {"tool_call": event.get("name"), "tool_input": event.get("data", {}).get("input")}

                        elif kind == "on_tool_end":
                            t_out = event.get("data", {}).get("output")
                            if hasattr(t_out, "content"):
                                t_out_str = t_out.content
                            else:
                                t_out_str = str(t_out)
                            yield {"tool_output": t_out_str}

                        elif kind == "on_chain_end" and event.get("name") == "agent":
                            node_out = event.get("data", {}).get("output")
                            if node_out and "response" in node_out:
                                resp = node_out["response"]
                                if isinstance(resp, dict) and "content" in resp:
                                    logger.info(f"CAPTURED FROM AGENT NODE: {repr(resp['content'])}")
                                    if resp.get("error_type") == "safety":
                                        safety_blocked = True
                                    if not final_text.strip() and resp["content"].strip() and not tools_called_in_attempt:
                                        final_text = resp["content"]
                                        yield {"replace_all": final_text}

                    if not final_text.strip() and not tools_called_in_attempt:
                        from agent.config import FALLBACK_RESPONSE
                        final_text = FALLBACK_RESPONSE["content"]
                        yield {"replace_all": final_text}

                if tools_called_in_attempt:
                    output_safety = {"safe": True, "reason": None}
                else:
                    with timed_operation("output_safety_check", chat_id=chat_id):
                        output_safety = await asyncio.to_thread(
                            run_output_safety,
                            final_text,
                            crisis_flag=safety.get("crisis_flag", False),
                            grey_area_flag=safety.get("grey_area_flag", False)
                        )

                is_safe = output_safety.get("safe", True)

                if is_safe:
                    assistant_content = final_text
                    break

                logger.warning(f"Post-stream safety failed on attempt {attempt + 1}: {output_safety.get('reason')}")

                if attempt < SAFETY_MAX_OUTPUT_RETRIES - 1:
                    # Send clear signal to frontend to wipe the bubble
                    yield {"clear": True}
                    # Update state_input to include the rejected message and the reason
                    from langchain_core.messages import AIMessage
                    state_input["messages"] = state_input["messages"] + [
                        AIMessage(content=final_text),
                        SystemMessage(content=f"Your previous response was flagged for safety reasons: {output_safety.get('reason')}. Please generate a new, safe response.")
                    ]

            if not is_safe:
                reason = output_safety.get('reason', '')
                if reason == "Response too short.":
                    # Provide a gentle, human-like fallback if the models fail to generate anything
                    fallback_msg = "أنا معك وأسمعك. هل يمكنك أن تخبرني المزيد عما تشعر به؟"
                    yield {"replace_all": fallback_msg}
                    assistant_content = fallback_msg
                    assistant_flag = "SAFE"
                else:
                    redacted_message = "[تم حجب هذه الرسالة لمخالفتها إرشادات الأمان]"
                    yield {"replace_all": redacted_message}
                    assistant_content = redacted_message
                    assistant_flag = "UNSAFE"

            # If the response is the fallback response (due to Groq safety refusal/block),
            # mark the user message as UNSAFE in the database so it is excluded from future history load
            if (safety_blocked or assistant_flag == "UNSAFE") and user_msg_id:
                try:
                    await asyncio.to_thread(Message.objects.filter(message_id=user_msg_id).update, safety_flag="UNSAFE")
                    logger.info(f"Marked user message {user_msg_id} as UNSAFE to prevent chat poisoning")
                except Exception as ex:
                    logger.error(f"Failed to mark user message as UNSAFE: {ex}")

            with timed_operation("save_response", chat_id=chat_id):
                await asyncio.to_thread(save_message, chat_id, role="assistant", content=assistant_content, safety_flag=assistant_flag, message_id=ai_msg_id, persona_id=persona_id)
                await asyncio.to_thread(update_chat_modify_date, chat_id)
            with timed_operation("memory_extraction", chat_id=chat_id):
                await extract_and_save_facts(user_id, user_message, final_text)

            logger.info(f"Agent runner completed successfully | chat_id: {chat_id}")

        except Exception as e:
            logger.error(f"Agent runner failed | chat_id: {chat_id} | error: {str(e)}")
            yield "Sorry, something went wrong while processing your message."
