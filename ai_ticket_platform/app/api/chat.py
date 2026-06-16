from __future__ import annotations

from fastapi import APIRouter, Query, status

from ai_ticket_platform.app.models.schemas import (
    ChatRequest,
    ChatResponse,
    RetrievedContext,
)
from ai_ticket_platform.app.services.rag_service import RAGService
from ai_ticket_platform.app.utils.logging import get_logger


logger = get_logger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "/ask",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
async def ask_question(
    payload: ChatRequest,
    department: str | None = Query(default=None),
) -> ChatResponse:
    """Answer user question using RAG over indexed documents."""
    logger.info(
        "Chat question request received",
        extra={
            "event": "chat_question_requested",
            "operation": "ask_question",
            "status": "started",
            "tenant_id": str(payload.tenant_id),
            "top_k": payload.top_k,
            "department": department,
            "message_length": len(payload.message),
        },
    )

    rag_service = RAGService()

    rag_answer = await rag_service.answer_question(
        tenant_id=payload.tenant_id,
        question=payload.message,
        top_k=payload.top_k,
        department=department,
    )

    logger.info(
        "Chat question request completed",
        extra={
            "event": "chat_question_completed",
            "operation": "ask_question",
            "status": "success",
            "tenant_id": str(payload.tenant_id),
            "context_count": len(rag_answer.contexts),
            "answer_length": len(rag_answer.answer),
        },
    )

    return ChatResponse(
        answer=rag_answer.answer,
        contexts=[
            RetrievedContext(
                document_id=context.document_id,
                chunk_id=context.chunk_id,
                content=context.content,
                score=context.score,
                metadata=context.metadata,
            )
            for context in rag_answer.contexts
        ],
    )
