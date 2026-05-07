from langchain_openai import ChatOpenAI,OpenAIEmbeddings
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
import json

load_dotenv()

# ── Embeddings model ───────────────────────────────────────
embeddings_model = OpenAIEmbeddings()

# ── Load emergency.json only (normalizer removed) ─────────────────────────────
def load_json(filepath: str) -> dict:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

emergency_cfg     = load_json("Backend/knowledgebase/emergency.json")
CRITICAL_KEYWORDS = emergency_cfg["critical"]
URGENT_KEYWORDS   = emergency_cfg["high_priority"]
MODERATE_KEYWORDS = emergency_cfg["moderate"]
print("✅ Emergency keywords loaded")

# ── Load system prompt ─────────────────────────────────────────────────────────
def load_system_prompt(filepath: str = "system_prompt.txt") -> str:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"System prompt file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read().strip()

system_prompt = load_system_prompt("system_prompt.txt")
print("✅ System prompt loaded\n")

# ── Two separate models ────────────────────────────────────────────────────────
# Extractor — low temperature, we want precise consistent output
extractor_llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.4        # strict, no creativity for extraction
)

# Conversation — slightly higher temperature for natural responses
chat_llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7
)

# ── Conversation prompt + chain ────────────────────────────────────────────────
prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

chain = prompt | chat_llm | StrOutputParser()

# ── Conversation memory ────────────────────────────────────────────────────────
chat_history = []


# ── Pre-embed all keywords from emergency.json at startup ──
def embed_keywords(keywords: list[str]):
    return np.array(embeddings_model.embed_documents(keywords))

CRITICAL_EMBEDDINGS  = embed_keywords(CRITICAL_KEYWORDS)
URGENT_EMBEDDINGS    = embed_keywords(URGENT_KEYWORDS)
MODERATE_EMBEDDINGS  = embed_keywords(MODERATE_KEYWORDS)
print("✅ Keyword embeddings created")


# ── Step 1: Extract symptoms ───────────────────────────────
def extract_symptoms(user_input: str) -> list[str]:
    extraction_prompt = f"""
Patient said: "{user_input}"
Extract medical symptoms. Return comma separated list only.
Remove severity words like mild, severe, slight.
If none found return: none
"""
    response = extractor_llm.invoke(extraction_prompt)
    raw = response.content.lower().strip()
    if raw == "none":
        return []
    return [s.strip() for s in raw.split(",") if s.strip()]


# ── Step 2: Categorize using similarity ───────────────────
SIMILARITY_THRESHOLD = 0.92  # tune this (0.80-0.90 recommended)

def categorize(symptoms: list[str]) -> dict:
    result = {
        "critical":      [],
        "high_priority": [],
        "moderate":      [],
        "unknown":       []
    }

    if not symptoms:
        return result

    # Embed all extracted symptoms in one batch
    symptom_embeddings = np.array(
        embeddings_model.embed_documents(symptoms)
    )

    for i, symptom in enumerate(symptoms):
        s_vec = symptom_embeddings[i].reshape(1, -1)

        # Check critical
        scores = cosine_similarity(s_vec, CRITICAL_EMBEDDINGS)[0]
        if scores.max() >= SIMILARITY_THRESHOLD:
            matched = CRITICAL_KEYWORDS[scores.argmax()]
            print(f"   [Similarity] '{symptom}' → '{matched}' "
                  f"({scores.max():.2f}) CRITICAL")
            result["critical"].append(matched)
            continue

        # Check high_priority
        scores = cosine_similarity(s_vec, URGENT_EMBEDDINGS)[0]
        if scores.max() >= SIMILARITY_THRESHOLD:
            matched = URGENT_KEYWORDS[scores.argmax()]
            print(f"   [Similarity] '{symptom}' → '{matched}' "
                  f"({scores.max():.2f}) URGENT")
            result["high_priority"].append(matched)
            continue

        # Check moderate
        scores = cosine_similarity(s_vec, MODERATE_EMBEDDINGS)[0]
        if scores.max() >= SIMILARITY_THRESHOLD:
            matched = MODERATE_KEYWORDS[scores.argmax()]
            print(f"   [Similarity] '{symptom}' → '{matched}' "
                  f"({scores.max():.2f}) MODERATE")
            result["moderate"].append(matched)
            continue

        # No match found
        print(f"   [Similarity] '{symptom}' → no match")
        result["unknown"].append(symptom)

    return result


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Get highest priority level
# ══════════════════════════════════════════════════════════════════════════════
def get_priority(categorized: dict) -> str:
    """
    Returns the single highest priority level found.
    Critical > High > Moderate > Low
    """
    if categorized["critical"]:
        return "critical"
    elif categorized["high_priority"]:
        return "high_priority"
    elif categorized["moderate"]:
        return "moderate"
    return "low"


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Build instant response for critical and high priority
# ══════════════════════════════════════════════════════════════════════════════
def get_priority_response(priority: str, categorized: dict) -> str | None:
    """
    Returns formatted instant response for critical/high_priority.
    Returns None for moderate/low so LLM handles those conversationally.
    """
    if priority == "critical":
        found = ", ".join(categorized["critical"])
        return (
            "\n🔴 EMERGENCY DETECTED\n"
            "─────────────────────────────────────\n"
            f"Detected:   {found}\n"
            "Urgency:    CRITICAL\n"
            "Department: Emergency / Immediate Care\n"
            "Action:     Call emergency services NOW\n"
            "            or go to the ER immediately.\n"
            "─────────────────────────────────────\n"
            "⚠️ This is AI-assisted triage, not a medical diagnosis.\n"
        )

    if priority == "high_priority":
        found = ", ".join(categorized["high_priority"])
        return (
            "\n🟠 URGENT — SAME DAY CARE NEEDED\n"
            "─────────────────────────────────────\n"
            f"Detected:   {found}\n"
            "Urgency:    HIGH\n"
            "Department: Urgent Care / Emergency Room\n"
            "Action:     Seek medical attention today.\n"
            "            Do not wait — visit urgent care now.\n"
            "─────────────────────────────────────\n"
            "⚠️ This is AI-assisted triage, not a medical diagnosis.\n"
        )

    return None  # moderate/low → LLM handles conversationally


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — LLM conversation for non-emergency cases
# ══════════════════════════════════════════════════════════════════════════════
def chat(user_input: str) -> str:
    """
    Sends original user input to LLM with full conversation history.
    LLM asks follow-up questions and gives final triage result.
    Original input used (not extracted) so conversation feels natural.
    """
    response = chain.invoke({
        "chat_history": chat_history,
        "input": user_input
    })
    # Save to history AFTER response
    chat_history.append(HumanMessage(content=user_input))
    chat_history.append(AIMessage(content=response))
    return response


# ══════════════════════════════════════════════════════════════════════════════
# MASTER PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
def process(user_input: str) -> str:
    """
    Full pipeline:

    1. LLM extracts all symptoms from any natural language input
       → Works for slang, informal, multilingual (no JSON normalizer needed)

    2. Extracted symptoms compared against emergency.json
       → critical / high_priority / moderate

    3. Critical or High → instant structured response, skip LLM chat

    4. Moderate / Low / Unknown → LLM asks follow-ups and gives triage
    """

    # ── Step 1: LLM extracts symptoms ─────────────────────────────────────────
    symptoms = extract_symptoms(user_input)
    print(f"   [Extracted]  {symptoms if symptoms else 'none detected'}")

    # ── Step 2: Categorize against emergency.json ──────────────────────────────
    categorized = categorize(symptoms)
    print(
        f"   [Matched]    "
        f"critical={categorized['critical']} | "
        f"urgent={categorized['high_priority']} | "
        f"moderate={categorized['moderate']} | "
        f"unknown={categorized['unknown']}"
    )

    # ── Step 3: Get priority ───────────────────────────────────────────────────
    priority = get_priority(categorized)
    print(f"   [Priority]   {priority.upper()}")

    # ── Step 4: Instant response for critical/high ─────────────────────────────
    instant = get_priority_response(priority, categorized)
    if instant:
        return instant

    # ── Step 5: LLM handles everything else ───────────────────────────────────
    print(f"   [Routing]    LLM conversation")
    return chat(user_input)


# ── Utilities ──────────────────────────────────────────────────────────────────
def clear_history():
    chat_history.clear()
    print("✅ Conversation cleared.\n")

def reload_prompt():
    global prompt, chain, system_prompt
    system_prompt = load_system_prompt("system_prompt.txt")
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ])
    chain = prompt | chat_llm | StrOutputParser()
    print("✅ System prompt reloaded!\n")


# ── Main loop ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("        Patient Triage Chatbot")
    print("  'quit'   → exit")
    print("  'clear'  → reset conversation")
    print("  'reload' → reload system_prompt.txt")
    print("=" * 50 + "\n")
    print("Welcome! I am a patient triage assistant.")
    print("How can I assist you today?\n")

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue
        elif user_input.lower() == "quit":
            print("Goodbye! Stay safe.")
            break
        elif user_input.lower() == "clear":
            clear_history()
        elif user_input.lower() == "reload":
            reload_prompt()
        else:
            response = process(user_input)
            print(f"\nBot: {response}\n")