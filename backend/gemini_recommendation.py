"""Optional Gemini wording provider for deterministic recommendations."""
from __future__ import annotations

import json
import os
from typing import Any, Callable, Mapping


GEMINI_DEFAULT_MODEL = "gemini-3.5-flash-lite"
GEMINI_MAX_OUTPUT_TOKENS = 384

# Gemini supports this compact subset of JSON Schema. Avoid Pydantic's
# ``additionalProperties`` output because older SDK versions pass it through
# to the API, which rejects it.
_TEXT_ITEM_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "rule_id": {"type": "STRING"},
        "category": {"type": "STRING"},
        "priority": {"type": "STRING", "enum": ["high", "mid", "low"]},
        "title": {"type": "STRING"},
        "reason": {"type": "STRING"},
        "action": {"type": "STRING"},
        "used_fact_ids": {"type": "ARRAY", "items": {"type": "STRING"}},
        "action_ids": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["rule_id", "category", "priority", "title", "reason", "action", "used_fact_ids", "action_ids"],
}

GEMINI_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "summary": {"type": "STRING"},
        "recommendations": {"type": "ARRAY", "items": _TEXT_ITEM_SCHEMA},
        "clinical_claim": {"type": "STRING", "nullable": True},
    },
    "required": ["summary", "recommendations", "clinical_claim"],
}


def _english_text(value: Any) -> str:
    if isinstance(value, Mapping):
        return str(value.get("en") or "")
    return str(value or "")


def _compact_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Keep prompts English-only and omit data Gemini may not use.

    The deterministic validator still compares the returned IDs against the
    complete internal candidates. This compact representation only lowers API
    input size and narrows the model's available information.
    """
    candidates = []
    for candidate in contract.get("candidates", []):
        candidates.append({
            "rule_id": candidate["rule_id"],
            "category": candidate["category"],
            "priority": candidate["priority"],
            "reason_facts": [
                {"fact_id": fact["fact_id"], "text": _english_text(fact.get("text"))}
                for fact in candidate.get("reason_facts", [])
            ],
            "allowed_actions": [
                {"action_id": action["action_id"], "text": _english_text(action.get("text"))}
                for action in candidate.get("allowed_actions", [])
            ],
        })
    return {
        "language": "en",
        "maximum_recommendations": contract["maximum_recommendations"],
        "candidates": candidates,
        "response_schema": contract["response_schema"],
    }


def _prompt(contract: Mapping[str, Any]) -> str:
    """Give Gemini only compact deterministic wording facts, never raw inputs."""
    instructions = (
        "You rewrite VocaSense recommendation wording in English.\n\n"
        "Return exactly one JSON object matching the supplied response schema.\n"
        "You must preserve every candidate's rule_id, category, priority, order, "
        "used_fact_ids, and action_ids exactly as supplied.\n"
        "Use only each candidate's reason_facts and allowed_actions.\n"
        "Do not calculate scores, add recommendations, diagnose, make medical claims, "
        "or claim that a behavior caused an acoustic result. clinical_claim must be null.\n\n"
        "Keep the summary within 120 English characters, each title within 50 characters, "
        "each reason within 180 characters, and each action within 160 characters.\n\n"
        "Deterministic contract:\n"
    )
    return instructions + json.dumps(_compact_contract(contract), ensure_ascii=False, separators=(",", ":"))


class GeminiRecommendationWorder:
    """Callable adapter accepted by RecommendationService's ai_worder hook."""

    def __init__(self, api_key: str, model: str = GEMINI_DEFAULT_MODEL) -> None:
        # Import lazily so deterministic fallback still works when the optional
        # package has not been installed in a deployment.
        from google import genai
        from google.genai import types

        self._client = genai.Client(api_key=api_key)
        self._types = types
        self._model = model

    def __call__(self, contract: dict[str, Any]) -> dict[str, Any]:
        response = self._client.models.generate_content(
            model=self._model,
            contents=_prompt(contract),
            config=self._types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GEMINI_RESPONSE_SCHEMA,
                temperature=0.1,
                max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS,
            ),
        )
        if not response.text:
            raise RuntimeError("Gemini returned no text response.")
        decoded = json.loads(response.text)
        if not isinstance(decoded, dict):
            raise ValueError("Gemini response must be a JSON object.")
        return decoded


def worder_from_environment() -> Callable[[dict[str, Any]], dict[str, Any]] | None:
    """Return None when Gemini is not configured, preserving local fallback."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return GeminiRecommendationWorder(
        api_key=api_key,
        model=os.getenv("GEMINI_MODEL", GEMINI_DEFAULT_MODEL),
    )
