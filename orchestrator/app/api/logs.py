from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, status
from ..core.sercurity import require_auth
from ..repositories.mock_repository import EXECUTION_LOGS_DB
from ..models.schemas import ExecutionLog

logs_router = APIRouter()


@logs_router.get("/admin/execution-logs", response_model=list[ExecutionLog])
def list_execution_logs(_: Annotated[dict[str, Any], Depends(require_auth)]):
    return EXECUTION_LOGS_DB


@logs_router.get("/admin/execution-logs/container/{target_container}", response_model=list[ExecutionLog])
def list_execution_logs_by_container(
    target_container: str,
    _: Annotated[dict[str, Any], Depends(require_auth)],
):
    return [
        log
        for log in EXECUTION_LOGS_DB
        if log.target_container == target_container
    ]


@logs_router.get("/admin/execution-logs/container/{target_container}/errors", response_model=list[ExecutionLog])
def list_execution_logs_with_errors_by_container(
    target_container: str,
    _: Annotated[dict[str, Any], Depends(require_auth)],
):
    return [
        log
        for log in EXECUTION_LOGS_DB
        if log.target_container == target_container and log.status != 0
    ]


@logs_router.get("/admin/execution-logs/script/{script_id}/errors", response_model=list[ExecutionLog])
def list_execution_logs_with_errors_by_script(
    script_id: int,
    _: Annotated[dict[str, Any], Depends(require_auth)],
):
    return [
        log
        for log in EXECUTION_LOGS_DB
        if log.script_id == script_id and log.status != 0
    ]
