from uuid import uuid4

from app.tools.schemas import ConceptArgs, HoursArgs, TaskArgs


CONCEPTS = {
    "rag": (
        "RAG combina recuperación de información "
        "con generación de texto."
    ),
    "embedding": (
        "Un embedding representa información "
        "mediante un vector numérico."
    ),
    "function calling": (
        "Function Calling permite al modelo "
        "solicitar la ejecución de funciones externas."
    ),
    "fastapi": (
        "FastAPI es un framework de Python "
        "para construir APIs con tipado y validación."
    ),
}


# Almacenamiento temporal para el laboratorio.
# Se pierde al reiniciar el proceso.
TASKS: list[dict] = []


def lookup_ai_concept(args: ConceptArgs) -> dict:
    key = args.concept.strip().lower()
    definition = CONCEPTS.get(key)

    return {
        "found": definition is not None,
        "concept": key,
        "definition": definition,
    }


def calculate_study_hours(args: HoursArgs) -> dict:
    total = args.hours_per_day * args.days

    return {"total_hours": round(total, 2)}


def create_study_task(args: TaskArgs) -> dict:
    item = {
        "id": str(uuid4()),
        "title": args.title,
        "estimated_hours": args.estimated_hours,
    }

    TASKS.append(item)

    return {"created": True, "task": item}
