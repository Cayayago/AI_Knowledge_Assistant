import pytest

from app.schemas.chat import ChatResponse
from app.services.assistant_service import BootstrapAssistantService


@pytest.mark.asyncio
async def test_service_answers_known_question() -> None:
    """T-01: el servicio responde correctamente a una pregunta conocida."""
    service = BootstrapAssistantService()

    response = await service.answer("¿Qué es FastAPI?")

    assert isinstance(response, ChatResponse)
    assert "FastAPI es un framework" in response.answer
    assert response.provider == "bootstrap-local"


@pytest.mark.asyncio
async def test_service_is_case_insensitive() -> None:
    service = BootstrapAssistantService()

    response = await service.answer("explícame PYDANTIC")

    assert "Pydantic valida" in response.answer


@pytest.mark.asyncio
async def test_service_returns_default_for_unknown_question() -> None:
    service = BootstrapAssistantService()

    response = await service.answer("¿Cuál es la capital de Francia?")

    assert response.answer == BootstrapAssistantService.default_answer
    assert response.provider == "bootstrap-local"
