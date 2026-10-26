from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .loai_thiet_bi import LoaiThietBi
    from .phong import Phong
    from .phieu_bao_hong import PhieuBaoHong

# 1. Base schema
class ThietBiBase(SQLModel):
    ma_tb: str = Field(primary_key=True, max_length=50, description="Mã thiết bị, ví dụ: ML_01-02")
    ma_loai: str = Field(foreign_key="loaithietbi.ma_loai", description="Thuộc loại thiết bị nào")
    ma_phong: Optional[str] = Field(default=None, foreign_key="phong.ma_phong", description="Phòng hiện tại, để trống = trong kho")
    ma_lo: Optional[str] = Field(default=None, max_length=50, description="Mã lô, ví dụ: ML_01 để tra nguồn gốc")
    ten_tb: Optional[str] = Field(default=None, max_length=255, description="Tên thiết bị riêng")
    cong_suat_w: Optional[float] = Field(default=None, description="Công suất riêng của máy (W)")
    nam_mua: Optional[int] = Field(default=None, description="Năm đưa vào sử dụng")
    tinh_trang: str = Field(default="Tốt", description="Tốt / Hỏng / Đang sửa / Thanh lý")
    da_xoa: bool = Field(default=False, description="Đánh dấu xóa mềm")

# 2. Table model
class ThietBi(ThietBiBase, table=True):
    __tablename__ = "thietbi"

    # Quan hệ
    loai_thiet_bi: Optional["LoaiThietBi"] = Relationship(back_populates="danh_sach_thiet_bi")
    phong: Optional["Phong"] = Relationship(back_populates="danh_sach_thiet_bi")
    danh_sach_phieu_bao_hong: List["PhieuBaoHong"] = Relationship(back_populates="thiet_bi")

# 3. Create schema
class ThietBiCreate(SQLModel):
    ma_tb: str
    ma_loai: str
    ma_phong: Optional[str] = None
    ma_lo: Optional[str] = None
    ten_tb: Optional[str] = None
    cong_suat_w: Optional[float] = None
    nam_mua: Optional[int] = None
    tinh_trang: Optional[str] = "Tốt"

# Hỗ trợ thêm hàng loạt theo lô (Admin thêm "10 máy lạnh, lô ML_01")
class ThietBiCreateBatch(SQLModel):
    ma_loai: str
    ma_lo: str
    so_luong: int = Field(gt=0, description="Số lượng máy cần tự động sinh")
    ma_phong: Optional[str] = None
    cong_suat_w: Optional[float] = None
    nam_mua: Optional[int] = None

# 4. Update schema
class ThietBiUpdate(SQLModel):
    ma_loai: Optional[str] = None
    ma_phong: Optional[str] = None
    ma_lo: Optional[str] = None
    ten_tb: Optional[str] = None
    cong_suat_w: Optional[float] = None
    nam_mua: Optional[int] = None
    tinh_trang: Optional[str] = None
    da_xoa: Optional[bool] = None

# 5. Read schema
class ThietBiRead(ThietBiBase):
    pass
