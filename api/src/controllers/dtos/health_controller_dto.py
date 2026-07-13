from pydantic import BaseModel


class HealthResponse(BaseModel):
    message: str
    version: str
    status: str
