import io
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("GEMINI_API_KEY", "test-key")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402

get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """A small, real, multi-paragraph PDF (an SLA-flavored services agreement) used to
    exercise extraction, chunking, and the upload endpoint end-to-end without hitting the
    OpenAI API."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    lines = [
        "MASTER SERVICES AGREEMENT",
        "",
        "This Master Services Agreement (\"Agreement\") is entered into between",
        "Acme Corp (\"Client\") and Globex Supplies Inc. (\"Vendor\").",
        "",
        "1. Term. This Agreement shall commence on January 1, 2026 and continue",
        "for a period of twelve (12) months, unless terminated earlier as provided herein.",
        "",
        "2. Payment Terms. Client shall pay Vendor within thirty (30) days of",
        "receipt of a valid invoice. Late payments accrue interest at 1.5% per month.",
        "",
        "3. Service Level. Vendor guarantees 99.9% uptime for all hosted services",
        "measured monthly. Failure to meet this threshold entitles Client to service credits.",
    ]
    y = 800
    for line in lines:
        c.drawString(50, y, line)
        y -= 20
    c.showPage()
    c.save()
    return buffer.getvalue()
