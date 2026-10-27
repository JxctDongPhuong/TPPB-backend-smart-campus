import os
from datetime import date, datetime, timedelta, timezone
from dotenv import load_dotenv
from sqlmodel import Session, select

# Nạp file .env
load_dotenv()

import app.database as db
from app.models import (
    CoSo, TaiKhoan, LoaiThietBi, Phong, ThietBi, LichPhong, YeuCauMuon, PhieuBaoHong, DienNang
)

def populate_neon_db():
    print("[Neon Seeder] Đang kết nối tới Neon DB và làm sạch dữ liệu cũ...")
    today = date.today()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)
    yesterday = today - timedelta(days=1)
    now = datetime.now(timezone.utc)

    with Session(db.engine) as session:
        # 1. Cơ sở CS1
        coso = session.get(CoSo, "CS1")
        if not coso:
            coso = CoSo(ma_cs="CS1", ten_cs="Cơ sở Chính - Khu Công nghệ cao", dia_chi="Khu CNC, TP.HCM")
            session.add(coso)
            session.commit()

        # 2. Tài khoản người dùng
        accounts_data = [
            (1, "admin", "Ban Quản Lý CSVC", "Admin"),
            (2, "gv_hung", "TS. Nguyễn Văn Hùng", "Giảng viên"),
            (3, "gv_an", "ThS. Trần Thị An", "Giảng viên"),
            (4, "sv_trang", "Đặng Minh Trang", "Sinh viên"),
            (5, "clb_it", "CLB Tin Học & AI", "Sinh viên")
        ]
        for ma_tk, username, hoten, role in accounts_data:
            acc = session.get(TaiKhoan, ma_tk)
            if not acc:
                acc = TaiKhoan(ma_tk=ma_tk, ten_dang_nhap=username, ho_ten=hoten, mat_khau_hash="hash_secret", vai_tro=role)
                session.add(acc)
        session.commit()

        # 3. Loại thiết bị
        device_types = [
            ("MAYLANH", "Máy điều hòa nhiệt độ Inverter", 2500),
            ("MAYCHIEU", "Máy chiếu Laser Projector", 400),
            ("MAYTINH", "Dàn máy tính trạm thực hành", 4500),
            ("QUAT", "Quạt trần thông gió công nghiệp", 120),
            ("DEN", "Hệ thống đèn LED chiếu sáng tiết kiệm điện", 350)
        ]
        for ma_loai, ten_loai, w in device_types:
            loai = session.get(LoaiThietBi, ma_loai)
            if not loai:
                loai = LoaiThietBi(ma_loai=ma_loai, ten_loai=ten_loai, cong_suat_mac_dinh_w=w)
                session.add(loai)
        session.commit()

        # 4. Danh sách 16 Phòng học phong phú (Tòa A, B, C, D từ tầng 1 đến 3)
        rooms_data = [
            # Tòa A
            ("A101", "CS1", "A", 1, "Phòng lý thuyết", 50, 25, 65.0, "Đang dùng"),
            ("A102", "CS1", "A", 1, "Phòng lý thuyết", 60, 30, 75.0, "Sẵn sàng"),
            ("A103", "CS1", "A", 1, "Phòng thực hành", 40, 20, 55.0, "Đang dùng"),
            ("A104", "CS1", "A", 1, "Phòng lý thuyết", 50, 25, 65.0, "Sẵn sàng"),
            ("A201", "CS1", "A", 2, "Phòng máy tính", 45, 45, 80.0, "Đang dùng"),
            ("A202", "CS1", "A", 2, "Phòng máy tính", 40, 40, 75.0, "Sẵn sàng"),

            # Tòa B
            ("B101", "CS1", "B", 1, "Phòng lý thuyết", 50, 25, 65.0, "Đang dùng"),
            ("B102", "CS1", "B", 1, "Phòng lý thuyết", 50, 25, 65.0, "Sẵn sàng"),
            ("B103", "CS1", "B", 1, "Phòng lý thuyết", 50, 25, 65.0, "Đang dùng"),
            ("B201", "CS1", "B", 2, "Phòng thực hành", 40, 20, 55.0, "Sẵn sàng"),
            ("B202", "CS1", "B", 2, "Phòng lý thuyết", 45, 22, 60.0, "Sẵn sàng"),
            ("B301", "CS1", "B", 3, "Hội trường", 150, 75, 180.0, "Sẵn sàng"),
            ("B302", "CS1", "B", 3, "Phòng học nhóm", 20, 10, 35.0, "Đang dùng"),

            # Tòa C & D
            ("C101", "CS1", "C", 1, "Phòng máy thực hành", 40, 40, 70.0, "Đang dùng"),
            ("C102", "CS1", "C", 1, "Phòng lý thuyết", 45, 22, 60.0, "Sẵn sàng"),
            ("D101", "CS1", "D", 1, "Phòng lý thuyết", 35, 18, 50.0, "Sẵn sàng")
        ]

        for ma_p, cs, toa, tang, loai, suc_chua, so_ban, dt, status in rooms_data:
            p = session.get(Phong, ma_p)
            if not p:
                p = Phong(
                    ma_phong=ma_p, ma_cs=cs, toa=toa, tang=tang,
                    loai_phong=loai, suc_chua=suc_chua, so_ban=so_ban,
                    dien_tich=dt, trang_thai=status, da_xoa=False
                )
                session.add(p)
            else:
                p.toa = toa
                p.tang = tang
                p.loai_phong = loai
                p.suc_chua = suc_chua
                p.trang_thai = status
                session.add(p)
        session.commit()

        # 5. Danh sách thiết bị phong phú cho từng phòng
        devices_data = [
            # A101
            ("TB_ML_A101", "MAYLANH", "A101", "ML_A1", "Điều hòa Daikin Inverter 2.5HP", 2500, 2023, "Tốt"),
            ("TB_MC_A101", "MAYCHIEU", "A101", "MC_A1", "Máy chiếu Panasonic Laser 4K", 400, 2023, "Tốt"),
            ("TB_QT_A101", "QUAT", "A101", "QT_A1", "Quạt trần thông gió Panasonic", 120, 2022, "Tốt"),
            
            # A201
            ("TB_ML_A201", "MAYLANH", "A201", "ML_A2", "Điều hòa trung tâm Panasonic A201", 2500, 2023, "Tốt"),
            ("TB_PC_A201", "MAYTINH", "A201", "PC_DELL", "Dàn 45 máy tính Dell Core i7", 4500, 2024, "Tốt"),
            ("TB_MC_A201", "MAYCHIEU", "A201", "MC_A2", "Máy chiếu Sony Laser Full HD", 450, 2023, "Tốt"),

            # A202
            ("TB_ML_A202", "MAYLANH", "A202", "ML_A2", "Điều hòa Daikin A202 (Đang chảy nước)", 2500, 2021, "Hỏng"),
            ("TB_PC_A202", "MAYTINH", "A202", "PC_HP", "Dàn 40 máy tính HP trạm", 4000, 2023, "Tốt"),

            # B101
            ("TB_ML_B101", "MAYLANH", "B101", "ML_B1", "Điều hòa Carrier Multi-split", 2500, 2022, "Tốt"),
            ("TB_MC_B101", "MAYCHIEU", "B101", "MC_B1", "Máy chiếu Epson Pro", 400, 2022, "Tốt"),

            # B301
            ("TB_ML_B301", "MAYLANH", "B301", "ML_B3", "Hệ thống điều hòa trung tâm Hội trường", 7500, 2023, "Tốt"),
            ("TB_MC_B301", "MAYCHIEU", "B301", "MC_B3", "Máy chiếu công suất lớn hội trường", 1200, 2023, "Tốt"),

            # C101
            ("TB_ML_C101", "MAYLANH", "C101", "ML_C1", "Điều hòa Daikin Eco", 2500, 2023, "Tốt"),
            ("TB_PC_C101", "MAYTINH", "C101", "PC_C1", "Dàn 40 máy tính chuyên Lab AI", 5000, 2024, "Tốt")
        ]

        for ma_tb, ma_loai, ma_phong, ma_lo, ten, w, nam, tt in devices_data:
            tb = session.get(ThietBi, ma_tb)
            if not tb:
                tb = ThietBi(
                    ma_tb=ma_tb, ma_loai=ma_loai, ma_phong=ma_phong, ma_lo=ma_lo,
                    ten_tb=ten, cong_suat_w=w, nam_mua=nam, tinh_trang=tt, da_xoa=False
                )
                session.add(tb)
            else:
                tb.tinh_trang = tt
                tb.ma_phong = ma_phong
                session.add(tb)
        session.commit()

        # 6. Lịch học chính khóa (Hôm nay, Ngày mai, và các ngày tới)
        schedules_data = [
            # Hôm nay
            ("A101", today, 1, "HOC", "Lập trình Python Nâng Cao - TS. Nguyễn Văn Hùng - CNTT-K15", 48),
            ("A103", today, 2, "HOC", "Cơ sở Dữ liệu Phân tán - ThS. Trần Thị An - HTTT-K15", 38),
            ("A201", today, 1, "HOC", "Thực hành Mạng Máy Tính - TS. Lê Quốc Bảo - KTPM-K16", 42),
            ("B101", today, 3, "HOC", "Trí Tuệ Nhân Tạo & Học Máy - PGS. Trần Nam - AI-K16", 45),
            ("B302", today, 2, "MUON", "Mượn phòng: Họp CLB Nghiên Cứu Khoa Học Sinh Viên", 18),
            ("C101", today, 1, "HOC", "Thực hành Lập trình Web Cloud - Giảng viên mời", 38),

            # Ngày mai
            ("A101", tomorrow, 2, "HOC", "Toán Rời Rạc & Lý Thuyết Đồ Thị - TS. Nguyễn Văn Hùng", 50),
            ("A102", tomorrow, 1, "HOC", "Kiến Trúc Máy Tính & Hợp Ngữ - ThS. Trần Thị An", 45),
            ("A201", tomorrow, 3, "HOC", "Thực hành An Toàn Thông Tin - TS. Lê Quốc Bảo", 40),
            ("B301", tomorrow, 2, "MUON", "Mượn: Hội thảo Giới Thiệu Công Nghệ AI Campus 2026", 120),
            ("C101", tomorrow, 2, "HOC", "Thực hành Điện Toán Đám Mây AWS - K15", 39)
        ]

        for ma_p, ng, ca, loai, nd, so_ng in schedules_data:
            existing = session.exec(
                select(LichPhong).where(LichPhong.ma_phong == ma_p, LichPhong.ngay == ng, LichPhong.ca == ca)
            ).first()
            if not existing:
                session.add(LichPhong(
                    ma_phong=ma_p, ngay=ng, ca=ca, loai=loai, noi_dung=nd, so_nguoi=so_ng
                ))
        session.commit()

        # 7. Yêu cầu mượn phòng (YeuCauMuon) với các trạng thái để test duyệt / hủy
        requests_data = [
            (101, 4, "A102", tomorrow, 3, 40, "Ôn tập thi cuối kỳ môn Cấu trúc dữ liệu", "Cần sử dụng máy chiếu và bảng", "ChoDuyet"),
            (102, 5, "B202", day_after, 2, 35, "Tập dượt thuyết trình cuộc thi Hackathon AI", "Cần phòng yên tĩnh", "ChoDuyet"),
            (103, 4, "B302", today, 4, 15, "Họp nhóm đồ án tốt nghiệp K15", "Không cần máy chiếu", "ChoDuyet"),
            (104, 2, "B301", day_after, 1, 100, "Tổ chức sinh hoạt công dân đầu khóa", "Đã duyệt ngày 27/10", "DaDuyet"),
            (105, 3, "A202", yesterday, 2, 40, "Thực hành ngoài giờ phòng máy A202", "Từ chối do điều hòa đang bảo trì", "TuChoi")
        ]

        for ma_yc, ma_tk, ma_p, ng, ca, so_ng, muc_dich, ghi_chu, tt in requests_data:
            req = session.get(YeuCauMuon, ma_yc)
            if not req:
                req = YeuCauMuon(
                    ma_yc=ma_yc, ma_tk=ma_tk, ma_phong=ma_p, ngay=ng, ca=ca,
                    so_nguoi=so_ng, muc_dich=muc_dich, ghi_chu=ghi_chu,
                    trang_thai=tt, ngay_gui=now
                )
                session.add(req)
            else:
                req.trang_thai = tt
                req.muc_dich = muc_dich
                session.add(req)
        session.commit()

        # 8. Phiếu báo hỏng thiết bị (PhieuBaoHong)
        reports_data = [
            (201, "A202", "TB_ML_A202", "Điều hòa A202 bị chảy nước và kêu to bất thường, không phả hơi lạnh", "DangXuLy", 4, now - timedelta(hours=5), "Kỹ thuật đã tiếp nhận, đang chờ vật tư thay thế"),
            (202, "A101", "TB_MC_A101", "Máy chiếu chập chờn cổng HDMI, hình ảnh bị đổi màu vàng", "Moi", 2, now - timedelta(hours=2), None),
            (203, "C101", "TB_PC_C101", "Máy tính trạm số 12 bị lỗi màn hình xanh khi chạy mô hình AI", "Moi", 3, now - timedelta(minutes=45), None),
            (204, "B101", "TB_ML_B101", "Điều hòa phòng B101 kêu rè rè đã được vệ sinh lưới lọc", "DaXuLy", 1, now - timedelta(days=2), "Đã vệ sinh lưới lọc và bơm gas xong")
        ]

        for ma_phieu, ma_p, ma_tb, mo_ta, tt, ma_tk, ngay_bao, gc in reports_data:
            rep = session.get(PhieuBaoHong, ma_phieu)
            if not rep:
                rep = PhieuBaoHong(
                    ma_phieu=ma_phieu, ma_phong=ma_p, ma_tb=ma_tb, mo_ta=mo_ta,
                    trang_thai=tt, ma_tk=ma_tk, ngay_bao=ngay_bao, ghi_chu_admin=gc
                )
                session.add(rep)
            else:
                rep.trang_thai = tt
                rep.mo_ta = mo_ta
                session.add(rep)
        session.commit()

        # 9. Chỉ số điện năng tiêu thụ (DienNang) & Cảnh báo lãng phí
        metrics_data = [
            ("A101", today, 16.5, 5.0),
            ("A103", today, 14.0, 4.5),
            ("A201", today, 32.5, 6.0),
            ("B101", today, 18.0, 4.0),
            ("C101", today, 28.0, 5.5),
            # Phòng lãng phí điện (Không có lịch nhưng tiêu thụ cao bất thường):
            ("A104", today, 18.2, 5.5),  # Lãng phí điện! Không có lịch ca nào hôm nay nhưng 18.2 kWh
            ("B102", today, 15.6, 4.8),  # Lãng phí điện!
            
            # Ngày hôm qua
            ("A101", yesterday, 22.0, 7.0),
            ("A201", yesterday, 38.0, 8.0),
            ("B301", yesterday, 45.0, 6.0)
        ]

        for ma_p, ng, kwh, gio in metrics_data:
            dn = session.get(DienNang, (ma_p, ng))
            if not dn:
                session.add(DienNang(ma_phong=ma_p, ngay=ng, kwh=kwh, so_gio_bat=gio))
            else:
                dn.kwh = kwh
                dn.so_gio_bat = gio
                session.add(dn)
        session.commit()

    print("[Neon Seeder] ĐÃ NẠP THÀNH CÔNG:")
    print(" - 16 Phòng học (Tòa A, B, C, D)")
    print(" - 14 Thiết bị chính")
    print(" - 11 Lịch học chính khóa và mượn phòng")
    print(" - 5 Yêu cầu mượn phòng (3 chờ duyệt, 1 đã duyệt, 1 từ chối)")
    print(" - 4 Phiếu báo hỏng (Mới, Đang xử lý, Đã xử lý)")
    print(" - 9 Bản ghi tiêu thụ điện năng (kèm phát hiện lãng phí điện A104, B102)")

if __name__ == "__main__":
    populate_neon_db()
