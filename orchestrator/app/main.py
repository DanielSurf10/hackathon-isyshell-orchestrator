from .api.logs import logs_router
from typing import Annotated, Any
from .api.auth import auth_router
from fastapi import Depends, FastAPI
from .api.scripts import scripts_router
from .core.sercurity import require_auth
from .api.execution import execution_router
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from fastapi.responses import FileResponse
from .db.database import SessionLocal, init_db
from .db.seed import seed_database

app = FastAPI(title="Orchestrator", version="0.1.0")


@app.on_event("startup")
def startup_event() -> None:
    init_db()
    with SessionLocal() as db:
        seed_database(db)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Para o hackathon, aceitamos de qualquer lugar.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(scripts_router, prefix="/api/v1")
app.include_router(execution_router, prefix="/api/v1")
app.include_router(logs_router, prefix="/api/v1")


BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "static" / "index.html"

@app.get("/", include_in_schema=False)
def read_root() -> FileResponse:
    return FileResponse(INDEX_FILE)


@app.get("/health")
def read_health(
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> dict[str, str]:
    return {"status": "ok"}
