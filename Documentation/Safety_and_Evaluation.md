# Safety and Evaluation

Clinical safety is an architectural priority in Aman, enforced through deterministic layers rather than relying solely on the language model's internal alignment.

![Message Flow & Firewall](images/Sequence%20Diagram%20(Message%20Flow%20&%20Firewall).png)

## Two-Stage Safety Firewall

### 1. Pre-Generation Input Screening
Before generation begins, every message is screened:
- **RED (Active Crisis)**: Detects suicidal ideation or self-harm using a fast keyword scanner and a lightweight semantic check (`all-MiniLM-L6-v2`) against the Qdrant `crisis_knowledge` collection. If flagged, the system overrides normal behavior to deliver a calm, life-affirming de-escalation response.
- **GRAY (Culturally Sensitive)**: Detects sensitive topics (e.g., family pressure, relationships) and routes them to careful, culturally aware clinical grounding.
- **SAFE**: Standard conversation.

### 2. Post-Generation Output Validation
After the LLM generates a response, a validator scans the text. If it detects unsafe advice, medical diagnoses, or inappropriate claims, it blocks the output and triggers a regenerate-and-retry loop.

## Evaluation Metrics

The system's integrity is validated across multiple dimensions using an offline test harness and LLM-as-a-judge (Gemini) scoring.

- **Retrieval Quality**: Measured via Context Precision (ranking of relevant passages) and Context Recall (coverage of required facts).
- **Response Quality**: Evaluated for Faithfulness (no clinical hallucinations), Empathy (validating user pain in natural Arabic), and Answer Relevancy.
- **Safety Classification**: Measured via a Confusion Matrix. The system optimizes for High Sensitivity (Recall) in the RED category to keep the False Negative Rate as close to zero as possible.
