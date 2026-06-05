import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()
from langchain.tools import tool

@tool
def dummy_tool(query: str) -> str:
    """A dummy tool."""
    return "Dummy result"

try:
    llm = ChatGroq(model_name="openai/gpt-oss-120b", api_key=os.getenv("GROQ_API_KEY"))
    
    print("STREAMING:")
    for chunk in llm.stream("Think step by step and answer what is 2+2"):
        if "reasoning_content" in chunk.additional_kwargs:
            print("REASON:", chunk.additional_kwargs["reasoning_content"], end="")
        else:
            print("CONTENT:", chunk.content, end="")
    print("\nSUCCESS")
except Exception as e:
    print("FAILED", e)
