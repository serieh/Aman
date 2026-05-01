from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from .prompts.builder import build_system_prompt


class AgentCreator:
    def __init__(self):
        print("Initializing AgentCreator...")
        self.llm = ChatOllama(
            model="qwen3.5:9b",
                temperature=0.7,
                stop=["<|im_start|>", "<|im_end|>", "<|endoftext|>"],
                # num_predict=150
            )
        system_prompt = build_system_prompt()
        self.agent = create_agent(
            model=self.llm,
            system_prompt=system_prompt,
        )

    def chat(self, history) -> str:
        print(f"Agent received message: {history}")

        response = self.agent.invoke({"messages": history})

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