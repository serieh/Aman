# Aman — Database Tables & ORM Schema
### Core Tables, Relationships, and Field Mappings

This document defines the physical PostgreSQL database tables and constraints corresponding exactly to the active Django ORM models inside `users/models.py` and `chats/models.py`.

---

## 1. Schema Diagram & Relationships

The database relies on a cascading relationship structure. Deleting a user purges all their chats. Deleting a chat purges all its messages and compiled summaries.

```
                  +-----------------------------------+
                  |               users               |
                  +-----------------------------------+
                  | id (PK)              : UUID       |
                  | name                 : VARCHAR    |
                  | email (Unique)       : VARCHAR    |
                  | password             : VARCHAR    |
                  | birthdate            : DATE       |
                  | gender               : VARCHAR    |
                  | country              : VARCHAR    |
                  | creation_date        : TIMESTAMPTZ|
                  +-----------------------------------+
                                    |
                                    | 1 user -> many chats
                                    v
                  +-----------------------------------+
                  |               chats               |
                  +-----------------------------------+
                  | chat_id (PK)         : UUID       |
                  | id (FK -> users)     : UUID       | <-- Column name is "id"
                  | title                : VARCHAR    |
                  | creation_date        : TIMESTAMPTZ|
                  | modify_date          : TIMESTAMPTZ|
                  +-----------------------------------+
                                    |
            +-----------------------+-----------------------+
            | 1 chat -> many messages                       | 1 chat -> many summaries
            v                                               v
+-----------------------------------+           +-----------------------------------+
|             messages              |           |             summaries             |
+-----------------------------------+           +-----------------------------------+
| message_id (PK)       : UUID      |           | summary_id (PK)       : UUID      |
| chat_id (FK -> chats) : UUID      |           | chat_id (FK -> chats) : UUID      |
| role                  : VARCHAR   |           | content               : TEXT      |
| content               : TEXT      |           | emotional_state       : JSONB     |
| creation_date         : TIMESTAMPTZ|           | safety_flag           : VARCHAR   |
| emotional_state       : JSONB     |           | version               : INTEGER   |
| safety_flag           : VARCHAR   |           | creation_date         : TIMESTAMPTZ|
| is_active             : BOOLEAN   |           +-----------------------------------+
+-----------------------------------+
```

---

## 2. Table Specifications

### 2.1 `users` Table
*   **Purpose**: Account and credential storage. A record must exist here before any chats can be initialized.
*   **Django Model**: `User` in `users/models.py`
*   **SQL DDL**:
    ```sql
    CREATE TABLE users (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name            VARCHAR(150) NOT NULL,
        email           VARCHAR(254) UNIQUE NOT NULL,
        password        VARCHAR(128) NOT NULL, -- Stored as pbkdf2_sha256/bcrypt hash
        birthdate       DATE NOT NULL,
        gender          VARCHAR(10) NOT NULL CHECK (gender IN ('male', 'female')),
        country         VARCHAR(2) NOT NULL, -- 2-letter ISO country code (e.g. 'SA', 'EG')
        creation_date   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    );
    ```

### 2.2 `chats` Table
*   **Purpose**: Manages unique chat sessions belonging to a user.
*   **Django Model**: `Chat` in `chats/models.py`
*   **SQL DDL**:
    ```sql
    CREATE TABLE chats (
        chat_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        id              UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- User FK column
        title           VARCHAR(255) NULL,
        creation_date   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        modify_date     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    );
    ```
    *Note: The user foreign key column in database is named `id` (configured via `db_column="id"` in Django ORM).*

### 2.3 `messages` Table
*   **Purpose**: Holds the history of all user queries and agent responses. 
*   **Django Model**: `Message` in `chats/models.py`
*   **SQL DDL**:
    ```sql
    CREATE TABLE messages (
        message_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        chat_id         UUID NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
        role            VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
        content         TEXT NOT NULL,
        creation_date   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        emotional_state JSONB NULL, -- e.g. {"emotion": "anxiety", "confidence": 0.82}
        safety_flag     VARCHAR(10) NULL, -- 'RED', 'ORANGE', 'YELLOW', 'GRAY'
        is_active       BOOLEAN NOT NULL DEFAULT TRUE
    );
    ```
    *Note: Active messages (`is_active = TRUE`) are injected into the agent context. Archived messages (`is_active = FALSE`) have been summarized and are excluded from the active context.*

### 2.4 `summaries` Table
*   **Purpose**: Stores rolling summaries created during history compression.
*   **Django Model**: `Summary` in `chats/models.py`
*   **SQL DDL**:
    ```sql
    CREATE TABLE summaries (
        summary_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        chat_id         UUID NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
        content         TEXT NOT NULL,
        emotional_state JSONB NULL, -- Aggregated emotional metrics across summarized history
        safety_flag     VARCHAR(10) NULL CHECK (safety_flag IN ('RED', 'ORANGE', 'YELLOW', 'GRAY')),
        version         INTEGER NOT NULL DEFAULT 1, -- Rolling summary version
        creation_date   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    );
    ```

---

## 3. Core Database Operations

### 3.1 Fetching Active Conversational Context
When loading active context for an ongoing conversation, the agent runs the following queries:
1.  **Retrieve Latest Summary**:
    ```sql
    SELECT content, emotional_state 
    FROM summaries 
    WHERE chat_id = <chat_id> 
    ORDER BY version DESC 
    LIMIT 1;
    ```
    If present, this summary is prepended to the reasoning context as a `SystemMessage`.
2.  **Retrieve Active Messages**:
    ```sql
    SELECT role, content, emotional_state 
    FROM messages 
    WHERE chat_id = <chat_id> AND is_active = TRUE 
    ORDER BY creation_date ASC;
    ```
    These messages are structured into `HumanMessage` and `AIMessage` objects and appended in chronological order.

### 3.2 Context Compaction (Automatic Summarization)
When active message count meets or exceeds `MAX_MESSAGES_BEFORE_SUMMARY` (default: 40):
1.  A background thread retrieves all active messages.
2.  The oldest 50% are selected for compression.
3.  The thread builds an LLM prompt containing the previous summary (if any) and the old messages to generate a new summary block.
4.  The new summary is saved with `version = last_version + 1`.
5.  The oldest messages are marked inactive in a single database transaction:
    ```sql
    UPDATE messages 
    SET is_active = FALSE 
    WHERE message_id IN (<old_message_ids>);
    ```
