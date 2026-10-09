from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
)
from app.services.assistant_service import (
    BootstrapAssistantService,
    get_assistant_service,
)


router = APIRouter(
    prefix="/api/v1/chat",
    tags=["chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
async def chat(
    payload: ChatRequest,
    service: Annotated[
        BootstrapAssistantService,
        Depends(get_assistant_service),
    ],
) -> ChatResponse:
    # El router solo recibe el request ya validado por Pydantic
    # y delega la lógica en la capa de servicio (RF-08).
    return await service.answer(
        payload.question,
    )
