import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import docker
from docker.errors import APIError, DockerException, NotFound
from fastapi import BackgroundTasks, HTTPException, status

from ..models.schemas import ExecutionLog, ExecuteScriptResponse, Script
from ..notifications.dispatcher import AlertDispatcher
from ..repositories.mock_repository import EXECUTION_LOGS_DB
from ..services.script_service import next_execution_log_id


# Status de erro
EXEC_STATUS_SUCCESS = 0
EXEC_STATUS_START_ERROR = -1


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


def get_docker_client() -> docker.DockerClient:
    return docker.from_env()


def validade_script_for_validation(script: Script, args: list[str]) -> None:
    if not script.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
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


def find_target_container(client: docker.DockerClient, target_container: str):
    try:
        return client.containers.get(target_container)
    except NotFound:
        pass

    containers = client.containers.list(
        all=True,
        filters={"label": f"com.docker.compose.service={target_container}"},
    )
    if containers:
        return containers[0]

    containers = client.containers.list(all=True)
    for container in containers:
        if container.name == target_container or target_container in container.name:
            return container

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Container {target_container} not found",
    )


def decode_bytes(value: bytes | None) -> str:
    if not value:
        return ""
    return value.decode("utf-8", errors="replace")


def build_alert_payload(
    *,
    script_id: int,
    target_container: str,
    status_code_value: int,
    output_error_log: str,
) -> dict[str, Any]:
    return {
        "script_id": script_id,
        "target_container": target_container,
        "status": status_code_value,
        "output_error_log": output_error_log,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def run_script_flow(
    script: Script,
    target_container: str,
    args: list[str],
) -> tuple[int, str, str, str]:
    parameters_used = " ".join(args) if args else ""
    client = get_docker_client()

    try:
        container = find_target_container(client, target_container)
    except HTTPException:
        raise
    except DockerException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao localizar container {target_container}: {exc}",
        ) from exc

    try:
        exec_result = container.exec_run(
            cmd=[script.path, *args],
            stdout=True,
            stderr=True,
            demux=True,
            workdir="/scripts",
        )
    except APIError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao iniciar execução no container {target_container}: {exc.explanation or str(exc)}",
        ) from exc
    except DockerException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao executar script no container {target_container}: {exc}",
        ) from exc

    stdout_bytes, stderr_bytes = (None, None)
    if isinstance(exec_result.output, tuple):
        stdout_bytes, stderr_bytes = exec_result.output
    else:
        stdout_bytes = exec_result.output

    exit_code = exec_result.exit_code if exec_result.exit_code is not None else 1
    output_log = decode_bytes(stdout_bytes)
    output_error_log = decode_bytes(stderr_bytes)

    return exit_code, output_log, output_error_log, parameters_used


async def dispatch_alert(dispatcher: AlertDispatcher, payload: dict[str, Any]) -> None:
    await dispatcher.dispatch(payload)


def dispatch_alert_in_background(dispatcher: AlertDispatcher, payload: dict[str, Any]) -> None:
    asyncio.run(dispatch_alert(dispatcher, payload))


def execute_script_in_background(
    script: Script,
    target_container: str,
    args: list[str],
    alert_dispatcher: AlertDispatcher,
) -> None:
    try:
        status_code_value, output_log, output_error_log, parameters_used = run_script_flow(
            script=script,
            target_container=target_container,
            args=args,
        )
    except HTTPException as exc:
        status_code_value = EXEC_STATUS_START_ERROR
        output_log = ""
        output_error_log = str(exc.detail)
        parameters_used = " ".join(args) if args else ""

    save_execution_log(
        script_id=script.id,
        target_container=target_container,
        parameters_used=parameters_used,
        status=status_code_value,
        output_log=output_log,
        output_error_log=output_error_log,
    )

    if status_code_value != EXEC_STATUS_SUCCESS:
        asyncio.run(
            alert_dispatcher.dispatch(
                build_alert_payload(
                    script_id=script.id,
                    target_container=target_container,
                    status_code_value=status_code_value,
                    output_error_log=output_error_log,
                )
            )
        )


def execute_script_flow(
    script: Script,
    target_container: str,
    args: list[str],
    run_in_background: bool,
    background_tasks: BackgroundTasks,
    alert_dispatcher: AlertDispatcher,
) -> ExecuteScriptResponse:

    try:
        validade_script_for_validation(script, args)
    except HTTPException as exc:
        status_code_value = EXEC_STATUS_START_ERROR
        save_execution_log(
            script_id=script.id,
            target_container=target_container,
            parameters_used=(" ".join(args) if args else ""),
            status=status_code_value,
            output_log="",
            output_error_log=str(exc.detail),
        )
        payload = build_alert_payload(
            script_id=script.id,
            target_container=target_container,
            status_code_value=status_code_value,
            output_error_log=str(exc.detail),
        )
        background_tasks.add_task(dispatch_alert_in_background, alert_dispatcher, payload)
        return ExecuteScriptResponse(
            status="error",
            message=str(exc.detail),
            script_id=script.id,
            target_container=target_container,
            time_stamp=datetime.now(timezone.utc),
        )

    if run_in_background:
        background_tasks.add_task(
            execute_script_in_background,
            script,
            target_container,
            args,
            alert_dispatcher,
        )
        return ExecuteScriptResponse(
            status="started",
            message="Execução iniciada em segundo plano",
            script_id=script.id,
            target_container=target_container,
            time_stamp=datetime.now(timezone.utc),
        )

    status_code_value, output_log, output_error_log, parameters_used = run_script_flow(
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

    if status_code_value != EXEC_STATUS_SUCCESS:
        payload = build_alert_payload(
            script_id=script.id,
            target_container=target_container,
            status_code_value=status_code_value,
            output_error_log=output_error_log,
        )
        background_tasks.add_task(dispatch_alert_in_background, alert_dispatcher, payload)

    return ExecuteScriptResponse(
        status="started",
        message=(
            "Script executado com sucesso."
            if status_code_value == EXEC_STATUS_SUCCESS
            else f"Script executado com erro interno. Exit code: {status_code_value}"
        ),
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
