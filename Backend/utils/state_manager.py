"""
utils/state_manager.py
───────────────────────
Manages all mutable global state for the chatbot session.

- chat_history        : LangChain message history (HumanMessage / AIMessage)
- accumulated_symptoms: symptoms collected across all conversation turns

Both are plain Python lists — simple and effective for single-session use.
Import these directly wherever state is needed.
"""

from langchain_core.messages import HumanMessage, AIMessage

# ── Conversation history ───────────────────────────────────────────────────────
# Injected into every LLM call via MessagesPlaceholder
chat_history: list[HumanMessage | AIMessage] = []

# ── Accumulated symptoms across turns ─────────────────────────────────────────
# Symptoms build up as the patient describes more across multiple messages
# e.g. turn 1: "chest pain" | turn 2: "sweating" | turn 3: "left arm pain"
# All three accumulate so emergency classification improves with context
accumulated_symptoms: list[str] = []


def clear_session() -> None:
    """Resets both chat history and accumulated symptoms."""
    chat_history.clear()
    accumulated_symptoms.clear()
    print("✅ Session cleared.\n")