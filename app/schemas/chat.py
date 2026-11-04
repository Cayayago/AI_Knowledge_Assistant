from pydantic import BaseModel, ConfigDict, Field


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

    temperature: float = Field(
        default=0.3,
        ge=0,
        le=1.5,
        description="Creatividad de la respuesta (0 = más precisa).",
    )

    top_p: float = Field(
        default=1.0,
        gt=0,
        le=1,
        description="Muestreo nucleus: fracción de tokens candidatos.",
    )

    max_tokens: int = Field(
        default=300,
        ge=1,
        le=2000,
        description="Longitud máxima de la respuesta en tokens.",
    )


class ChatResponse(BaseModel):
    answer: str
    provider: str = Field(
        description="Proveedor LLM que generó la respuesta.",
        examples=["openrouter"],
    )
    model: str = Field(
        description="Modelo usado para generar la respuesta.",
        examples=["openrouter/free"],
    )
