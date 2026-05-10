
import os
import json

# ── Project root (two levels up from this file) 
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_json(filepath: str) -> dict:
    """Load a JSON file. filepath is relative to project root."""
    full_path = os.path.join(ROOT_DIR, filepath)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"JSON file not found: {full_path}")
    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_system_prompt(filepath: str = "system_prompt.txt") -> str:
    """Load system prompt text file. filepath is relative to project root."""
    full_path = os.path.join(ROOT_DIR, filepath)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"System prompt not found: {full_path}")
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read().strip()


# ── Load all knowledge base files at import time 
emergency_cfg   = load_json("Backend/knowledgebase/emergency.json")
department_cfg  = load_json("Backend/knowledgebase/department_info.json")
system_prompt   = load_system_prompt("system_prompt.txt")

# ── Emergency keyword lists 
EMERGENCY_KEYWORDS = emergency_cfg["emergency"]
URGENT_KEYWORDS    = emergency_cfg["urgent"]
MODERATE_KEYWORDS  = emergency_cfg["routine"]

print("✅ Emergency keywords loaded")
print("✅ Department info loaded")
print("✅ System prompt loaded")