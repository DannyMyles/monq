from functools import lru_cache

from google import genai
from google.genai import types

from app.config import get_settings


@lru_cache
def _client() -> genai.Client:
    return genai.Client(api_key=get_settings().gemini_api_key)


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Batch-embed a list of texts in a single API call."""
    if not texts:
        return []
    settings = get_settings()
    result = _client().models.embed_content(model=settings.gemini_embedding_model, contents=texts)
    return [embedding.values for embedding in result.embeddings]


def get_embedding(text: str) -> list[float]:
    return get_embeddings([text])[0]


def chat_completion(messages: list[dict], json_mode: bool = False) -> str:
    """Generic chat-completion call. `messages` uses the OpenAI-style shape
    ({"role": "system"|"user"|"assistant", "content": str}) so callers (classification,
    retrieval/RAG prompting) stay provider-agnostic; this function does the translation
    to Gemini's system_instruction + role="user"/"model" content format.
    """
    settings = get_settings()
    system_instruction: str | None = None
    contents: list[types.Content] = []
    for message in messages:
        if message["role"] == "system":
            system_instruction = message["content"]
            continue
        gemini_role = "model" if message["role"] == "assistant" else "user"
        contents.append(
            types.Content(role=gemini_role, parts=[types.Part(text=message["content"])])
        )

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0,
        response_mime_type="application/json" if json_mode else None,
    )
    response = _client().models.generate_content(
        model=settings.gemini_chat_model, contents=contents, config=config
    )
    return response.text or ""
