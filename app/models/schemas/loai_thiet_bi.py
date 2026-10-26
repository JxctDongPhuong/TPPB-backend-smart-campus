from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .thiet_bi import ThietBi

# 1. Base schema
class LoaiThietBiBase(SQLModel):
    ma_loai: str = Field(primary_key=True, max_length=50, description="Ví dụ: MAYLANH, QUAT, MAYCHIEU")
    ten_loai: str = Field(max_length=255, description="Tên loại thiết bị")
    cong_suat_mac_dinh_w: Optional[float] = Field(default=None, description="Công suất mặc định (W)")
    tuoi_tho_chuan_nam: Optional[int] = Field(default=None, description="Tuổi thọ chuẩn (năm) để cảnh báo thay thế")

# 2. Table model
class LoaiThietBi(LoaiThietBiBase, table=True):
    __tablename__ = "loaithietbi"

    # Quan hệ 1 Loại -> Nhiều Thiết bị
    danh_sach_thiet_bi: List["ThietBi"] = Relationship(back_populates="loai_thiet_bi")

# 3. Create schema
class LoaiThietBiCreate(LoaiThietBiBase):
    pass

# 4. Update schema
class LoaiThietBiUpdate(SQLModel):
    ten_loai: Optional[str] = None
    cong_suat_mac_dinh_w: Optional[float] = None
    tuoi_tho_chuan_nam: Optional[int] = None

# 5. Read schema
class LoaiThietBiRead(LoaiThietBiBase):
    pass
