import pytest
from pydantic import ValidationError

from app.schemas.chat import ChatRequest


def test_chat_request_accepts_valid_question() -> None:
    request = ChatRequest(question="  ¿Qué es FastAPI?  ")

    # str_strip_whitespace elimina espacios al inicio y al final
    assert request.question == "¿Qué es FastAPI?"


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
