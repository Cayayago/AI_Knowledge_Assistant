import json

from app.tools.registry import execute_tool, tool_definitions


def test_tool_definitions_expose_three_tools_with_strict_schemas() -> None:
    definitions = tool_definitions()

    names = [d["function"]["name"] for d in definitions]
    assert names == [
        "lookup_ai_concept",
        "calculate_study_hours",
        "create_study_task",
    ]
    for definition in definitions:
        assert definition["type"] == "function"
        assert definition["function"]["parameters"]["additionalProperties"] is False


def test_calculate_study_hours() -> None:
    result = execute_tool(
        "calculate_study_hours",
        json.dumps({"hours_per_day": 2, "days": 5}),
        confirm_actions=False,
    )

    assert result == {"ok": True, "data": {"total_hours": 10.0}}


def test_lookup_ai_concept_is_case_insensitive() -> None:
    result = execute_tool(
        "lookup_ai_concept", '{"concept": "  RAG "}', confirm_actions=False
    )

    assert result["ok"] is True
    assert result["data"]["found"] is True
    assert result["data"]["concept"] == "rag"


def test_lookup_unknown_concept_returns_not_found() -> None:
    result = execute_tool(
        "lookup_ai_concept", '{"concept": "blockchain"}', confirm_actions=False
    )

    assert result["data"] == {
        "found": False,
        "concept": "blockchain",
        "definition": None,
    }


def test_unknown_tool() -> None:
    assert execute_tool("borrar_todo", "{}", confirm_actions=True) == {
        "ok": False,
        "error": "unknown_tool",
    }


def test_write_tool_requires_confirmation() -> None:
    args = json.dumps({"title": "Repasar RAG", "estimated_hours": 2})

    assert execute_tool("create_study_task", args, confirm_actions=False) == {
        "ok": False,
        "error": "confirmation_required",
    }


def test_write_tool_runs_when_confirmed() -> None:
    args = json.dumps({"title": "Repasar RAG", "estimated_hours": 2})

    result = execute_tool("create_study_task", args, confirm_actions=True)

    assert result["ok"] is True
    assert result["data"]["created"] is True
    assert result["data"]["task"]["title"] == "Repasar RAG"


def test_invalid_arguments_are_rejected() -> None:
    for raw in (
        "no es json",
        '{"hours_per_day": 0, "days": 5}',
        '{"hours_per_day": 2, "days": 5, "extra": 1}',
    ):
        assert execute_tool(
            "calculate_study_hours", raw, confirm_actions=False
        ) == {"ok": False, "error": "invalid_arguments"}
