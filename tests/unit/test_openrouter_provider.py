"""Pruebas del proveedor OpenRouter SIN red.

httpx.MockTransport intercepta la petición HTTP y devuelve una respuesta
simulada, así se prueba el código real del proveedor sin gastar créditos.
"""

import httpx
import pytest

from app.providers.base import LLMProviderError
from app.providers.openrouter import OpenRouterProvider


def make_provider(handler, api_key: str = "test-key") -> OpenRouterProvider:
    return OpenRouterProvider(
        api_key=api_key,
        model="openrouter/free",
        base_url="https://openrouter.ai/api/v1/",
        transport=httpx.MockTransport(handler),
    )


MESSAGES = [{"role": "user", "content": "Hola"}]


@pytest.mark.asyncio
async def test_generate_returns_content_and_sends_correct_request() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["Authorization"]
        seen["body"] = request.read().decode()
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "  Hola, ¿en qué te ayudo?  "}}]},
        )

    answer = await make_provider(handler).generate(MESSAGES, max_tokens=50)

    assert answer == "Hola, ¿en qué te ayudo?"
    assert seen["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert seen["auth"] == "Bearer test-key"
    assert '"max_tokens":50' in seen["body"].replace(" ", "")


@pytest.mark.asyncio
async def test_generate_without_api_key_raises() -> None:
    provider = make_provider(lambda request: httpx.Response(200), api_key="")

    with pytest.raises(LLMProviderError, match="OPENROUTER_API_KEY"):
        await provider.generate(MESSAGES)


@pytest.mark.asyncio
async def test_generate_http_error_raises() -> None:
    provider = make_provider(lambda request: httpx.Response(401, json={}))

    with pytest.raises(LLMProviderError, match="HTTP 401"):
        await provider.generate(MESSAGES)


@pytest.mark.asyncio
async def test_generate_http_error_includes_openrouter_message() -> None:
    provider = make_provider(
        lambda request: httpx.Response(
            404, json={"error": {"message": "No endpoints found", "code": 404}}
        )
    )

    with pytest.raises(LLMProviderError, match="HTTP 404 - No endpoints found"):
        await provider.generate(MESSAGES)


@pytest.mark.asyncio
async def test_generate_timeout_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout", request=request)

    with pytest.raises(LLMProviderError, match="Tiempo de espera"):
        await make_provider(handler).generate(MESSAGES)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body",
    [{}, {"choices": []}, {"choices": [{"message": {"content": "   "}}]}],
)
async def test_generate_invalid_format_raises(body: dict) -> None:
    provider = make_provider(lambda request: httpx.Response(200, json=body))

    with pytest.raises(LLMProviderError, match="Formato"):
        await provider.generate(MESSAGES)


@pytest.mark.asyncio
async def test_generate_empty_content_by_length_explains_max_tokens() -> None:
    body = {
        "choices": [
            {"message": {"content": "", "reasoning": "Pensando..."}, "finish_reason": "length"}
        ]
    }
    provider = make_provider(lambda request: httpx.Response(200, json=body))

    with pytest.raises(LLMProviderError, match="max_tokens"):
        await provider.generate(MESSAGES)


@pytest.mark.asyncio
async def test_generate_error_inside_200_response_raises() -> None:
    body = {"error": {"message": "Provider returned error", "code": 502}}
    provider = make_provider(lambda request: httpx.Response(200, json=body))

    with pytest.raises(LLMProviderError, match="Provider returned error"):
        await provider.generate(MESSAGES)
