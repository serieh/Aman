# Credits and Acknowledgements

This project relies heavily on the open-source community.

## Open-Source Technologies and Models
- **Language Models**: [Groq](https://groq.com/) for fast inference (using `openai/gpt-oss-120b`), and Google's [Gemma](https://ai.google.dev/gemma) family via [Ollama](https://ollama.com/) for local fallbacks.
- **Embeddings**: [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) for multilingual semantic mapping, and [`all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) for low-latency safety classification.
- **Emotion Detection**: [AnasAlokla/multilingual_go_emotions](https://huggingface.co/AnasAlokla/multilingual_go_emotions) for fine-grained Arabic emotion tracking.
- **Core Frameworks**: [Django](https://www.djangoproject.com/), [React](https://react.dev/), [Vite](https://vitejs.dev/), [Tailwind CSS](https://tailwindcss.com/), [Zustand](https://github.com/pmndrs/zustand).
- **AI Tooling & Databases**: [LangGraph](https://langchain.com/langgraph) for orchestration, [Qdrant](https://qdrant.tech/) for vector storage, and [PostgreSQL](https://www.postgresql.org/).

## Data Sources
- **Shifaa Corpus**: An open dataset of Arabic mental health consultations provided by [Ahmed-Selem](https://huggingface.co/datasets/Ahmed-Selem/Shifaa_Arabic_Mental_Health_Consultations).
- **WHO Guidelines**: The [World Health Organization World Mental Health Report](https://www.who.int/publications/i/item/9789240049338) (English and Arabic).
