# Aman — Unified URL & API Route Mapping
### Comprehensive Directory of Pages, Views, Routes, and JSON Payloads

This document represents the absolute, compiled source of truth for the entire URL space, view configurations, routing tables, and REST API schemas for the **Aman** backend. 

All user-facing page views and REST endpoints are consolidated below under a single, unified reference guide.

---

## 1. Django Routing & App Structure

### 1.1 Flat Application Architecture
Aman is organized as a flat set of top-level Django packages under the project root (`backend/`). This maintains high readability and clean module imports:

```
backend/
├── core/         → Project config, standard settings, and root URL routing
├── api/          → App: Login/Register page templates; signup, login, and JWT blacklist APIs
├── users/        → App: User profile settings panel; user profile CRUD APIs
├── chats/        → App: Client dashboard, chat room interface; chat list, details, and agent trigger APIs
└── agent/        → Module: Independent LangGraph AI Conversational Agent Engine
```

### 1.2 Root Routing Configuration
The main system routing config in `backend/core/urls.py` delegates URL parsing directly to each app-level routing file:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Includes app routing tables directly (REST APIs only)
    path("",  include("api.urls")),     # Auth REST APIs
    path("",  include("users.urls")),   # User profile REST APIs
    path("",  include("chats.urls")),   # Chats REST APIs
]
```

### 1.3 App-Level URL Configurations

#### Auth App Routing — `backend/api/urls.py`
```python
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

prefix = "api/v1/auth/"

urlpatterns = [
    # Pages
    path("login/",    views.LoginPageView.as_view()),

    # API
    path(f"{prefix}register/", views.RegisterView.as_view()),
    path(f"{prefix}login/",    views.LoginView.as_view()),
    path(f"{prefix}refresh/",  TokenRefreshView.as_view()),  # built-in SimpleJWT view
    path(f"{prefix}logout/",   views.LogoutView.as_view()),
]
```

#### User App Routing — `backend/users/urls.py`
```python
from django.urls import path
from . import views

urlpatterns = [
    # Page
    path("settings/", views.SettingsPageView.as_view()),

    # API
    path("api/v1/users/me/", views.UserMeView.as_view()),
]
```

#### Chat App Routing — `backend/chats/urls.py`
```python
from django.urls import path
from . import views

urlpatterns = [
    # Pages
    path("dashboard/", views.DashboardPageView.as_view()),
    path("",           views.DashboardPageView.as_view()),
    path("chat/",      views.DashboardPageView.as_view()),
    path("chat/<uuid:chat_id>/", views.ChatRoomPageView.as_view()),

    # API
    path("api/v1/chats/",                        views.ChatListView.as_view()),
    path("api/v1/chats/<uuid:chat_id>/",          views.ChatDetailView.as_view()),
    path("api/v1/chats/<uuid:chat_id>/message/",  views.MessageView.as_view()),
]
```

---

## 2. Unified Routing Table

All REST endpoints operate on JSON requests/responses and are standardized under the `/api/v1/` prefix. Authentication relies on **JSON Web Tokens (JWT)**.

| Category | HTTP Method | URL Path | View Class | Purpose / Response |
| :--- | :---: | :--- | :--- | :--- |
| **Auth REST API** | `POST` | `/api/v1/auth/register/` | `RegisterView` | Signs up new user; returns JWT `access` & `refresh` |
| **Auth REST API** | `POST` | `/api/v1/auth/login/` | `LoginView` | Authenticates credentials; returns JWT tokens |
| **Auth REST API** | `POST` | `/api/v1/auth/refresh/` | `TokenRefreshView` | DRF SimpleJWT token refresh endpoint |
| **Auth REST API** | `POST` | `/api/v1/auth/logout/` | `LogoutView` | Blacklists refresh token |
| **Profile API** | `GET` | `/api/v1/users/me/` | `UserMeView` | Retrieves current logged-in user profile details |
| **Profile API** | `PUT` | `/api/v1/users/me/` | `UserMeView` | Partially updates user profile details |
| **Profile API** | `DELETE` | `/api/v1/users/me/` | `UserMeView` | Completely deletes user account (cascades all data) |
| **Profile API** | `POST` | `/api/v1/users/change-password/` | `ChangePasswordView` | Changes user password |
| **Chat REST API** | `GET` | `/api/v1/chats/` | `ChatListView` | Lists active user chats (ordered by most recent modification) |
| **Chat REST API** | `POST` | `/api/v1/chats/` | `ChatListView` | Creates a new empty chat session |
| **Chat REST API** | `DELETE` | `/api/v1/chats/history/` | `DeleteHistoryView` | Deletes all of the user's chat history and wipes long-term memory |
| **Chat REST API** | `DELETE` | `/api/v1/chats/memory/` | `DeleteMemoryView` | Wipes long-term memory while keeping chat history intact |
| **Chat REST API** | `GET` | `/api/v1/chats/<uuid:chat_id>/` | `ChatDetailView` | Fetches chat title and all active messages |
| **Chat REST API** | `PATCH` | `/api/v1/chats/<uuid:chat_id>/` | `ChatDetailView` | Renames a specific chat session |
| **Chat REST API** | `DELETE` | `/api/v1/chats/<uuid:chat_id>/` | `ChatDetailView` | Deletes specified chat session and all messages/summaries |
| **Agent REST API** | `POST` | `/api/v1/chats/<uuid:chat_id>/message/` | `MessageView` | Sends message to AI agent; streams real-time LLM response chunks |

*Note: Page rendering routes (like `/login/` or `/dashboard/`) are now handled exclusively by the React SPA (Vite/React Router) running on port 5173, communicating directly with the `/api/v1/` endpoints.*

---

## 3. Authentication API Payload Specifications

### 3.1 Register User
*   **Method**: `POST`
*   **Path**: `/api/v1/auth/register/`
*   **Access**: `AllowAny`
*   **Request Body (`application/json`)**:
    ```json
    {
      "name": "Sarah Connor",
      "email": "sarah@sky.net",
      "password": "strong-password-here",
      "birthdate": "1984-11-26",
      "gender": "female",
      "country": "US"
    }
    ```
*   **Success Response (`201 Created`)**:
    ```json
    {
      "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```

### 3.2 Login (Token Obtain)
*   **Method**: `POST`
*   **Path**: `/api/v1/auth/login/`
*   **Access**: `AllowAny`
*   **Request Body (`application/json`)**:
    ```json
    {
      "email": "sarah@sky.net",
      "password": "strong-password-here"
    }
    ```
*   **Success Response (`200 OK`)**:
    ```json
    {
      "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
*   **Error Response (`401 Unauthorized`)**:
    ```json
    {
      "error": "Invalid credentials"
    }
    ```

### 3.3 Token Refresh
*   **Method**: `POST`
*   **Path**: `/api/v1/auth/refresh/`
*   **Access**: `AllowAny`
*   **Request Body (`application/json`)**:
    ```json
    {
      "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
*   **Success Response (`200 OK`)**:
    ```json
    {
      "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```

### 3.4 Logout
*   **Method**: `POST`
*   **Path**: `/api/v1/auth/logout/`
*   **Access**: `IsAuthenticated` (Bearer Token required)
*   **Request Body (`application/json`)**:
    ```json
    {
      "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
*   **Success Response (`302 Found`)**: Redirects browser client to `/login/` after blacklisting the refresh token.

---

## 4. Profile API Payload Specifications

### 4.1 Get Profile
*   **Method**: `GET`
*   **Path**: `/api/v1/users/me/`
*   **Access**: `IsAuthenticated`
*   **Success Response (`200 OK`)**:
    ```json
    {
      "id": "e44d320a-8bf8-4682-965a-063fb5584bf7",
      "name": "Sarah Connor",
      "email": "sarah@sky.net",
      "birthdate": "1984-11-26",
      "gender": "female",
      "country": "US",
      "creation_date": "2026-05-21T18:15:30Z"
    }
    ```

### 4.2 Update Profile (Partial)
*   **Method**: `PUT`
*   **Path**: `/api/v1/users/me/`
*   **Access**: `IsAuthenticated`
*   **Request Body (`application/json`)** *(Fields like `email`, `id`, and `creation_date` are protected and ignored)*:
    ```json
    {
      "name": "Sarah J. Connor",
      "country": "EG"
    }
    ```
*   **Success Response (`200 OK`)**: Returns updated profile JSON.

### 4.3 Delete Account
*   **Method**: `DELETE`
*   **Path**: `/api/v1/users/me/`
*   **Access**: `IsAuthenticated`
*   **Success Response (`204 No Content`)**: Deletes the user account. This triggers a **database-level cascade purge**, deleting all linked `chats`, `messages`, and rolling `summaries` permanently.

---

## 5. Chats & Agent API Payload Specifications

### 5.1 List Chats
*   **Method**: `GET`
*   **Path**: `/api/v1/chats/`
*   **Access**: `IsAuthenticated`
*   **Success Response (`200 OK`)**:
    ```json
    [
      {
        "chat_id": "b9f93c01-7fa1-4a41-b844-32ff56aa41be",
        "title": "Dealing with Future Stress",
        "creation_date": "2026-05-21T18:20:00Z",
        "modify_date": "2026-05-21T19:10:00Z"
      }
    ]
    ```

### 5.2 Create Chat Session
*   **Method**: `POST`
*   **Path**: `/api/v1/chats/`
*   **Access**: `IsAuthenticated`
*   **Success Response (`201 Created`)**:
    ```json
    {
      "chat_id": "8cbe675a-a309-411a-bb10-911cb75949e2",
      "title": null,
      "creation_date": "2026-05-21T22:15:00Z",
      "modify_date": "2026-05-21T22:15:00Z"
    }
    ```

### 5.3 Get Chat Details & Messages
*   **Method**: `GET`
*   **Path**: `/api/v1/chats/<uuid:chat_id>/`
*   **Access**: `IsAuthenticated` (ownership verified; yields `404` if accessing another user's chat)
*   **Success Response (`200 OK`)**:
    ```json
    {
      "chat_id": "b9f93c01-7fa1-4a41-b844-32ff56aa41be",
      "title": "Dealing with Future Stress",
      "creation_date": "2026-05-21T18:20:00Z",
      "modify_date": "2026-05-21T19:10:00Z",
      "messages": [
        {
          "message_id": "22ffaa11-8899-aabb-ccdd-eeff00112233",
          "role": "user",
          "content": "I've been feeling really anxious about tomorrow.",
          "creation_date": "2026-05-21T19:09:00Z",
          "emotional_state": {"emotion": "anxiety", "confidence": 0.88},
          "safety_flag": null
        },
        {
          "message_id": "55eedd22-1122-3344-5566-778899aabbcc",
          "role": "assistant",
          "content": "It is completely understandable to feel overwhelmed when thinking about the future...",
          "creation_date": "2026-05-21T19:10:00Z",
          "emotional_state": null,
          "safety_flag": null
        }
      ]
    }
    ```

### 5.4 Delete Chat Session
*   **Method**: `DELETE`
*   **Path**: `/api/v1/chats/<uuid:chat_id>/`
*   **Access**: `IsAuthenticated`
*   **Success Response (`204 No Content`)**: Completely deletes the conversation session, purging its active messages and historical summaries from the database.

### 5.5 Send Message to AI Agent (Main Product Core)
*   **Method**: `POST`
*   **Path**: `/api/v1/chats/<uuid:chat_id>/message/`
*   **Access**: `IsAuthenticated`
*   **Request Body (`application/json`)**:
    ```json
    {
      "content": "I am feeling extremely lonely today.",
      "model": "2"
    }
    ```
    *   `content`: The textual prompt from the user (string, maximum 1000 characters).
    *   `model`: The preferred Ollama model tier (optional choice).
        *   `"1"`: Groq Thinking Model (`openai/gpt-oss-120b`) - higher quality, slower reasoning.
        *   `"2"` (Default): Gemma-4 Fast Model (`gemma4:e2b`) - speedy response times.
*   **Success Response (`200 OK`)**:
    ```json
    {
      "reply": "I hear you, and I am here with you. Loneliness can be such a heavy weight to carry..."
    }
    ```
    *Note: The user's input message and the assistant's processed response are both automatically persisted in the PostgreSQL database before the API responds.*
