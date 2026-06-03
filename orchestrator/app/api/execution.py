from ..core.sercurity import require_auth
from typing import Annotated, Any, Literal
from ..services.script_service import get_script_by_id
from ..services.execution_service import execute_script_flow
from ..models.schemas import ExecuteScriptResponse, ExecuteScriptRequest, ExecuteScriptManyRequest
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends

execution_router = APIRouter()


@execution_router.post("/ops/execute", response_model=ExecuteScriptResponse)
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


@execution_router.post("/ops/execute-many", response_model=list[ExecuteScriptResponse])
def execute_script_many(
    body: ExecuteScriptManyRequest,
    background_tasks: BackgroundTasks,
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> list[ExecuteScriptResponse]:
    script = get_script_by_id(body.script_id)

    if script is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Script {body.script_id} not found",
        )

    responses: list[ExecuteScriptResponse] = []

    for container in body.target_containers:
        responses.append(
            execute_script_flow(
                script,
                container,
                body.args,
                True,
                background_tasks,
            )
        )

    return responses
