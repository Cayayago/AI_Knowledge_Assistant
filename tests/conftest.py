import copy
from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.chat import get_assistant_service
from app.main import app
from app.providers.base import LLMProviderError
from app.services.assistant_service import AssistantService


class FakeProvider:
    """Proveedor LLM falso: responde sin llamar a internet.

    Guarda los argumentos recibidos para poder verificarlos en las pruebas.
    """

    name = "fake"
    model = "fake-model"

    def __init__(self, answer: str = "Respuesta simulada", fail: bool = False):
        self.answer = answer
        self.fail = fail
        self.calls: list[dict] = []

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        top_p: float = 1.0,
        max_tokens: int = 300,
    ) -> str:
        self.calls.append(
            {
                "messages": messages,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
            }
        )
        if self.fail:
            raise LLMProviderError("OpenRouter respondió HTTP 500")
        return self.answer


class FakeToolProvider:
    """Proveedor falso con tool calling: entrega respuestas guionadas.

    Cada llamada a complete_with_tools devuelve la siguiente respuesta de
    la lista y guarda una copia de los mensajes que recibió.
    """

    name = "fake"
    model = "fake-model"

    def __init__(self, responses: list[dict[str, Any]] | None = None, fail: bool = False):
        self.responses = list(responses or [])
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    async def complete_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        temperature: float = 0.3,
        top_p: float = 1.0,
        max_tokens: int = 300,
    ) -> dict[str, Any]:
        self.calls.append({"messages": copy.deepcopy(messages), "tools": tools})
        if self.fail:
            raise LLMProviderError("OpenRouter respondió HTTP 500")
        return self.responses.pop(0)


def tool_call(name: str, arguments: str, call_id: str = "call_1") -> dict[str, Any]:
    """Construye un tool_call con el formato que devuelve OpenRouter."""
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": arguments},
    }


@pytest.fixture(autouse=True)
def no_real_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Las pruebas nunca usan la API key real del archivo .env."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)


@pytest.fixture
def fake_provider() -> FakeProvider:
    return FakeProvider()


@pytest_asyncio.fixture
async def client(fake_provider: FakeProvider) -> AsyncIterator[AsyncClient]:
    """Cliente HTTPX asíncrono contra la app en memoria (ASGITransport).

    Reemplaza el servicio real por uno con FakeProvider usando
    app.dependency_overrides, así /api/v1/chat no sale a internet.
    """
    app.dependency_overrides[get_assistant_service] = (
        lambda: AssistantService(fake_provider)
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as async_client:
        yield async_client

    app.dependency_overrides.clear()
