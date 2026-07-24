from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import ChatMessage, Document
from app.schemas import ChatMessageOut, ChatRequest, ChatResponse, SourceOut
from app.services import llm_client
from app.services.retrieval import ChunkEmbedding, build_rag_messages, rank_chunks

router = APIRouter(prefix="/api/documents", tags=["chat"])

_SNIPPET_LEN = 300


@router.post("/{document_id}/chat", response_model=ChatResponse)
def chat_with_document(
    document_id: str, request: ChatRequest, db: Session = Depends(get_db)
) -> ChatResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    if document.status != "ready":
        raise HTTPException(
            status_code=409, detail=f"Document is not ready for chat (status={document.status})."
        )

    settings = get_settings()

    question_embedding = llm_client.get_embedding(request.question)
    chunk_embeddings = [
        ChunkEmbedding(
            chunk_index=c.chunk_index,
            page_number=c.page_number,
            text=c.text,
            embedding=c.embedding,
        )
        for c in document.chunks
    ]
    ranked = rank_chunks(question_embedding, chunk_embeddings, top_k=settings.rag_top_k)

    history_limit = settings.chat_history_turns * 2
    recent_messages = list(document.messages)[-history_limit:]
    history = [(m.role, m.content) for m in recent_messages]

    messages = build_rag_messages(request.question, ranked, history)
    answer = llm_client.chat_completion(messages)

    db.add(ChatMessage(document_id=document.id, role="user", content=request.question))
    db.add(ChatMessage(document_id=document.id, role="assistant", content=answer))
    db.commit()

    sources = [
        SourceOut(
            chunk_index=c.chunk_index,
            page_number=c.page_number,
            snippet=c.text[:_SNIPPET_LEN],
            score=c.score,
        )
        for c in ranked
    ]
    return ChatResponse(answer=answer, sources=sources)


@router.get("/{document_id}/messages", response_model=list[ChatMessageOut])
def get_chat_history(document_id: str, db: Session = Depends(get_db)) -> list[ChatMessageOut]:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.document_id == document_id)
        .order_by(ChatMessage.created_at)
    )
    return [ChatMessageOut.model_validate(m) for m in db.scalars(stmt)]
