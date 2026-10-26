from datetime import date, datetime
from typing import List, Optional
from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import (
    LichPhong, LichPhongCreate,
    YeuCauMuon, YeuCauMuonCreate, YeuCauMuonDuyet
)

# ==================== LỊCH PHÒNG ====================

def get_schedules(
    session: Session,
    ma_phong: Optional[str] = None,
    ngay: Optional[date] = None
) -> List[LichPhong]:
    query = select(LichPhong)
    if ma_phong:
        query = query.where(LichPhong.ma_phong == ma_phong)
    if ngay:
        query = query.where(LichPhong.ngay == ngay)
    return session.exec(query).all()

def create_schedule(session: Session, schedule_data: LichPhongCreate) -> LichPhong:
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
    
    # Xóa cache để AI cập nhật lịch mới ngay lập tức
    from app.service.chatBotSvc import campus_cache
    campus_cache.invalidate()
    
    return db_schedule

# ==================== YÊU CẦU MƯỢN PHÒNG ====================

def get_booking_requests(
    session: Session,
    trang_thai: Optional[str] = None
) -> List[YeuCauMuon]:
    query = select(YeuCauMuon)
    if trang_thai:
        query = query.where(YeuCauMuon.trang_thai == trang_thai)
    return session.exec(query).all()

def submit_booking_request(
    session: Session,
    request_data: YeuCauMuonCreate,
    ma_tk_nguoi_gui: int
) -> YeuCauMuon:
    # Kiểm tra xem phòng ca đó đã có lịch học/lịch mượn chưa
    da_co_lich = session.exec(
        select(LichPhong).where(
            LichPhong.ma_phong == request_data.ma_phong,
            LichPhong.ngay == request_data.ngay,
            LichPhong.ca == request_data.ca
        )
    ).first()
    
    if da_co_lich:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phòng đã có lịch học hoặc đã có người mượn ca này!"
        )

    db_request = YeuCauMuon(
        ma_tk=ma_tk_nguoi_gui,
        ma_phong=request_data.ma_phong,
        ngay=request_data.ngay,
        ca=request_data.ca,
        so_nguoi=request_data.so_nguoi,
        muc_dich=request_data.muc_dich,
        ghi_chu=request_data.ghi_chu,
        trang_thai="ChoDuyet",
        ngay_gui=datetime.utcnow()
    )
    session.add(db_request)
    session.commit()
    session.refresh(db_request)
    return db_request

def process_booking_request(
    session: Session,
    ma_yc: int,
    action: YeuCauMuonDuyet,
    ma_tk_admin: int
) -> YeuCauMuon:
    db_request = session.get(YeuCauMuon, ma_yc)
    if not db_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy yêu cầu mượn")

    if db_request.trang_thai != "ChoDuyet":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Yêu cầu này đã được xử lý trước đó")

    if action.trang_thai == "DaDuyet":
        # Kiểm tra trùng lịch trước khi duyệt
        da_co_lich = session.exec(
            select(LichPhong).where(
                LichPhong.ma_phong == db_request.ma_phong,
                LichPhong.ngay == db_request.ngay,
                LichPhong.ca == db_request.ca
            )
        ).first()
        if da_co_lich:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trùng lịch! Phòng này đã được cấp cho người khác")

        # Tự động tạo 1 dòng mới trong LichPhong
        new_schedule = LichPhong(
            ma_phong=db_request.ma_phong,
            ngay=db_request.ngay,
            ca=db_request.ca,
            loai="MUON",
            noi_dung=f"Mượn: {db_request.muc_dich}",
            so_nguoi=db_request.so_nguoi,
            ma_yc=db_request.ma_yc
        )
        session.add(new_schedule)

    db_request.trang_thai = action.trang_thai
    db_request.nguoi_duyet = ma_tk_admin
    db_request.ngay_duyet = datetime.utcnow()
    if action.ghi_chu:
        db_request.ghi_chu = action.ghi_chu

    session.add(db_request)
    session.commit()
    session.refresh(db_request)

    # Xóa cache nếu duyệt mượn phòng thành công
    if action.trang_thai == "DaDuyet":
        from app.service.chatBotSvc import campus_cache
        campus_cache.invalidate()

    return db_request
