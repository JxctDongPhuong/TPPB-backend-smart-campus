from typing import List, Optional
from fastapi import HTTPException, status
from sqlmodel import Session, select
from datetime import datetime, timezone

from app.models import (
    ThietBi, ThietBiCreate, ThietBiCreateBatch,
    PhieuBaoHong, PhieuBaoHongCreate, PhieuBaoHongUpdate,
    Phong
)

# Hằng số trạng thái phiếu báo hỏng
TRANG_THAI_MOI = "Moi"
TRANG_THAI_DANG_XU_LY = "DangXuLy"
TRANG_THAI_DA_XU_LY = "DaXuLy"
TRANG_THAI_TU_CHOI = "TuChoi"
TRANG_THAI_HOAN_TAT = [TRANG_THAI_DA_XU_LY, TRANG_THAI_TU_CHOI, "Đã xử lý", "Từ chối"]

# Hằng số tình trạng thiết bị mặc định
TINH_TRANG_TOT = "Tốt"

# ==================== 1. QUẢN LÝ THIẾT BỊ ====================

def get_devices(
    session: Session,
    ma_phong: Optional[str] = None,
    ma_loai: Optional[str] = None,
    tinh_trang: Optional[str] = None
) -> List[ThietBi]:
    """
    Tra cứu danh sách thiết bị theo phòng, loại hoặc tình trạng hoạt động.
    """
    query = select(ThietBi).where(ThietBi.da_xoa == False)
    if ma_phong is not None:
        query = query.where(ThietBi.ma_phong == ma_phong)
    if ma_loai:
        query = query.where(ThietBi.ma_loai == ma_loai)
    if tinh_trang:
        query = query.where(ThietBi.tinh_trang == tinh_trang)
    return session.exec(query).all()

def create_device(session: Session, data: ThietBiCreate) -> ThietBi:
    """
    Thêm mới một thiết bị đơn lẻ vào hệ thống.
    """
    existing = session.get(ThietBi, data.ma_tb)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mã thiết bị đã tồn tại")
    
    db_device = ThietBi.model_validate(data)
    session.add(db_device)
    session.commit()
    session.refresh(db_device)
    return db_device

def create_devices_batch(session: Session, batch: ThietBiCreateBatch) -> List[ThietBi]:
    """
    Tự động sinh thiết bị hàng loạt theo lô:
    ML_01-01, ML_01-02, ... ML_01-10
    """
    created_list = []
    current_index = 1

    for _ in range(batch.so_luong):
        ma_tb = f"{batch.ma_lo}-{current_index:02d}"
        while session.get(ThietBi, ma_tb):
            current_index += 1
            ma_tb = f"{batch.ma_lo}-{current_index:02d}"

        new_device = ThietBi(
            ma_tb=ma_tb,
            ma_loai=batch.ma_loai,
            ma_lo=batch.ma_lo,
            ma_phong=batch.ma_phong,
            cong_suat_w=batch.cong_suat_w,
            nam_mua=batch.nam_mua,
            tinh_trang=TINH_TRANG_TOT
        )
        session.add(new_device)
        created_list.append(new_device)
        current_index += 1

    session.commit()
    for d in created_list:
        session.refresh(d)
    return created_list

# ==================== 2. QUẢN LÝ PHIẾU BÁO HỎNG ====================

def get_reports(session: Session, trang_thai: Optional[str] = None) -> List[PhieuBaoHong]:
    """
    Lấy danh sách các phiếu báo hỏng thiết bị/sự cố.
    """
    query = select(PhieuBaoHong)
    if trang_thai:
        query = query.where(PhieuBaoHong.trang_thai == trang_thai)
    return session.exec(query).all()

def submit_report(session: Session, data: PhieuBaoHongCreate, ma_tk_nguoi_bao: int) -> PhieuBaoHong:
    """
    Gửi phiếu báo hỏng thiết bị mới từ sinh viên hoặc giảng viên.
    """
    clean_room = data.ma_phong.replace("Phòng ", "").replace("phòng ", "").strip() if data.ma_phong else None

    # Nếu có mã thiết bị, cập nhật tình trạng thiết bị thành "Hỏng"
    if data.ma_tb:
        dev = session.get(ThietBi, data.ma_tb)
        if dev:
            dev.tinh_trang = "Hỏng"
            session.add(dev)
            if not clean_room and dev.ma_phong:
                clean_room = dev.ma_phong

    # Đảm bảo mã phòng hợp lệ để không vi phạm ràng buộc Foreign Key
    if clean_room:
        room_exists = session.get(Phong, clean_room)
        if not room_exists:
            first_room = session.exec(select(Phong)).first()
            if first_room:
                clean_room = first_room.ma_phong
    else:
        first_room = session.exec(select(Phong)).first()
        if first_room:
            clean_room = first_room.ma_phong

    report = PhieuBaoHong(
        ma_tk=ma_tk_nguoi_bao,
        ma_phong=clean_room,
        ma_tb=data.ma_tb,
        mo_ta=data.mo_ta,
        trang_thai=TRANG_THAI_MOI,
        ngay_bao=datetime.now(timezone.utc)
    )
    session.add(report)
    session.commit()
    session.refresh(report)
    return report

def update_report(session: Session, ma_phieu: int, update_data: PhieuBaoHongUpdate) -> PhieuBaoHong:
    """
    Cập nhật tiến độ xử lý phiếu báo hỏng (Dành cho Quản trị viên/Kỹ thuật).
    """
    report = session.get(PhieuBaoHong, ma_phieu)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy phiếu báo hỏng")

    data_dict = update_data.model_dump(exclude_unset=True)
    for k, v in data_dict.items():
        setattr(report, k, v)
        
    if update_data.trang_thai in TRANG_THAI_HOAN_TAT:
        if not report.ngay_xu_ly:
            report.ngay_xu_ly = datetime.now(timezone.utc)
        # Tự động khôi phục tình trạng thiết bị về "Tốt" khi phiếu đã xử lý xong
        if report.ma_tb:
            dev = session.get(ThietBi, report.ma_tb)
            if dev:
                dev.tinh_trang = "Tốt"
                session.add(dev)
    elif update_data.trang_thai == "DangXuLy":
        if report.ma_tb:
            dev = session.get(ThietBi, report.ma_tb)
            if dev:
                dev.tinh_trang = "Đang sửa"
                session.add(dev)

    session.add(report)
    session.commit()
    session.refresh(report)
    return report
