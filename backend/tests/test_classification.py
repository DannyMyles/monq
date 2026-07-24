import json

from app.services import classification, llm_client


def test_classifies_into_known_type(monkeypatch):
    monkeypatch.setattr(
        llm_client,
        "chat_completion",
        lambda messages, json_mode=False: json.dumps(
            {"type": "NDA", "reasoning": "Contains mutual confidentiality obligations."}
        ),
    )

    result = classification.classify_document("This Non-Disclosure Agreement is entered into...")

    assert result.document_type == "NDA"
    assert "confidentiality" in result.reasoning


def test_unrecognized_label_falls_back_to_other(monkeypatch):
    monkeypatch.setattr(
        llm_client,
        "chat_completion",
        lambda messages, json_mode=False: json.dumps(
            {"type": "Marketing Flyer", "reasoning": "Not a real procurement type."}
        ),
    )

    result = classification.classify_document("Some ambiguous text.")

    assert result.document_type == "Other"


def test_unparseable_response_falls_back_to_other(monkeypatch):
    monkeypatch.setattr(
        llm_client, "chat_completion", lambda messages, json_mode=False: "not valid json"
    )

    result = classification.classify_document("Some text.")

    assert result.document_type == "Other"
    assert result.reasoning


def test_prompt_lists_all_standard_types():
    for doc_type in classification.DOCUMENT_TYPES:
        assert doc_type in classification._SYSTEM_PROMPT
