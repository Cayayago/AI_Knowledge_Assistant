from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.info import router as info_router
from app.core.config import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "API educativa del curso de Ingeniería de Sistemas de IA "
        "con integración LLM a través de OpenRouter."
    ),
    version=settings.version,
)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(info_router)
