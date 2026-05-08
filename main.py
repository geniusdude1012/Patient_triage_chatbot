"""
main.py
────────
Entry point for the Patient Triage Chatbot.

Responsibilities:
- Start the chatbot session
- Handle user commands (quit / clear / reload)
- Call triage_engine.process() for every patient message

All business logic lives in Backend/services/.
This file stays clean — it only handles I/O.
"""

from dotenv import load_dotenv
load_dotenv()

from Backend.services.triage_engine        import process
from Backend.utils.state_manager           import clear_session
from Backend.config.loaders                import load_system_prompt
from Backend.chains.conversational_chain   import rebuild_chain


def reload_prompt() -> None:
    """Hot-reload system_prompt.txt without restarting."""
    new_prompt = load_system_prompt("system_prompt.txt")
    rebuild_chain(new_prompt)
    print("✅ System prompt reloaded!\n")


def main() -> None:
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
            clear_session()

        elif user_input.lower() == "reload":
            reload_prompt()

        else:
            response = process(user_input)
            print(f"\nBot: {response}\n")


if __name__ == "__main__":
    main()