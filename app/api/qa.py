"""Q&A endpoint with multi-turn conversation support."""
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Conversation, ConversationMessage
from app.schemas import AskRequest, AskResponse
from app.services.llm_service import answer_question

router = APIRouter(prefix="/qa", tags=["qa"])


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest, db: AsyncSession = Depends(get_db)):
    if not request.question.strip():
        raise HTTPException(400, "Question cannot be empty")

    # ── Resolve conversation ──
    if request.conversation_id:
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id == request.conversation_id)
            .options(selectinload(Conversation.messages))
        )
        conv = result.scalar_one_or_none()
        if conv is None:
            raise HTTPException(404, f"Conversation {request.conversation_id} not found")
        # messages already eager-loaded
        history = [{"role": m.role, "content": m.content} for m in conv.messages]
    else:
        conv = Conversation(
            id=str(uuid.uuid4()),
            document_ids_json=json.dumps(request.document_ids) if request.document_ids else None,
        )
        db.add(conv)
        await db.flush()
        history = []  # brand-new conversation — no prior turns

    # ── Answer ──
    result = await answer_question(
        request.question,
        db,
        document_ids=request.document_ids,
        history=history,
        conversation_id=conv.id,
    )

    # ── Persist this turn ──
    db.add(ConversationMessage(conversation_id=conv.id, role="user", content=request.question))
    db.add(ConversationMessage(conversation_id=conv.id, role="assistant", content=result.answer))
    await db.commit()

    return result
