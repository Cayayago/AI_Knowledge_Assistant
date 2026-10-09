"""Configuración central de la aplicación.

Se concentra aquí el nombre, la versión y el entorno para no repetir
esos valores en varios archivos (main.py, /health, /api/v1/info).
No se usan secretos ni archivos .env en este incremento.
"""

import os

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "AI Knowledge Assistant"
    service_id: str = "ai-knowledge-assistant"
    version: str = "0.1.0"
    environment: str = os.getenv("APP_ENV", "development")
    llm_enabled: bool = False  # Módulo 0: todavía NO hay LLM integrado.


settings = Settings()
