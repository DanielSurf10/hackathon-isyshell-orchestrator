from .api.logs import logs_router
from typing import Annotated, Any
from .api.auth import auth_router
from fastapi import Depends, FastAPI
from .api.scripts import scripts_router
from .core.sercurity import require_auth
from .api.execution import execution_router

app = FastAPI(title="Orchestrator", version="0.1.0")

app.include_router(auth_router, prefix="/api/v1")
app.include_router(scripts_router, prefix="/api/v1")
app.include_router(execution_router, prefix="/api/v1")
app.include_router(logs_router, prefix="/api/v1")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"service": "orchestrator", "status": "running"}


@app.get("/health")
def read_health(
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> dict[str, str]:
    return {"status": "ok"}
