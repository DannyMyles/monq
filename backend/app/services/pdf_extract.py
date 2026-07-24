from dataclasses import dataclass

from pypdf import PdfReader


@dataclass
class PageText:
    page_number: int  # 1-indexed
    text: str


def extract_pages(file_path: str) -> list[PageText]:
    """Extract raw text per page from a PDF file on disk."""
    reader = PdfReader(file_path)
    pages: list[PageText] = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(PageText(page_number=i, text=text))
    return pages
