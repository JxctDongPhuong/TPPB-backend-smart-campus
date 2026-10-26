from typing import Optional, List, Any
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str = Field(description="Vai trò người gửi: 'user' hoặc 'assistant'")
    content: str = Field(description="Nội dung tin nhắn")

class ChatRequest(BaseModel):
    message: str = Field(description="Câu hỏi hiện tại của người dùng")
    history: Optional[List[ChatMessage]] = Field(
        default=[],
        description="Lịch sử các câu hỏi và trả lời trước đó để AI duy trì mạch hội thoại (Multi-turn)"
    )
    user_id: Optional[int] = None
    model: Optional[str] = Field(
        default="gemini-3.1-flash-lite",
        description="Model Gemini muốn sử dụng ('gemini-3.1-flash-lite' hoặc 'gemini-3.5-flash-lite')"
    )

class ChatResponse(BaseModel):
    reply: str
    action_taken: Optional[str] = None
    model_used: Optional[str] = None
    data_source: Optional[str] = None
    data: Optional[Any] = Field(default=None, description="Dữ liệu cấu trúc gốc từ Tool nếu có")
