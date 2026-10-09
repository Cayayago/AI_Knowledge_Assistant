from fastapi import APIRouter

from app.core.config import settings
from app.schemas.info import InfoResponse


router = APIRouter(
    prefix="/api/v1",
    tags=["info"],
)


@router.get(
    "/info",
    response_model=InfoResponse,
)
async def info() -> InfoResponse:
    return InfoResponse(
        name=settings.app_name,
        version=settings.version,
        environment=settings.environment,
        llm_enabled=settings.llm_enabled,
    )
