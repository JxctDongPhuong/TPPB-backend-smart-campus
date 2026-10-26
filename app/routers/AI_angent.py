# File này được giữ lại làm alias tương thích ngược. 
# Khuyến nghị sử dụng router chính tại app/routers/ai_agent.py
from .ai_agent import router
from app.models import ChatRequest, ChatResponse, ChatMessage

__all__ = ["router", "ChatRequest", "ChatResponse", "ChatMessage"]
