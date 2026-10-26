import logging
from datetime import date
from typing import Optional, Dict, Any, List
from sqlmodel import Session, select, func

from app.models import Phong, LichPhong

logger = logging.getLogger("smart_campus.tools.room")

def tim_phong_trong(
    session: Session,
    ngay: Optional[str] = None,
    ca: Optional[int] = None,
    loai_phong: Optional[str] = None,
    suc_chua_toi_thieu: Optional[int] = None
) -> Dict[str, Any]:
    """
    Tra cứu danh sách phòng học còn trống theo ngày, ca học, loại phòng hoặc sức chứa.
    Dùng khi người dùng hỏi tìm phòng trống, mượn phòng học nhóm, tìm phòng máy tính, hội trường.
    """
    try:
        # Kiểm tra xem hệ thống đã có dữ liệu phòng chưa
        total_rooms = session.exec(select(func.count(Phong.ma_phong)).where(Phong.da_xoa == False)).one()
        if total_rooms == 0:
            return {
                "status": "no_data",
                "message": "Cơ sở dữ liệu hệ thống hiện tại chưa có dữ liệu phòng học nào được khởi tạo.",
                "danh_sach_phong": []
            }

        target_date = date.fromisoformat(ngay) if ngay else date.today()
        
        # 1. Lọc danh sách phòng theo tiêu chí loại phòng & sức chứa
        query_rooms = select(Phong).where(Phong.da_xoa == False)
        if loai_phong:
            query_rooms = query_rooms.where(Phong.loai_phong.ilike(f"%{loai_phong}%"))
        if suc_chua_toi_thieu:
            query_rooms = query_rooms.where(Phong.suc_chua >= suc_chua_toi_thieu)
            
        all_candidate_rooms = session.exec(query_rooms).all()
        if not all_candidate_rooms:
            return {
                "status": "not_found",
                "message": f"Không có phòng nào phù hợp với yêu cầu (Loại: {loai_phong or 'Bất kỳ'}, Sức chứa >= {suc_chua_toi_thieu or 0}).",
                "danh_sach_phong": []
            }

        # 2. Tìm các phòng đã có lịch học vào ngày và ca đó
        query_occupied = select(LichPhong.ma_phong).where(LichPhong.ngay == target_date)
        if ca is not None:
            query_occupied = query_occupied.where(LichPhong.ca == ca)
            
        occupied_room_ids = set(session.exec(query_occupied).all())

        # 3. Lọc ra các phòng trống
        available_rooms = [
            {
                "ma_phong": r.ma_phong,
                "loai_phong": r.loai_phong,
                "toa": r.toa,
                "tang": r.tang,
                "suc_chua": r.suc_chua,
                "trang_thai": r.trang_thai
            }
            for r in all_candidate_rooms
            if r.ma_phong not in occupied_room_ids and r.trang_thai != "Bảo trì"
        ]

        if not available_rooms:
            return {
                "status": "occupied",
                "message": f"Vào ngày {target_date}{f' Ca {ca}' if ca else ''}, toàn bộ phòng phù hợp đều đã kín lịch.",
                "danh_sach_phong": []
            }

        return {
            "status": "success",
            "ngay": str(target_date),
            "ca": ca,
            "tong_so_phong_trong": len(available_rooms),
            "danh_sach_phong": available_rooms[:10], # Trả về tối đa 10 phòng tiêu biểu
            "message": f"Tìm thấy {len(available_rooms)} phòng trống phù hợp."
        }
    except Exception as e:
        logger.error(f"[Tool tim_phong_trong Error]: {e}")
        return {
            "status": "error",
            "message": f"Lỗi trong quá trình tra cứu phòng trống: {str(e)}",
            "danh_sach_phong": []
        }

def tra_cuu_lich_phong(
    session: Session,
    ma_phong: str,
    ngay: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tra cứu chi tiết lịch học/hoạt động của một phòng cụ thể trong ngày hoặc sắp tới.
    """
    try:
        room = session.get(Phong, ma_phong)
        if not room:
            return {
                "status": "not_found",
                "message": f"Phòng '{ma_phong}' không tồn tại trong hệ thống."
            }

        target_date = date.fromisoformat(ngay) if ngay else date.today()
        query = select(LichPhong).where(
            LichPhong.ma_phong == ma_phong,
            LichPhong.ngay >= target_date
        ).order_by(LichPhong.ngay, LichPhong.ca)

        schedules = session.exec(query).all()
        if not schedules:
            return {
                "status": "empty",
                "message": f"Phòng {ma_phong} hiện tại chưa có lịch học nào từ ngày {target_date} trở đi.",
                "danh_sach_lich": []
            }

        return {
            "status": "success",
            "ma_phong": ma_phong,
            "loai_phong": room.loai_phong,
            "danh_sach_lich": [
                {
                    "ngay": str(s.ngay),
                    "ca": s.ca,
                    "loai": s.loai,
                    "noi_dung": s.noi_dung,
                    "so_nguoi": s.so_nguoi
                }
                for s in schedules[:8]
            ]
        }
    except Exception as e:
        logger.error(f"[Tool tra_cuu_lich_phong Error]: {e}")
        return {
            "status": "error",
            "message": f"Lỗi tra cứu lịch phòng {ma_phong}: {str(e)}"
        }
