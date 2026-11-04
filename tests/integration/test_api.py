import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient) -> None:
    """T-02: GET /health retorna HTTP 200."""
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_chat_valid_question_returns_200(client: AsyncClient) -> None:
    """T-03: POST /api/v1/chat con una pregunta válida retorna HTTP 200."""
    response = await client.post(
        "/api/v1/chat",
        json={"question": "Explícame Pydantic"},
    )

    assert response.status_code == 200

    body = response.json()
    assert set(body) == {"answer", "provider"}
    assert body["provider"] == "bootstrap-local"
    assert "Pydantic" in body["answer"]


@pytest.mark.asyncio
async def test_chat_short_question_returns_422(client: AsyncClient) -> None:
    """T-04: POST /api/v1/chat con una pregunta demasiado corta retorna 422."""
    response = await client.post(
        "/api/v1/chat",
        json={"question": "a"},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "question"]


@pytest.mark.asyncio
async def test_info_returns_200_and_llm_disabled(client: AsyncClient) -> None:
    """T-05: GET /api/v1/info retorna HTTP 200 y llm_enabled = false."""
    response = await client.get("/api/v1/info")

    assert response.status_code == 200

    body = response.json()
    assert body["llm_enabled"] is False
    assert body["name"] == "AI Knowledge Assistant"
    assert body["version"] == "0.1.0"
    assert body["environment"] == "development"


@pytest.mark.asyncio
async def test_chat_long_question_returns_422(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/chat",
        json={"question": "x" * 2001},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_missing_question_returns_422(client: AsyncClient) -> None:
    response = await client.post("/api/v1/chat", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_docs_and_openapi_are_available(client: AsyncClient) -> None:
    """RF-09: la documentación OpenAPI está disponible en /docs."""
    docs = await client.get("/docs")
    openapi = await client.get("/openapi.json")

    assert docs.status_code == 200
    assert openapi.status_code == 200

    paths = openapi.json()["paths"]
    assert {"/health", "/api/v1/chat", "/api/v1/info"} <= set(paths)
