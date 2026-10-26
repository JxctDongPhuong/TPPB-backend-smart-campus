import os
import logging
from contextlib import contextmanager
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session

# Nạp file .env
load_dotenv()

logger = logging.getLogger("smart_campus.database")

# Lấy connection string từ file .env, nếu không có thì fallback về SQLite
DATABASE_URL = os.getenv("NEON_API_DB") or os.getenv("DATABASE_URL") or "sqlite:///./campus.db"

# Xử lý tương thích kết nối giữa SQLite và PostgreSQL (Neon)
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif DATABASE_URL.startswith("postgres://"):
    # SQLAlchemy 2.x yêu cầu driver postgresql+psycopg2://
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args
)

def init_db():
    """Khởi tạo toàn bộ các bảng trong database nếu chưa tồn tại"""
    try:
        import app.models  # noqa: F401
        SQLModel.metadata.create_all(engine)
        logger.info("[Database] Đã khởi tạo cấu trúc bảng Database thành công.")
    except Exception as e:
        logger.error(f"[Database Error] Lỗi khi khởi tạo database: {e}")
        raise e

def get_session():
    """Dependency cung cấp session làm việc với DB cho các Router kèm try-catch và auto-rollback"""
    session = Session(engine)
    try:
        yield session
    except Exception as e:
        logger.error(f"[Database Session Error] Lỗi trong phiên làm việc DB: {e}")
        session.rollback()
        raise e
    finally:
        session.close()

@contextmanager
def get_safe_session():
    """Context manager cung cấp session an toàn cho AI tools và background services"""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error(f"[Database SafeSession Error] Đã rollback phiên làm việc do lỗi: {e}")
        session.rollback()
        raise e
    finally:
        session.close()
