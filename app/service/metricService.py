import logging
from datetime import date
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlmodel import Session, select, func

from app.models import DienNang, DienNangCreate, LichPhong, Phong

logger = logging.getLogger("smart_campus.metrics")

def get_energy_metrics(
    session: Session,
    ma_phong: Optional[str] = None,
    tu_ngay: Optional[date] = None,
    den_ngay: Optional[date] = None
) -> List[DienNang]:
    try:
        query = select(DienNang)
        if ma_phong:
            query = query.where(DienNang.ma_phong == ma_phong)
        if tu_ngay:
            query = query.where(DienNang.ngay >= tu_ngay)
        if den_ngay:
            query = query.where(DienNang.ngay <= den_ngay)
        return session.exec(query).all()
    except Exception as e:
        logger.error(f"[MetricService Error] Lỗi khi truy vấn get_energy_metrics: {e}")
        return []

def record_energy_metric(session: Session, data: DienNangCreate) -> Optional[DienNang]:
    # 1. Kiểm tra phòng có tồn tại hay không
    phong = session.get(Phong, data.ma_phong)
    if not phong or phong.da_xoa:
        valid_rooms = [p.ma_phong for p in session.exec(select(Phong).where(Phong.da_xoa == False)).all()]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Wrong parameter 'ma_phong'",
                "value_received": data.ma_phong,
                "message": f"Phòng '{data.ma_phong}' không tồn tại trong hệ thống.",
                "recommendation": f"Vui lòng chọn một trong các mã phòng hợp lệ hiện có: {valid_rooms}, hoặc tạo phòng '{data.ma_phong}' trước."
            }
        )

    try:
        existing = session.get(DienNang, (data.ma_phong, data.ngay))
        if existing:
            existing.kwh = data.kwh
            existing.so_gio_bat = data.so_gio_bat
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing

        db_metric = DienNang.model_validate(data)
        session.add(db_metric)
        session.commit()
        session.refresh(db_metric)
        return db_metric
    except Exception as e:
        session.rollback()
        logger.error(f"[MetricService Error] Lỗi khi lưu record_energy_metric: {e}")
        raise e

def detect_waste_energy(
    session: Session,
    ngay: date,
    nguong_kwh_lang_phi: float = 5.0
) -> Dict[str, Any]:
    """
    Thuật toán phát hiện lãng phí điện năng (Idle Waste):
    Đối chiếu DienNang với LichPhong: nếu phòng tiêu thụ điện > ngưỡng quy định
    nhưng trong ngày không có ca học nào, cảnh báo thiết bị bị bỏ quên.
    Đã bổ sung try-catch và kiểm tra rõ ràng trường hợp DB chưa có bản ghi đo.
    """
    alerts = []
    try:
        metrics_in_day = session.exec(select(DienNang).where(DienNang.ngay == ngay)).all()

        # Kiểm tra nếu DB chưa có bản ghi nào của ngày này
        if not metrics_in_day:
            return {
                "ngay": str(ngay),
                "has_data": False,
                "tong_so_phong_lang_phi": 0,
                "danh_sach_canh_bao": [],
                "thong_bao": f"Chưa có dữ liệu đo đạc điện năng cho ngày {ngay} trong hệ thống."
            }

        for item in metrics_in_day:
            count_schedules = session.exec(
                select(func.count(LichPhong.ma_lich)).where(
                    LichPhong.ma_phong == item.ma_phong,
                    LichPhong.ngay == ngay
                )
            ).one()

            if count_schedules == 0 and item.kwh >= nguong_kwh_lang_phi:
                alerts.append({
                    "ma_phong": item.ma_phong,
                    "ngay": str(item.ngay),
                    "kwh_tieu_thu": item.kwh,
                    "so_ca_hoc": 0,
                    "muc_do": "Cao" if item.kwh > 15 else "Trung bình",
                    "canh_bao": "Phòng không có lịch học nhưng phát sinh tiêu thụ điện bất thường (Nghi vấn quên tắt thiết bị)."
                })

        return {
            "ngay": str(ngay),
            "has_data": True,
            "tong_so_phong_lang_phi": len(alerts),
            "danh_sach_canh_bao": alerts,
            "thong_bao": f"Tìm thấy {len(alerts)} phòng có dấu hiệu lãng phí điện." if alerts else "Không phát hiện lãng phí điện trong ngày."
        }
    except Exception as e:
        logger.error(f"[MetricService Error] Lỗi khi detect_waste_energy ngày {ngay}: {e}")
        return {
            "ngay": str(ngay),
            "has_data": False,
            "tong_so_phong_lang_phi": 0,
            "danh_sach_canh_bao": [],
            "thong_bao": f"Lỗi hệ thống khi đọc dữ liệu điện năng: {str(e)}"
        }

def get_energy_summary(
    session: Session,
    tu_ngay: Optional[date] = None,
    den_ngay: Optional[date] = None
) -> Dict[str, Any]:
    try:
        query = select(DienNang)
        if tu_ngay:
            query = query.where(DienNang.ngay >= tu_ngay)
        if den_ngay:
            query = query.where(DienNang.ngay <= den_ngay)
            
        records = session.exec(query).all()
        if not records:
            return {
                "has_data": False,
                "tong_kwh": 0.0,
                "so_ban_ghi": 0,
                "trung_binh_kwh_moi_phong": 0.0,
                "thong_bao": "Hệ thống chưa ghi nhận dữ liệu điện năng nào trong khoảng thời gian này."
            }

        tong_kwh = sum(r.kwh for r in records)
        return {
            "has_data": True,
            "tong_kwh": round(tong_kwh, 2),
            "so_ban_ghi": len(records),
            "trung_binh_kwh_moi_phong": round(tong_kwh / len(records), 2),
            "thong_bao": f"Tổng cộng {len(records)} lượt đo, tổng tiêu thụ: {round(tong_kwh, 2)} kWh."
        }
    except Exception as e:
        logger.error(f"[MetricService Error] Lỗi khi get_energy_summary: {e}")
        return {
            "has_data": False,
            "tong_kwh": 0.0,
            "so_ban_ghi": 0,
            "trung_binh_kwh_moi_phong": 0.0,
            "thong_bao": f"Lỗi truy vấn dữ liệu điện năng: {str(e)}"
        }
