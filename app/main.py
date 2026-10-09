from fastapi import FastAPI

from app.api.routes.chat import (
    router as chat_router,
)
from app.api.routes.health import (
    router as health_router,
)
from app.api.routes.info import (
    router as info_router,
)
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    description=(
        "API evolutiva para el curso. "
    ),
    version=settings.version,
)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(info_router)
