import pytest
from pydantic import ValidationError

from app.schemas.chat import ChatRequest


def test_chat_request_accepts_valid_question_and_defaults() -> None:
    request = ChatRequest(question="  ¿Qué es FastAPI?  ")

    # str_strip_whitespace elimina espacios al inicio y al final
    assert request.question == "¿Qué es FastAPI?"
    assert request.temperature == 0.3
    assert request.top_p == 1.0
    assert request.max_tokens == 300


@pytest.mark.parametrize(
    "question",
    ["", "ab", "   ", "x" * 2001],
)
def test_chat_request_rejects_invalid_length(question: str) -> None:
    with pytest.raises(ValidationError):
        ChatRequest(question=question)


def test_chat_request_accepts_limits() -> None:
    assert ChatRequest(question="abc").question == "abc"
    assert len(ChatRequest(question="x" * 2000).question) == 2000


@pytest.mark.parametrize(
    "field, value",
    [
        ("temperature", -0.1),
        ("temperature", 1.6),
        ("top_p", 0),
        ("top_p", 1.1),
        ("max_tokens", 0),
        ("max_tokens", 2001),
    ],
)
def test_chat_request_rejects_invalid_generation_params(
    field: str, value: float
) -> None:
    with pytest.raises(ValidationError):
        ChatRequest(question="¿Qué es FastAPI?", **{field: value})
