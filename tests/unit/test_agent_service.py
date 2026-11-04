import json

import pytest

from app.services.agent_service import (
    SYSTEM_PROMPT,
    AgentExecutionError,
    AgentService,
)
from tests.conftest import FakeToolProvider, tool_call


@pytest.mark.asyncio
async def test_agent_answers_directly_without_tools() -> None:
    provider = FakeToolProvider([{"content": "Hola, soy tu asistente."}])

    result = await AgentService(provider).ask("Hola")

    assert result.answer == "Hola, soy tu asistente."
    assert result.tools_used == []
    messages = provider.calls[0]["messages"]
    assert messages[0] == {"role": "system", "content": SYSTEM_PROMPT}
    assert len(provider.calls[0]["tools"]) == 3


@pytest.mark.asyncio
async def test_agent_executes_tool_and_sends_result_back() -> None:
    provider = FakeToolProvider([
        {
            "content": None,
            "tool_calls": [
                tool_call(
                    "calculate_study_hours",
                    '{"hours_per_day": 2, "days": 5}',
                )
            ],
        },
        {"content": "Estudiarás 10 horas."},
    ])

    result = await AgentService(provider).ask(
        "Si estudio 2 horas diarias durante 5 días, ¿cuántas horas estudiaré?"
    )

    assert result.answer == "Estudiarás 10 horas."
    assert result.tools_used == ["calculate_study_hours"]

    # En la 2.a ronda el LLM recibe el pedido y el resultado de la herramienta.
    second_round = provider.calls[1]["messages"]
    assert second_round[-2]["role"] == "assistant"
    assert second_round[-1]["role"] == "tool"
    assert second_round[-1]["tool_call_id"] == "call_1"
    assert json.loads(second_round[-1]["content"]) == {
        "ok": True,
        "data": {"total_hours": 10.0},
    }


@pytest.mark.asyncio
async def test_agent_write_tool_without_confirmation_is_blocked() -> None:
    provider = FakeToolProvider([
        {
            "tool_calls": [
                tool_call(
                    "create_study_task",
                    '{"title": "Repasar RAG", "estimated_hours": 2}',
                )
            ]
        },
        {"content": "No pude crear la tarea sin confirmación."},
    ])

    result = await AgentService(provider).ask("Crea una tarea para repasar RAG")

    tool_message = provider.calls[1]["messages"][-1]
    assert json.loads(tool_message["content"]) == {
        "ok": False,
        "error": "confirmation_required",
    }
    assert result.tools_used == ["create_study_task"]


@pytest.mark.asyncio
async def test_agent_stops_after_max_steps() -> None:
    loop = {"tool_calls": [tool_call("lookup_ai_concept", '{"concept": "rag"}')]}
    provider = FakeToolProvider([loop, loop])

    with pytest.raises(AgentExecutionError, match="Límite de rondas"):
        await AgentService(provider).ask("¿Qué es RAG?", max_steps=2)

    assert len(provider.calls) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        {"tool_calls": [{"function": {"name": "x", "arguments": "{}"}}]},
        {"tool_calls": [{"id": "c1", "function": "no-es-dict"}]},
        {"tool_calls": [{"id": "c1", "function": {"name": "x", "arguments": {}}}]},
        {"tool_calls": "no-es-lista"},
        {"content": "   "},
    ],
)
async def test_agent_rejects_invalid_llm_responses(response: dict) -> None:
    provider = FakeToolProvider([response])

    with pytest.raises(AgentExecutionError):
        await AgentService(provider).ask("¿Qué es RAG?")
