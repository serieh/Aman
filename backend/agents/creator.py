from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated, Sequence
import operator, json
from langchain_core.messages import SystemMessage, HumanMessage
from .prompts.summary import summary_prompt

# Import for any tool here, e.g.:
# from .tools.rag import rag_tool

class AgentState(TypedDict):
    messages: Annotated[Sequence, operator.add]
    user_id: str
    chat_id: str
    emotion_context: dict | None   


# Tools will be added here when YOU MY FRIEND finshed them :|
TOOLS = []

def build_llm():
    llm = ChatOllama(model="qwen3.5:4b", stop=["<|im_start|>", "<|im_end|>"],num_ctx=32768,) 
    return llm.bind_tools(TOOLS)

async def summarize(user_message: str):
    llm = ChatOllama(model="qwen3.5:4b", format="json")
    messages = [
        SystemMessage(content = summary_prompt),
        HumanMessage(content=user_message)
    ]

    reply = llm.invoke(messages)
    parsed = json.loads(reply.content)

    return parsed


def agent_node(state: AgentState) -> dict:
    """
    Core LLM node. Receives the full message list, calls the LLM,
    and returns the response (which may contain tool_calls).
    """
    llm = build_llm()
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


def should_use_tools(state: AgentState) -> str:
    """
    Edge condition: did the LLM ask to call a tool?
    Returns "tools" → ToolNode, or "end" → done.
    """
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "end"


def build_graph() -> object:
    tool_node = ToolNode(TOOLS)

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")

    graph.add_conditional_edges(
        "agent",
        should_use_tools,
        {"tools": "tools", "end": END},
    )

    graph.add_edge("tools", "agent")

    return graph.compile()


GRAPH = build_graph()