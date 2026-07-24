import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import Chunk, Document
from app.schemas import ChunkOut, DocumentSummary
from app.services import llm_client
from app.services.chunking import chunk_pages
from app.services.classification import classify_document
from app.services.pdf_extract import extract_pages

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _to_summary(document: Document) -> DocumentSummary:
    return DocumentSummary(
        id=document.id,
        original_filename=document.original_filename,
        status=document.status,
        page_count=document.page_count,
        chunk_count=len(document.chunks),
        classification=document.classification,
        classification_reasoning=document.classification_reasoning,
        error_message=document.error_message,
        created_at=document.created_at,
    )


@router.post("/upload", response_model=DocumentSummary, status_code=status.HTTP_201_CREATED)
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)) -> DocumentSummary:
    settings = get_settings()

    is_pdf = (file.content_type == "application/pdf") or (
        file.filename or ""
    ).lower().endswith(".pdf")
    if not is_pdf:
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    content = file.file.read()
    if not content:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413, detail=f"File exceeds the {settings.max_upload_mb}MB upload limit."
        )

    stored_name = f"{uuid.uuid4()}.pdf"
    stored_path = Path(settings.storage_dir) / stored_name
    stored_path.write_bytes(content)

    document = Document(
        original_filename=file.filename or stored_name,
        stored_path=str(stored_path),
        status="processing",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        pages = extract_pages(str(stored_path))
        document.page_count = len(pages)

        chunk_results = chunk_pages(
            pages,
            token_budget=settings.chunk_token_budget,
            token_overlap=settings.chunk_token_overlap,
        )
        if chunk_results:
            embeddings = llm_client.get_embeddings([c.text for c in chunk_results])
            for chunk_result, embedding in zip(chunk_results, embeddings):
                db.add(
                    Chunk(
                        document_id=document.id,
                        chunk_index=chunk_result.chunk_index,
                        text=chunk_result.text,
                        token_count=chunk_result.token_count,
                        page_number=chunk_result.page_number,
                        embedding=embedding,
                    )
                )

        full_text = "\n\n".join(page.text for page in pages)
        classification = classify_document(full_text)
        document.classification = classification.document_type
        document.classification_reasoning = classification.reasoning
        document.status = "ready"
        db.commit()
    except Exception as exc:  # noqa: BLE001 - persist failure state for any processing error
        document.status = "failed"
        document.error_message = str(exc)
        db.commit()

    db.refresh(document)
    # Always 201: the document resource was created either way. `status`/`error_message`
    # tell the client whether processing (extract -> chunk -> embed -> classify) succeeded,
    # so the frontend can render a "failed" badge with the reason instead of losing the
    # document's id behind a bare error response.
    return _to_summary(document)


@router.get("/{document_id}", response_model=DocumentSummary)
def get_document(document_id: str, db: Session = Depends(get_db)) -> DocumentSummary:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return _to_summary(document)


@router.get("/{document_id}/chunks", response_model=list[ChunkOut])
def get_document_chunks(document_id: str, db: Session = Depends(get_db)) -> list[ChunkOut]:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return [ChunkOut.model_validate(c) for c in document.chunks]


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, db: Session = Depends(get_db)) -> None:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    stored_path = Path(document.stored_path)
    if stored_path.exists():
        stored_path.unlink()
    db.delete(document)
    db.commit()
