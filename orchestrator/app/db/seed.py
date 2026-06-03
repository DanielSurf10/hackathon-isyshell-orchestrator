from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import ExecutionLogORM, ScriptORM


def seed_database(db: Session) -> None:
    has_scripts = db.scalar(select(ScriptORM.id).limit(1)) is not None
    if has_scripts:
        return

    scripts = [
        ScriptORM(
            id=1,
            name="Backup DB",
            description="Executa backup da base",
            path="/scripts/backup.sh",
            allow_params=True,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        ),
        ScriptORM(
            id=2,
            name="Health Check",
            description="Valida containers do orquestrador",
            path="/scripts/health_check.sh",
            allow_params=False,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        ),
        ScriptORM(
            id=3,
            name="Bugado",
            description="Não executar",
            path="/scripts/bugado.sh",
            allow_params=False,
            is_active=False,
            created_at=datetime.now(timezone.utc),
        ),
    ]

    execution_logs = [
        ExecutionLogORM(
            id=1,
            script_id=1,
            target_container="db-container",
            parameters_used="--full",
            status=0,
            output_log="Backup concluído com sucesso",
            output_error_log="",
            executed_at=datetime.now(timezone.utc),
        ),
        ExecutionLogORM(
            id=2,
            script_id=2,
            target_container="api-container",
            parameters_used="",
            status=500,
            output_log="",
            output_error_log="Container indisponível",
            executed_at=datetime.now(timezone.utc),
        ),
    ]

    db.add_all([*scripts, *execution_logs])
    db.commit()
