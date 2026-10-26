from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import (
    room_router,
    booking_router,
    devices_router,
    metrics_router,
    ai_router
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tự động tạo các bảng SQLite khi khởi động server
    init_db()
    yield

app = FastAPI(
    title="Smart Campus API",
    description="Hệ thống Quản lý Phòng học, Năng lượng & AI Agent tối ưu điện năng",
    version="1.0.0",
    lifespan=lifespan
)

# Cấu hình CORS để Frontend (React/Vite) gọi API không bị chặn
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gắn các routers vào hệ thống
app.include_router(room_router, prefix="/api")
app.include_router(booking_router, prefix="/api")
app.include_router(devices_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(ai_router, prefix="/api")

@app.get("/", tags=["Hệ Thống"])
def root():
    return {
        "message": "Smart Campus API Backend đang hoạt động bình thường!",
        "docs": "/docs",
        "redoc": "/redoc"
    }
