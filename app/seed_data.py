import logging
from datetime import date, datetime, timedelta, timezone
from sqlmodel import Session, select

from app.database import engine, init_db
from app.models import (
    Phong, CoSo, LoaiThietBi, ThietBi, LichPhong, DienNang, PhieuBaoHong, TaiKhoan
)

logger = logging.getLogger("smart_campus.seed")

def seed_sample_data():
    """Nạp dữ liệu mẫu khởi đầu vào cơ sở dữ liệu để trải nghiệm đầy đủ chức năng"""
    init_db()
    
    with Session(engine) as session:
        print("[Seed Data] Bat dau kiem tra va nap du lieu mau vao database...")
        today = date.today()
        now = datetime.now(timezone.utc)

        # 0. Tài khoản mẫu
        admin_user = session.get(TaiKhoan, 1)
        if not admin_user:
            admin_user = TaiKhoan(
                ma_tk=1,
                ten_dang_nhap="admin",
                ho_ten="Ban Quan Ly Co So Vat Chat",
                mat_khau_hash="admin_hash_secret",
                vai_tro="Admin"
            )
            session.add(admin_user)
            session.commit()

        # 1. Cơ sở
        coso_main = session.get(CoSo, "CS1")
        if not coso_main:
            coso_main = CoSo(ma_cs="CS1", ten_cs="Co so Chinh - Khu Cong nghe cao", dia_chi="Khu CNC, TP.HCM")
            session.add(coso_main)
            session.commit()

        # 2. Danh mục Loại Thiết Bị
        loai_tb1 = session.get(LoaiThietBi, "MAYLANH")
        if not loai_tb1:
            loai_tb1 = LoaiThietBi(ma_loai="MAYLANH", ten_loai="May dieu hoa nhiet do", cong_suat_mac_dinh_w=2500)
            session.add(loai_tb1)

        loai_tb2 = session.get(LoaiThietBi, "MAYCHIEU")
        if not loai_tb2:
            loai_tb2 = LoaiThietBi(ma_loai="MAYCHIEU", ten_loai="May chieu Projector", cong_suat_mac_dinh_w=400)
            session.add(loai_tb2)

        loai_tb3 = session.get(LoaiThietBi, "MAYTINH")
        if not loai_tb3:
            loai_tb3 = LoaiThietBi(ma_loai="MAYTINH", ten_loai="Dan may tinh phong lab", cong_suat_mac_dinh_w=5000)
            session.add(loai_tb3)
        session.commit()

        # 3. Phòng học
        existing_phong = session.exec(select(Phong)).first()
        if not existing_phong:
            phong_list = [
                Phong(ma_phong="A101", ten_phong="Phong Ly Thuyet A101", ma_cs="CS1", toa="A", tang=1, loai_phong="Phòng lý thuyết", suc_chua=50, trang_thai="Sẵn sàng"),
                Phong(ma_phong="A102", ten_phong="Phong Ly Thuyet A102", ma_cs="CS1", toa="A", tang=1, loai_phong="Phòng lý thuyết", suc_chua=60, trang_thai="Sẵn sàng"),
                Phong(ma_phong="A201", ten_phong="Phong May Tinh Lab 1", ma_cs="CS1", toa="A", tang=2, loai_phong="Phòng máy tính", suc_chua=45, trang_thai="Sẵn sàng"),
                Phong(ma_phong="A202", ten_phong="Phong May Tinh Lab 2", ma_cs="CS1", toa="A", tang=2, loai_phong="Phòng máy tính", suc_chua=40, trang_thai="Sẵn sàng"),
                Phong(ma_phong="B301", ten_phong="Hoi Truong Lon B301", ma_cs="CS1", toa="B", tang=3, loai_phong="Hội trường", suc_chua=150, trang_thai="Sẵn sàng"),
                Phong(ma_phong="B302", ten_phong="Phong Hoc Nhom B302", ma_cs="CS1", toa="B", tang=3, loai_phong="Phòng học nhóm", suc_chua=15, trang_thai="Sẵn sàng"),
            ]
            session.add_all(phong_list)
            session.commit()

        # 4. Thiết bị trong phòng
        existing_tb = session.exec(select(ThietBi)).first()
        if not existing_tb:
            tb_list = [
                ThietBi(ma_tb="TB_ML_A101", ma_phong="A101", ma_loai="MAYLANH", ten_tb="Dieu hoa Daikin 1", tinh_trang="Tốt"),
                ThietBi(ma_tb="TB_MC_A101", ma_phong="A101", ma_loai="MAYCHIEU", ten_tb="May chieu Panasonic", tinh_trang="Tốt"),
                ThietBi(ma_tb="TB_PC_A201", ma_phong="A201", ma_loai="MAYTINH", ten_tb="Dan 45 PC Dell", tinh_trang="Tốt"),
                ThietBi(ma_tb="TB_ML_A202", ma_phong="A202", ma_loai="MAYLANH", ten_tb="Dieu hoa Panasonic A202", tinh_trang="Hỏng"),
            ]
            session.add_all(tb_list)
            session.commit()

        # 5. Phiếu báo hỏng mẫu
        existing_phieu = session.exec(select(PhieuBaoHong)).first()
        if not existing_phieu:
            phieu = PhieuBaoHong(
                ma_phong="A202",
                ma_tb="TB_ML_A202",
                mo_ta="Dieu hoa A202 bi chay nuoc va keu to, khong lam mat",
                trang_thai="DangXuLy",
                ma_tk=1,
                ngay_bao=now
            )
            session.add(phieu)
            session.commit()

        # 6. Lịch phòng hôm nay
        existing_lich = session.exec(select(LichPhong)).first()
        if not existing_lich:
            lich_list = [
                LichPhong(ma_phong="A101", ngay=today, ca=1, loai="HOC", noi_dung="Lap trinh Python Nang Cao - ThS. Nguyen Van A - CNTT-K15", so_nguoi=45),
                LichPhong(ma_phong="A201", ngay=today, ca=2, loai="HOC", noi_dung="Thuc hanh Mang May Tinh - TS. Tran Thi B - KTPM-K16", so_nguoi=40),
                LichPhong(ma_phong="A102", ngay=today + timedelta(days=1), ca=3, loai="HOC", noi_dung="Co so Du lieu - ThS. Le Hoang C - HTTT-K15", so_nguoi=50),
            ]
            session.add_all(lich_list)
            session.commit()

        # 7. Điện năng tiêu thụ
        existing_dien = session.exec(select(DienNang)).first()
        if not existing_dien:
            dien_list = [
                DienNang(ma_phong="A101", ngay=today, kwh=12.5, so_gio_bat=4.0),
                DienNang(ma_phong="A201", ngay=today, kwh=18.0, so_gio_bat=3.5),
                DienNang(ma_phong="B302", ngay=today, kwh=8.5, so_gio_bat=6.0),
            ]
            session.add_all(dien_list)
            session.commit()

        print("[Seed Data] Da nap thanh cong 6 phong hoc, 4 thiet bi, 1 phieu bao hong, 3 lich hoc va 3 ban ghi dien nang!")

if __name__ == "__main__":
    seed_sample_data()
