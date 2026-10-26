import logging
from datetime import date
from typing import Optional, Dict, Any
from sqlmodel import Session, select, func

from app.models import DienNang
from app.service.metricService import detect_waste_energy, get_energy_summary

logger = logging.getLogger("smart_campus.tools.energy")

def kiem_tra_lang_phi_dien(
    session: Session,
    ngay: Optional[str] = None
) -> Dict[str, Any]:
    """
    Phát hiện và cảnh báo các phòng học đang lãng phí điện (Idle Waste).
    Dùng khi người dùng hỏi về lãng phí điện, phòng nào quên tắt điện, thiết bị chạy không có người.
    """
    try:
        # Kiểm tra trước xem DB có dữ liệu điện năng nào không
        total_records = session.exec(select(func.count(DienNang.ma_phong))).one()
        if total_records == 0:
            return {
                "status": "no_data",
                "has_data": False,
                "message": "Cơ sở dữ liệu hệ thống hiện tại chưa có dữ liệu đo đạc chỉ số điện năng nào. Vui lòng nạp hoặc ghi nhận dữ liệu công tơ điện trước khi phân tích lãng phí."
            }

        target_date = date.fromisoformat(ngay) if ngay else date.today()
        result = detect_waste_energy(session, target_date)

        if not result.get("has_data", False):
            return {
                "status": "no_data_for_date",
                "has_data": False,
                "ngay": str(target_date),
                "message": f"Chưa có bản ghi điện năng nào trong ngày {target_date} để phân tích lãng phí."
            }

        return {
            "status": "success",
            "has_data": True,
            "ngay": result["ngay"],
            "tong_so_phong_lang_phi": result["tong_so_phong_lang_phi"],
            "danh_sach_canh_bao": result["danh_sach_canh_bao"],
            "message": result["thong_bao"]
        }
    except Exception as e:
        logger.error(f"[Tool kiem_tra_lang_phi_dien Error]: {e}")
        return {
            "status": "error",
            "has_data": False,
            "message": f"Lỗi khi kiểm tra lãng phí điện: {str(e)}"
        }

def tra_cuu_tong_quan_dien(
    session: Session,
    tu_ngay: Optional[str] = None,
    den_ngay: Optional[str] = None
) -> Dict[str, Any]:
    """
    Xem tổng hợp mức tiêu thụ điện năng toàn trường (tổng số kWh, trung bình phòng).
    Dùng khi người dùng hỏi tổng tiền điện, tổng số điện tiêu thụ, thống kê kWh.
    """
    try:
        start_date = date.fromisoformat(tu_ngay) if tu_ngay else None
        end_date = date.fromisoformat(den_ngay) if den_ngay else None

        result = get_energy_summary(session, tu_ngay=start_date, den_ngay=end_date)
        if not result.get("has_data", False):
            return {
                "status": "no_data",
                "has_data": False,
                "message": "Hệ thống chưa ghi nhận bất kỳ dữ liệu tiêu thụ điện nào trong khoảng thời gian này."
            }

        return {
            "status": "success",
            "has_data": True,
            "tong_kwh": result["tong_kwh"],
            "so_ban_ghi": result["so_ban_ghi"],
            "trung_binh_kwh_moi_phong": result["trung_binh_kwh_moi_phong"],
            "message": result["thong_bao"]
        }
    except Exception as e:
        logger.error(f"[Tool tra_cuu_tong_quan_dien Error]: {e}")
        return {
            "status": "error",
            "has_data": False,
            "message": f"Lỗi khi tra cứu tổng quan điện năng: {str(e)}"
        }
