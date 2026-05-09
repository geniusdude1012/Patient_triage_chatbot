# 🏥 Patient Triage Chatbot

An AI-powered hospital triage assistant that helps patients find the right care quickly. Patients describe their symptoms in natural language (typed or spoken), and the system classifies urgency, matches the appropriate department, and guides them with clear action steps.

---

## Approach

The system combines **rule-based emergency detection** with **LLM-powered conversation** to triage patients effectively:

1. **Symptom Extraction** — GPT-3.5 extracts standardized medical symptoms from any natural language input, handling slang, informal phrasing, and voice transcription.

2. **Emergency Classification** — Extracted symptoms are embedded using OpenAI Embeddings and compared via cosine similarity against a curated emergency keyword database (`emergency.json`). Symptoms are classified into three priority levels: **Emergency**, **Urgent**, or **Routine**.

3. **Department Matching** — The same embeddings are compared against department examples in `department_info.json` to route the patient to the correct hospital department. An LLM fallback handles cases where no close match is found.

4. **Conversational Triage** — For non-emergency cases, a LangChain conversation chain asks 2–3 smart follow-up questions (duration, severity, related symptoms) before giving a final recommendation.

5. **Voice Support** — Patients can speak their symptoms using the built-in mic recorder. Audio is transcribed via OpenAI Whisper and fed into the same pipeline as typed input.

6. **Session History** — Each patient session (identified by name + UUID) is saved as a JSON file on session end, recording the full conversation, symptoms collected, and final priority.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  FRONTEND (Streamlit)                │
│                                                      │
│  welcome_page.py   →   app.py   →   chat_ui.py      │
│  (name input)          (main UI)    (message render) │
│                          │                           │
│                   api_client.py                      │
│              (HTTP calls via httpx)                  │
└──────────────────────────┬──────────────────────────┘
                           │ HTTP POST /api/chat
                           ▼
┌─────────────────────────────────────────────────────┐
│                   API LAYER (FastAPI)                │
│                                                      │
│   app.py → routes/chat.py → routes/session.py       │
│              │                    │                  │
│         session_store.py    history_writer.py        │
│         (per-user memory)   (saves JSON on end)      │
└──────────────────────────┬──────────────────────────┘
                           │ calls
                           ▼
┌─────────────────────────────────────────────────────┐
│                 AI SERVICES (Backend)                │
│                                                      │
│            triage_engine.py (orchestrator)           │
│           ┌──────────────┬───────────────┐           │
│  symptom_extractor  emergency_classifier  dept_matcher│
│  (GPT-3.5 extract)  (embeddings + cosine) (embeddings)│
│           └──────────────┴───────────────┘           │
│      conversation_service     department_fallback    │
│      (LangChain chain)        (LLM dept suggestion)  │
└─────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────┐
│              KNOWLEDGE BASE (JSON files)             │
│                                                      │
│  emergency.json          department_info.json        │
│  (critical / urgent /    (dept examples,             │
│   routine keywords)       recommendations)           │
│                                                      │
│  system_prompt.txt                                   │
│  (LLM personality + rules)                           │
└─────────────────────────────────────────────────────┘
```

---

## Project Structure

```
Patient_triage_chatbot/
│
├── Frontend/
│   ├── app.py                        # Main Streamlit UI entry point
│   ├── api_client.py                 # All HTTP calls to FastAPI
│   └── components/
│       ├── welcome_page.py           # Name input landing page
│       ├── chat_ui.py                # Message bubble rendering
│       └── voice_input.py            # Mic recorder + Whisper transcription
│
├── Backend/
│   ├── api/
│   │   ├── app.py                    # FastAPI app + CORS + router setup
│   │   ├── schemas.py                # Pydantic request/response models
│   │   ├── session_store.py          # In-memory per-user session storage
│   │   └── routes/
│   │       ├── chat.py               # POST /api/chat endpoint
│   │       └── session.py            # POST /api/session/start and /end
│   │
│   ├── chains/
│   │   └── conversational_chain.py   # LangChain chain definition
│   │
│   ├── config/
│   │   └── loaders.py                # Loads all JSON + system prompt
│   │
│   ├── models/
│   │   ├── llm_models.py             # LLM + embeddings model instances
│   │   └── prompts.py                # All prompt templates
│   │
│   ├── services/
│   │   ├── triage_engine.py          # Master pipeline orchestrator
│   │   ├── symptom_extractor.py      # LLM symptom extraction
│   │   ├── emergency_classifier.py   # Cosine similarity classification
│   │   ├── department_matcher.py     # Department semantic matching
│   │   ├── department_fallback.py    # LLM department suggestion fallback
│   │   └── conversation_service.py   # LangChain conversational triage
│   │
│   ├── utils/
│   │   ├── formatters.py             # Markdown response formatting
│   │   ├── state_manager.py          # Global chat history + symptoms
│   │   └── history_writer.py         # Saves session to JSON file
│   │
│   └── knowledgebase/
│       ├── emergency.json            # Emergency / urgent / routine keywords
│       └── department_info.json      # Department examples + recommendations
│
├── sessions/                         # Auto-created — saved session JSON files
├── system_prompt.txt                 # LLM personality and triage rules
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### Prerequisites

- Python 3.10+
- An OpenAI API key

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd Patient_triage_chatbot
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-your-openai-key-here
```

### 5. Run the FastAPI backend

```bash
# From the project root
uvicorn Backend.api.app:app --reload
```

API will be available at `http://localhost:8000`

### 6. Run the Streamlit frontend

Open a second terminal:

```bash
# From the project root
streamlit run Frontend/app.py
```

App will open at `http://localhost:8501`

### 7. Using the chatbot

1. Enter your name on the welcome page and click **Start Consultation**
2. Describe your symptoms by typing or using the mic button
3. Answer the follow-up questions from the assistant
4. Receive urgency level, department routing, and recommended action
5. Click **End Session** to save your session history

---

## Requirements

```
langchain
langchain-core
langchain-openai
langchain-community
openai
fastapi
uvicorn[standard]
streamlit
httpx
numpy
scikit-learn
python-dotenv
pydantic
```

---

## Assumptions Made

- **Single hospital context** — the system is designed for one hospital with departments defined in `department_info.json`. Adding or removing departments only requires editing that file.

- **English language primary** — the LLM extraction handles informal English well. Other languages may work via GPT-3.5 but are not explicitly tested.

- **In-memory session storage** — sessions are stored in a Python dict during the conversation. If the FastAPI server restarts mid-session, history is lost. For production, replace with Redis.

- **Threshold-based matching** — emergency classification uses a cosine similarity threshold of 0.92 and department matching uses 0.88. These values were tuned for the current knowledge base and may need adjustment if the JSON files are significantly expanded.

- **No authentication** — the system has no login or patient identity verification. The username entered on the welcome page is used only for session labeling and history file naming.

- **Session history is local** — completed sessions are saved as JSON files in the `sessions/` folder. There is no database integration — this is designed as a starting point for connecting to a database later.

- **Voice input requires internet** — voice transcription uses the OpenAI Whisper API, which requires an active internet connection and consumes API credits.

- **Not a medical diagnosis tool** — this system is designed for initial triage routing only. All responses include a disclaimer that this is AI-assisted triage and not a medical diagnosis.

---

## Author

**Saujanya Shrestha**
Computer Engineer | AI Engineer | QA Automation Engineer
[GitHub](https://github.com/geniusdude1012) • [LinkedIn](https://www.linkedin.com/in/saujanya-shrestha-9551a4291/)
