import logging
from contextlib import contextmanager
from sqlmodel import SQLModel, create_engine, Session

logger = logging.getLogger("smart_campus.database")

# Đường dẫn file SQLite lưu trữ ngay trong project
DATABASE_URL = "sqlite:///./campus.db"

# connect_args={"check_same_thread": False} cần thiết khi dùng SQLite với FastAPI đa luồng
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

def init_db():
    """Khởi tạo toàn bộ các bảng trong database nếu chưa tồn tại (kèm try-catch an toàn)"""
    try:
        # Import models để nạp metadata
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
