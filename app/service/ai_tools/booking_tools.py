import logging
from datetime import date
from typing import Optional, Dict, Any
from sqlmodel import Session, select

from app.models import Phong, LichPhong, YeuCauMuon, TaiKhoan

logger = logging.getLogger("smart_campus.tools.booking")

def kiem_tra_kha_dung_dat_phong(
    session: Session,
    ma_phong: str,
    ngay: str,
    ca: int
) -> Dict[str, Any]:
    """
    Kiểm tra xem một phòng học có thể đặt/mượn vào ngày và ca học cụ thể hay không.
    Dùng khi người dùng muốn kiểm tra trước khi đặt phòng.
    """
    try:
        clean_room = ma_phong.replace("Phòng ", "").replace("phòng ", "").strip()
        room = session.get(Phong, clean_room)
        if not room:
            return {
                "status": "not_found",
                "kha_dung": False,
                "message": f"Phòng {clean_room} không tồn tại trong hệ thống."
            }

        if room.trang_thai == "Bảo trì":
            return {
                "status": "maintenance",
                "kha_dung": False,
                "message": f"Phòng {clean_room} đang trong diện bảo trì, tạm thời không thể sử dụng."
            }

        target_date = date.fromisoformat(ngay)

        # Kiểm tra lịch học chính khóa
        schedule = session.exec(
            select(LichPhong).where(
                LichPhong.ma_phong == clean_room,
                LichPhong.ngay == target_date,
                LichPhong.ca == ca
            )
        ).first()

        if schedule:
            return {
                "status": "busy",
                "kha_dung": False,
                "message": f"Phòng {clean_room} đã có lịch học ({schedule.ten_mon_hoc}) vào Ca {ca} ngày {target_date}."
            }

        # Kiểm tra đơn mượn phòng đã duyệt
        existing_booking = session.exec(
            select(YeuCauMuon).where(
                YeuCauMuon.ma_phong == clean_room,
                YeuCauMuon.ngay == target_date,
                YeuCauMuon.ca == ca,
                (YeuCauMuon.trang_thai == "DaDuyet") | (YeuCauMuon.trang_thai == "Đã duyệt")
            )
        ).first()

        if existing_booking:
            return {
                "status": "booked",
                "kha_dung": False,
                "message": f"Phòng {clean_room} đã được duyệt cho người khác mượn vào Ca {ca} ngày {target_date}."
            }

        return {
            "status": "available",
            "kha_dung": True,
            "ma_phong": clean_room,
            "loai_phong": room.loai_phong,
            "ngay": str(target_date),
            "ca": ca,
            "message": f"Phòng {clean_room} hoàn toàn trống và sẵn sàng để đăng ký mượn vào Ca {ca} ngày {target_date}."
        }
    except Exception as e:
        logger.error(f"[Tool kiem_tra_kha_dung_dat_phong Error]: {e}")
        return {
            "status": "error",
            "kha_dung": False,
            "message": f"Lỗi kiểm tra khả dụng phòng: {str(e)}"
        }

def tao_yeu_cau_muon_phong(
    session: Session,
    ma_phong: str,
    ngay: str,
    ca: int,
    ly_do: str,
    so_nguoi: Optional[int] = 30,
    ma_tk: int = 1
) -> Dict[str, Any]:
    """
    Tạo đơn đăng ký mượn phòng học gửi tới Ban Quản lý duyệt.
    Cho phép nếu là tài khoản Admin hoặc Giảng viên (Giáo viên).
    """
    try:
        clean_room = ma_phong.replace("Phòng ", "").replace("phòng ", "").strip()

        # Kiểm tra vai trò tài khoản: Chỉ Admin hoặc Giảng viên mới được duyệt tạo yêu cầu mượn phòng
        acc = session.get(TaiKhoan, ma_tk)
        if acc:
            role_lower = (acc.vai_tro or "").lower()
            allowed = any(r in role_lower for r in ["admin", "quản lý", "giảng viên", "giáo viên"])
            if not allowed:
                return {
                    "status": "permission_denied",
                    "message": f"Tài khoản {acc.ho_ten} ({acc.vai_tro}) không được phép tạo đơn mượn phòng qua Nexus AI. Chỉ tài khoản Giảng viên hoặc Admin mới có quyền gửi yêu cầu mượn phòng."
                }

        check = kiem_tra_kha_dung_dat_phong(session, clean_room, ngay, ca)
        if not check.get("kha_dung", False):
            return {
                "status": "rejected",
                "message": f"Không thể tạo đơn mượn: {check.get('message')}"
            }

        target_date = date.fromisoformat(ngay)
        new_request = YeuCauMuon(
            ma_tk=ma_tk or 1,
            ma_phong=clean_room,
            ngay=target_date,
            ca=ca,
            so_nguoi=so_nguoi or 30,
            muc_dich=ly_do or "Mượn phòng giảng dạy / học tập qua Nexus AI",
            trang_thai="ChoDuyet"
        )
        session.add(new_request)
        session.commit()
        session.refresh(new_request)

        user_label = f"bởi {acc.ho_ten} ({acc.vai_tro})" if acc else "thành công"
        return {
            "status": "success",
            "ma_yc": new_request.ma_yc,
            "ma_phong": clean_room,
            "ngay_muon": str(target_date),
            "ca": ca,
            "message": f"Đã gửi đơn mượn phòng {clean_room} (Mã đơn #{new_request.ma_yc}) cho Ca {ca} ngày {target_date} {user_label}. Đơn đã được chuyển tới Ban Quản trị CSVC để phê duyệt."
        }
    except Exception as e:
        session.rollback()
        logger.error(f"[Tool tao_yeu_cau_muon_phong Error]: {e}")
        return {
            "status": "error",
            "message": f"Lỗi tạo đơn mượn phòng: {str(e)}"
        }
