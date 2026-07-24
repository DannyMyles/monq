import json
from dataclasses import dataclass

from app.constants import DOCUMENT_TYPES, FALLBACK_DOCUMENT_TYPE
from app.services import llm_client

_SYSTEM_PROMPT = f"""You are a procurement document classifier for an enterprise strategic \
procurement platform. Classify the given document text into exactly one of these standard \
procurement document types:

{", ".join(DOCUMENT_TYPES)}

Respond with a JSON object only, in this exact shape:
{{"type": "<one of the types above>", "reasoning": "<one sentence explaining the classification>"}}

If the document does not clearly match any specific type, use "Other".
"""

# Keep the classification prompt cheap: the opening of a document (title, parties, purpose)
# is almost always sufficient to identify its type.
_MAX_CHARS_FOR_CLASSIFICATION = 8000


@dataclass
class ClassificationResult:
    document_type: str
    reasoning: str


def classify_document(full_text: str) -> ClassificationResult:
    excerpt = full_text[:_MAX_CHARS_FOR_CLASSIFICATION]
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": f"Document text:\n\n{excerpt}"},
    ]
    raw = llm_client.chat_completion(messages, json_mode=True)
    return _parse_response(raw)


def _parse_response(raw: str) -> ClassificationResult:
    try:
        data = json.loads(raw)
        doc_type = str(data.get("type", "")).strip()
        reasoning = str(data.get("reasoning", "")).strip()
    except (json.JSONDecodeError, AttributeError):
        doc_type = ""
        reasoning = "Model response could not be parsed; defaulted to Other."

    if doc_type not in DOCUMENT_TYPES:
        doc_type = FALLBACK_DOCUMENT_TYPE
        if not reasoning:
            reasoning = "Model returned an unrecognized label; defaulted to Other."

    return ClassificationResult(document_type=doc_type, reasoning=reasoning or "")
