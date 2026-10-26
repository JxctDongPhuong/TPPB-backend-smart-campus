from datetime import date
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .phong import Phong

# 1. Base schema
class DienNangBase(SQLModel):
    ma_phong: str = Field(foreign_key="phong.ma_phong", primary_key=True, description="Khóa chính 1: Phòng")
    ngay: date = Field(primary_key=True, description="Khóa chính 2: Ngày ghi nhận (YYYY-MM-DD)")
    kwh: float = Field(ge=0, description="Điện năng tiêu thụ trong ngày (kWh)")
    so_gio_bat: Optional[float] = Field(default=None, ge=0, le=24, description="Số giờ thiết bị hoạt động")

# 2. Table model
class DienNang(DienNangBase, table=True):
    __tablename__ = "diennang"

    # Quan hệ
    phong: Optional["Phong"] = Relationship(back_populates="danh_sach_dien_nang")

# 3. Create schema
class DienNangCreate(DienNangBase):
    pass

# 4. Update schema
class DienNangUpdate(SQLModel):
    kwh: Optional[float] = None
    so_gio_bat: Optional[float] = None

# 5. Read schema
class DienNangRead(DienNangBase):
    pass
