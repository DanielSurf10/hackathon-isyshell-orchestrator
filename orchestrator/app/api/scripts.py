import os
from pathlib import Path
from typing import Annotated, Any
from datetime import datetime, timezone
from ..core.sercurity import require_auth
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..repositories.database_repository import (
    create_script as create_script_repository,
    list_scripts as list_scripts_repository,
    update_script_status as update_script_status_repository,
)
from ..services.script_service import get_script_by_id
from fastapi import APIRouter, HTTPException, status, Depends
from ..models.schemas import Script, CreateScriptRequest, UpdateScriptStatusRequest

scripts_router = APIRouter()


@scripts_router.get("/admin/scripts", response_model=list[Script])
def list_scripts(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> list[Script]:
    return list_scripts_repository(db)


@scripts_router.post("/admin/scripts/create", response_model=Script)
def create_script(
    body: CreateScriptRequest,
    db: Annotated[Session, Depends(get_db)],
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

    return create_script_repository(
        name=body.name,
        description=body.description,
        path=body.path,
        allow_params=body.allow_params,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        db=db,
    )


@scripts_router.put("/admin/scripts/{script_id}/status", status_code=status.HTTP_204_NO_CONTENT)
def update_script_status(
    script_id: int,
    body: UpdateScriptStatusRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> None:
    script = get_script_by_id(script_id, db)
    if script is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Script {script_id} not found",
        )

    update_script_status_repository(script_id, body.is_active, db)

    return None
