import math

from app.services.retrieval import (
    ChunkEmbedding,
    RankedChunk,
    build_rag_messages,
    cosine_similarity,
    rank_chunks,
)


def test_cosine_similarity_identical_vectors_is_one():
    assert math.isclose(cosine_similarity([1.0, 0.0], [1.0, 0.0]), 1.0, rel_tol=1e-6)


def test_cosine_similarity_orthogonal_vectors_is_zero():
    assert math.isclose(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0, abs_tol=1e-9)


def test_cosine_similarity_opposite_vectors_is_negative_one():
    assert math.isclose(cosine_similarity([1.0, 0.0], [-1.0, 0.0]), -1.0, rel_tol=1e-6)


def test_cosine_similarity_zero_vector_returns_zero():
    assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0


def test_rank_chunks_orders_by_similarity_descending():
    query = [1.0, 0.0]
    chunks = [
        ChunkEmbedding(chunk_index=0, page_number=1, text="unrelated", embedding=[0.0, 1.0]),
        ChunkEmbedding(chunk_index=1, page_number=1, text="exact match", embedding=[1.0, 0.0]),
        ChunkEmbedding(chunk_index=2, page_number=2, text="somewhat related", embedding=[0.7, 0.7]),
    ]

    ranked = rank_chunks(query, chunks, top_k=3)

    assert [r.chunk_index for r in ranked] == [1, 2, 0]
    assert ranked[0].score > ranked[1].score > ranked[2].score


def test_rank_chunks_respects_top_k():
    query = [1.0, 0.0]
    chunks = [
        ChunkEmbedding(chunk_index=i, page_number=None, text=f"chunk {i}", embedding=[1.0, 0.0])
        for i in range(10)
    ]

    ranked = rank_chunks(query, chunks, top_k=3)

    assert len(ranked) == 3


def test_build_rag_messages_includes_context_and_history_and_question():
    ranked = [
        RankedChunk(chunk_index=0, page_number=2, text="Payment is due in 30 days.", score=0.9)
    ]
    history = [("user", "What vendor is this?"), ("assistant", "Globex Supplies Inc.")]

    messages = build_rag_messages("When is payment due?", ranked, history)

    assert messages[0]["role"] == "system"
    assert "ONLY" in messages[0]["content"]
    assert messages[1] == {"role": "user", "content": "What vendor is this?"}
    assert messages[2] == {"role": "assistant", "content": "Globex Supplies Inc."}
    final = messages[-1]
    assert final["role"] == "user"
    assert "Payment is due in 30 days." in final["content"]
    assert "[chunk 0" in final["content"]
    assert "When is payment due?" in final["content"]
