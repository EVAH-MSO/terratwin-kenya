from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "not configured yet",
    }
