from datetime import date
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint

if TYPE_CHECKING:
    from .phong import Phong
    from .yeu_cau_muon import YeuCauMuon

# 1. Base schema
class LichPhongBase(SQLModel):
    ma_phong: str = Field(foreign_key="phong.ma_phong", description="Phòng học")
    ngay: date = Field(description="Ngày diễn ra (YYYY-MM-DD)")
    ca: int = Field(ge=1, le=4, description="Ca học 1 đến 4")
    loai: str = Field(description="HOC / MUON")
    noi_dung: str = Field(max_length=255, description="Tên lớp môn học hoặc mục đích mượn")
    so_nguoi: Optional[int] = Field(default=None, description="Số lượng người tham gia")
    ma_yc: Optional[int] = Field(default=None, foreign_key="yeucaumuon.ma_yc", description="Sinh từ yêu cầu mượn nếu có")

# 2. Table model
class LichPhong(LichPhongBase, table=True):
    __tablename__ = "lichphong"
    __table_args__ = (
        # Ràng buộc Database chặn trùng lịch trên cùng (ma_phong, ngay, ca)
        UniqueConstraint("ma_phong", "ngay", "ca", name="uq_lich_phong_ngay_ca"),
    )

    ma_lich: Optional[int] = Field(default=None, primary_key=True, description="Mã lịch tự tăng")

    # Quan hệ
    phong: Optional["Phong"] = Relationship(back_populates="danh_sach_lich")
    yeu_cau_muon: Optional["YeuCauMuon"] = Relationship(back_populates="lich_sinh_ra")

# 3. Create schema
class LichPhongCreate(LichPhongBase):
    pass

# 4. Update schema
class LichPhongUpdate(SQLModel):
    loai: Optional[str] = None
    noi_dung: Optional[str] = None
    so_nguoi: Optional[int] = None

# 5. Read schema
class LichPhongRead(LichPhongBase):
    ma_lich: int
