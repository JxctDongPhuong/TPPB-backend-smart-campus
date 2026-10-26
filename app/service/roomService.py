from typing import List, Optional
from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import (
    Phong, PhongCreate, PhongUpdate, CoSo
)

# Re-export các hàm Thiết bị & Báo hỏng từ deviceService để tương thích ngược 100%
from .deviceService import (
    get_devices, create_device, create_devices_batch,
    get_reports, submit_report, update_report
)

# ==================== PHÒNG HỌC ====================

def get_rooms(
    session: Session,
    ma_cs: Optional[str] = None,
    toa: Optional[str] = None,
    tang: Optional[int] = None,
    loai_phong: Optional[str] = None
) -> List[Phong]:
    """
    Tra cứu danh sách phòng học theo cơ sở, tòa, tầng hoặc loại phòng.
    """
    query = select(Phong).where(Phong.da_xoa == False)
    if ma_cs:
        query = query.where(Phong.ma_cs == ma_cs)
    if toa:
        query = query.where(Phong.toa == toa)
    if tang is not None:
        query = query.where(Phong.tang == tang)
    if loai_phong:
        query = query.where(Phong.loai_phong == loai_phong)
    return session.exec(query).all()

def get_room_by_id(session: Session, ma_phong: str) -> Phong:
    """
    Lấy thông tin chi tiết một phòng học theo mã phòng.
    """
    phong = session.get(Phong, ma_phong)
    if not phong or phong.da_xoa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy phòng học")
    return phong

def create_room(session: Session, room_data: PhongCreate) -> Phong:
    """
    Tạo mới một phòng học trong hệ thống kèm kiểm tra và gợi ý tham số.
    """
    # 1. Kiểm tra trùng mã phòng
    existing = session.get(Phong, room_data.ma_phong)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Duplicate parameter 'ma_phong'",
                "message": f"Mã phòng '{room_data.ma_phong}' đã tồn tại.",
                "recommendation": "Vui lòng chọn một mã phòng khác chưa được sử dụng."
            }
        )
    
    # 2. Kiểm tra mã cơ sở có tồn tại không
    coso = session.get(CoSo, room_data.ma_cs)
    if not coso:
        valid_cs = [c.ma_cs for c in session.exec(select(CoSo)).all()]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Wrong parameter 'ma_cs'",
                "value_received": room_data.ma_cs,
                "message": f"Mã cơ sở '{room_data.ma_cs}' không tồn tại trong hệ thống.",
                "recommendation": f"Vui lòng chọn một trong các mã cơ sở hợp lệ hiện có: {valid_cs}, hoặc tạo mới cơ sở '{room_data.ma_cs}' trước."
            }
        )
    
    try:
        db_room = Phong.model_validate(room_data)
        session.add(db_room)
        session.commit()
        session.refresh(db_room)
        return db_room
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Database error",
                "message": "Không thể lưu dữ liệu phòng vào database.",
                "recommendation": str(e)
            }
        )

def update_room(session: Session, ma_phong: str, room_data: PhongUpdate) -> Phong:
    """
    Cập nhật thông tin phòng học.
    """
    db_room = get_room_by_id(session, ma_phong)

    # Nếu cập nhật ma_cs, kiểm tra tồn tại
    if room_data.ma_cs is not None:
        coso = session.get(CoSo, room_data.ma_cs)
        if not coso:
            valid_cs = [c.ma_cs for c in session.exec(select(CoSo)).all()]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Wrong parameter 'ma_cs'",
                    "value_received": room_data.ma_cs,
                    "message": f"Mã cơ sở '{room_data.ma_cs}' không tồn tại trong hệ thống.",
                    "recommendation": f"Vui lòng chọn một trong các mã cơ sở hợp lệ hiện có: {valid_cs}."
                }
            )

    try:
        update_dict = room_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(db_room, key, value)
            
        session.add(db_room)
        session.commit()
        session.refresh(db_room)
        return db_room
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Database error",
                "message": "Lỗi khi cập nhật phòng.",
                "recommendation": str(e)
            }
        )

def delete_room(session: Session, ma_phong: str) -> dict:
    """
    Đánh dấu xóa mềm (soft-delete) phòng học.
    """
    db_room = get_room_by_id(session, ma_phong)
    db_room.da_xoa = True
    session.add(db_room)
    session.commit()
    return {"message": f"Đã xóa phòng {ma_phong} thành công"}
