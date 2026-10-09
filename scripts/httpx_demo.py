"""Demostración de HTTPX asíncrono contra la API en ejecución.

Requiere la API levantada en otra terminal:
    fastapi dev app/main.py
Luego:
    python scripts/httpx_demo.py
"""

import asyncio
import time

import httpx


BASE_URL = "http://127.0.0.1:8000"


async def ask(client: httpx.AsyncClient, question: str) -> dict:
    response = await client.post(
        "/api/v1/chat",
        json={"question": question},
    )
    return {"status": response.status_code, "body": response.json()}


async def main() -> None:
    async with httpx.AsyncClient(
        base_url=BASE_URL,
        timeout=5.0,
    ) as client:

        try:
            health_response = await client.get("/health")
        except httpx.ConnectError:
            print(
                f"No se pudo conectar a {BASE_URL}. "
                "Inicia la API con: fastapi dev app/main.py"
            )
            return

        print("Health:", health_response.json())

        info_response = await client.get("/api/v1/info")
        print("Info:", info_response.json())

        # Varias peticiones concurrentes con asyncio.gather
        questions = [
            "¿Qué es AsyncIO?",
            "¿Qué es FastAPI?",
            "¿Para qué sirve Pydantic?",
        ]

        start = time.perf_counter()
        results = await asyncio.gather(
            *(ask(client, q) for q in questions)
        )
        elapsed = time.perf_counter() - start

        for question, result in zip(questions, results):
            print(f"Chat [{question}] ->", result)

        print(f"{len(questions)} peticiones concurrentes en {elapsed:.3f} s")

        # Entrada inválida: Pydantic la rechaza con HTTP 422
        invalid = await client.post(
            "/api/v1/chat",
            json={"question": "a"},
        )
        print("Pregunta inválida ->", invalid.status_code)


if __name__ == "__main__":
    asyncio.run(main())
