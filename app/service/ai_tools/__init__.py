import logging
import inspect
from typing import Dict, Any, Callable, Optional
from sqlmodel import Session

from .room_tools import tim_phong_trong, tra_cuu_lich_phong
from .energy_tools import kiem_tra_lang_phi_dien, tra_cuu_tong_quan_dien
from .device_tools import tra_cuu_thiet_bi_hong, tao_phieu_bao_hong
from .booking_tools import kiem_tra_kha_dung_dat_phong, tao_yeu_cau_muon_phong
from .formatters import format_tool_response

logger = logging.getLogger("smart_campus.tools")

# Bảng tra cứu các hàm công cụ (Registry)
TOOL_REGISTRY: Dict[str, Callable] = {
    "tim_phong_trong": tim_phong_trong,
    "tra_cuu_lich_phong": tra_cuu_lich_phong,
    "kiem_tra_lang_phi_dien": kiem_tra_lang_phi_dien,
    "tra_cuu_tong_quan_dien": tra_cuu_tong_quan_dien,
    "tra_cuu_thiet_bi_hong": tra_cuu_thiet_bi_hong,
    "tao_phieu_bao_hong": tao_phieu_bao_hong,
    "kiem_tra_kha_dung_dat_phong": kiem_tra_kha_dung_dat_phong,
    "tao_yeu_cau_muon_phong": tao_yeu_cau_muon_phong,
}

# Danh sách Function Declarations tiêu chuẩn cho Gemini SDK
# Mỗi tool mô tả rõ ràng mục đích, tham số để AI tự động chọn đúng tool theo kịch bản
GEMINI_TOOL_DECLARATIONS = [
    {
        "name": "tim_phong_trong",
        "description": "Tra cứu danh sách các phòng học còn trống theo ngày, ca học, loại phòng (ví dụ: 'máy tính', 'lý thuyết') hoặc sức chứa tối thiểu.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "ngay": {"type": "STRING", "description": "Ngày muốn tìm kiếm dạng YYYY-MM-DD. Nếu không truyền, mặc định là hôm nay."},
                "ca": {"type": "INTEGER", "description": "Ca học (từ 1 đến 6)."},
                "loai_phong": {"type": "STRING", "description": "Loại phòng như 'Phòng máy tính', 'Phòng lý thuyết', 'Hội trường'..."},
                "suc_chua_toi_thieu": {"type": "INTEGER", "description": "Số lượng chỗ ngồi tối thiểu cần tìm."}
            }
        }
    },
    {
        "name": "tra_cuu_lich_phong",
        "description": "Tra cứu lịch học chi tiết của một phòng học cụ thể trong ngày hoặc sắp tới.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "ma_phong": {"type": "STRING", "description": "Mã phòng học cần tra cứu (ví dụ: 'A101', 'B203')."},
                "ngay": {"type": "STRING", "description": "Ngày cần tra cứu dạng YYYY-MM-DD."}
            },
            "required": ["ma_phong"]
        }
    },
    {
        "name": "kiem_tra_lang_phi_dien",
        "description": "Phát hiện và cảnh báo các phòng học đang lãng phí điện năng (Idle Waste: có điện tiêu thụ nhưng không có lịch học). Dùng khi hỏi về lãng phí điện, phòng quên tắt điện.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "ngay": {"type": "STRING", "description": "Ngày cần kiểm tra lãng phí dạng YYYY-MM-DD (mặc định hôm nay)."}
            }
        }
    },
    {
        "name": "tra_cuu_tong_quan_dien",
        "description": "Xem thống kê tổng quan điện năng tiêu thụ toàn trường (tổng kWh, số lượt đo, trung bình phòng).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "tu_ngay": {"type": "STRING", "description": "Từ ngày dạng YYYY-MM-DD."},
                "den_ngay": {"type": "STRING", "description": "Đến ngày dạng YYYY-MM-DD."}
            }
        }
    },
    {
        "name": "tra_cuu_thiet_bi_hong",
        "description": "Tra cứu danh sách các thiết bị hoặc phòng học đang bị báo hỏng cần bảo trì, sửa chữa.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "ma_phong": {"type": "STRING", "description": "Lọc theo mã phòng cụ thể nếu có (ví dụ: 'A101')."}
            }
        }
    },
    {
        "name": "tao_phieu_bao_hong",
        "description": "Tạo phiếu báo hỏng thiết bị hoặc sự cố phòng học (ví dụ: máy chiếu hỏng, điều hòa không mát, bóng đèn cháy...).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "ma_phong": {"type": "STRING", "description": "Mã phòng gặp sự cố (ví dụ: 'A201')."},
                "mo_ta_loi": {"type": "STRING", "description": "Mô tả chi tiết sự cố hoặc thiết bị hỏng."},
                "muc_do_uu_tien": {"type": "STRING", "description": "Mức độ ưu tiên: 'Thấp', 'Trung bình', 'Cao'."}
            },
            "required": ["ma_phong", "mo_ta_loi"]
        }
    },
    {
        "name": "kiem_tra_kha_dung_dat_phong",
        "description": "Kiểm tra xem một phòng học có đủ điều kiện để mượn vào ngày và ca học cụ thể không.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "ma_phong": {"type": "STRING", "description": "Mã phòng muốn kiểm tra (ví dụ 'A102')."},
                "ngay": {"type": "STRING", "description": "Ngày muốn mượn YYYY-MM-DD."},
                "ca": {"type": "INTEGER", "description": "Ca học muốn mượn (1-6)."}
            },
            "required": ["ma_phong", "ngay", "ca"]
        }
    },
    {
        "name": "tao_yeu_cau_muon_phong",
        "description": "Gửi đơn mượn phòng học chính thức sau khi người dùng xác nhận muốn đặt phòng.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "ma_phong": {"type": "STRING", "description": "Mã phòng muốn mượn (ví dụ 'A102')."},
                "ngay": {"type": "STRING", "description": "Ngày muốn mượn YYYY-MM-DD."},
                "ca": {"type": "INTEGER", "description": "Ca học (1-6)."},
                "ly_do": {"type": "STRING", "description": "Lý do mượn phòng (học nhóm, hội thảo, thi...)."}
            },
            "required": ["ma_phong", "ngay", "ca", "ly_do"]
        }
    }
]

def execute_ai_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    session: Session,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Dispatcher thực thi Tool được chọn kèm try-catch an toàn tuyệt đối.
    """
    handler = TOOL_REGISTRY.get(tool_name)
    if not handler:
        logger.warning(f"[Tool Dispatcher] Không tìm thấy tool có tên: {tool_name}")
        return {
            "status": "not_implemented",
            "message": f"Chức năng '{tool_name}' chưa được hỗ trợ."
        }

    try:
        # Nếu có user_id và tool yêu cầu/chấp nhận ma_tk, tự động gán
        if user_id is not None:
            sig = inspect.signature(handler)
            if "ma_tk" in sig.parameters and "ma_tk" not in arguments:
                arguments["ma_tk"] = user_id

        logger.info(f"[Tool Execution] Đang chạy tool '{tool_name}' với tham số: {arguments}")
        result = handler(session=session, **arguments)
        return result
    except TypeError as te:
        logger.error(f"[Tool Param Error] Sai tham số khi gọi tool {tool_name}: {te}")
        return {
            "status": "invalid_arguments",
            "message": f"Tham số gọi công cụ không hợp lệ: {str(te)}"
        }
    except Exception as e:
        logger.error(f"[Tool Unexpected Error] Lỗi khi thực thi tool {tool_name}: {e}")
        return {
            "status": "error",
            "message": f"Đã xảy ra lỗi hệ thống khi thực thi công cụ: {str(e)}"
        }
