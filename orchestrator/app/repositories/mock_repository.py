from datetime import datetime, timezone
from ..models.schemas import Script, ExecutionLog

SCRIPTS_DB = [
    Script(
        id=1,
        name="Backup DB",
        description="Executa backup da base",
        path="/app/scripts/backup.sh",
        allow_params=True,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    ),
    Script(
        id=2,
        name="Health Check",
        description="Valida containers do orquestrador",
        path="/app/scripts/health_check.sh",
        allow_params=False,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    ),
	Script(
        id=3,
        name="Bugado",
        description="Não executar",
        path="/app/scripts/bugado.sh",
        allow_params=False,
        is_active=False,
        created_at=datetime.now(timezone.utc),
    ),
]

EXECUTION_LOGS_DB = [
    ExecutionLog(
        id=1,
        script_id=1,
        target_container="db-container",
        parameters_used="--full",
        status=0,
        output_log="Backup concluído com sucesso",
        output_error_log="",
        executed_at=datetime.now(timezone.utc),
    ),
    ExecutionLog(
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
