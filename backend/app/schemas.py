from datetime import datetime

from pydantic import BaseModel, Field


class DocumentSummary(BaseModel):
    id: str
    original_filename: str
    status: str
    page_count: int
    chunk_count: int
    classification: str | None
    classification_reasoning: str | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChunkOut(BaseModel):
    chunk_index: int
    page_number: int | None
    text: str

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class SourceOut(BaseModel):
    chunk_index: int
    page_number: int | None
    snippet: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceOut]


class ChatMessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
