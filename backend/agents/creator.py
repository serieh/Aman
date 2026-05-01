from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from .prompts.builder import build_system_prompt


class AgentCreator:
    def __init__(self):
        print("Initializing AgentCreator...")
        self.llm = ChatOllama(
            model="qwen3.5:9b",
            stop=["<|im_start|>", "<|im_end|>", "<|endoftext|>"],
        )
        self.agent = create_agent(self.llm, tools=[], system_prompt=build_system_prompt())

    async def chat(self, history) -> str:
        print(f"Agent received message: {history}")

        response = await self.agent.ainvoke({"messages": history})

        last = response["messages"][-1].content
        if isinstance(last, list):
            reply = " ".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in last
            ).strip()
        else:
            reply = last

        print(f"Agent reply: {reply}")
        return reply

    async def llm_call(self, prompt: str) -> str:
        print(f"LLM received message: {prompt}")
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        print(f"LLM response: {response.content}")
        return response.content