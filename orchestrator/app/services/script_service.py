from ..repositories.mock_repository import SCRIPTS_DB, EXECUTION_LOGS_DB
from ..models.schemas import Script


def get_script_by_id(script_id: int) -> Script | None:
    return next((script for script in SCRIPTS_DB if script.id == script_id), None)


def next_execution_log_id() -> int:
    return max((log.id for log in EXECUTION_LOGS_DB), default=0) + 1
