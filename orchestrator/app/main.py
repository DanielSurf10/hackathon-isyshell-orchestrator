import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Literal
from pathlib import Path
import subprocess
from subprocess import TimeoutExpired

import jwt
from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from .models import Script, ExecutionLog
from .mock_repository import SCRIPTS_DB, EXECUTION_LOGS_DB

app = FastAPI(title="Orchestrator", version="0.1.0")

ALGORITHM = "HS256"
JWT_EXPIRES_MINUTES = 100

# Token permanente estará dentro de um banco de dados
PERMANENT_AUTH_TOKEN = "tokenlegalebonito"

# JWT virá de um arquivo .env
JWT_SECRET = "algumsecretlegal"

# Status de erro
EXEC_STATUS_QUEUED = 0
EXEC_STATUS_SUCCESS = 1
EXEC_STATUS_START_ERROR = 2
EXEC_STATUS_SCRIPT_ERROR = 3

bearer_scheme = HTTPBearer(auto_error=False)


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


def get_script_by_id(script_id: int) -> Script | None:
    return next((script for script in SCRIPTS_DB if script.id == script_id), None)


def next_execution_log_id() -> int:
    return max((log.id for log in EXECUTION_LOGS_DB), default=0) + 1


def save_execution_log(
        *,
        script_id: int,
        target_container: str,
        parameters_used: str,
        status: int,
        output_log: str,
        output_error_log: str,
) -> ExecutionLog:
    execution_log = ExecutionLog(
        id=next_execution_log_id(),
        script_id=script_id,
        target_container=target_container,
        parameters_used=parameters_used,
        status=status,
        output_log=output_log,
        output_error_log=output_error_log,
        executed_at=datetime.now(timezone.utc),
    )

    EXECUTION_LOGS_DB.append(execution_log)
    return execution_log


def validade_script_for_validation(script: Script, args: list[str]) -> None:
    if not script.is_active:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="A execução do script está desativada",
        )

    if not script.allow_params and args:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Script não pode receber argumentos",
        )

    file_path = Path(script.path)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Script file {'{'}{file_path}{'}'} not found",
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path to script is not a file",
        )

    if not os.access(str(file_path), os.X_OK):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Script file {'{'}{file_path}{'}'} is not executable",
        )


def run_script_flow(
        script: Script,
        target_container: str,
        args: list[str],
) -> tuple[int, str, str, str, Literal["started", "error"]]:
    parameters_used = " ".join(args) if args else ""


    # lógica de execução no para os outros containers
    # mudar esses valores para os valores que vier da execução

    # exec_status = 0     # exit code
    # output = ""         # saída padrão (fd 0)
    # output_error = ""   # saída de erro (fd 2)

    command = [script.path, *args]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )

    # Vou mudar isso
    except TimeoutExpired:
        return (
            EXEC_STATUS_SCRIPT_ERROR,
            "",
            "Execução excedeu o tempo limite",
            parameters_used,
            "error",
        )

    except:
        return (
            EXEC_STATUS_SCRIPT_ERROR,
            "",
            "Algo deu errado",
            parameters_used,
            "error",
        )

    # Finalização, montar os logs e retornar
    return (
        result.returncode,
        result.stdout,
        result.stderr,
        parameters_used,
        "started",
    )


def execute_script_flow(
        script: Script,
        target_container: str,
        args: list[str],
        run_in_background: bool,
        background_tasks: BackgroundTasks,
) -> ExecuteScriptResponse:

    try:
        validade_script_for_validation(script, args)
    except HTTPException as exc:
        save_execution_log(
            script_id=script.id,
            target_container=target_container,
            parameters_used=(" ".join(args) if args else ""),
            status=EXEC_STATUS_START_ERROR,
            output_log="",
            output_error_log=str(exc.detail),
        )
        return ExecuteScriptResponse(
            status="error",
            message=str(exc.detail),
            script_id=script.id,
            target_container=target_container,
            time_stamp=datetime.now(timezone.utc),
        )

    if run_in_background:
        background_tasks.add_task(
            run_script_flow,
            script,
            target_container,
            args,
        )
        return ExecuteScriptResponse(
            status="started",
            message="Execução iniciada em segundo plano",
            script_id=script.id,
            target_container=target_container,
            time_stamp=datetime.now(timezone.utc),
        )

    status_code_value, output_log, output_error_log, parameters_used, response_status = run_script_flow(
        script=script,
        target_container=target_container,
        args=args
    )

    save_execution_log(
        script_id=script.id,
        target_container=target_container,
        parameters_used=parameters_used,
        status=status_code_value,
        output_log=output_log,
        output_error_log=output_error_log,
    )

    return ExecuteScriptResponse(
        status=response_status,
        message="Script inciado com sucesso.",
        script_id=script.id,
        target_container=target_container,
        time_stamp=datetime.now(timezone.utc),
    )


# def run_script_in_background(
#         script: Script,
#         target_container: str,
#         args: list[str],
# ) -> None:
#     execute_script_flow(script, target_container, args)


def create_access_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=JWT_EXPIRES_MINUTES)
    # aqui vai mudar quando for fazer um token para cada usuário
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "exp"]},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


def require_auth(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais ausentes",
        )
    return decode_access_token(credentials.credentials)


@app.post("/api/v1/auth/token", response_model=AuthTokenResponse)
def issue_token(body: AuthTokenRequest) -> AuthTokenResponse:
    if not secrets.compare_digest(body.token, PERMANENT_AUTH_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    # aqui vai mudar quando for fazer um token para cada usuário
    access_token = create_access_token(subject="orchestrator-user")
    return AuthTokenResponse(
        access_token=access_token,
        expires_in=JWT_EXPIRES_MINUTES * 60
    )


@app.get("/")
def read_root() -> dict[str, str]:
    return {"service": "orchestrator", "status": "running"}


@app.get("/health")
def read_health(
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/admin/scripts", response_model=list[Script])
def list_scripts(
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> list[Script]:
    return SCRIPTS_DB


@app.post("/api/v1/admin/scripts/create", response_model=Script)
def create_script(
    body: CreateScriptRequest,
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> Script:

    file_path = Path(body.path)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Script file {'{'}{file_path}{'}'} not found",
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path is not a file",
        )

    if not os.access(str(file_path), os.X_OK):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Script file {'{'}{file_path}{'}'} is not executable",
        )

    new_id = max((script.id for script in SCRIPTS_DB), default=0) + 1
    new_script = Script(
        id=new_id,
        name=body.name,
        description=body.description,
        path=body.path,
        allow_params=body.allow_params,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    SCRIPTS_DB.append(new_script)

    return new_script


@app.put("/api/v1/admin/scripts/{script_id}/status", status_code=status.HTTP_204_NO_CONTENT)
def update_script_status(
    script_id: int,
    body: UpdateScriptStatusRequest,
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> None:
    script = get_script_by_id(script_id)
    if script is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Script {script_id} not found",
        )

    script.is_active = body.is_active

    return None


@app.post("/api/v1/ops/execute", response_model=ExecuteScriptResponse)
def execute_script(
    body: ExecuteScriptRequest,
    background_tasks: BackgroundTasks,
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> ExecuteScriptResponse:
    script = get_script_by_id(body.script_id)

    if script is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Script {body.script_id} not found",
        )
    return execute_script_flow(
        script,
        body.target_container,
        body.args,
        body.run_in_background,
        background_tasks
    )
