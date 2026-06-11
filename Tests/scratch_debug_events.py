import asyncio
from agent.graph import build_graph
agent_app = build_graph()
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
    
    async for event in agent_app.astream_events(state, config=config, version="v1"):
        if event["event"] == "on_chain_end":
            print(f"on_chain_end | name: {event.get('name')}")
            if event.get("name") == "agent_node":
                print("FOUND AGENT NODE!")
                print(event["data"])

if __name__ == "__main__":
    asyncio.run(main())
