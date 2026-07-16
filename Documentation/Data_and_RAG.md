# Data and RAG Pipeline

The Retrieval-Augmented Generation (RAG) pipeline grounds Aman's generative responses in verified clinical literature and culturally relevant consultation records, preventing unsupported medical claims.

## Knowledge Sources

The vector database is populated from two primary data types:
1. **Structured Consultation Logs (Shifaa Corpus)**: Over 35,000 real-world Arabic psychiatric consultations formatted as Q&A pairs. This dataset helps the agent understand how distress is expressed in local dialects.
2. **Academic and Clinical Literature**: Includes the Arabic and English versions of the WHO World Mental Health Report, and research on Arabic NLP and regional healthcare perceptions.

## Processing and Chunking Strategy

- **Structured Data**: Preserves natural boundaries (one row equals one semantic chunk).
- **Unstructured PDFs**: Split along topical or section boundaries rather than fixed token counts.
- **Metadata**: Every chunk is tagged with language, topic, and source metadata to filter queries at runtime.

## Embeddings and Retrieval

Processed text is converted into dense vectors using the `BAAI/bge-m3` embedding model. This model provides strong multilingual representation, aligning Arabic and English text in a shared vector space. At runtime (in Thinking mode), the user's query is embedded and compared against the `amaan_knowledge` collection using cosine similarity to fetch the most relevant context for the LLM.

## Long-Term User Memory

For authenticated users, the system maintains a separate Qdrant collection named `user_memory`. Background processes asynchronously extract persistent biographical facts from chat interactions and save them as semantic vectors. This allows the agent to recall past context seamlessly without overloading the active conversational context window.
