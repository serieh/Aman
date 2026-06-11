import asyncio
import os
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

async def main():
    llm = ChatGroq(
        model_name="openai/gpt-oss-120b",
        api_key=os.getenv("GROQ_API_KEY", "missing"),
        max_retries=0
    )
    try:
        response = await llm.ainvoke([HumanMessage(content="Hello")])
        print("Success:", response.content)
    except Exception as e:
        print("Error:", repr(e))

if __name__ == "__main__":
    asyncio.run(main())
