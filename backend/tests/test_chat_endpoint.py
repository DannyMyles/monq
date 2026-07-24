from app.models import Chunk, Document
from app.services import llm_client


def _seed_ready_document(db_session) -> str:
    document = Document(
        original_filename="agreement.pdf",
        stored_path="/tmp/agreement.pdf",
        page_count=1,
        status="ready",
        classification="SLA",
    )
    db_session.add(document)
    db_session.flush()

    chunks = [
        Chunk(
            document_id=document.id,
            chunk_index=0,
            text="Vendor guarantees 99.9% uptime measured monthly.",
            token_count=10,
            page_number=1,
            embedding=[1.0, 0.0, 0.0],
        ),
        Chunk(
            document_id=document.id,
            chunk_index=1,
            text="Client shall pay Vendor within thirty (30) days of invoice receipt.",
            token_count=12,
            page_number=1,
            embedding=[0.0, 1.0, 0.0],
        ),
    ]
    db_session.add_all(chunks)
    db_session.commit()
    return document.id


def test_chat_returns_grounded_answer_with_sources(client, db_session, monkeypatch):
    document_id = _seed_ready_document(db_session)

    # question embedding aligns with chunk 0 (uptime), not chunk 1 (payment terms)
    monkeypatch.setattr(llm_client, "get_embedding", lambda text: [1.0, 0.0, 0.0])
    monkeypatch.setattr(
        llm_client,
        "chat_completion",
        lambda messages: "The vendor guarantees 99.9% uptime [chunk 0].",
    )

    response = client.post(
        f"/api/documents/{document_id}/chat", json={"question": "What is the uptime guarantee?"}
    )

    assert response.status_code == 200
    body = response.json()
    assert "99.9%" in body["answer"]
    assert body["sources"][0]["chunk_index"] == 0
    assert body["sources"][0]["score"] > body["sources"][1]["score"]


def test_chat_persists_history_for_followup_context(client, db_session, monkeypatch):
    document_id = _seed_ready_document(db_session)
    monkeypatch.setattr(llm_client, "get_embedding", lambda text: [1.0, 0.0, 0.0])

    captured_messages = []

    def fake_chat_completion(messages):
        captured_messages.append(messages)
        return "answer"

    monkeypatch.setattr(llm_client, "chat_completion", fake_chat_completion)

    client.post(f"/api/documents/{document_id}/chat", json={"question": "First question?"})
    client.post(f"/api/documents/{document_id}/chat", json={"question": "Follow-up question?"})

    # second call's prompt should include the first turn's user question and answer
    second_call_messages = captured_messages[1]
    joined = " ".join(m["content"] for m in second_call_messages)
    assert "First question?" in joined
    assert "answer" in joined

    history_response = client.get(f"/api/documents/{document_id}/messages")
    assert history_response.status_code == 200
    assert len(history_response.json()) == 4  # 2 user + 2 assistant messages


def test_chat_404_for_unknown_document(client):
    response = client.post("/api/documents/does-not-exist/chat", json={"question": "hi"})
    assert response.status_code == 404


def test_chat_409_when_document_not_ready(client, db_session):
    document = Document(
        original_filename="agreement.pdf",
        stored_path="/tmp/agreement.pdf",
        status="processing",
    )
    db_session.add(document)
    db_session.commit()

    response = client.post(f"/api/documents/{document.id}/chat", json={"question": "hi"})
    assert response.status_code == 409


def test_chat_422_for_empty_question(client, db_session):
    document_id = _seed_ready_document(db_session)
    response = client.post(f"/api/documents/{document_id}/chat", json={"question": ""})
    assert response.status_code == 422
