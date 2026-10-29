from fastapi import APIRouter

from app.core.settings import settings

router = APIRouter(prefix="/api/v1/config", tags=["Config"])


@router.get("")
def public_config():
    """Non-secret settings the frontend needs before anyone logs in."""
    return {
        "demo_enabled": settings.DEMO_ENABLED,
        "demo_max_messages": settings.DEMO_MAX_MESSAGES,
        "demo_ttl_hours": settings.DEMO_USER_TTL_HOURS,
    }
