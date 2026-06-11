import json
import os

CHECKPOINT_FILE = "test_results_v3.json"
REPORT_FILE = "evaluation_report_v3.md"

def evaluate_results():
    if not os.path.exists(CHECKPOINT_FILE):
        print(f"Error: {CHECKPOINT_FILE} not found.")
        return

    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    report_lines = [
        "# Aman Testing Evaluation Report V3",
        "",
        f"**Total Chats Evaluated:** {len(data)}",
        ""
    ]

    rag_triggers = 0
    tools_used = 0
    safety_triggers = 0
    refusals = 0
    short_responses = 0

    for chat_id, chat_data in data.items():
        report_lines.append(f"## {chat_id}")
        
        messages = chat_data.get("messages", [])
        for i, msg in enumerate(messages):
            if msg["role"] == "user":
                emotion = msg.get("meta_emotion", "Unknown")
                safety = msg.get("meta_safety", "Unknown")
                
                report_lines.append(f"- **Turn {i//2 + 1} (User)**:")
                report_lines.append(f"  - Detected Emotion: `{emotion}`")
                report_lines.append(f"  - Safety Flag Assigned: `{safety}`")
                
                if safety and safety not in ["SAFE", "None"]:
                    safety_triggers += 1
                    
            elif msg["role"] == "assistant":
                tools = msg.get("tools", [])
                report_lines.append(f"- **Turn {i//2} (Aman)**:")
                
                if tools:
                    for t in tools:
                        tools_used += 1
                        name = t.get("name")
                        inp = t.get("input")
                        if name == "rag_search":
                            rag_triggers += 1
                        report_lines.append(f"  - 🛠️ **Tool Executed**: `{name}` with input `{inp}`")
                else:
                    report_lines.append("  - No tools called.")
                    
                content = msg.get("content", "")
                if len(content.strip()) < 5:
                    report_lines.append("  - ⚠️ **WARNING**: Response too short (Possible safety strip).")
                    short_responses += 1
                elif "flagged and removed" in content:
                    report_lines.append("  - 🛑 **SAFETY**: Response was successfully blocked by Output Firewall.")
                    refusals += 1
                elif "Hello there. I'm Aman." in content:
                    report_lines.append("  - ⚠️ **WARNING**: Generic greeting bug triggered after RAG tool execution.")

        report_lines.append("\n---\n")

    report_lines.insert(4, f"**Total RAG Triggers:** {rag_triggers}")
    report_lines.insert(5, f"**Total Tool Calls:** {tools_used}")
    report_lines.insert(6, f"**Total High-Risk Inputs Detected:** {safety_triggers}")
    report_lines.insert(7, f"**Total System Block Refusals:** {refusals}")
    report_lines.insert(8, f"**Total Short/Empty Responses:** {short_responses}")
    report_lines.insert(9, "")

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"Evaluation complete. Report saved to {REPORT_FILE}")

if __name__ == "__main__":
    evaluate_results()
