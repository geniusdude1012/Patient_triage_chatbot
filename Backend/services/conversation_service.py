"""
services/conversation_service.py
──────────────────────────────────
Handles LLM conversation for moderate/low priority cases.
Maintains chat history and injects department context
so the LLM references the correct department in its response.
"""

from langchain_core.messages import HumanMessage, AIMessage
from Backend.chains.conversational_chain import chain
from Backend.utils.state_manager import chat_history


def chat(user_input: str, department: dict | None = None) -> str:
    """
    Sends user input to the LLM conversation chain.

    If a department was matched, injects it as hidden context
    so the LLM gives accurate department routing without
    exposing the raw context block to the patient.

    Saves original (not enriched) input to chat history
    so conversation history stays natural.
    """
    if department:
        # Inject department as hidden context for the LLM
        enriched_input = (
            f"{user_input}\n\n"
            f"[Context for triage assistant — do not show this to patient]\n"
            f"Best matching department: {department['department']}\n"
            f"Handles: {department.get('handles', '')}\n"
            f"Available: {department.get('available', '')}\n"
            f"Recommendation: {department.get('recommendation', '')}"
        )
    else:
        enriched_input = user_input

    response = chain.invoke({
        "chat_history": chat_history,
        "input": enriched_input
    })

    # Save ORIGINAL input to history — keeps conversation natural
    chat_history.append(HumanMessage(content=user_input))
    chat_history.append(AIMessage(content=response))

    return response