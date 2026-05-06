from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os
import json

load_dotenv()

# ── Load JSON files ────────────────────────────────────────────────────────────
def load_json(filepath: str) -> dict:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

normalizer    = load_json("Backend/knowledgebase/symptoms_normalizer.json")
emergency_cfg = load_json("Backend/knowledgebase/emergency.json")
EMERGENCY_KEYWORDS = emergency_cfg["critical"]

print("✅ Normalizer loaded")
print("✅ Emergency keywords loaded")

# ── Load system prompt ─────────────────────────────────────────────────────────
def load_system_prompt(filepath: str = "system_prompt.txt") -> str:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"System prompt file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read().strip()

system_prompt = load_system_prompt("system_prompt.txt")
print("✅ System prompt loaded\n")

# ── Model ──────────────────────────────────────────────────────────────────────
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

# ── Prompt ─────────────────────────────────────────────────────────────────────
prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

# ── Chain ──────────────────────────────────────────────────────────────────────
chain = prompt | llm | StrOutputParser()

# ── Conversation memory ────────────────────────────────────────────────────────
chat_history = []


# ── Step 1: Normalize ──────────────────────────────────────────────────────────
def normalize(user_input: str) -> str:
    """
    Replaces informal symptom words with standard medical terms.
    Example: 'tummy ache' → 'abdominal pain'
    """
    text = user_input.lower().strip()
    for informal, standard in normalizer.items():
        if informal in text:
            text = text.replace(informal, standard)
            print(f"   [Normalizer] '{informal}' → '{standard}'")
    return text


# ── Step 2: Emergency check ────────────────────────────────────────────────────
def check_emergency(normalized_text: str) -> bool:
    """
    Scans normalized input for critical emergency keywords.
    Returns True if any critical keyword is found.
    """
    for keyword in EMERGENCY_KEYWORDS:
        if keyword in normalized_text:
            print(f"   [Emergency] Keyword detected: '{keyword}'")
            return True
    return False


def get_emergency_response() -> str:
    return (
        "\nEMERGENCY DETECTED\n"
        "─────────────────────────────\n"
        "Urgency:    Emergency\n"
        "Department: Emergency / Immediate Care\n"
        "Action:     Please go to the emergency department\n"
        "            immediately or call emergency services now.\n"
        "─────────────────────────────\n"
        "This is AI-assisted triage and not a medical diagnosis.\n"
    )


# ── Step 3: LLM chat ───────────────────────────────────────────────────────────
def chat(user_input: str) -> str:
    """
    Sends normalized input to LLM with full conversation history.
    """
    response = chain.invoke({
        "chat_history": chat_history,
        "input": user_input
    })
    # Save to history AFTER getting response
    chat_history.append(HumanMessage(content=user_input))
    chat_history.append(AIMessage(content=response))
    return response


# ── Master pipeline ────────────────────────────────────────────────────────────
def process(user_input: str) -> str:
    """
    Full pipeline:
    1. Normalize input
    2. Check emergency → instant response if critical
    3. Send to LLM if not emergency
    """
    # Step 1 — Normalize
    normalized = normalize(user_input)

    # Step 2 — Emergency check
    if check_emergency(normalized):
        return get_emergency_response()

    # Step 3 — LLM handles it
    return chat(normalized)


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
    chain = prompt | llm | StrOutputParser()
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
            response = process(user_input)   # ← only change in main loop
            print(f"\nBot: {response}\n")