from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

# Handler bắt lỗi toàn vẹn cơ sở dữ liệu (Khóa ngoại, trùng lặp, thiếu trường)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    orig = str(exc.orig) if hasattr(exc, "orig") else str(exc)
    orig_lower = orig.lower()

    if "violates foreign key constraint" in orig_lower or "foreignkeyviolation" in orig_lower:
        error_type = "Wrong Parameter / Foreign Key Error"
        message = "Dữ liệu tham chiếu không tồn tại trong hệ thống (Sai mã khóa ngoại)."
        recommendation = "Vui lòng kiểm tra lại các trường liên kết (như ma_cs, ma_phong, ma_loai, ma_tb) xem đã tồn tại trong danh mục tương ứng chưa."
    elif "violates unique constraint" in orig_lower or "uniqueviolation" in orig_lower:
        error_type = "Duplicate Parameter / Unique Error"
        message = "Dữ liệu đã tồn tại trong hệ thống (Trùng khóa chính hoặc lịch đã có người dùng)."
        recommendation = "Vui lòng kiểm tra lại mã định danh hoặc chọn thời gian/phòng khác không bị trùng."
    elif "violates not-null constraint" in orig_lower or "notnullviolation" in orig_lower:
        error_type = "Missing Parameter / Not-Null Error"
        message = "Thiếu trường dữ liệu bắt buộc."
        recommendation = "Vui lòng kiểm tra lại payload và điền đầy đủ các thông tin bắt buộc theo tài liệu API (/docs)."
    else:
        error_type = "Database Constraint Error"
        message = "Lỗi vi phạm ràng buộc cơ sở dữ liệu."
        recommendation = "Vui lòng kiểm tra lại kiểu dữ liệu và tính hợp lệ của các tham số gửi lên."

    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "error_type": error_type,
            "message": message,
            "recommendation": recommendation,
            "database_detail": orig.split("\n")[0]
        }
    )

def register_exception_handlers(app: FastAPI):
    """Đăng ký toàn bộ exception handlers cho ứng dụng FastAPI"""
    app.add_exception_handler(IntegrityError, integrity_error_handler)
