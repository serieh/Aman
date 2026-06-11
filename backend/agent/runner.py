import threading, asyncio
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
from agent.memory.long_term_memory import retrieve_user_facts, extract_and_save_facts


logger = get_logger(__name__)
logger.info("Agent runner initialized")


def _generate_title_background(user_message: str, chat_id: str):
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


async def run_agent(user_id: str, chat_id: str, user_message: str, model_preference: str = "2", mode: str = "normal"):
    logger.info(f"Async Agent runner started | chat_id: {chat_id} | id: {user_id} | mode: {mode}")

    try:
        # Load history synchronously using thread
        history = await asyncio.to_thread(load_history, chat_id)

        if not history:
            chat_title = await asyncio.to_thread(
                lambda: Chat.objects.filter(chat_id=chat_id).values_list("title", flat=True).first()
            )
            if not chat_title or chat_title == "Untitled Chat":
                logger.debug(f"Starting background title generation | chat_id: {chat_id}")
                threading.Thread(
                    target=_generate_title_background,
                    args=(user_message, chat_id),
                    daemon=True
                ).start()
        
        emotion = await asyncio.to_thread(estimate_emotion, user_message)
        safety = await asyncio.to_thread(run_input_safety, user_message)
        safety_tier = safety.get("safety_tier")
        category_hints = safety.get("category_hints", "")

        try:
            user = await asyncio.to_thread(User.objects.get, id=user_id)
            age = (date.today() - user.birthdate).days // 365 if user.birthdate else "unknown"
            user_context = (
                f"Name: {user.name}\n"
                f"Age: {age}\n"
                f"Gender: {user.gender}\n"
                f"Country: {user.country}\n"
            )
        except Exception:
            user_context = ""

        # Retrieve long-term facts
        facts = await asyncio.to_thread(retrieve_user_facts, user_id, user_message)
        if facts:
            user_context += f"\nHere are some permanent facts you remember about the user:\n{facts}\n"

        # Fetch recent emotion and flag history
        def _fetch_histories():
            from chats.models import Message
            recent_msgs = Message.objects.filter(chat_id=chat_id, role="user").order_by("-creation_date")[:5]
            emotions = []
            flags = []
            for m in reversed(recent_msgs):
                if m.emotional_state:
                    import json
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
            
        emotion_history, flag_history = await asyncio.to_thread(_fetch_histories)

        system_prompt = build_system_prompt(
            emotion=emotion,
            safety_flag=safety_tier,
            grey_area_categories=category_hints,
            user_context=user_context,
            mode=mode,
            emotion_history=emotion_history,
            flag_history=flag_history,
        )

        messages = [
            SystemMessage(content=system_prompt), 
            *history,                               
            HumanMessage(content=user_message),
        ]
        
        # We pass state to the graph
        state_input = {
            "messages": messages,
            "user_id": user_id,
            "chat_id": chat_id,
            "model_preference": model_preference
        }
        
        # Persist user message immediately
        await asyncio.to_thread(
            save_message,
            chat_id,
            role="user",
            content=user_message,
            emotional_state=emotion,
            safety_flag=safety_tier,
        )

        is_safe = True
        assistant_content = ""
        assistant_flag = safety_tier

        for attempt in range(SAFETY_MAX_OUTPUT_RETRIES):
            final_text = ""
            tools_called_in_attempt = False
            # Run graph in streaming mode
            async for event in GRAPH.astream_events(state_input, version="v1"):
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
                            if not final_text.strip() and resp["content"].strip() and not tools_called_in_attempt:
                                final_text = resp["content"]
                                yield {"replace_all": final_text}

            if not final_text.strip() and not tools_called_in_attempt:
                from agent.config import FALLBACK_RESPONSE
                final_text = FALLBACK_RESPONSE["content"]
                yield {"replace_all": final_text}

            if tools_called_in_attempt:
                is_safe = True
                output_safety = {"safe": True, "reason": None}
            else:
                output_safety = await asyncio.to_thread(
                    run_output_safety,
                    final_text,
                    crisis_flag=safety.get("crisis_flag", False),
                    grey_area_flag=safety.get("grey_area_flag", False)
                )
                is_safe = output_safety.get("safe", True)
            
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

        await asyncio.to_thread(save_message, chat_id, role="assistant", content=assistant_content, safety_flag=assistant_flag)
        await asyncio.to_thread(update_chat_modify_date, chat_id)
        
        # Extract new facts in background
        asyncio.create_task(extract_and_save_facts(user_id, user_message, final_text))
        
        logger.info(f"Agent runner completed successfully | chat_id: {chat_id}")
        
    except Exception as e:
        logger.error(f"Agent runner failed | chat_id: {chat_id} | error: {str(e)}")
        yield "Sorry, something went wrong while processing your message."
