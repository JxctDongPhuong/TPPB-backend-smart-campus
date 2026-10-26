from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.database import get_session
from app.models import (
    ThietBiCreate, ThietBiCreateBatch, ThietBiRead,
    PhieuBaoHongCreate, PhieuBaoHongRead, PhieuBaoHongUpdate
)
from app.service import deviceService

router = APIRouter(prefix="/devices", tags=["Thiết Bị & Báo Hỏng"])

# ==================== 1. THIẾT BỊ ====================

@router.get("/", response_model=List[ThietBiRead], summary="Lấy danh sách thiết bị")
def get_all_devices(
    ma_phong: Optional[str] = Query(None, description="Lọc theo phòng (hoặc để trống = trong kho)"),
    ma_loai: Optional[str] = Query(None, description="Lọc theo loại thiết bị (MAYLANH, QUAT...)"),
    tinh_trang: Optional[str] = Query(None, description="Tốt / Hỏng / Đang sửa / Thanh lý"),
    session: Session = Depends(get_session)
):
    return deviceService.get_devices(session, ma_phong=ma_phong, ma_loai=ma_loai, tinh_trang=tinh_trang)

@router.post("/", response_model=ThietBiRead, status_code=status.HTTP_201_CREATED, summary="Thêm một thiết bị đơn lẻ")
def create_device(data: ThietBiCreate, session: Session = Depends(get_session)):
    return deviceService.create_device(session, data)

@router.post("/batch", response_model=List[ThietBiRead], status_code=status.HTTP_201_CREATED, summary="Tự động sinh thiết bị hàng loạt theo lô")
def create_devices_batch(batch: ThietBiCreateBatch, session: Session = Depends(get_session)):
    return deviceService.create_devices_batch(session, batch)

# ==================== 2. PHIẾU BÁO HỎNG ====================

@router.get("/reports", response_model=List[PhieuBaoHongRead], summary="Danh sách phiếu báo hỏng")
def get_reports(
    trang_thai: Optional[str] = Query(None, description="Moi / DangXuLy / DaXuLy / TuChoi"),
    session: Session = Depends(get_session)
):
    return deviceService.get_reports(session, trang_thai=trang_thai)

@router.post("/reports", response_model=PhieuBaoHongRead, status_code=status.HTTP_201_CREATED, summary="Gửi phiếu báo hỏng thiết bị")
def submit_report(
    data: PhieuBaoHongCreate,
    ma_tk_nguoi_bao: int = Query(..., description="Mã tài khoản người báo"),
    session: Session = Depends(get_session)
):
    return deviceService.submit_report(session, data, ma_tk_nguoi_bao)

@router.put("/reports/{ma_phieu}", response_model=PhieuBaoHongRead, summary="Admin cập nhật tiến độ xử lý báo hỏng")
def update_report(
    ma_phieu: int,
    update_data: PhieuBaoHongUpdate,
    session: Session = Depends(get_session)
):
    return deviceService.update_report(session, ma_phieu, update_data)
