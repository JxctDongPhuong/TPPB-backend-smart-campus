from typing import List, Optional
from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import (
    Phong, PhongCreate, PhongUpdate
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
    Tạo mới một phòng học trong hệ thống.
    """
    existing = session.get(Phong, room_data.ma_phong)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mã phòng đã tồn tại")
    
    db_room = Phong.model_validate(room_data)
    session.add(db_room)
    session.commit()
    session.refresh(db_room)
    return db_room

def update_room(session: Session, ma_phong: str, room_data: PhongUpdate) -> Phong:
    """
    Cập nhật thông tin phòng học.
    """
    db_room = get_room_by_id(session, ma_phong)
    update_dict = room_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(db_room, key, value)
        
    session.add(db_room)
    session.commit()
    session.refresh(db_room)
    return db_room

def delete_room(session: Session, ma_phong: str) -> dict:
    """
    Đánh dấu xóa mềm (soft-delete) phòng học.
    """
    db_room = get_room_by_id(session, ma_phong)
    db_room.da_xoa = True
    session.add(db_room)
    session.commit()
    return {"message": f"Đã xóa phòng {ma_phong} thành công"}
