# Aman — Frontend UI/UX Design Specification

## 1. Project Context & Requirements
- **Goal:** Provide a safe, empathetic, and factually grounded bilingual (Arabic/English) space for users experiencing emotional distress.
- **Vibe & Tone:** Warm, calming, non-judgmental, modern, and highly responsive.
- **Current Backend Capabilities:** Django + Django REST Framework handling authentication (JWT), chat history storage, and streaming LLM responses via a LangGraph AI engine.
- **Design Intent:** The UI should follow a modern, Gemini-inspired design language. It must accommodate planned features like voice input (mic) and text-to-speech, even if they are stubbed out for now.

## 2. Frameworks & Tools
To achieve the best UI/UX experience and match the dynamic nature of the designs, a modern Single Page Application (SPA) architecture is recommended:

- **Core Stack:** **React** (Frontend SPA) + **Django** (Backend API).
- **Build Tool:** **Vite** for fast, modern React development.
- **Styling:** **Vanilla CSS** with modern features (CSS variables, flexbox/grid) or **Tailwind CSS**. Key visual effects rely heavily on `backdrop-filter` for glassmorphism and animated CSS gradients.
- **State Management:** **React Context** or **Zustand** for lightweight global state (managing active chat, user profile, and JWT auth tokens).
- **Routing:** **React Router DOM** for client-side routing between Login and Dashboard/Chat views without full page reloads, ensuring smooth transitions.
- **API Communication:** **Axios** or native `fetch` for REST API calls. Crucially, the frontend must handle **Server-Sent Events (SSE)** or readable streams for the real-time streamed LLM responses coming from the `/api/v1/chats/<uuid>/message/` endpoint.

## 3. UI Design Language (Gemini-Inspired)
- **Colors:** Soft, fluid pastel gradients (purples, calming blues, warm oranges) against a clean light or deep dark background.
- **Typography:** Modern, legible sans-serif (e.g., Inter, Roboto, or Google Sans).
- **Shapes:** Generous border-radiuses. Pill-shaped input fields and buttons (fully rounded ends), and softly rounded rectangles for modals and message bubbles.
- **Interactions:** Glassmorphic overlays (blurring the background), smooth fade-ins, and subtle glowing animations when the AI is "thinking" or processing emotions.

## 4. Pages & Layout Descriptions

### 4.1 Authentication (Login / Register) Page
*   **Desktop Layout (Split-Screen):**
    *   **Left Side:** A soft, glowing, fluid pastel gradient background. A frosted glass (glassmorphism) panel sits in the center displaying the Aman logo and a welcoming tagline ("Welcome to Aman. Find your emotional balance...").
    *   **Right Side:** A minimalist, solid-color area containing the authentication form. It features pill-shaped input fields (Email, Password), a vibrant glowing "Continue" pill button, and secondary options for OAuth (Google, Apple).
*   **Mobile Layout (Single-Column):**
    *   The glowing gradient serves as a top header graphic. The clean login/signup form sits centrally below it, maximizing vertical space for easy touch interaction.

### 4.2 Main Dashboard & New Chat (Empty State)
*   **Desktop Layout:**
    *   **Sidebar (Left):** A clean pane featuring the Aman logo, a prominent pill-shaped "New Chat +" button, and a grouped list of past conversations (Today, Yesterday, This Week). At the bottom, a settings gear icon and the user's avatar.
    *   **Main Area:** A large, welcoming screen with a beautiful gradient background. It features a large, centered greeting: *"How are you feeling today?"* Below this are horizontally arranged, rounded suggestion chips ("I'm feeling anxious", "Let's talk about stress").
    *   **Model Selection:** Located at the top right or top center of the main area, a sleek dropdown or toggle allowing the user to select the AI model tier (e.g., "Gemma-4 Fast" vs "Gemma-4 Thinking" as defined in the backend API).
    *   **Input Bar:** Anchored at the bottom center. A floating, pill-shaped input field with icons for a microphone, attachments, and a glowing submit arrow.
*   **Mobile Layout:**
    *   The sidebar is accessible via a top-left hamburger menu. The main screen focuses entirely on the central greeting, suggestion chips, and the floating input bar docked to the bottom. The model selector is accessible via a subtle top-bar dropdown.

### 4.3 Active Chat Room Interface
*   **Desktop Layout:**
    *   **Sidebar:** Remains visible for easy navigation between chats.
    *   **Chat Flow:** The conversation replaces the empty state greeting. User messages are right-aligned inside soft, solid-color pill bubbles. Aman's responses are left-aligned or take up a wider central block without a restricting bubble, featuring the Aman avatar icon next to the text.
    *   **AI Status:** When Aman is generating text or processing ("thinking..."), a subtle glowing gradient animation plays around the avatar or text block.
    *   **Top Bar:** The model selection dropdown remains visible at the top.
    *   **Input Bar:** The same floating pill-shaped input bar remains at the bottom.
*   **Mobile Layout:**
    *   Full-screen conversational flow. The input bar at the bottom expands smoothly as the user types. The chat bubbles are optimized for readability with generous padding.

### 4.4 User Profile & Settings Modal
*   **Desktop & Mobile Layout:**
    *   Instead of navigating to a new page, clicking the settings gear/avatar opens a sleek, glassmorphic modal overlaying the current screen (blurring the dashboard/chat behind it).
    *   **Tabs:** Divided into logical sections like `[Account Details]`, `[Preferences]`, and `[Security]`.
    *   **Content (Preferences):** Features large, smooth toggle switches for App Theme (Light Mode / Dark Mode) and Notification Alerts. Dropdowns are available for Language selection (Arabic/English).
    *   **Actions:** A vibrant "Save Changes" pill button and a subtle "Cancel" button.

## 5. Notes on Implementation vs. Design
- **Future Features (Mic / Attachments):** The microphone and attachment icons are present in the design for future-proofing. However, backend support for voice input (STT) and file uploads are currently marked as `[PLANNED]`. These buttons should be visually present but either disabled or trigger a "Coming Soon" toast message when clicked.
- **Model Selection Implementation:** The backend explicitly supports a `model` parameter (`"1"` for thinking, `"2"` for fast). The UI must dynamically pass this selection in the payload to the `/api/v1/chats/<uuid>/message/` endpoint.
- **SPA vs Django Templates:** The backend currently serves separate HTML templates for different routes (`/login/`, `/settings/`, `/dashboard/`). For the best UX, these should be replaced or bypassed. The React frontend should be built as a single bundle (SPA) that exclusively consumes the REST APIs (`/api/v1/...`), taking over all routing responsibilities.
