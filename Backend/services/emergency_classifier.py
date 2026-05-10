
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from Backend.config.loaders import EMERGENCY_KEYWORDS, URGENT_KEYWORDS, MODERATE_KEYWORDS
from Backend.models.llm_models import embeddings_model

# ── Similarity threshold ───────────────────────────────────────────────────────
# 0.92 = strict — only genuine matches pass
THRESHOLD = 0.92

# ── Pre-embed all keywords once at startup ────────────────────────────────────
print("   Embedding emergency keywords...", end=" ")
EMERGENCY_EMBEDDINGS = np.array(embeddings_model.embed_documents(EMERGENCY_KEYWORDS))
URGENT_EMBEDDINGS    = np.array(embeddings_model.embed_documents(URGENT_KEYWORDS))
MODERATE_EMBEDDINGS  = np.array(embeddings_model.embed_documents(MODERATE_KEYWORDS))
print("✅ Emergency keyword embeddings created")


def categorize(symptoms: list[str]) -> dict:
    """
    Compares each extracted symptom against all 3 priority lists
    using cosine similarity on OpenAI embeddings.

    Returns:
        {
            "emergency": [...],
            "urgent":    [...],
            "routine":   [...],
            "unknown":   [...]
        }
    """
    result = {
        "emergency": [],
        "urgent":    [],
        "routine":   [],
        "unknown":   []
    }

    if not symptoms:
        return result

    symptom_embeddings = np.array(embeddings_model.embed_documents(symptoms))

    for i, symptom in enumerate(symptoms):
        s_vec = symptom_embeddings[i].reshape(1, -1)

        # Check emergency first (highest priority)
        scores = cosine_similarity(s_vec, EMERGENCY_EMBEDDINGS)[0]
        if scores.max() >= THRESHOLD:
            matched = EMERGENCY_KEYWORDS[scores.argmax()]
            print(f"   [Classifier] '{symptom}' → '{matched}' ({scores.max():.2f}) EMERGENCY")
            result["emergency"].append(matched)
            continue

        # Check urgent
        scores = cosine_similarity(s_vec, URGENT_EMBEDDINGS)[0]
        if scores.max() >= THRESHOLD:
            matched = URGENT_KEYWORDS[scores.argmax()]
            print(f"   [Classifier] '{symptom}' → '{matched}' ({scores.max():.2f}) URGENT")
            result["urgent"].append(matched)
            continue

        # Check routine
        scores = cosine_similarity(s_vec, MODERATE_EMBEDDINGS)[0]
        if scores.max() >= THRESHOLD:
            matched = MODERATE_KEYWORDS[scores.argmax()]
            print(f"   [Classifier] '{symptom}' → '{matched}' ({scores.max():.2f}) ROUTINE")
            result["routine"].append(matched)
            continue

        print(f"   [Classifier] '{symptom}' → no match")
        result["unknown"].append(symptom)

    return result


def get_priority(categorized: dict) -> str:
    """Returns the single highest priority level."""
    if categorized["emergency"]:
        return "emergency"
    elif categorized["urgent"]:
        return "urgent"
    elif categorized["routine"]:
        return "routine"
    return "low"