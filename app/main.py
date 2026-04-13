from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.api.documents import router as documents_router
from app.api.qa import router as qa_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="企业文档问答系统",
    description="Enterprise document Q&A with RAG (Retrieval-Augmented Generation)",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(documents_router, prefix="/api")
app.include_router(qa_router, prefix="/api")

_static = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=_static), name="static")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def index():
    return FileResponse(_static / "index.html")
