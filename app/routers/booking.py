from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.database import get_session
from app.service import bookingService
from app.models import (
    LichPhong, LichPhongCreate, LichPhongRead,
    YeuCauMuon, YeuCauMuonCreate, YeuCauMuonRead, YeuCauMuonDuyet
)

router = APIRouter(prefix="/booking", tags=["Lịch & Mượn Phòng"])

@router.get("/schedule", response_model=List[LichPhongRead], summary="Tra cứu lịch phòng theo ngày/phòng")
def get_schedules(
    ma_phong: Optional[str] = Query(None, description="Lọc theo phòng"),
    ngay: Optional[date] = Query(None, description="Lọc theo ngày (YYYY-MM-DD)"),
    session: Session = Depends(get_session)
):
    return bookingService.get_schedules(session, ma_phong=ma_phong, ngay=ngay)

@router.post("/schedule", response_model=LichPhongRead, status_code=status.HTTP_201_CREATED, summary="Thêm lịch học chính khóa")
def create_schedule(schedule_data: LichPhongCreate, session: Session = Depends(get_session)):
    # Kiểm tra trùng lịch (ma_phong, ngay, ca)
    existing = session.exec(
        select(LichPhong).where(
            LichPhong.ma_phong == schedule_data.ma_phong,
            LichPhong.ngay == schedule_data.ngay,
            LichPhong.ca == schedule_data.ca
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phòng này trong ca này đã có lịch!")

    db_schedule = LichPhong.model_validate(schedule_data)
    session.add(db_schedule)
    session.commit()
    session.refresh(db_schedule)
    return db_schedule

@router.delete("/schedule/{ma_lich}", summary="Xóa lịch phòng học")
def delete_schedule(ma_lich: int, session: Session = Depends(get_session)):
    return bookingService.delete_schedule(session, ma_lich)

# ==================== 2. YÊU CẦU MƯỢN PHÒNG (YeuCauMuon) ====================

@router.get("/requests", response_model=List[YeuCauMuonRead])
def get_booking_requests(trang_thai: Optional[str] = None, session: Session = Depends(get_session)):
    return bookingService.get_booking_requests(session, trang_thai=trang_thai)

@router.post("/requests", response_model=YeuCauMuonRead)
def submit_booking_request(request_data: YeuCauMuonCreate, ma_tk_nguoi_gui: int, session: Session = Depends(get_session)):
    return bookingService.submit_booking_request(session, request_data, ma_tk_nguoi_gui)

@router.put("/requests/{ma_yc}/process", response_model=YeuCauMuonRead)
def process_booking_request(ma_yc: int, action: YeuCauMuonDuyet, ma_tk_admin: int, session: Session = Depends(get_session)):
    return bookingService.process_booking_request(session, ma_yc, action, ma_tk_admin)
