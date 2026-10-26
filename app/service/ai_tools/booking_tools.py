import logging
from datetime import date
from typing import Optional, Dict, Any
from sqlmodel import Session, select

from app.models import Phong, LichPhong, YeuCauMuon

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
        room = session.get(Phong, ma_phong)
        if not room:
            return {
                "status": "not_found",
                "kha_dung": False,
                "message": f"Phòng {ma_phong} không tồn tại trong hệ thống."
            }

        if room.trang_thai == "Bảo trì":
            return {
                "status": "maintenance",
                "kha_dung": False,
                "message": f"Phòng {ma_phong} đang trong diện bảo trì, tạm thời không thể sử dụng."
            }

        target_date = date.fromisoformat(ngay)

        # Kiểm tra lịch học chính khóa
        schedule = session.exec(
            select(LichPhong).where(
                LichPhong.ma_phong == ma_phong,
                LichPhong.ngay == target_date,
                LichPhong.ca == ca
            )
        ).first()

        if schedule:
            return {
                "status": "busy",
                "kha_dung": False,
                "message": f"Phòng {ma_phong} đã có lịch học ({schedule.ten_mon_hoc}) vào Ca {ca} ngày {target_date}."
            }

        # Kiểm tra đơn mượn phòng đã duyệt
        existing_booking = session.exec(
            select(YeuCauMuon).where(
                YeuCauMuon.ma_phong == ma_phong,
                YeuCauMuon.ngay_muon == target_date,
                YeuCauMuon.ca == ca,
                YeuCauMuon.trang_thai == "Đã duyệt"
            )
        ).first()

        if existing_booking:
            return {
                "status": "booked",
                "kha_dung": False,
                "message": f"Phòng {ma_phong} đã được duyệt cho người khác mượn vào Ca {ca} ngày {target_date}."
            }

        return {
            "status": "available",
            "kha_dung": True,
            "ma_phong": ma_phong,
            "loai_phong": room.loai_phong,
            "ngay": str(target_date),
            "ca": ca,
            "message": f"Phòng {ma_phong} hoàn toàn trống và sẵn sàng để đăng ký mượn vào Ca {ca} ngày {target_date}."
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
    ma_tk: int = 1
) -> Dict[str, Any]:
    """
    Tạo đơn đăng ký mượn phòng học gửi tới Ban Quản lý duyệt.
    Dùng khi người dùng đồng ý mượn phòng sau khi kiểm tra phòng trống.
    """
    try:
        check = kiem_tra_kha_dung_dat_phong(session, ma_phong, ngay, ca)
        if not check.get("kha_dung", False):
            return {
                "status": "rejected",
                "message": f"Không thể tạo đơn mượn: {check.get('message')}"
            }

        target_date = date.fromisoformat(ngay)
        new_request = YeuCauMuon(
            ma_tk=ma_tk,
            ma_phong=ma_phong,
            ngay_muon=target_date,
            ca=ca,
            ly_do=ly_do,
            trang_thai="Chờ duyệt"
        )
        session.add(new_request)
        session.commit()
        session.refresh(new_request)

        return {
            "status": "success",
            "ma_yc": new_request.ma_yc,
            "ma_phong": ma_phong,
            "ngay_muon": str(target_date),
            "ca": ca,
            "message": f"Đã gửi đơn mượn phòng {ma_phong} (Mã đơn #{new_request.ma_yc}) cho Ca {ca} ngày {target_date}. Vui lòng chờ duyệt."
        }
    except Exception as e:
        session.rollback()
        logger.error(f"[Tool tao_yeu_cau_muon_phong Error]: {e}")
        return {
            "status": "error",
            "message": f"Lỗi tạo đơn mượn phòng: {str(e)}"
        }
