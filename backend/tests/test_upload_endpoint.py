import json

from app.services import llm_client


def _mock_llm(monkeypatch, doc_type="SLA"):
    monkeypatch.setattr(
        llm_client,
        "get_embeddings",
        lambda texts: [[0.1, 0.2, 0.3] for _ in texts],
    )
    monkeypatch.setattr(
        llm_client,
        "get_embedding",
        lambda text: [0.1, 0.2, 0.3],
    )
    monkeypatch.setattr(
        llm_client,
        "chat_completion",
        lambda messages, json_mode=False: json.dumps(
            {"type": doc_type, "reasoning": "Mentions uptime guarantees and service credits."}
        ),
    )


def test_upload_rejects_non_pdf(client):
    response = client.post(
        "/api/documents/upload",
        files={"file": ("notes.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_rejects_empty_file(client):
    response = client.post(
        "/api/documents/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 422


def test_upload_extracts_chunks_and_classifies(client, sample_pdf_bytes, monkeypatch):
    _mock_llm(monkeypatch, doc_type="SLA")

    response = client.post(
        "/api/documents/upload",
        files={"file": ("agreement.pdf", sample_pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "ready"
    assert body["classification"] == "SLA"
    assert body["page_count"] == 1
    assert body["chunk_count"] >= 1

    chunks_response = client.get(f"/api/documents/{body['id']}/chunks")
    assert chunks_response.status_code == 200
    assert len(chunks_response.json()) == body["chunk_count"]


def test_get_document_404_for_unknown_id(client):
    response = client.get("/api/documents/does-not-exist")
    assert response.status_code == 404


def test_upload_persists_failed_status_on_processing_error(
    client, sample_pdf_bytes, monkeypatch, db_session
):
    def _boom(texts):
        raise RuntimeError("embedding service unavailable")

    monkeypatch.setattr(llm_client, "get_embeddings", _boom)

    response = client.post(
        "/api/documents/upload",
        files={"file": ("agreement.pdf", sample_pdf_bytes, "application/pdf")},
    )

    # the document resource was created; status/error_message communicate the failure so
    # the frontend can still render a "failed" card instead of losing the document's id
    # behind a bare error response
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "failed"
    assert "embedding service unavailable" in body["error_message"]

    from app.models import Document

    documents = db_session.query(Document).all()
    assert len(documents) == 1
    assert documents[0].status == "failed"
    assert "embedding service unavailable" in documents[0].error_message


def test_delete_document_removes_it(client, sample_pdf_bytes, monkeypatch):
    _mock_llm(monkeypatch)
    upload = client.post(
        "/api/documents/upload",
        files={"file": ("agreement.pdf", sample_pdf_bytes, "application/pdf")},
    )
    doc_id = upload.json()["id"]

    delete_response = client.delete(f"/api/documents/{doc_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/documents/{doc_id}")
    assert get_response.status_code == 404
