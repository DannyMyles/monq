import re
from dataclasses import dataclass

import tiktoken

from app.services.pdf_extract import PageText

_ENCODING = tiktoken.get_encoding("cl100k_base")


@dataclass
class Piece:
    text: str
    page_number: int


@dataclass
class ChunkResult:
    chunk_index: int
    text: str
    token_count: int
    page_number: int | None


def _split_into_paragraphs(text: str) -> list[str]:
    """Split page text on blank lines; collapses internal whitespace within a paragraph."""
    blocks = re.split(r"\n\s*\n", text)
    paragraphs = []
    for block in blocks:
        collapsed = re.sub(r"\s+", " ", block).strip()
        if collapsed:
            paragraphs.append(collapsed)
    return paragraphs


def _split_oversized(text: str, page_number: int, budget: int) -> list[Piece]:
    """Fallback for a paragraph that alone exceeds the token budget: split on sentence
    boundaries, and as a last resort hard-split by raw token count for pathological
    run-on text with no sentence punctuation."""
    tokens = _ENCODING.encode(text)
    if len(tokens) <= budget:
        return [Piece(text=text, page_number=page_number)]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    pieces: list[Piece] = []
    current: list[str] = []
    current_tokens = 0
    for sentence in sentences:
        stoks = len(_ENCODING.encode(sentence))
        if current and current_tokens + stoks > budget:
            pieces.append(Piece(text=" ".join(current), page_number=page_number))
            current = []
            current_tokens = 0
        current.append(sentence)
        current_tokens += stoks
    if current:
        pieces.append(Piece(text=" ".join(current), page_number=page_number))

    final_pieces: list[Piece] = []
    for piece in pieces:
        ptoks = _ENCODING.encode(piece.text)
        if len(ptoks) <= budget:
            final_pieces.append(piece)
        else:
            for i in range(0, len(ptoks), budget):
                final_pieces.append(
                    Piece(text=_ENCODING.decode(ptoks[i : i + budget]), page_number=page_number)
                )
    return final_pieces


def chunk_pages(
    pages: list[PageText],
    token_budget: int = 500,
    token_overlap: int = 75,
) -> list[ChunkResult]:
    """Paragraph-aware, token-budgeted chunking with overlap.

    Paragraphs are the base unit so a chunk boundary never lands mid-sentence unless a
    single paragraph itself exceeds the budget. Consecutive chunks share `token_overlap`
    tokens of trailing context so a fact split across a paragraph boundary still appears
    whole in at least one chunk.
    """
    pieces: list[Piece] = []
    for page in pages:
        for paragraph in _split_into_paragraphs(page.text):
            pieces.extend(_split_oversized(paragraph, page.page_number, token_budget))

    chunks: list[ChunkResult] = []
    current_tokens: list[int] = []
    current_page: int | None = None
    chunk_index = 0

    for piece in pieces:
        piece_tokens = _ENCODING.encode(piece.text)

        if current_tokens and len(current_tokens) + len(piece_tokens) > token_budget:
            chunks.append(
                ChunkResult(
                    chunk_index=chunk_index,
                    text=_ENCODING.decode(current_tokens),
                    token_count=len(current_tokens),
                    page_number=current_page,
                )
            )
            chunk_index += 1
            overlap_tokens = current_tokens[-token_overlap:] if token_overlap > 0 else []
            current_tokens = list(overlap_tokens)
            current_page = piece.page_number

        if not current_tokens:
            current_page = piece.page_number

        current_tokens.extend(piece_tokens)

    if current_tokens:
        chunks.append(
            ChunkResult(
                chunk_index=chunk_index,
                text=_ENCODING.decode(current_tokens),
                token_count=len(current_tokens),
                page_number=current_page,
            )
        )

    return chunks
