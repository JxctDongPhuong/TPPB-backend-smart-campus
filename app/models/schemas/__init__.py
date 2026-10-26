from .coso import CoSo, CoSoBase, CoSoCreate, CoSoUpdate, CoSoRead
from .phong import Phong, PhongBase, PhongCreate, PhongUpdate, PhongRead
from .loai_thiet_bi import LoaiThietBi, LoaiThietBiBase, LoaiThietBiCreate, LoaiThietBiUpdate, LoaiThietBiRead
from .thiet_bi import ThietBi, ThietBiBase, ThietBiCreate, ThietBiCreateBatch, ThietBiUpdate, ThietBiRead
from .tai_khoan import TaiKhoan, TaiKhoanBase, TaiKhoanCreate, TaiKhoanUpdate, TaiKhoanRead
from .lich_phong import LichPhong, LichPhongBase, LichPhongCreate, LichPhongUpdate, LichPhongRead
from .yeu_cau_muon import YeuCauMuon, YeuCauMuonBase, YeuCauMuonCreate, YeuCauMuonDuyet, YeuCauMuonRead
from .phieu_bao_hong import PhieuBaoHong, PhieuBaoHongBase, PhieuBaoHongCreate, PhieuBaoHongUpdate, PhieuBaoHongRead
from .dien_nang import DienNang, DienNangBase, DienNangCreate, DienNangUpdate, DienNangRead
from .ai_agent import ChatMessage, ChatRequest, ChatResponse

__all__ = [
    # 1. Cơ sở
    "CoSo", "CoSoBase", "CoSoCreate", "CoSoUpdate", "CoSoRead",
    # 2. Phòng
    "Phong", "PhongBase", "PhongCreate", "PhongUpdate", "PhongRead",
    # 3. Loại thiết bị
    "LoaiThietBi", "LoaiThietBiBase", "LoaiThietBiCreate", "LoaiThietBiUpdate", "LoaiThietBiRead",
    # 4. Thiết bị
    "ThietBi", "ThietBiBase", "ThietBiCreate", "ThietBiCreateBatch", "ThietBiUpdate", "ThietBiRead",
    # 5. Tài khoản
    "TaiKhoan", "TaiKhoanBase", "TaiKhoanCreate", "TaiKhoanUpdate", "TaiKhoanRead",
    # 6. Lịch phòng
    "LichPhong", "LichPhongBase", "LichPhongCreate", "LichPhongUpdate", "LichPhongRead",
    # 7. Yêu cầu mượn
    "YeuCauMuon", "YeuCauMuonBase", "YeuCauMuonCreate", "YeuCauMuonDuyet", "YeuCauMuonRead",
    # 8. Phiếu báo hỏng
    "PhieuBaoHong", "PhieuBaoHongBase", "PhieuBaoHongCreate", "PhieuBaoHongUpdate", "PhieuBaoHongRead",
    # 9. Điện năng
    "DienNang", "DienNangBase", "DienNangCreate", "DienNangUpdate", "DienNangRead",
    # 10. AI Agent
    "ChatMessage", "ChatRequest", "ChatResponse",
]
