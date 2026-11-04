import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import get_settings
from app.providers.base import LLMProviderError
from app.providers.openrouter import OpenRouterProvider
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.services.agent_service import AgentExecutionError, AgentService


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/agent",
    tags=["Agent (Módulo III)"],
)


def get_agent_service() -> AgentService:
    """Dependencia: construye el agente con el proveedor OpenRouter.

    En las pruebas se reemplaza con app.dependency_overrides.
    """
    settings = get_settings()

    provider = OpenRouterProvider(
        api_key=settings.openrouter_api_key,
        model=settings.openrouter_model,
        base_url=settings.openrouter_base_url,
    )

    return AgentService(provider)


@router.post("/chat", response_model=AgentChatResponse)
async def chat_agent(
    request: AgentChatRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> AgentChatResponse:
    try:
        result = await service.ask(
            question=request.question,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            confirm_actions=request.confirm_actions,
            max_steps=request.max_steps,
        )

    except (AgentExecutionError, LLMProviderError) as exc:
        logger.warning("Fallo del agente: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="No se pudo completar la ejecución del agente",
        ) from exc

    return AgentChatResponse(
        answer=result.answer,
        provider=service.provider.name,
        model=service.provider.model,
        tools_used=result.tools_used,
    )
