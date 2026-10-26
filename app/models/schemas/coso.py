from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .phong import Phong

# 1. Base schema: các trường chung
class CoSoBase(SQLModel):
    ma_cs: str = Field(primary_key=True, max_length=20, description="Ví dụ: CS01")
    ten_cs: str = Field(max_length=255, description="Tên cơ sở")
    dia_chi: Optional[str] = Field(default=None, max_length=500, description="Địa chỉ")

# 2. Table model: bảng trong Database
class CoSo(CoSoBase, table=True):
    __tablename__ = "coso"

    # Quan hệ 1 Cơ sở -> Nhiều Phòng
    danh_sach_phong: List["Phong"] = Relationship(back_populates="co_so")

# 3. Create schema: payload khi tạo mới
class CoSoCreate(CoSoBase):
    pass

# 4. Update schema: payload khi cập nhật
class CoSoUpdate(SQLModel):
    ten_cs: Optional[str] = None
    dia_chi: Optional[str] = None

# 5. Read schema: trả về cho client
class CoSoRead(CoSoBase):
    pass
