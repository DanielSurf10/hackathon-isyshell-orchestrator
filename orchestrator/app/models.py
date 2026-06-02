from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

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
