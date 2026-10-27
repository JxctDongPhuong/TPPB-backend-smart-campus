from typing import Optional
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.models import ChatMessage, ChatRequest, ChatResponse
from app.service import chatBotSvc

router = APIRouter(prefix="/ai", tags=["AI Agent Trợ Lý Thông Minh"])

@router.post("/chat", response_model=ChatResponse, summary="Gửi câu hỏi tới AI Agent trợ lý Campus (Hỗ trợ Multi-turn)")
def chat_with_agent(payload: ChatRequest, session: Session = Depends(get_session)):
    # Chuyển đổi ChatMessage Pydantic models thành dict cho service
    history_dicts = [msg.model_dump() for msg in payload.history] if payload.history else []
    
    result = chatBotSvc.handle_chat(
        session,
        message=payload.message,
        history=history_dicts,
        user_id=payload.user_id,
        user_name=payload.user_name,
        user_role=payload.user_role,
        model_name=payload.model
    )
    return ChatResponse(**result)

@router.get("/analyzize", summary="Lấy các gợi ý tối ưu điện năng tự động từ AI")
@router.get("/analyze", summary="Alias lấy gợi ý tối ưu điện năng tự động từ AI")
@router.get("/suggestions", summary="Alias lấy gợi ý tối ưu điện năng tự động từ AI")
def get_ai_suggestions(
    model: Optional[str] = "gemini-3.1-flash-lite",
    session: Session = Depends(get_session)
):
    return chatBotSvc.get_ai_suggestions(session, model_name=model)
