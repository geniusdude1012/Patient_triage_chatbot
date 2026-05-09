"""
services/department_matcher.py
────────────────────────────────
Matches extracted symptoms against department_info.json
using OpenAI embeddings + cosine similarity.

Returns the best matching department or None if no match found.
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from Backend.config.loaders import department_cfg
from Backend.models.llm_models import embeddings_model

# ── Similarity threshold ───────────────────────────────────────────────────────
# Lower than emergency threshold — departments are broader matches
DEPT_THRESHOLD = 0.88
# ── Pre-embed all department examples at startup ───────────────────────────────
print("   Embedding department keywords...", end=" ")

DEPARTMENT_DATA: dict = {}
for dept_name, dept_info in department_cfg.items():
    examples = dept_info.get("examples", [])
    if examples:
        DEPARTMENT_DATA[dept_name] = {
            "embeddings":     np.array(embeddings_model.embed_documents(examples)),
            "examples":       examples,
            "handles":        dept_info.get("handles", ""),
            "available":      dept_info.get("available", ""),
            "recommendation": dept_info.get("recommendation", "")
        }

print("✅ Department embeddings created")


def match_department(symptoms: list[str]) -> dict | None:
    """
    Finds the best matching department for the given symptoms.

    Matching logic:
    - Embeds each extracted symptom
    - Compares against all department example embeddings
    - Returns the department with the highest single similarity score

    Returns:
        {
            "department":      str,
            "handles":         str,
            "available":       str,
            "recommendation":  str,
            "matched_symptom": str,
            "score":           float,
            "source":          "json"
        }
        or None if no department scores above threshold.
    """
    if not symptoms:
        return None

    symptom_embeddings = np.array(embeddings_model.embed_documents(symptoms))

    best_dept    = None
    best_name    = None
    best_score   = 0.0
    best_symptom = None

    for dept_name, dept_info in DEPARTMENT_DATA.items():
        dept_embeddings = dept_info["embeddings"]

        for i, symptom in enumerate(symptoms):
            s_vec     = symptom_embeddings[i].reshape(1, -1)
            scores    = cosine_similarity(s_vec, dept_embeddings)[0]
            max_score = scores.max()

            if max_score >= DEPT_THRESHOLD and max_score > best_score:
                best_score   = max_score
                best_name    = dept_name
                best_dept    = dept_info
                best_symptom = symptom
                print(f"   [Dept Match] '{symptom}' → '{dept_name}' ({max_score:.2f})")

    if best_name:
        return {
            "department":      best_name,
            "handles":         best_dept["handles"],
            "available":       best_dept["available"],
            "recommendation":  best_dept["recommendation"],
            "matched_symptom": best_symptom,
            "score":           best_score,
            "source":          "json"
        }

    print("   [Dept Match] No department matched above threshold")
    return None