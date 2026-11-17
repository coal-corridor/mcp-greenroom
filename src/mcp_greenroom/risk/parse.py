"""Parse the classifier's answer into a RiskResult. Anything off is ClassifierUnavailable.

The answer is untrusted model output. Errors name what was wrong, never the text itself.
"""

import json
import math
from typing import Any

from mcp_greenroom.interfaces import ClassifierUnavailable
from mcp_greenroom.models import Capability, RiskResult

ANSWER_KEYS = frozenset({"score", "capabilities", "evidence", "rationale"})

# The answer shape, for structured output on the live call (output_config.format).
ANSWER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "score": {"type": "number"},
        "capabilities": {
            "type": "array",
            "items": {"type": "string", "enum": [c.value for c in Capability]},
        },
        "evidence": {"type": "string"},
        "rationale": {"type": "string"},
    },
    "required": ["score", "capabilities", "evidence", "rationale"],
    "additionalProperties": False,
}


def _unavailable(what: str) -> ClassifierUnavailable:
    return ClassifierUnavailable(
        f"Classifier answer unreadable: {what}. "
        "The tool goes to human review; check the prompt and the recording run."
    )


def _strip_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        text = text.removeprefix("```").removesuffix("```")
        text = text.removeprefix("json").strip()
    return text


def _load(text: str) -> dict[str, Any]:
    try:
        data = json.loads(_strip_fence(text))
    except ValueError:
        raise _unavailable("not one JSON value") from None
    if not isinstance(data, dict):
        raise _unavailable(f"expected a JSON object, received {type(data).__name__}")
    unknown = set(data) - ANSWER_KEYS
    if unknown:
        raise _unavailable(f"unexpected keys {sorted(ascii(k)[:40] for k in unknown)}")
    return data


def _score(data: dict[str, Any]) -> float:
    score = data.get("score")
    if isinstance(score, bool) or not isinstance(score, int | float):
        raise _unavailable("score must be a number from 0.0 to 1.0")
    if not math.isfinite(score) or not 0.0 <= score <= 1.0:
        raise _unavailable("score must be a number from 0.0 to 1.0")
    return float(score)


def _capabilities(data: dict[str, Any]) -> frozenset[Capability]:
    raw = data.get("capabilities")
    if not isinstance(raw, list) or not all(isinstance(c, str) for c in raw):
        raise _unavailable("capabilities must be a list of strings")
    known = {c.value for c in Capability}
    if not set(raw) <= known:
        raise _unavailable(f"unknown capability tag, expected some of {sorted(known)}")
    return frozenset(Capability(c) for c in raw)


def parse_answer(text: str, tool_name: str, model_id: str, prompt_hash: str) -> RiskResult:
    data = _load(text)
    for key in ("evidence", "rationale"):
        if not isinstance(data.get(key, ""), str):
            raise _unavailable(f"{key} must be a string")
    return RiskResult(
        tool_name=tool_name,
        score=_score(data),
        capabilities=_capabilities(data),
        model_id=model_id,
        prompt_hash=prompt_hash,
    )
