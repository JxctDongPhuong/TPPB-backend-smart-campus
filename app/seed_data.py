import logging
from datetime import date, datetime, timedelta
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
        # Kiểm tra nếu đã có dữ liệu phòng thì không nạp đè
        existing = session.exec(select(Phong)).first()
        if existing:
            print("[Seed Data] Database da co du lieu, bo qua buoc khoi tao mau.")
            return

        print("[Seed Data] Bat dau nap du lieu mau vao campus.db...")
        today = date.today()
        now = datetime.utcnow()

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
        tb_list = [
            ThietBi(ma_tb="TB_ML_A101", ma_phong="A101", ma_loai="MAYLANH", ten_tb="Dieu hoa Daikin 1", tinh_trang="Tốt"),
            ThietBi(ma_tb="TB_MC_A101", ma_phong="A101", ma_loai="MAYCHIEU", ten_tb="May chieu Panasonic", tinh_trang="Tốt"),
            ThietBi(ma_tb="TB_PC_A201", ma_phong="A201", ma_loai="MAYTINH", ten_tb="Dan 45 PC Dell", tinh_trang="Tốt"),
            ThietBi(ma_tb="TB_ML_A202", ma_phong="A202", ma_loai="MAYLANH", ten_tb="Dieu hoa Panasonic A202", tinh_trang="Hỏng"),
        ]
        session.add_all(tb_list)
        session.commit()

        # 5. Phiếu báo hỏng mẫu
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

        # 6. Lịch phòng hôm nay (A101 có ca 1, A201 có ca 2, các phòng khác trống)
        lich_list = [
            LichPhong(ma_phong="A101", ngay=today, ca=1, ten_mon_hoc="Lap trinh Python Nang Cao", giang_vien="ThS. Nguyen Van A", lop="CNTT-K15", trang_thai="Sắp diễn ra"),
            LichPhong(ma_phong="A201", ngay=today, ca=2, ten_mon_hoc="Thuc hanh Mang May Tinh", giang_vien="TS. Tran Thi B", lop="KTPM-K16", trang_thai="Sắp diễn ra"),
            LichPhong(ma_phong="A102", ngay=today + timedelta(days=1), ca=3, ten_mon_hoc="Co so Du lieu", giang_vien="ThS. Le Hoang C", lop="HTTT-K15", trang_thai="Sắp diễn ra"),
        ]
        session.add_all(lich_list)
        session.commit()

        # 7. Điện năng tiêu thụ (Mô phỏng cả phòng bình thường và phòng có lãng phí idle waste)
        dien_list = [
            # A101 có lịch ca 1 -> tiêu thụ 12.5 kWh là hợp lý
            DienNang(ma_phong="A101", ngay=today, kwh=12.5, so_gio_bat=4.0),
            # A201 có lịch ca 2 -> tiêu thụ 18.0 kWh là hợp lý
            DienNang(ma_phong="A201", ngay=today, kwh=18.0, so_gio_bat=3.5),
            # B302 KHÔNG có lịch hôm nay nhưng tiêu thụ 8.5 kWh -> Cảnh báo lãng phí Idle Waste!
            DienNang(ma_phong="B302", ngay=today, kwh=8.5, so_gio_bat=6.0),
        ]
        session.add_all(dien_list)
        session.commit()

        print("[Seed Data] Da nap thanh cong 6 phong hoc, 4 thiet bi, 1 phieu bao hong, 3 lich hoc va 3 ban ghi dien nang!")

if __name__ == "__main__":
    seed_sample_data()
