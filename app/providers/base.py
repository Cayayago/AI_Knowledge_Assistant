from typing import Protocol


class LLMProviderError(Exception):
    """Error al obtener una respuesta del proveedor LLM."""


class LLMProvider(Protocol):
    """Contrato que debe cumplir cualquier proveedor de LLM.

    Un Protocol define la "forma" esperada: cualquier clase que tenga un
    método `generate` con esta firma sirve como proveedor (OpenRouter,
    un proveedor falso para pruebas, otro proveedor en el futuro...).
    """

    @property
    def name(self) -> str: ...

    @property
    def model(self) -> str: ...

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        top_p: float = 1.0,
        max_tokens: int = 300,
    ) -> str:
        # Los puntos suspensivos indican que la implementación la aporta
        # cada clase concreta que cumpla este protocolo.
        ...
