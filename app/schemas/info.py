from pydantic import BaseModel


class InfoResponse(BaseModel):
    name: str
    version: str
    environment: str
    llm_enabled: bool
    llm_provider: str
    llm_model: str
