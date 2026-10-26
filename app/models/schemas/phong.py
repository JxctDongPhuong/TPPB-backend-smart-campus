from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .coso import CoSo
    from .thiet_bi import ThietBi
    from .lich_phong import LichPhong
    from .dien_nang import DienNang
    from .phieu_bao_hong import PhieuBaoHong
    from .yeu_cau_muon import YeuCauMuon

# 1. Base schema
class PhongBase(SQLModel):
    ma_phong: str = Field(primary_key=True, max_length=50, description="Ví dụ: CS01-A101")
    ma_cs: str = Field(foreign_key="coso.ma_cs", description="Mã cơ sở")
    toa: Optional[str] = Field(default=None, max_length=50, description="Tòa nhà (A, B, C...)")
    tang: Optional[int] = Field(default=None, description="Tầng")
    loai_phong: str = Field(description="Lý thuyết / Máy tính / Thực hành / Hội trường")
    suc_chua: Optional[int] = Field(default=40, description="Sức chứa người")
    so_ban: Optional[int] = Field(default=None, description="Số bàn")
    dien_tich: Optional[float] = Field(default=None, description="Diện tích (m2)")
    trang_thai: str = Field(default="Đang dùng", description="Đang dùng / Bảo trì")
    da_xoa: bool = Field(default=False, description="Đánh dấu xóa mềm")

# 2. Table model
class Phong(PhongBase, table=True):
    __tablename__ = "phong"

    # Quan hệ
    co_so: Optional["CoSo"] = Relationship(back_populates="danh_sach_phong")
    danh_sach_thiet_bi: List["ThietBi"] = Relationship(back_populates="phong")
    danh_sach_lich: List["LichPhong"] = Relationship(back_populates="phong")
    danh_sach_dien_nang: List["DienNang"] = Relationship(back_populates="phong")
    danh_sach_phieu_bao_hong: List["PhieuBaoHong"] = Relationship(back_populates="phong")
    danh_sach_yeu_cau_muon: List["YeuCauMuon"] = Relationship(back_populates="phong")

# 3. Create schema
class PhongCreate(SQLModel):
    ma_phong: str
    ma_cs: str
    toa: Optional[str] = None
    tang: Optional[int] = None
    loai_phong: str
    suc_chua: Optional[int] = 40
    so_ban: Optional[int] = None
    dien_tich: Optional[float] = None
    trang_thai: Optional[str] = "Đang dùng"

# 4. Update schema
class PhongUpdate(SQLModel):
    ma_cs: Optional[str] = None
    toa: Optional[str] = None
    tang: Optional[int] = None
    loai_phong: Optional[str] = None
    suc_chua: Optional[int] = None
    so_ban: Optional[int] = None
    dien_tich: Optional[float] = None
    trang_thai: Optional[str] = None
    da_xoa: Optional[bool] = None

# 5. Read schema
class PhongRead(PhongBase):
    pass
