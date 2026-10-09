from app.schemas.chat import BOOTSTRAP_PROVIDER, ChatResponse


class BootstrapAssistantService:
    """Servicio local de bootstrap.

    No usa ningún LLM: responde con un pequeño diccionario de
    conocimiento por palabra clave. En módulos posteriores esta clase
    se podrá reemplazar por un servicio que llame a un LLM real sin
    tocar el router.
    """

    _knowledge = {
        "fastapi": (
            "FastAPI es un framework de Python para "
            "construir APIs basado en type hints y ASGI."
        ),
        "pydantic": (
            "Pydantic valida y serializa datos a partir "
            "de anotaciones de tipo de Python."
        ),
        "asyncio": (
            "AsyncIO permite escribir código concurrente "
            "con async y await para tareas orientadas a E/S."
        ),
        "httpx": (
            "HTTPX es un cliente HTTP para Python con "
            "interfaces síncrona y asíncrona."
        ),
        "pytest": (
            "pytest es un framework de pruebas para Python "
            "con descubrimiento automático, asserts y fixtures."
        ),
    }

    default_answer = (
        "La API está operativa. "
        "En el siguiente módulo conectaremos "
        "el primer LLM."
    )

    async def answer(
        self,
        question: str,
    ) -> ChatResponse:

        normalized_question = question.lower()

        for keyword, answer in self._knowledge.items():
            if keyword in normalized_question:
                return ChatResponse(
                    answer=answer,
                    provider=BOOTSTRAP_PROVIDER,
                )

        return ChatResponse(
            answer=self.default_answer,
            provider=BOOTSTRAP_PROVIDER,
        )


_service = BootstrapAssistantService()


def get_assistant_service() -> BootstrapAssistantService:
    """Dependencia de FastAPI que entrega el servicio al router."""
    return _service
