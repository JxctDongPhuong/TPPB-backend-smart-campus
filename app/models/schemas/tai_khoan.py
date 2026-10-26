from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .yeu_cau_muon import YeuCauMuon
    from .phieu_bao_hong import PhieuBaoHong

# 1. Base schema
class TaiKhoanBase(SQLModel):
    ten_dang_nhap: str = Field(unique=True, index=True, max_length=100, description="Tên đăng nhập duy nhất")
    ho_ten: str = Field(max_length=255, description="Họ và tên")
    email: Optional[str] = Field(default=None, max_length=255, description="Email liên lạc")
    vai_tro: str = Field(default="SinhVien", description="Admin / SinhVien")
    hoat_dong: bool = Field(default=True, description="Trạng thái kích hoạt / Khóa")

# 2. Table model
class TaiKhoan(TaiKhoanBase, table=True):
    __tablename__ = "taikhoan"

    ma_tk: Optional[int] = Field(default=None, primary_key=True, description="Mã tài khoản tự tăng")
    mat_khau_hash: str = Field(description="Bản băm mật khẩu bảo mật")

    # Quan hệ
    danh_sach_yeu_cau_gui: List["YeuCauMuon"] = Relationship(
        back_populates="nguoi_gui",
        sa_relationship_kwargs={"foreign_keys": "YeuCauMuon.ma_tk"}
    )
    danh_sach_yeu_cau_duyet: List["YeuCauMuon"] = Relationship(
        back_populates="nguoi_duyet_rel",
        sa_relationship_kwargs={"foreign_keys": "YeuCauMuon.nguoi_duyet"}
    )
    danh_sach_phieu_bao: List["PhieuBaoHong"] = Relationship(
        back_populates="nguoi_bao",
        sa_relationship_kwargs={"foreign_keys": "PhieuBaoHong.ma_tk"}
    )

# 3. Create schema (Khi đăng ký / tạo tài khoản cần mật khẩu thô)
class TaiKhoanCreate(TaiKhoanBase):
    mat_khau: str = Field(min_length=6, description="Mật khẩu thô (sẽ được hash khi lưu)")

# 4. Update schema
class TaiKhoanUpdate(SQLModel):
    ho_ten: Optional[str] = None
    email: Optional[str] = None
    mat_khau: Optional[str] = None
    vai_tro: Optional[str] = None
    hoat_dong: Optional[bool] = None

# 5. Read schema (Không bao giờ trả mật khẩu về client)
class TaiKhoanRead(TaiKhoanBase):
    ma_tk: int
