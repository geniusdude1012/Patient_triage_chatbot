from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder
)
from langchain_core.messages import SystemMessage
from config.loaders import load_system_prompt

system_prompt = load_system_prompt("system_prompt.txt")

# ── 1. Conversation prompt (your existing one — unchanged) ────────────────────
conversation_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])


# ── 2. Symptom extraction prompt ──────────────────────────────────────────────
def build_symptom_extraction_prompt(user_input: str) -> str:
    return f"""
Patient said: "{user_input}"

Extract all medical symptoms mentioned. Keep descriptive qualifiers like mild, severe, sudden.

Rules:
- Return ONLY a comma separated list of symptom phrases
- Keep qualifiers: "mild fever" not "fever", "severe headache" not "headache"
- No explanations, no bullet points, no extra words
- If no symptom found, return exactly: none

Examples:
Input:  "i have mild fever and im sweating"
Output: mild fever, sweating

Input:  "bad chest pain and cant breathe"
Output: chest pain, can't breathe

Input:  "slight cough and runny nose"
Output: slight cough, runny nose

Input:  "{user_input}"
Output:"""


# ── 3. Department fallback prompt ─────────────────────────────────────────────
def build_department_fallback_prompt(symptoms: list, priority: str) -> str:
    urgency_map = {
        "emergency": "Emergency",
        "urgent":    "Urgent",
        "routine":   "Routine",
        "low":       "Routine"
    }
    urgency_label = urgency_map.get(priority, "Routine")
    symptoms_str  = ", ".join(symptoms)

    return f"""
A hospital patient has the following symptoms: {symptoms_str}
Assessed urgency level: {urgency_label}

Suggest the most appropriate hospital department for this patient.
Respond ONLY in this exact JSON format — no markdown, no explanation:

{{
  "department": "Department Name",
  "handles": "One line describing what this department handles",
  "available": "Typical availability e.g. 9AM - 5PM or 24/7",
  "recommendation": "Clear, simple action instruction for the patient"
}}
"""