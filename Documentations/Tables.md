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

**Purpose:** Stores the full conversation history for every chat. When a user continues an existing chat, the backend fetches all **active** rows for that `chat_id` and injects them into the LLM's context window so the agent remembers the conversation. When a chat grows too long, older messages are archived by setting `is_active = FALSE` and a summary is written to the Summaries table instead. Archived messages are never deleted — they stay in the table for reference but are excluded from the LLM context.

**Columns:**

| Column | Type | Description |
|---|---|---|
| `message_id` | UUID | Primary key, auto-generated |
| `chat_id` | UUID | Foreign key linking to `chats.chat_id`. Deleted automatically if the chat is deleted |
| `role` | VARCHAR(20) | Who sent the message: `user`, `assistant`, or `system` |
| `content` | TEXT | The actual text of the message |
| `creation_date` | TIMESTAMPTZ | Timestamp of when the message was sent |
| `emotional_state` | JSONB | Emotion snapshot captured at the time of the message (e.g., `{"emotion": "sadness", "score": 0.84}`) |
| `safety_flag` | TEXT | Safety tier triggered by the message, if any: `RED`, `ORANGE`, `YELLOW`, or `GRAY` |
| `is_active` | BOOLEAN | `TRUE` = included in LLM context. `FALSE` = archived (was summarized, excluded from context) |

```sql
CREATE TABLE messages (
    message_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id         UUID NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content         TEXT NOT NULL,
    creation_date   TIMESTAMPTZ DEFAULT NOW(),
    emotional_state JSONB,
    safety_flag     TEXT,
    is_active       BOOLEAN DEFAULT TRUE
);
```

---

## 4. Summaries Table

**Purpose:** Stores the full history of rolling summaries for each chat. Every time the active messages exceed the context limit, the oldest messages are archived (`is_active = FALSE`) and a **new summary row is inserted** — it does not overwrite the previous one. Each row is immutable once written. The `version` column tracks the order. When loading context, the backend always fetches the latest version (highest `version` number). Older versions are never used for inference but are preserved for reference and future longitudinal analysis.

**Columns:**

| Column | Type | Description |
|---|---|---|
| `summary_id` | UUID | Primary key, auto-generated |
| `chat_id` | UUID | Foreign key linking to `chats.chat_id`. Deleted automatically if the chat is deleted |
| `content` | TEXT | The condensed summary of all archived messages up to this point |
| `emotional_state` | JSONB | Aggregated emotional snapshot across all archived messages up to this version |
| `safety_flag` | TEXT | The highest safety tier seen across all archived messages up to this version, if any: `RED`, `ORANGE`, `YELLOW`, or `GRAY` |
| `version` | INTEGER | Increments by 1 each time a new summary is generated for this chat (1, 2, 3...) |
| `creation_date` | TIMESTAMPTZ | Timestamp of when this summary version was created |

```sql
CREATE TABLE summaries (
    summary_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id         UUID NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    content         TEXT NOT NULL,
    emotional_state JSONB,
    safety_flag     TEXT,
    version         INTEGER NOT NULL DEFAULT 1,
    creation_date   TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 5. Schema Overview

```
users
  user_id (PK)
  name
  email
  password
  preferred_language
  country
  creation_date
       │
       │ one user → many chats
       ▼
chats
  chat_id (PK)
  user_id (FK → users)
  title
  creation_date
  modify_date
       │
       ├─────────────────────────────────────┐
       │ one chat → many messages            │ one chat → many summaries
       ▼                                     ▼
messages                               summaries
  message_id (PK)                        summary_id (PK)
  chat_id (FK → chats)                   chat_id (FK → chats)
  role                                   content
  content                                emotional_state
  creation_date                          safety_flag
  emotional_state                        version          ← 1, 2, 3...
  safety_flag                            creation_date
  is_active
```

---

## 6. Relationships & Cascade Rules

| Relationship | Type | On Delete |
|---|---|---|
| `users` → `chats` | One-to-many | Deleting a user deletes all their chats |
| `chats` → `messages` | One-to-many | Deleting a chat deletes all its messages |
| `chats` → `summaries` | One-to-many | Deleting a chat deletes all its summaries |

---

## 7. Context Loading Logic

When the agent loads context for a chat, it always follows this order:

```
1. SELECT content FROM summaries
   WHERE chat_id = $1
   ORDER BY version DESC
   LIMIT 1
   → inject as the first item in context (if any summary exists)

2. SELECT * FROM messages
   WHERE chat_id = $1 AND is_active = TRUE
   ORDER BY creation_date ASC
   → inject in chronological order after the summary
```

**Summarization trigger** — runs before loading context if active messages exceed the limit:

```
if COUNT(active messages) > MAX_MESSAGES (e.g. 40):

    1. Take the oldest 20 active messages
    2. Get the current latest summary (if any)
    3. Generate a new summary:
         new_summary = LLM(latest_summary + oldest_20_messages)
    4. Get current max version for this chat (0 if none)
    5. INSERT into summaries (chat_id, content, emotional_state, safety_flag, version)
         VALUES ($chat_id, new_summary, ..., max_version + 1)
    6. SET is_active = FALSE on those 20 messages
    7. Continue with context load as normal
```

After summarization, the context the LLM receives looks like:

```
[SUMMARY v3] "User has been struggling with work stress since week 1.
              Mentioned feeling isolated. Dominant emotion: sadness.
              In week 2, discussed conflict with manager..."

[user]       "today was really bad again"
[assistant]  "I'm sorry to hear that. What happened today?"
[user]       "my manager criticized me in front of everyone"
...          (remaining active messages)
```

Older summary versions (v1, v2) remain in the table but are never loaded into the LLM context.

---

## 8. Notes

- **Passwords** must always be stored as bcrypt hashes. Never store plaintext.
- **`preferred_language`** accepted values: `ar` (Arabic), `en` (English), `auto` (detect from input).
- **`safety_flag`** accepted values: `RED`, `ORANGE`, `YELLOW`, `GRAY`, or `NULL` (no flag).
- **`role`** accepted values in messages: `user`, `assistant`, `system`.
- **`emotional_state`** expected shape: `{"emotion": "sadness", "score": 0.84}` — stored as JSONB for flexibility.
- **`summaries.version`** starts at 1 and increments by 1 each time a new summary is generated for that chat. The application is responsible for computing `MAX(version) + 1` before each insert.
- **`chats.modify_date`** should be updated by the application every time a new message is added to the chat.