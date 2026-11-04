import pytest
from httpx import AsyncClient

from app.api.agent import get_agent_service
from app.main import app
from app.services.agent_service import AgentService
from tests.conftest import FakeProvider, FakeToolProvider, tool_call


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_chat_valid_question_returns_200(
    client: AsyncClient, fake_provider: FakeProvider
) -> None:
    response = await client.post(
        "/api/v1/chat",
        json={"question": "Explícame Pydantic"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Respuesta simulada",
        "provider": "fake",
        "model": "fake-model",
    }
    # El router pasó la pregunta y los valores por defecto al proveedor
    call = fake_provider.calls[0]
    assert call["messages"][-1]["content"] == "Explícame Pydantic"
    assert call["temperature"] == 0.3
    assert call["max_tokens"] == 300


@pytest.mark.asyncio
async def test_chat_forwards_generation_params(
    client: AsyncClient, fake_provider: FakeProvider
) -> None:
    response = await client.post(
        "/api/v1/chat",
        json={
            "question": "¿Qué es AsyncIO?",
            "temperature": 1.0,
            "top_p": 0.8,
            "max_tokens": 100,
        },
    )

    assert response.status_code == 200
    call = fake_provider.calls[0]
    assert (call["temperature"], call["top_p"], call["max_tokens"]) == (1.0, 0.8, 100)


@pytest.mark.asyncio
async def test_chat_short_question_returns_422(
    client: AsyncClient, fake_provider: FakeProvider
) -> None:
    response = await client.post("/api/v1/chat", json={"question": "a"})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "question"]
    assert fake_provider.calls == []  # el LLM nunca se llamó


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body",
    [
        {"question": "x" * 2001},
        {},
        {"question": "¿Qué es FastAPI?", "temperature": 2},
        {"question": "¿Qué es FastAPI?", "max_tokens": 0},
    ],
)
async def test_chat_invalid_body_returns_422(
    client: AsyncClient, body: dict
) -> None:
    response = await client.post("/api/v1/chat", json=body)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_provider_error_returns_502(
    client: AsyncClient, fake_provider: FakeProvider
) -> None:
    fake_provider.fail = True

    response = await client.post(
        "/api/v1/chat", json={"question": "¿Qué es FastAPI?"}
    )

    assert response.status_code == 502
    assert "HTTP 500" in response.json()["detail"]


@pytest.mark.asyncio
async def test_info_without_api_key_reports_llm_disabled(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/info")

    assert response.status_code == 200
    body = response.json()
    assert body["llm_enabled"] is False
    assert body["name"] == "AI Knowledge Assistant"
    assert body["version"] == "0.3.0"
    assert body["llm_provider"] == "openrouter"
    assert body["llm_model"] == "openrouter/free"


@pytest.mark.asyncio
async def test_info_with_api_key_reports_llm_enabled(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    response = await client.get("/api/v1/info")

    assert response.json()["llm_enabled"] is True


@pytest.mark.asyncio
async def test_docs_and_openapi_are_available(client: AsyncClient) -> None:
    docs = await client.get("/docs")
    openapi = await client.get("/openapi.json")

    assert docs.status_code == 200
    assert openapi.status_code == 200
    paths = openapi.json()["paths"]
    assert {"/health", "/api/v1/chat", "/api/v1/info", "/api/v1/agent/chat"} <= set(paths)


def use_agent(provider: FakeToolProvider) -> None:
    """Reemplaza el agente real por uno con proveedor falso."""
    app.dependency_overrides[get_agent_service] = (
        lambda: AgentService(provider)
    )


@pytest.mark.asyncio
async def test_agent_chat_returns_answer_and_tools_used(
    client: AsyncClient,
) -> None:
    use_agent(FakeToolProvider([
        {"tool_calls": [tool_call("lookup_ai_concept", '{"concept": "rag"}')]},
        {"content": "RAG combina recuperación y generación."},
    ]))

    response = await client.post(
        "/api/v1/agent/chat", json={"question": "¿Qué es RAG?"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "RAG combina recuperación y generación.",
        "provider": "fake",
        "model": "fake-model",
        "tools_used": ["lookup_ai_concept"],
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body",
    [
        {"question": "¿Qué es RAG?", "max_steps": 6},
        {"question": "¿Qué es RAG?", "max_steps": 0},
        {"question": "a"},
    ],
)
async def test_agent_chat_invalid_body_returns_422(
    client: AsyncClient, body: dict
) -> None:
    response = await client.post("/api/v1/agent/chat", json=body)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_agent_chat_provider_error_returns_502(
    client: AsyncClient,
) -> None:
    use_agent(FakeToolProvider(fail=True))

    response = await client.post(
        "/api/v1/agent/chat", json={"question": "¿Qué es RAG?"}
    )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "No se pudo completar la ejecución del agente"
    )
