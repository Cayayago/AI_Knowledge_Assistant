from app.providers.base import LLMProvider


SYSTEM_PROMPT = """
Eres AI Knowledge Assistant, un asistente
educativo especializado en tecnología.

Responde en español claro.
Explica los conceptos con ejemplos sencillos.
Si no tienes suficiente información, indícalo.
No inventes referencias ni datos.
""".strip()


class AssistantService:
    """Lógica del asistente: arma el prompt y delega en el proveedor LLM.

    No sabe nada de HTTP ni de OpenRouter: recibe cualquier objeto que
    cumpla el protocolo LLMProvider (inyección de dependencias).
    """

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    def build_messages(self, question: str) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]

    async def ask(
        self,
        question: str,
        temperature: float = 0.3,
        top_p: float = 1.0,
        max_tokens: int = 300,
    ) -> str:
        return await self.provider.generate(
            messages=self.build_messages(question),
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )
