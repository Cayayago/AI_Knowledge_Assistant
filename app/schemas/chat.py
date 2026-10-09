from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


BOOTSTRAP_PROVIDER = "bootstrap-local"


class ChatRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    question: str = Field(
        min_length=3,
        max_length=2000,
        description="Pregunta del usuario (3 a 2000 caracteres).",
        examples=["¿Qué es FastAPI?"],
    )


class ChatResponse(BaseModel):
    answer: str
    provider: Literal["bootstrap-local"] = Field(
        default=BOOTSTRAP_PROVIDER,
        description=(
            "Identifica que la respuesta proviene de una "
            "implementación local de bootstrap, no de un LLM real."
        ),
    )
