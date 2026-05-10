from langchain_core.messages import HumanMessage, AIMessage
from Backend.chains.conversational_chain import chain
from Backend.utils.state_manager import chat_history


def chat(user_input: str, department: dict | None = None) -> str:
    # Always inject dept context if we have it — not just first time
    if department:
        enriched_input = (
            f"{user_input}\n\n"
            f"[Context — do not show to patient]\n"
            f"Best matching department: {department['department']}\n"
            f"Handles: {department.get('handles', '')}\n"
            f"Available: {department.get('available', '')}\n"
            f"Recommendation: {department.get('recommendation', '')}\n"
            f"If the patient asks which department, tell them: {department['department']}"
        )
    else:
        enriched_input = user_input

    response = chain.invoke({
        "chat_history": chat_history,
        "input": enriched_input
    })

    chat_history.append(HumanMessage(content=user_input))
    chat_history.append(AIMessage(content=response))
    return response