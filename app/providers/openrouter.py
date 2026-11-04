from typing import Any

import httpx

from app.providers.base import LLMProviderError


class OpenRouterProvider:
    """Proveedor LLM que usa la API de OpenRouter (compatible con OpenAI).

    - generate(): respuesta de texto (POST /api/v1/chat).
    - complete_with_tools(): respuesta que puede pedir herramientas
      (POST /api/v1/agent/chat, Módulo III).
    """

    name = "openrouter"

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        timeout: float = 30.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        # transport permite simular OpenRouter en las pruebas (sin red).
        self._transport = transport

    async def _request(
        self,
        messages: list[dict[str, Any]],
        temperature: float,
        top_p: float,
        max_tokens: int,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Llama a /chat/completions y devuelve el primer choice."""

        if not self.api_key:
            raise LLMProviderError(
                "No se configuró OPENROUTER_API_KEY"
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            # Sin streaming: se recibe la respuesta completa de una vez.
            "stream": False,
        }

        if tools is not None:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                transport=self._transport,
            ) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )

                response.raise_for_status()
                data = response.json()

        except httpx.TimeoutException as exc:
            raise LLMProviderError(
                "Tiempo de espera agotado"
            ) from exc

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            reason = self._error_message(exc.response)
            raise LLMProviderError(
                f"OpenRouter respondió HTTP {status}"
                + (f" - {reason}" if reason else "")
            ) from exc

        except (httpx.RequestError, ValueError) as exc:
            raise LLMProviderError(
                "Error de comunicación con el proveedor"
            ) from exc

        # OpenRouter puede responder HTTP 200 con un error dentro del JSON.
        if isinstance(data, dict) and data.get("error"):
            message = str(data["error"].get("message", "")).strip()
            raise LLMProviderError(
                f"El proveedor devolvió un error: {message or 'sin detalle'}"
            )

        try:
            choice = data["choices"][0]
            if not isinstance(choice["message"], dict):
                raise TypeError("Mensaje inválido")
            return choice

        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError(
                "Formato de respuesta LLM inválido"
            ) from exc

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        top_p: float = 1.0,
        max_tokens: int = 300,
    ) -> str:
        choice = await self._request(
            messages, temperature, top_p, max_tokens
        )

        content = choice["message"].get("content")

        if not isinstance(content, str) or not content.strip():
            # Modelos de razonamiento: si max_tokens se agota mientras
            # "piensan", la respuesta visible (content) llega vacía.
            if choice.get("finish_reason") == "length":
                raise LLMProviderError(
                    "El modelo agotó max_tokens antes de responder; "
                    "aumenta max_tokens (los modelos de razonamiento "
                    "gastan tokens pensando)"
                )
            raise LLMProviderError(
                "Formato de respuesta LLM inválido"
            )

        return content.strip()

    async def complete_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        temperature: float = 0.3,
        top_p: float = 1.0,
        max_tokens: int = 300,
    ) -> dict[str, Any]:
        """Devuelve el mensaje del asistente (content y/o tool_calls)."""
        choice = await self._request(
            messages, temperature, top_p, max_tokens, tools=tools
        )
        return choice["message"]

    @staticmethod
    def _error_message(response: httpx.Response) -> str:
        """Extrae el mensaje de error que envía OpenRouter, si existe."""
        try:
            error = response.json().get("error", {})
            return str(error.get("message", "")).strip()
        except (ValueError, AttributeError):
            return ""
