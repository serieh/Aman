import asyncio
from agent.graph import agent_node
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

async def main():
    state = {
        "messages": [HumanMessage(content="Ya 3alam, I'm crying uncontrollably, chest tight, I can't breathe; attacker shoved his hands on my back, crushing me in a violent embrace that left me shaking.")],
        "user_id": "test_user",
        "chat_id": "test_chat",
        "model_preference": "1",
    }
    config = RunnableConfig()
    result = await agent_node(state, config)
    print("Agent Node Result:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
