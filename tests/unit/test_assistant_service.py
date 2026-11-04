import pytest

from app.services.assistant_service import SYSTEM_PROMPT, AssistantService
from tests.conftest import FakeProvider


@pytest.mark.asyncio
async def test_service_returns_provider_answer() -> None:
    provider = FakeProvider(answer="FastAPI es un framework web.")
    service = AssistantService(provider)

    answer = await service.ask("¿Qué es FastAPI?")

    assert answer == "FastAPI es un framework web."


@pytest.mark.asyncio
async def test_service_sends_system_prompt_and_question() -> None:
    provider = FakeProvider()
    service = AssistantService(provider)

    await service.ask("¿Qué es Pydantic?")

    messages = provider.calls[0]["messages"]
    assert messages[0] == {"role": "system", "content": SYSTEM_PROMPT}
    assert messages[1] == {"role": "user", "content": "¿Qué es Pydantic?"}


@pytest.mark.asyncio
async def test_service_forwards_generation_parameters() -> None:
    provider = FakeProvider()
    service = AssistantService(provider)

    await service.ask(
        "¿Qué es AsyncIO?", temperature=0.9, top_p=0.5, max_tokens=50
    )

    call = provider.calls[0]
    assert call["temperature"] == 0.9
    assert call["top_p"] == 0.5
    assert call["max_tokens"] == 50
