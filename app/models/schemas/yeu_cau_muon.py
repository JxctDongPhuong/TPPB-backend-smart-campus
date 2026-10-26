from datetime import date, datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .tai_khoan import TaiKhoan
    from .phong import Phong
    from .lich_phong import LichPhong

# 1. Base schema
class YeuCauMuonBase(SQLModel):
    ma_tk: int = Field(foreign_key="taikhoan.ma_tk", description="Người tạo yêu cầu")
    ma_phong: str = Field(foreign_key="phong.ma_phong", description="Phòng muốn mượn")
    ngay: date = Field(description="Ngày cần mượn (YYYY-MM-DD)")
    ca: int = Field(ge=1, le=4, description="Ca muốn mượn (1-4)")
    so_nguoi: int = Field(gt=0, description="Số lượng người tham gia")
    muc_dich: str = Field(max_length=500, description="Mục đích sử dụng phòng")
    trang_thai: str = Field(default="ChoDuyet", description="ChoDuyet / DaDuyet / TuChoi / DaHuy")
    ghi_chu: Optional[str] = Field(default=None, max_length=500, description="Ghi chú thêm hoặc lý do từ chối")

# 2. Table model
class YeuCauMuon(YeuCauMuonBase, table=True):
    __tablename__ = "yeucaumuon"

    ma_yc: Optional[int] = Field(default=None, primary_key=True, description="Mã yêu cầu tự tăng")
    ngay_gui: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Thời điểm gửi yêu cầu")
    nguoi_duyet: Optional[int] = Field(default=None, foreign_key="taikhoan.ma_tk", description="Admin xử lý")
    ngay_duyet: Optional[datetime] = Field(default=None, description="Thời điểm duyệt")

    # Quan hệ
    nguoi_gui: Optional["TaiKhoan"] = Relationship(
        back_populates="danh_sach_yeu_cau_gui",
        sa_relationship_kwargs={"foreign_keys": "YeuCauMuon.ma_tk"}
    )
    nguoi_duyet_rel: Optional["TaiKhoan"] = Relationship(
        back_populates="danh_sach_yeu_cau_duyet",
        sa_relationship_kwargs={"foreign_keys": "YeuCauMuon.nguoi_duyet"}
    )
    phong: Optional["Phong"] = Relationship(back_populates="danh_sach_yeu_cau_muon")
    lich_sinh_ra: Optional["LichPhong"] = Relationship(back_populates="yeu_cau_muon")

# 3. Create schema (Sinh viên gửi lên)
class YeuCauMuonCreate(SQLModel):
    ma_phong: str
    ngay: date
    ca: int
    so_nguoi: int
    muc_dich: str
    ghi_chu: Optional[str] = None

# 4. Admin duyệt / từ chối
class YeuCauMuonDuyet(SQLModel):
    trang_thai: str = Field(description="DaDuyet / TuChoi")
    ghi_chu: Optional[str] = None

# 5. Read schema
class YeuCauMuonRead(YeuCauMuonBase):
    ma_yc: int
    ngay_gui: datetime
    nguoi_duyet: Optional[int] = None
    ngay_duyet: Optional[datetime] = None
