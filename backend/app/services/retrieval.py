from dataclasses import dataclass

import numpy as np

_SYSTEM_PROMPT = """You are a procurement assistant answering questions about a single uploaded \
document. You are given CONTEXT chunks retrieved from that document plus, optionally, recent \
conversation history.

Rules:
- Answer using ONLY information found in the CONTEXT chunks below. Do not use outside knowledge \
and do not guess.
- If the CONTEXT does not contain enough information to answer, respond exactly: \
"I can't find that in this document." Do not speculate beyond that.
- When you use a chunk, cite it inline like [chunk 2].
- Be concise and directly answer the question asked.
"""


@dataclass
class ChunkEmbedding:
    chunk_index: int
    page_number: int | None
    text: str
    embedding: list[float]


@dataclass
class RankedChunk:
    chunk_index: int
    page_number: int | None
    text: str
    score: float


def cosine_similarity(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a, dtype=float), np.array(b, dtype=float)
    denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
    if denom == 0.0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def rank_chunks(
    query_embedding: list[float],
    chunks: list[ChunkEmbedding],
    top_k: int,
) -> list[RankedChunk]:
    """Score every chunk against the query embedding and return the top-k by cosine similarity.

    A full scan is used deliberately: for a single "current document" with at most a few
    hundred chunks this is fast, and it avoids the operational overhead of an ANN index
    (ivfflat/HNSW) that would only pay off at multi-document / large-corpus scale.
    """
    scored = [
        RankedChunk(
            chunk_index=c.chunk_index,
            page_number=c.page_number,
            text=c.text,
            score=cosine_similarity(query_embedding, c.embedding),
        )
        for c in chunks
    ]
    scored.sort(key=lambda c: c.score, reverse=True)
    return scored[:top_k]


def build_rag_messages(
    question: str,
    ranked_chunks: list[RankedChunk],
    history: list[tuple[str, str]],
) -> list[dict]:
    """Assemble the chat-completion messages: system grounding prompt, labeled context
    blocks, recent history for follow-up continuity, then the new question."""
    context_blocks = "\n\n".join(
        f"[chunk {c.chunk_index}"
        + (f", page {c.page_number}" if c.page_number is not None else "")
        + f"]\n{c.text}"
        for c in ranked_chunks
    )

    messages: list[dict] = [{"role": "system", "content": _SYSTEM_PROMPT}]
    for role, content in history:
        messages.append({"role": role, "content": content})

    messages.append(
        {
            "role": "user",
            "content": f"CONTEXT:\n{context_blocks}\n\nQUESTION: {question}",
        }
    )
    return messages
