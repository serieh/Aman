from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated, Sequence
import operator, json
from langchain_core.messages import SystemMessage, HumanMessage
from .prompts.summary import summary_prompt
from pydantic import BaseModel

llm_name = "qwen3.5:4b"

# Import for any tool here, e.g.:
# from .tools.rag import rag_tool


class ResponseFormat(BaseModel):
    content: str
    emotional_state: dict        # e.g. {"emotion": "sadness", "confidence": 0.84}
    # safety_flag: str  


class AgentState(TypedDict):
    messages: Annotated[Sequence, operator.add]
    user_id: str
    chat_id: str
    emotion_context: dict | None   
    response: dict | None # it works and i dont like it


# Tools will be added here when YOU MY FRIEND finshed them :|
TOOLS = []

def build_llm():
    llm = ChatOllama(model=llm_name, stop=["<|im_start|>", "<|im_end|>"],num_ctx=32768,).bind_tools(TOOLS)
    structured_llm = llm.with_structured_output(ResponseFormat)
    return structured_llm

async def summarize(user_message: str):
    llm = ChatOllama(model=llm_name, format="json")
    messages = [
        SystemMessage(content = summary_prompt),
        HumanMessage(content=user_message)
    ]

    reply = llm.invoke(messages)
    parsed = json.loads(reply.content)

    return parsed


def agent_node(state: AgentState):
    llm = build_llm()
    response = llm.invoke(state["messages"])
    return {"response": response.model_dump()}


def should_use_tools(state: AgentState) -> str:
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