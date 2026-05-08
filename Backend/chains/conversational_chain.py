"""
chains/conversational_chain.py
────────────────────────────────
Builds and exports the main LangChain conversation chain.

Chain structure:
    prompt → chat_llm → StrOutputParser

Also exports rebuild_chain() so reload_prompt() in main.py
can hot-swap the system prompt without restarting.
"""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from Backend.config.loaders import system_prompt, load_system_prompt
from Backend.models.llm_models import chat_llm


def _build_prompt(prompt_text: str) -> ChatPromptTemplate:
    """Builds a fresh ChatPromptTemplate from a system prompt string."""
    return ChatPromptTemplate.from_messages([
        SystemMessage(content=prompt_text),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ])


# ── Build the chain at startup ────────────────────────────────────────────────
_prompt = _build_prompt(system_prompt)   # ← use the loaded string directly
chain   = _prompt | chat_llm | StrOutputParser()


def rebuild_chain(new_system_prompt: str):
    """
    Rebuilds the chain with a new system prompt.
    Called by reload_prompt() in main.py after editing system_prompt.txt.
    """
    global _prompt, chain
    _prompt = _build_prompt(new_system_prompt)
    chain   = _prompt | chat_llm | StrOutputParser()
    return chain