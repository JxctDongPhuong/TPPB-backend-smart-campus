from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.database import get_session
from app.models import PhongCreate, PhongRead, PhongUpdate
from app.service import roomService

router = APIRouter(prefix="/rooms", tags=["Phòng Học"])

@router.get("/", response_model=List[PhongRead], summary="Lấy danh sách phòng học")
def get_all_rooms(
    ma_cs: Optional[str] = Query(None, description="Lọc theo mã cơ sở"),
    toa: Optional[str] = Query(None, description="Lọc theo tòa"),
    tang: Optional[int] = Query(None, description="Lọc theo tầng"),
    loai_phong: Optional[str] = Query(None, description="Lọc theo loại phòng"),
    session: Session = Depends(get_session)
):
    return roomService.get_rooms(session, ma_cs=ma_cs, toa=toa, tang=tang, loai_phong=loai_phong)

@router.get("/{ma_phong}", response_model=PhongRead, summary="Lấy thông tin chi tiết một phòng")
def get_room_by_id(ma_phong: str, session: Session = Depends(get_session)):
    return roomService.get_room_by_id(session, ma_phong)

@router.post("/", response_model=PhongRead, status_code=status.HTTP_201_CREATED, summary="Tạo mới phòng học")
def create_room(room_data: PhongCreate, session: Session = Depends(get_session)):
    return roomService.create_room(session, room_data)

@router.put("/{ma_phong}", response_model=PhongRead, summary="Cập nhật thông tin phòng học")
def update_room(ma_phong: str, room_data: PhongUpdate, session: Session = Depends(get_session)):
    return roomService.update_room(session, ma_phong, room_data)

@router.delete("/{ma_phong}", summary="Xóa mềm phòng học")
def delete_room(ma_phong: str, session: Session = Depends(get_session)):
    return roomService.delete_room(session, ma_phong)
