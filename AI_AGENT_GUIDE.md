# 📚 TÀI LIỆU HƯỚNG DẪN XÂY DỰNG AI AGENT (SMART CAMPUS BACKEND)

Tài liệu này giải thích chi tiết toàn bộ kiến trúc, luồng xử lý và cách code một **AI Agent thông minh** tích hợp vào hệ thống Backend (FastAPI + SQLModel + Google Gemini/OpenAI).

---

## 🏛 1. BẢN CHẤT KIẾN TRÚC: HỆ THỐNG HOẠT ĐỘNG NHƯ THẾ NÀO?

Một hệ thống Backend tích hợp AI Agent hoạt động theo nguyên lý phân tầng chặt chẽ:

```
[Client / Frontend / Swagger]
            │
            ▼  (1) Gửi Request HTTP POST /api/ai/chat
┌────────────────────────────────────────────────────────┐
│  ROUTER LAYER (app/routers/ai_agent.py)                │
│  - Tiếp nhận request, kiểm tra cú pháp Pydantic        │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼  (2) Chuyển dữ liệu qua Service
┌────────────────────────────────────────────────────────┐
│  SERVICE LAYER (app/service/chatBotSvc.py)             │
│                                                        │
│  ├── [A] Lấy dữ liệu thực tế (Database Context)       │
│  │   └── Đọc SQLite: Phòng, Lịch học, Điện năng        │
│  │   └── Dùng bộ nhớ đệm (Lazy Loading Cache)          │
│  │                                                     │
│  ├── [B] Ghép System Prompt (Quy tắc & Vai trò)       │
│  │                                                     │
│  └── [C] Gọi LLM Bên Ngoài (Google Gemini / OpenAI)    │
│      └── Thử model chính (gemini-3.1-flash-lite)      │
│      └── Tự động fallback nếu model nghẽn/lỗi         │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼  (3) Trả JSON phản hồi
[Client nhận được câu trả lời chính xác theo thực tế]
```

---

## 🧩 2. BỐN BƯỚC XÂY DỰNG TỪ A ĐẾN Z

### BƯỚC 1: ĐỊNH NGHĨA KHUNG DỮ LIỆU (SCHEMAS)
Nằm tại: `app/models/schemas/ai_agent.py` và xuất ra ở `app/models/schemas/__init__.py`.

Mục đích: Định nghĩa chuẩn cấu trúc dữ liệu đầu vào (Request) và đầu ra (Response) bằng Pydantic.

```python
# app/models/schemas/ai_agent.py
from typing import Optional, List
from pydantic import BaseModel, Field

# 1. Cấu trúc tin nhắn lịch sử (Multi-turn)
class ChatMessage(BaseModel):
    role: str       # "user" hoặc "assistant"
    content: str    # Nội dung tin nhắn

# 2. Cấu trúc Client gửi lên
class ChatRequest(BaseModel):
    message: str                                    # Câu hỏi hiện tại
    history: Optional[List[ChatMessage]] = []       # Lịch sử hội thoại
    user_id: Optional[int] = None
    model: Optional[str] = "gemini-3.1-flash-lite"  # Model chỉ định

# 3. Cấu trúc Backend trả về
class ChatResponse(BaseModel):
    reply: str
    action_taken: Optional[str] = None
    model_used: Optional[str] = None
    data_source: Optional[str] = None
```

---

### BƯỚC 2: CHUẨN BỊ DỮ LIỆU THỰC TẾ (DATA GROUNDING / CONTEXT)
Nằm tại: `app/service/chatBotSvc.py` -> hàm `build_campus_context_from_db(session)`

**Tại sao cần bước này?**
Mô hình AI lớn (LLM) bên ngoài không hề biết trường của bạn có bao nhiêu phòng hay hôm nay ai đang học. Ta phải truy vấn database nội bộ và tóm tắt thành dạng văn bản ngắn gọn để đưa vào làm ngữ cảnh cho AI.

```python
def build_campus_context_from_db(session: Session) -> str:
    # 1. Đọc danh sách phòng học
    rooms = session.exec(select(Phong).where(Phong.da_xoa == False)).all()
    rooms_text = "\n".join([f"- Phòng {r.ma_phong}: {r.loai_phong}, {r.suc_chua} chỗ" for r in rooms])

    # 2. Đọc lịch học hôm nay
    today = date.today()
    schedules = session.exec(select(LichPhong).where(LichPhong.ngay == today)).all()
    schedules_text = "\n".join([f"- Phòng {s.ma_phong} bận Ca {s.ca}" for s in schedules])

    # 3. Đóng gói thành văn bản ngữ cảnh
    return f"""
    [DỮ LIỆU CAMPUS HÔM NAY]:
    - Danh sách phòng: {rooms_text}
    - Lịch học: {schedules_text}
    """
```

---

### BƯỚC 3: THIẾT KẾ SYSTEM PROMPT (LUẬT ỨNG XỬ CHO AI)
Nằm tại: `app/service/chatBotSvc.py` -> biến `CAMPUS_SYSTEM_PROMPT`

Prompt là "bản hợp đồng" bắt buộc AI phải tuân thủ:
1. **Vai trò**: Trợ lý AI Điều Hành Smart Campus.
2. **Quy tắc độ dài**: Hỏi đâu đáp đó, tối đa 1-3 câu, cấm chào hỏi rườm rà, cấm lặp lại câu hỏi.
3. **Tính chính trực**: Chỉ dựa vào dữ liệu thực tế được cấp, không bịa đặt phòng học không tồn tại.

---

### BƯỚC 4: KẾT NỐI VỚI MÔ HÌNH AI NGOÀI (GEMINI / OPENAI SDK)
Nằm tại: `app/service/chatBotSvc.py` -> hàm `call_gemini`

Sử dụng thư viện chính thức `google-genai` kèm cơ chế **Fallback thông minh**:

```python
from google import genai
from google.genai import types

def call_gemini(contents, requested_model="gemini-3.1-flash-lite"):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Danh sách thử lần lượt: Model yêu cầu -> Các model dự phòng
    candidates = [requested_model, "gemini-3.5-flash-lite", "gemini-2.5-flash"]
    
    for model_name in candidates:
        try:
            print(f"[Gemini API] Dang goi model {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=CAMPUS_SYSTEM_PROMPT,
                    temperature=0.2 # Nhiệt độ thấp = câu trả lời chính xác, súc tích
                )
            )
            if response and response.text:
                return response.text.strip(), model_name
        except Exception as e:
            # Nếu model nghẽn hoặc hết hạn mức quota, tự nhảy sang model kế tiếp
            print(f"Lỗi {model_name}, thử model tiếp theo...")
            continue
```

---

## ⚡ 3. CÁC KỸ THUẬT TỐI ƯU HÓA QUAN TRỌNG ĐÃ ÁP DỤNG

### 1. Lazy Loading & In-Memory Cache (Tránh lặp query DB)
* **Vấn đề**: Mỗi lần user chat 1 câu mà lại chạy `SELECT *` đọc toàn bộ database thì hệ thống sẽ rất chậm và tốn tài nguyên.
* **Giải pháp**: Thiết kế class `CampusContextCache` lưu dữ liệu vào RAM:
  - **Lần đầu tiên**: Đọc Database 1 lần và nạp vào RAM (`was_lazy_loaded = True`).
  - **Từ lần 2 trở đi**: Lấy thẳng từ RAM gửi cho AI (thời gian truy xuất = **0ms**).
  - Có thời gian sống TTL (mặc định 10 phút tự làm mới 1 lần).

### 2. Thread-Safe Double Checked Locking
* Dùng `threading.Lock()` bọc lấy cache. Khi có 10 người cùng chat ở giây đầu tiên, chỉ duy nhất 1 luồng được đọc Database, 9 luồng còn lại chờ và dùng ngay kết quả trong RAM (tránh nghẽn DB / Cache Stampede).

### 3. Cache Invalidation Hook (Xóa Cache khi có dữ liệu mới)
* Khi có người đặt phòng thành công (`bookingService.create_schedule`) hoặc Admin bấm duyệt đơn mượn:
  - Tự động gọi `campus_cache.invalidate()`.
  - Cache cũ bị hủy ngay lập tức ➔ Đảm bảo AI luôn trả lời đúng lịch học mới nhất, không báo sót phòng đã bị người khác mượn.

### 4. Multi-turn Chat History (Ghi nhớ cuộc trò chuyện)
* Client gửi kèm mảng `history`. Backend chuyển đổi thành các block `types.Content(role="user"/"model")` gửi cho Gemini.
* Nhờ đó khi hỏi *"Tìm phòng A101"* rồi hỏi tiếp *"Phòng đó có máy chiếu không?"*, AI vẫn hiểu *"Phòng đó"* là phòng A101.

---

## 🚀 4. NẾU MUỐN ĐỔI SANG OPENAI HOẶC DEEPSEEK THÌ SAO?

Nhờ cấu trúc chia tầng chuẩn hóa, bạn **không cần sửa lại Router hay Database**. Bạn chỉ cần thay thế đúng hàm `call_gemini` trong file `app/service/chatBotSvc.py`:

```python
# Ví dụ chuyển sang OpenAI:
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": CAMPUS_SYSTEM_PROMPT},
        *history_messages,
        {"role": "user", "content": full_prompt}
    ]
)
return response.choices[0].message.content, "gpt-4o-mini"
```

---

## 📂 5. BẢN ĐỒ CÁC FILE LIÊN QUAN TRONG PROJECT

| Đường dẫn file | Vai trò trong hệ thống |
| :--- | :--- |
| [app/models/schemas/ai_agent.py](file:///d:/Smart-campus/Smart-campus-backEnd/app/models/schemas/ai_agent.py) | Khung Pydantic (`ChatRequest`, `ChatResponse`, `ChatMessage`) |
| [app/models/schemas/__init__.py](file:///d:/Smart-campus/Smart-campus-backEnd/app/models/schemas/__init__.py) | Export gom toàn bộ Schemas dùng chung |
| [app/routers/ai_agent.py](file:///d:/Smart-campus/Smart-campus-backEnd/app/routers/ai_agent.py) | API tiếp nhận Request (`POST /api/ai/chat`, `GET /api/ai/analize`) |
| [app/service/chatBotSvc.py](file:///d:/Smart-campus/Smart-campus-backEnd/app/service/chatBotSvc.py) | **"Bộ não"**: System Prompt, Cache, Logic RAG và gọi Gemini SDK |
| [app/service/bookingService.py](file:///d:/Smart-campus/Smart-campus-backEnd/app/service/bookingService.py) | Chứa Hook tự động xóa cache khi có người mượn phòng mới |
| [app/service/roomService.py](file:///d:/Smart-campus/Smart-campus-backEnd/app/service/roomService.py) | Chứa Hook tự động xóa cache khi thêm/sửa/xóa phòng học |
