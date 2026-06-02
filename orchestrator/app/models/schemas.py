from typing import Literal
from datetime import datetime
from pydantic import BaseModel, Field


class Script(BaseModel):
    id: int
    name: str
    description: str
    path: str
    allow_params: bool
    is_active: bool
    created_at: datetime


class ExecutionLog(BaseModel):
    id: int
    script_id: int
    target_container: str
    parameters_used: str = ""
    status: int
    output_log: str
    output_error_log: str
    executed_at: datetime


class AuthTokenRequest(BaseModel):
    token: str = Field(..., min_length=8)


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class CreateScriptRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    allow_params: bool


class UpdateScriptStatusRequest(BaseModel):
    is_active: bool


class ExecuteScriptRequest(BaseModel):
    script_id: int
    target_container: str = Field(..., min_length=1)
    args: list[str] = Field(default_factory=list)
    run_in_background: bool = False


class ExecuteScriptResponse(BaseModel):
    status: Literal["started", "error"]
    message: str
    script_id: int
    target_container: str
    time_stamp: datetime
