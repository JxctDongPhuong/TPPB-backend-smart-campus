from .room import router as room_router
from .booking import router as booking_router
from .devices import router as devices_router
from .metrics import router as metrics_router
from .ai_agent import router as ai_router

__all__ = [
    "room_router",
    "booking_router",
    "devices_router",
    "metrics_router",
    "ai_router"
]
