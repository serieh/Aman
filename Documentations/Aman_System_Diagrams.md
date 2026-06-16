# Aman: AI-Powered Emotional Wellness Agent - System Diagrams

These diagrams reflect the finalized system architecture, replacing the legacy concepts. You can render these diagrams by pasting the code blocks into [Mermaid Live Editor](https://mermaid.live/) or directly including them in markdown viewers that support Mermaid (like GitHub or Notion).

## 1. System Architecture Diagram

This diagram shows the high-level interaction between the React Frontend, Django API, LangGraph Orchestrator, and the AI/Database layers.

```mermaid
graph TD
    %% Define Styles
    classDef frontend fill:#61dafb,stroke:#333,stroke-width:2px,color:#000
    classDef backend fill:#092e20,stroke:#333,stroke-width:2px,color:#fff
    classDef database fill:#336791,stroke:#333,stroke-width:2px,color:#fff
    classDef ai fill:#f2a900,stroke:#333,stroke-width:2px,color:#000
    
    %% Nodes
    subgraph "Client Layer"
        Client["📱 Web Interface<br/>(React SPA)"]
        Voice["🎙️ Voice Processing Module<br/>(Audio In/Out)"]
    end
    
    subgraph "Backend API Layer (Django)"
        DRF["🐍 Django REST Framework<br/>(JWT Auth, Routing)"]
    end
    
    subgraph "Relational Storage"
        PG[("🐘 PostgreSQL<br/>(Users, Chats, Messages)")]
    end
    
    subgraph "AI Orchestration Layer"
        LangGraph["🧠 LangGraph Agent<br/>(State Manager & Firewall)"]
        Tools["🛠️ Tools (RAG Node)"]
    end
    
    subgraph "AI Engine & Vector DB"
        LLM["☁️ Groq API<br/>(openai/gpt-oss-120b)"]
        Ollama["🦙 Ollama Local Host<br/>(gemma4:e2b Fallback)"]
        Qdrant[("🔍 Qdrant Vector DB<br/>(bge-m3 Embeddings)")]
    end

    %% Connections
    Client -- "Text/UI Actions" --> DRF
    Voice -- "Speech-to-Text / Text-to-Speech" --> DRF
    DRF -- "ORM Reads/Writes" --> PG
    DRF -- "Payloads" --> LangGraph
    LangGraph -- "Routes to" --> Tools
    Tools -- "Semantic Search" --> Qdrant
    LangGraph -- "Inference Requests" --> LLM
    LangGraph -- "Fallback Requests" --> Ollama
    
    %% Apply Styles
    class Client,Voice frontend
    class DRF,LangGraph,Tools backend
    class PG,Qdrant database
    class LLM,Ollama ai
```

## 2. Use Case Diagram

This diagram maps what the primary actor (the User) and the System can do, rendered as a compatible Mermaid flowchart.

```mermaid
graph TB
    %% Define Styles
    classDef actor fill:#eaeaea,stroke:#333,stroke-width:2px,color:#000
    classDef usecase fill:#d4edda,stroke:#28a745,stroke-width:1px,color:#155724
    
    actor_user["👤 User (Person in Distress)"]
    actor_system["⚙️ System / Background Tasks"]
    
    subgraph "Aman Web Application Boundary"
        UC1["Register & Login"]
        UC2["Manage Profile & Settings"]
        UC2a["Clear AI Memory / History"]
        UC3["Create New Chat"]
        UC4["Send Text/Voice Message"]
        UC5["Receive Empathetic Reply"]
        
        UC6["Execute Crisis Firewall"]
        UC7["Generate Chat Title"]
        UC8["Run Background Summarization"]
        UC9["Retrieve RAG Guidelines"]
    end
    
    actor_user --> UC1
    actor_user --> UC2
    actor_user --> UC2a
    actor_user --> UC3
    actor_user --> UC4
    UC4 -.->|triggers| UC5
    
    actor_system --> UC6
    actor_system --> UC7
    actor_system --> UC8
    actor_system --> UC9
    
    UC4 -.->|includes| UC6
    UC4 -.->|extends| UC9
    
    class actor_user,actor_system actor
    class UC1,UC2,UC2a,UC3,UC4,UC5,UC6,UC7,UC8,UC9 usecase
```

## 3. Class & Entity Relationship Diagram (Database Schema)

This defines how the relational database is structured, showcasing the cascading rules.

```mermaid
erDiagram
    USER {
        uuid id PK
        string name
        string email "Unique"
        date birthdate
        string gender
        string country
        datetime creation_date
    }
    
    CHAT {
        uuid chat_id PK
        uuid user_id FK
        string title
        string persona_id
        datetime creation_date
        datetime modify_date
    }
    
    MESSAGE {
        uuid message_id PK
        uuid chat_id FK
        string role "user or assistant"
        text content
        jsonb emotional_state
        string safety_flag
        boolean is_active
        datetime creation_date
    }
    
    SUMMARY {
        uuid summary_id PK
        uuid chat_id FK
        text content
        jsonb emotional_state
        string safety_flag
        int version
        datetime creation_date
    }
    
    %% Relationships
    USER ||--o{ CHAT : "has (Cascade Delete)"
    CHAT ||--o{ MESSAGE : "contains (Cascade Delete)"
    CHAT ||--o{ SUMMARY : "archives (Cascade Delete)"
```

## 4. Sequence Diagram (Message Flow & Firewall)

This shows the chronological flow of data when a user sends a message.

```mermaid
sequenceDiagram
    participant U as User
    participant V as Voice Module (In/Out)
    participant API as Django DRF
    participant DB as PostgreSQL
    participant LG as LangGraph
    participant QD as Qdrant (RAG)
    participant LLM as AI Models

    U->>V: Speak input (or type text)
    V->>API: Process to Text & POST payload (JWT)
    API->>DB: Verify Chat exists & is owned by User
    
    API->>LG: Dispatch user_message
    
    activate LG
    LG->>LG: Gate 1: Check Crisis Keywords
    LG->>QD: Gate 2: Semantic Crisis Check (MiniLM)
    
    alt Crisis Detected
        LG-->>API: Escalate! Override prompt
    else Normal Message
        LG->>DB: Load active messages & last summary
        LG->>LLM: ChatGroq (or gemma4:e2b fallback) with Context
        LLM-->>LG: Request RAG Tool
        LG->>QD: Search clinical/cultural guidelines
        QD-->>LG: Return top 3 passages
        LG->>LLM: Return tool context
        LLM-->>LG: Final empathetic response (JSON)
    end
    
    LG->>DB: Save User & Assistant Messages
    LG-->>API: Return response payload
    deactivate LG
    
    API-->>V: Return text & emotion metrics
    V-->>U: Synthesize speech & play audio (or display text)
    
    %% Background processing
    par Background Summarization
        API->>LLM: Fast LLM (gemma4:e2b) summarize oldest 50%
        LLM-->>API: Returned summary
        API->>DB: Save new Summary, update Message is_active=False
    and Background Title Generation
        API->>LLM: Fast LLM (gemma4:e2b) generate chat title
        LLM-->>API: Returned title
        API->>DB: Update chat title
    end
```
