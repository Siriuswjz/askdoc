"""Q&A endpoint."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import AskRequest, AskResponse
from app.services.llm_service import answer_question

router = APIRouter(prefix="/qa", tags=["qa"])


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest, db: AsyncSession = Depends(get_db)):
    if not request.question.strip():
        raise HTTPException(400, "Question cannot be empty")
    return await answer_question(request.question, db, document_ids=request.document_ids)
