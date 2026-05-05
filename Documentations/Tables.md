# Aman — Database Tables

---

## 1. Users Table

**Purpose:** Stores account information for every registered user. This is the root table — a user must exist here before they can own any chats or messages. All other tables trace back to a `user_id`.

**Columns:**

| Column | Type | Description |
|---|---|---|
| `user_id` | UUID | Primary key, auto-generated |
| `name` | VARCHAR(150) | The user's display name |
| `email` | VARCHAR(255) | The user's email address, must be unique |
| `password` | TEXT | The user's password, stored as a bcrypt hash |
| `preferred_language` | VARCHAR(10) | Language preference: `ar`, `en`, or `auto` |
| `country` | VARCHAR(100) | Optional. Used to route regional emergency hotlines when a safety flag is triggered |
| `creation_date` | TIMESTAMPTZ | Timestamp of when the account was created |

```sql
CREATE TABLE users (
    user_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(150) NOT NULL,
    email               VARCHAR(255) UNIQUE NOT NULL,
    password            TEXT NOT NULL,
    preferred_language  VARCHAR(10) DEFAULT 'auto',
    country             VARCHAR(100),
    creation_date       TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 2. Chats Table

**Purpose:** Manages the individual chat sessions belonging to each user. Each user can have multiple independent chats. This table acts as the parent container for all messages — a chat must exist here before messages can be added to it. Every API request must verify that the requesting user owns the chat they're accessing.

**Columns:**

| Column | Type | Description |
|---|---|---|
| `chat_id` | UUID | Primary key, auto-generated |
| `user_id` | UUID | Foreign key linking to `users.user_id`. Deleted automatically if the user is deleted |
| `title` | VARCHAR(255) | A short title for the session, auto-generated from the user's first message |
| `creation_date` | TIMESTAMPTZ | Timestamp of when the chat was created |
| `modify_date` | TIMESTAMPTZ | Timestamp of the most recent activity in the chat |

```sql
CREATE TABLE chats (
    chat_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title           VARCHAR(255),
    creation_date   TIMESTAMPTZ DEFAULT NOW(),
    modify_date     TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 3. Messages Table

**Purpose:** Stores the full conversation history for every chat. When a user continues an existing chat, the backend fetches all rows for that `chat_id` and injects them into the LLM's context window so the agent remembers the conversation. Messages can have the role `summary` or `assistant` to represent condensed older messages when a conversation grows too long for the context window.

**Columns:**

| Column | Type | Description |
|---|---|---|
| `message_id` | UUID | Primary key, auto-generated |
| `chat_id` | UUID | Foreign key linking to `chats.chat_id`. Deleted automatically if the chat is deleted |
| `role` | VARCHAR(20) | Who sent the message: `user`, `assistant`, `system`, or `summary` |
| `content` | TEXT | The actual text of the message |
| `creation_date` | TIMESTAMPTZ | Timestamp of when the message was sent |
| `emotional_state` | JSONB | Emotion snapshot captured at the time of the message (e.g., `{"emotion": "sadness", "score": 0.84}`) |
| `safety_flag` | TEXT | Safety tier triggered by the message, if any: `RED`, `ORANGE`, `YELLOW`, or `GRAY` |

```sql
CREATE TABLE messages (
    message_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id         UUID NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'summary')),
    content         TEXT NOT NULL,
    creation_date   TIMESTAMPTZ DEFAULT NOW(),
    emotional_state JSONB,
    safety_flag     TEXT
);
```

---

## 4. Messages Backup Table

**Purpose:** An archive of messages that were summarized and removed from the main `messages` table. When a conversation grows too long for the LLM's context window, older messages are condensed into a `summary` or `assistant`  row in `messages` and the originals are moved here. These rows are kept for record-keeping but are no longer injected into the LLM's context. The `summary_id` column points to the `summary` row in `messages` that replaced them.

**Columns:**

| Column | Type | Description |
|---|---|---|
| `message_id` | UUID | Same UUID as the original message — no new ID is generated |
| `chat_id` | UUID | Foreign key linking to `chats.chat_id` |
| `role` | VARCHAR(20) | Same role as the original: `user`, `assistant`, `system`, or `summary` |
| `content` | TEXT | The original message content |
| `emotional_state` | JSONB | Emotion data from the original message |
| `safety_flag` | TEXT | Safety flag from the original message |
| `original_creation_date` | TIMESTAMPTZ | When the original message was created |
| `backup_date` | TIMESTAMPTZ | When the message was moved to this archive table |
| `summary_id` | UUID | Points to the `summary` row in `messages` that replaced this message |

```sql
CREATE TABLE messages_backup (
    message_id              UUID PRIMARY KEY,
    chat_id                 UUID NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    role                    VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'summary')),
    content                 TEXT NOT NULL,
    emotional_state         JSONB,
    safety_flag             TEXT,
    original_creation_date  TIMESTAMPTZ,
    backup_date             TIMESTAMPTZ DEFAULT NOW(),
    summary_id              UUID
);
```
