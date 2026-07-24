import tiktoken

from app.services.chunking import chunk_pages
from app.services.pdf_extract import PageText

_ENCODING = tiktoken.get_encoding("cl100k_base")


def _lorem_paragraph(n_words: int, seed: str) -> str:
    return " ".join(f"{seed}{i}" for i in range(n_words))


def test_respects_token_budget():
    # Each paragraph is small, but there are enough of them that the packer must split
    # across multiple chunks rather than returning one giant chunk.
    paragraphs = "\n\n".join(_lorem_paragraph(40, "word") for _ in range(20))
    pages = [PageText(page_number=1, text=paragraphs)]

    chunks = chunk_pages(pages, token_budget=100, token_overlap=20)

    assert len(chunks) > 1
    for chunk in chunks:
        # allow a little slack: a single paragraph may push slightly over budget
        # before the packer detects it needs to close the chunk
        assert chunk.token_count <= 100 + 40


def test_overlap_shares_trailing_tokens_between_chunks():
    paragraphs = "\n\n".join(_lorem_paragraph(30, "tok") for _ in range(10))
    pages = [PageText(page_number=1, text=paragraphs)]

    chunks = chunk_pages(pages, token_budget=80, token_overlap=20)

    assert len(chunks) >= 2
    # the last `token_overlap` tokens of chunk 0 must reappear as the first tokens of chunk 1
    first_tokens = _ENCODING.encode(chunks[0].text)
    second_tokens = _ENCODING.encode(chunks[1].text)
    assert first_tokens[-20:] == second_tokens[:20]


def test_paragraph_boundaries_preserved_when_possible():
    pages = [
        PageText(
            page_number=1,
            text="First paragraph sentence one. Sentence two.\n\nSecond paragraph starts here.",
        )
    ]

    chunks = chunk_pages(pages, token_budget=500, token_overlap=50)

    assert len(chunks) == 1
    assert "First paragraph" in chunks[0].text
    assert "Second paragraph" in chunks[0].text


def test_oversized_paragraph_falls_back_to_sentence_split():
    huge_paragraph = " ".join(f"Sentence number {i} has some content." for i in range(200))
    pages = [PageText(page_number=3, text=huge_paragraph)]

    chunks = chunk_pages(pages, token_budget=50, token_overlap=10)

    assert len(chunks) > 1
    assert all(c.page_number == 3 for c in chunks)
    for chunk in chunks:
        assert chunk.token_count <= 50 + 15  # small slack for sentence-level granularity


def test_empty_page_produces_no_chunks():
    pages = [PageText(page_number=1, text="   \n\n  ")]
    chunks = chunk_pages(pages, token_budget=100, token_overlap=10)
    assert chunks == []
