from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, status
from ..core.sercurity import require_auth
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..repositories.database_repository import (
    list_execution_logs as list_execution_logs_repository,
    list_execution_logs_by_container as list_execution_logs_by_container_repository,
    list_execution_logs_with_errors_by_container as list_execution_logs_with_errors_by_container_repository,
    list_execution_logs_with_errors_by_script as list_execution_logs_with_errors_by_script_repository,
)
from ..models.schemas import ExecutionLog

logs_router = APIRouter()


@logs_router.get("/admin/execution-logs", response_model=list[ExecutionLog])
def list_execution_logs(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[dict[str, Any], Depends(require_auth)],
):
    return list_execution_logs_repository(db)


@logs_router.get("/admin/execution-logs/container/{target_container}", response_model=list[ExecutionLog])
def list_execution_logs_by_container(
    target_container: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[dict[str, Any], Depends(require_auth)],
):
    return list_execution_logs_by_container_repository(target_container, db)


@logs_router.get("/admin/execution-logs/container/{target_container}/errors", response_model=list[ExecutionLog])
def list_execution_logs_with_errors_by_container(
    target_container: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[dict[str, Any], Depends(require_auth)],
):
    return list_execution_logs_with_errors_by_container_repository(target_container, db)


@logs_router.get("/admin/execution-logs/script/{script_id}/errors", response_model=list[ExecutionLog])
def list_execution_logs_with_errors_by_script(
    script_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[dict[str, Any], Depends(require_auth)],
):
    return list_execution_logs_with_errors_by_script_repository(script_id, db)
