from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.database import get_session
from app.models import DienNangCreate, DienNangRead
from app.service import metricService

router = APIRouter(prefix="/metrics", tags=["Chỉ Số Điện Năng"])

@router.get("/", response_model=List[DienNangRead], summary="Tra cứu lịch sử tiêu thụ điện theo phòng hoặc ngày")
def get_energy_metrics(
    ma_phong: Optional[str] = Query(None, description="Lọc theo phòng"),
    tu_ngay: Optional[date] = Query(None, description="Từ ngày (YYYY-MM-DD)"),
    den_ngay: Optional[date] = Query(None, description="Đến ngày (YYYY-MM-DD)"),
    session: Session = Depends(get_session)
):
    return metricService.get_energy_metrics(session, ma_phong=ma_phong, tu_ngay=tu_ngay, den_ngay=den_ngay)

@router.post("/", response_model=DienNangRead, status_code=status.HTTP_201_CREATED, summary="Ghi nhận chỉ số điện tiêu thụ theo ngày")
def record_energy_metric(data: DienNangCreate, session: Session = Depends(get_session)):
    return metricService.record_energy_metric(session, data)

@router.get("/waste-alerts", summary="Phát hiện và cảnh báo phòng lãng phí điện (Idle Waste)")
def detect_waste_energy(
    ngay: Optional[date] = Query(default_factory=date.today, description="Ngày cần kiểm tra"),
    nguong_kwh_lang_phi: float = Query(5.0, description="Ngưỡng kWh tiêu thụ bất thường khi không có lịch"),
    session: Session = Depends(get_session)
):
    return metricService.detect_waste_energy(session, ngay=ngay, nguong_kwh_lang_phi=nguong_kwh_lang_phi)

@router.get("/summary", summary="Thống kê tổng hợp điện năng phục vụ vẽ biểu đồ Dashboard")
def get_energy_summary(
    tu_ngay: Optional[date] = Query(None),
    den_ngay: Optional[date] = Query(None),
    session: Session = Depends(get_session)
):
    return metricService.get_energy_summary(session, tu_ngay=tu_ngay, den_ngay=den_ngay)
