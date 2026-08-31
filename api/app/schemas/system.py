from pydantic import BaseModel


class RootResponse(BaseModel):
    message: str
    version: str
    status: str


class HealthResponse(RootResponse):
    pass
