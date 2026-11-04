"""Configuración central de la aplicación.

Los valores sensibles (la API key de OpenRouter) se leen de variables de
entorno o de un archivo .env local que NUNCA se sube a Git.
Ver .env.example para saber qué variables definir.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Carga las variables del archivo .env (si existe) en os.environ.
load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str
    service_id: str
    version: str
    environment: str
    openrouter_api_key: str
    openrouter_model: str
    openrouter_base_url: str

    @property
    def llm_enabled(self) -> bool:
        """El LLM está habilitado solo si hay una API key configurada."""
        return bool(self.openrouter_api_key)


def get_settings() -> Settings:
    return Settings(
        app_name="AI Knowledge Assistant",
        service_id="ai-knowledge-assistant",
        version="0.3.0",
        environment=os.getenv("APP_ENV", "development"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
        openrouter_model=os.getenv(
            "OPENROUTER_MODEL", "openrouter/free"
        ),
        openrouter_base_url=os.getenv(
            "OPENROUTER_BASE_URL",
            "https://openrouter.ai/api/v1",
        ),
    )
