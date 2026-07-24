from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import Base, engine
from app.routers import chat, documents

settings = get_settings()

# create_all is sufficient here: no migrations are needed for this assessment's scope
# (documented as an explicit out-of-scope tradeoff vs. Alembic in DESIGN.md).
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Monq Procurement Document Assistant", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
