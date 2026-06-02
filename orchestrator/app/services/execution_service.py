import os
import subprocess
from pathlib import Path
from typing import Literal
from subprocess import TimeoutExpired
from datetime import datetime, timezone
from fastapi import HTTPException, status, BackgroundTasks
from ..services.script_service import next_execution_log_id
from ..repositories.mock_repository import EXECUTION_LOGS_DB
from ..models.schemas import ExecutionLog, ExecuteScriptResponse, Script


# Status de erro
EXEC_STATUS_QUEUED = 0
EXEC_STATUS_SUCCESS = 1
EXEC_STATUS_START_ERROR = 2
EXEC_STATUS_SCRIPT_ERROR = 3


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
