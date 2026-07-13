import operator
import asyncio
import inspect
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig

from .llm import structured_llm_thinking, structured_llm_fast, tools
from logger import get_logger
from .config import LLM_MAX_RETRIES, FALLBACK_RESPONSE

logger = get_logger(__name__)
logger.info("Creator agent module loaded")

# Build a name -> LangChain tool registry from the tools list
TOOL_REGISTRY = {tool.name: tool for tool in tools}

class AgentState(TypedDict):
    messages: Annotated[Sequence, operator.add]
    user_id: str
    chat_id: str
    response: dict | None
    model_preference: str
    

async def agent_node(state: AgentState, config: RunnableConfig):
    chat_id = state.get("chat_id", "unknown")
    model_preference = state.get("model_preference", "2")
    logger.info(f"Agent node processing | chat_id: {chat_id} | model_tier: {model_preference}")

    llm = structured_llm_thinking if model_preference == "1" else structured_llm_fast

    for attempt in range(1, LLM_MAX_RETRIES + 1):
        try:
            # Pass config so astream_events can intercept the chat model stream
            response = await llm.ainvoke(state["messages"], config=config)
            
            # If it's a tool call, update messages state and continue graph execution
            if getattr(response, "tool_calls", None):
                logger.info(f"LLM tool call generated | chat_id: {chat_id} | attempt: {attempt}")
                return {"messages": [response]}
            
            # Otherwise, it's final ResponseFormat object
            resp_dict = response.model_dump() if hasattr(response, "model_dump") else {"content": response.content}
            logger.info(f"LLM final response generated | chat_id: {chat_id} | attempt: {attempt}")
            return {"response": resp_dict}

        except Exception as e:
            logger.warning(f"Agent node attempt {attempt}/{LLM_MAX_RETRIES} failed | chat_id: {chat_id} | error: {str(e)}")
            if attempt == LLM_MAX_RETRIES:
                logger.error(f"Agent node exhausted retries, using fallback | chat_id: {chat_id}")
                return {"response": FALLBACK_RESPONSE}
            

async def async_parallel_tool_node(state: AgentState, config: RunnableConfig):
    """
    Replaces ToolNode. Runs all tool_calls from the last AI message
    concurrently using asyncio.gather(), then returns all results as
    ToolMessage objects appended to messages.
    """
    last_message = state["messages"][-1]
    tool_calls = last_message.tool_calls  # list of dicts: {id, name, args}

    async def _invoke_one(tc: dict) -> ToolMessage:
        tool_name = tc["name"]
        tool_args = tc["args"]
        tool_id = tc["id"]
        tool_fn = TOOL_REGISTRY.get(tool_name)

        if tool_fn is None:
            return ToolMessage(
                content=f"Error: tool '{tool_name}' not found.",
                tool_call_id=tool_id,
                name=tool_name
            )

        try:
            # Replicate InjectedState: if the tool expects 'user_id', pass it explicitly
            raw_fn = getattr(tool_fn, "func", tool_fn)
            sig = inspect.signature(raw_fn)
            invocation_args = dict(tool_args)
            if "user_id" in sig.parameters:
                invocation_args["user_id"] = state["user_id"]

            result = await tool_fn.ainvoke(invocation_args, config=config)
            content = result if isinstance(result, str) else str(result)
        except Exception as e:
            logger.warning(f"Tool '{tool_name}' failed: {e}")
            content = f"Error: Tool '{tool_name}' failed to execute. Details: {str(e)}"

        return ToolMessage(
            content=content,
            tool_call_id=tool_id,
            name=tool_name
        )

    # Run all tool calls concurrently
    tool_names = [tc["name"] for tc in tool_calls]
    logger.info(f"Parallel tool execution started | tools: {tool_names} | chat_id: {state.get('chat_id')}")
    
    results = await asyncio.gather(
        *[_invoke_one(tc) for tc in tool_calls],
        return_exceptions=True
    )

    tool_messages = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            tool_messages.append(ToolMessage(
                content=f"Error: Tool execution raised an exception. Details: {str(r)}",
                tool_call_id=tool_calls[i]["id"],
                name=tool_calls[i]["name"]
            ))
        else:
            tool_messages.append(r)

    logger.info(f"Parallel tool execution completed | tools: {tool_names}")
    return {"messages": tool_messages}


def should_use_tools(state: AgentState) -> str:
    """
    Edge condition: did the LLM ask to call a tool?
    Returns "tools" → ToolNode, or "end" → done.
    """
    tool_calls_count = sum(1 for m in state["messages"] if getattr(m, "tool_calls", None))
    if tool_calls_count >= 3:
        logger.warning(f"Max tool iterations reached ({tool_calls_count}). Forcing end.")
        return "end"

    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return "end"

def build_graph() -> object:
    logger.info("Building agent graph")

    graph = StateGraph(AgentState)
    graph.add_node("tools", async_parallel_tool_node)
    graph.add_node("agent", agent_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges(
        "agent",
        should_use_tools,
        {"tools": "tools", "end": END},
    )
    graph.add_edge("tools", "agent")

    logger.info("Agent graph compiled successfully")
    return graph.compile()

GRAPH = build_graph()