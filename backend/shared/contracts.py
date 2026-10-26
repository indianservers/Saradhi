from typing import Literal

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class Health(BaseModel):
    status: Literal["ok", "ready", "not_ready"]
    dependencies: dict[str, Literal["ok", "unavailable"]] = {}


class PrincipalView(BaseModel):
    subject: str
    roles: list[str]
