from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .tai_khoan import TaiKhoan
    from .phong import Phong
    from .thiet_bi import ThietBi

# 1. Base schema
class PhieuBaoHongBase(SQLModel):
    ma_phong: str = Field(foreign_key="phong.ma_phong", description="Phòng xảy ra sự cố (bắt buộc)")
    ma_tb: Optional[str] = Field(default=None, foreign_key="thietbi.ma_tb", description="Mã thiết bị nếu biết, để trống nếu không rõ")
    mo_ta: str = Field(max_length=1000, description="Mô tả hiện tượng hư hỏng")
    trang_thai: str = Field(default="Moi", description="Moi / DangXuLy / DaXuLy / TuChoi")

# 2. Table model
class PhieuBaoHong(PhieuBaoHongBase, table=True):
    __tablename__ = "phieubaohong"

    ma_phieu: Optional[int] = Field(default=None, primary_key=True, description="Mã phiếu tự tăng")
    ma_tk: int = Field(foreign_key="taikhoan.ma_tk", description="Người gửi báo hỏng")
    ngay_bao: datetime = Field(default_factory=datetime.utcnow, description="Thời điểm báo")
    ghi_chu_admin: Optional[str] = Field(default=None, max_length=500, description="Ghi chú kết quả xử lý của quản trị viên")
    ngay_xu_ly: Optional[datetime] = Field(default=None, description="Thời điểm hoàn tất xử lý")

    # Quan hệ
    nguoi_bao: Optional["TaiKhoan"] = Relationship(
        back_populates="danh_sach_phieu_bao",
        sa_relationship_kwargs={"foreign_keys": "PhieuBaoHong.ma_tk"}
    )
    phong: Optional["Phong"] = Relationship(back_populates="danh_sach_phieu_bao_hong")
    thiet_bi: Optional["ThietBi"] = Relationship(back_populates="danh_sach_phieu_bao_hong")

# 3. Create schema (Sinh viên báo hỏng)
class PhieuBaoHongCreate(SQLModel):
    ma_phong: str
    ma_tb: Optional[str] = None
    mo_ta: str

# 4. Update schema (Admin cập nhật tiến độ / gán mã máy nếu lúc báo sinh viên để trống)
class PhieuBaoHongUpdate(SQLModel):
    ma_tb: Optional[str] = None
    trang_thai: Optional[str] = None
    ghi_chu_admin: Optional[str] = None
    ngay_xu_ly: Optional[datetime] = None

# 5. Read schema
class PhieuBaoHongRead(PhieuBaoHongBase):
    ma_phieu: int
    ma_tk: int
    ngay_bao: datetime
    ghi_chu_admin: Optional[str] = None
    ngay_xu_ly: Optional[datetime] = None
