import os
import json
import logging
from datetime import date, datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from sqlmodel import Session

from google import genai
from google.genai import types

from app.service.ai_tools import (
    GEMINI_TOOL_DECLARATIONS,
    execute_ai_tool,
    format_tool_response
)
from app.service.metricService import detect_waste_energy, get_energy_summary

logger = logging.getLogger("smart_campus.chatbot")

# Nạp biến môi trường từ .env
load_dotenv()

# Danh sách các model hỗ trợ với ưu tiên hàng đầu theo yêu cầu
SUPPORTED_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-2.0-flash",
]

def get_system_prompt() -> str:
    today_str = date.today().strftime("%Y-%m-%d")
    return f"""
Bạn là Trợ lý AI Điều Hành Smart Campus trường đại học.
HÔM NAY LÀ NGÀY: {today_str} (Mọi câu hỏi về 'hôm nay', 'chiều nay', 'hiện tại' đều ứng với ngày {today_str}).
Nhiệm vụ của bạn là hỗ trợ sinh viên, giảng viên và ban quản lý tra cứu phòng học, kiểm tra lịch mượn, phát hiện lãng phí điện năng và tiếp nhận sự cố kỹ thuật.

QUY TẮC PHẢN HỒI BẮT BUỘC (TUÂN THỦ 100%):
1. TRẢ LỜI TRỰC DIỆN, NGẮN GỌN, ĐÚNG TRỌNG TÂM:
   - TUYỆT ĐỐI KHÔNG chào hỏi rườm rà (Bỏ toàn bộ các câu: "Chào bạn, tôi là trợ lý...").
   - TUYỆT ĐỐI KHÔNG lặp lại câu hỏi của người dùng ("Bạn đang muốn tìm...", "Dựa vào yêu cầu...").
   - Hỏi đâu đáp đó, câu trả lời từ 1 đến 3 câu súc tích.
2. SỬ DỤNG CÔNG CỤ (TOOLS):
   - Khi người dùng cần tìm phòng trống, kiểm tra lịch học, báo hỏng thiết bị, kiểm tra lãng phí điện năng hoặc đặt phòng: BẮT BUỘC gọi công cụ tương ứng để lấy dữ liệu thực tế từ cơ sở dữ liệu.
   - Khi gọi công cụ cho ngày hôm nay, hãy truyền tham số ngày là "{today_str}".
   - TUYỆT ĐỐI KHÔNG tự bịa đặt số liệu khi chưa gọi công cụ.
3. KHI HỆ THỐNG CHƯA CÓ DỮ LIỆU (status = 'no_data'):
   - Nói thẳng rõ ràng: "Hiện tại hệ thống chưa ghi nhận dữ liệu trong cơ sở dữ liệu."
   - TUYỆT ĐỐI KHÔNG báo kết quả là '0 phòng' hay '0 kWh' khi thực tế là hệ thống chưa có dữ liệu đo đạc.
"""

def get_gemini_client() -> Optional[genai.Client]:
    """Khởi tạo Client Gemini an toàn kèm try-catch"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("[Gemini API] Chưa cấu hình GEMINI_API_KEY trong file .env.")
            return None
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.error(f"[Gemini Client Error] Lỗi khởi tạo genai.Client: {e}")
        return None


def handle_chat(
    session: Session,
    message: str,
    history: Optional[List[Dict[str, str]]] = None,
    user_id: Optional[int] = None,
    model_name: Optional[str] = "gemini-3.1-flash-lite"
) -> Dict[str, Any]:
    """
    Xử lý câu hỏi qua mô hình AI Agent Tools (Function Calling):
    - Tự động phân tích ý định và kích hoạt Tool tương ứng
    - Không hard-code if-else
    - Try-catch an toàn tuyệt đối mọi bước tương tác DB và API
    """
    client = get_gemini_client()
    if not client:
        return {
            "reply": "Chưa cấu hình GEMINI_API_KEY trong file .env của hệ thống Backend.",
            "action_taken": "error_config",
            "model_used": "none",
            "data_source": "none",
            "data": None
        }

    requested_model = model_name or "gemini-3.1-flash-lite"
    candidates = [requested_model] + [m for m in SUPPORTED_MODELS if m != requested_model]

    # Chuẩn bị danh sách Tools cho Gemini
    gemini_tools = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(**decl) for decl in GEMINI_TOOL_DECLARATIONS
            ]
        )
    ]

    # Xây dựng lịch sử hội thoại Multi-turn
    gemini_contents: List[types.Content] = []
    if history:
        for item in history:
            role = "model" if item.get("role") in ["assistant", "model"] else "user"
            content_text = item.get("content", "")
            if content_text:
                gemini_contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=content_text)]
                    )
                )

    # Tin nhắn hiện tại của người dùng
    user_content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=message)]
    )
    gemini_contents.append(user_content)

    # Thử lần lượt các model trong danh sách fallback
    last_error = None
    for model in candidates:
        try:
            logger.info(f"[Gemini Agent] Đang xử lý câu hỏi với model: {model}...")
            
            # Lần gọi 1: Cho AI phân tích và quyết định có cần kích hoạt Tool không
            response = client.models.generate_content(
                model=model,
                contents=gemini_contents,
                config=types.GenerateContentConfig(
                    system_instruction=get_system_prompt(),
                    temperature=0.2,
                    tools=gemini_tools
                )
            )

            # Trường hợp 1: AI kích hoạt một Tool theo kịch bản
            if response and response.function_calls:
                fn_call = response.function_calls[0]
                tool_name = fn_call.name
                tool_args = dict(fn_call.args) if fn_call.args else {}
                logger.info(f"[Gemini Agent] AI quyết định kích hoạt tool: '{tool_name}' với tham số: {tool_args}")

                # Thực thi Tool với Session DB và user_id an toàn
                tool_result = execute_ai_tool(tool_name, tool_args, session=session, user_id=user_id)

                # Format trực tiếp dữ liệu từ Tool thành Markdown câu trả lời hoàn chỉnh (Đúng 1 lượt call AI)
                reply_text = format_tool_response(tool_name, tool_args, tool_result)

                return {
                    "reply": reply_text,
                    "action_taken": tool_name,  # Phân loại hành động tự động từ tên Tool
                    "model_used": model,
                    "data_source": f"tool:{tool_name}",
                    "data": tool_result
                }

            # Trường hợp 2: AI trả lời trực tiếp (câu hỏi thông thường, giải thích)
            elif response and response.text:
                return {
                    "reply": response.text.strip(),
                    "action_taken": "general_consulting",
                    "model_used": model,
                    "data_source": "llm_direct",
                    "data": None
                }

        except Exception as e:
            logger.warning(f"[Gemini Agent Error] Model {model} gặp sự cố: {e}. Đang thử model tiếp theo...")
            last_error = e
            continue

    # Nếu tất cả model đều lỗi
    return {
        "reply": f"Hệ thống trợ lý AI tạm thời gián đoạn kết nối: {str(last_error)}",
        "action_taken": "error",
        "model_used": "none",
        "data_source": "error",
        "data": None
    }


def refresh_campus_cache(session: Session) -> str:
    """Hỗ trợ endpoint làm mới cache nếu router cần gọi"""
    return "Đã làm mới cơ chế tra cứu dữ liệu thời gian thực."


def get_ai_suggestions(
    session: Session,
    model_name: Optional[str] = "gemini-3.1-flash-lite"
) -> Dict[str, Any]:
    """
    AI phân tích tối ưu điện năng dạng JSON có cấu trúc.
    Kèm kiểm tra dữ liệu chặt chẽ tránh trả về '0 0' khi chưa có dữ liệu trong DB.
    """
    today = date.today()

    try:
        waste_info = detect_waste_energy(session, today)
        energy_summary = get_energy_summary(session)

        # XỬ LÝ TRƯỜNG HỢP DB CHƯA CÓ DỮ LIỆU: Không gọi AI để tránh trả ra kết quả '0 0'
        if not waste_info.get("has_data") and not energy_summary.get("has_data"):
            return {
                "status": "no_data",
                "summary": f"Hệ thống hiện tại chưa ghi nhận dữ liệu đo đạc điện năng cho ngày {today}.",
                "total_wasted_kwh": None,
                "estimated_wasted_vnd": None,
                "suggestions": [],
                "policy_advice": "Vui lòng cập nhật hoặc nạp dữ liệu công tơ điện vào hệ thống trước khi chạy phân tích tối ưu năng lượng.",
                "model_used": "system_guard"
            }

        prompt = f"""
Số liệu điện năng Smart Campus ngày ({today}):
- Cảnh báo lãng phí: {json.dumps(waste_info.get('danh_sach_canh_bao', []), ensure_ascii=False)}
- Tổng hợp điện năng: {json.dumps(energy_summary, ensure_ascii=False)}

Yêu cầu:
Giả sử giá điện là 2.500 VNĐ / kWh, trả về JSON duy nhất (không bọc markdown, không dẫn nhập):
{{
  "summary": "Tóm tắt ngắn gọn trong 1 câu",
  "total_wasted_kwh": <số>,
  "estimated_wasted_vnd": <số>,
  "suggestions": [
    {{
      "id": 1,
      "title": "Tiêu đề đề xuất",
      "description": "Mô tả ngắn",
      "potential_savings_kwh": <số>,
      "priority": "Cao" hoặc "Trung bình" hoặc "Thấp",
      "recommended_action": "Hành động ngắn"
    }}
  ],
  "policy_advice": "Khuyến nghị chính sách ngắn"
}}
"""
        client = get_gemini_client()
        if not client:
            return {
                "summary": "Chưa cấu hình API Key.",
                "total_wasted_kwh": None,
                "estimated_wasted_vnd": None,
                "suggestions": []
            }

        model_to_use = model_name or "gemini-3.1-flash-lite"
        response = client.models.generate_content(
            model=model_to_use,
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
            config=types.GenerateContentConfig(
                system_instruction="Chỉ trả về JSON thuần túy, không có text dẫn nhập.",
                temperature=0.1
            )
        )

        clean_text = response.text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        parsed = json.loads(clean_text)
        parsed["model_used"] = model_to_use
        return parsed

    except Exception as e:
        logger.error(f"[get_ai_suggestions Error]: {e}")
        return {
            "status": "error",
            "summary": f"Không thể phân tích dữ liệu điện năng lúc này: {str(e)}",
            "total_wasted_kwh": None,
            "estimated_wasted_vnd": None,
            "suggestions": []
        }
