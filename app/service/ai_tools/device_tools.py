import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlmodel import Session, select, func

from app.models import ThietBi, PhieuBaoHong, Phong

logger = logging.getLogger("smart_campus.tools.device")

def tra_cuu_thiet_bi_hong(
    session: Session,
    ma_phong: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tra cứu danh sách các thiết bị hoặc phòng học đang có phiếu báo hỏng, sự cố chờ sửa chữa.
    Dùng khi người dùng hỏi thiết bị hỏng, điều hòa hỏng, máy chiếu hỏng, tình hình bảo trì.
    """
    try:
        # Kiểm tra xem có thiết bị nào trong DB không
        total_devices = session.exec(select(func.count(ThietBi.ma_tb))).one()
        if total_devices == 0:
            return {
                "status": "no_data",
                "message": "Cơ sở dữ liệu chưa có danh sách thiết bị nào được lưu.",
                "danh_sach_hong": []
            }

        query = select(PhieuBaoHong).where(PhieuBaoHong.trang_thai != "Đã xử lý")
        if ma_phong:
            query = query.where(PhieuBaoHong.ma_phong == ma_phong)

        tickets = session.exec(query).all()
        if not tickets:
            return {
                "status": "empty",
                "message": f"Hiện tại không có thiết bị nào đang báo hỏng{f' tại phòng {ma_phong}' if ma_phong else ' trong toàn trường'}.",
                "danh_sach_hong": []
            }

        return {
            "status": "success",
            "tong_so_su_co": len(tickets),
            "danh_sach_hong": [
                {
                    "ma_phieu": t.ma_phieu,
                    "ma_phong": t.ma_phong,
                    "ma_tb": t.ma_tb,
                    "mo_ta": t.mo_ta,
                    "trang_thai": t.trang_thai,
                    "ngay_bao": str(t.ngay_bao)
                }
                for t in tickets[:10]
            ],
            "message": f"Tìm thấy {len(tickets)} phiếu báo hỏng đang chờ xử lý."
        }
    except Exception as e:
        logger.error(f"[Tool tra_cuu_thiet_bi_hong Error]: {e}")
        return {
            "status": "error",
            "message": f"Lỗi khi tra cứu thiết bị hỏng: {str(e)}",
            "danh_sach_hong": []
        }

def tao_phieu_bao_hong(
    session: Session,
    ma_phong: str,
    mo_ta_loi: str,
    muc_do_uu_tien: str = "Trung bình",
    ma_tb: Optional[int] = None,
    ma_tk: int = 1
) -> Dict[str, Any]:
    """
    Tạo nhanh phiếu báo hỏng thiết bị hoặc sự cố phòng học để đội bảo trì tiếp nhận.
    Dùng khi người dùng yêu cầu báo hỏng máy chiếu, điều hòa, bóng đèn hỏng...
    """
    try:
        # Kiểm tra phòng có tồn tại không
        room = session.get(Phong, ma_phong)
        if not room:
            return {
                "status": "error",
                "message": f"Không tìm thấy phòng {ma_phong} trong hệ thống để tạo phiếu báo hỏng."
            }

        new_ticket = PhieuBaoHong(
            ma_phong=ma_phong,
            ma_tb=str(ma_tb) if ma_tb else None,
            mo_ta=mo_ta_loi,
            trang_thai="Moi",
            ma_tk=ma_tk,
            ngay_bao=datetime.now(timezone.utc)
        )
        session.add(new_ticket)
        session.commit()
        session.refresh(new_ticket)

        return {
            "status": "success",
            "ma_phieu": new_ticket.ma_phieu,
            "ma_phong": ma_phong,
            "mo_ta": mo_ta_loi,
            "message": f"Đã tạo thành công phiếu báo hỏng #{new_ticket.ma_phieu} cho phòng {ma_phong}. Đội kỹ thuật sẽ tiếp nhận xử lý."
        }
    except Exception as e:
        session.rollback()
        logger.error(f"[Tool tao_phieu_bao_hong Error]: {e}")
        return {
            "status": "error",
            "message": f"Không thể tạo phiếu báo hỏng: {str(e)}"
        }
