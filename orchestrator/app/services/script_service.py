from sqlalchemy.orm import Session

from ..db.models import ScriptORM
from ..repositories.database_repository import get_script_by_id as get_script_by_id_repository


def get_script_by_id(script_id: int, db: Session | None = None) -> ScriptORM | None:
    return get_script_by_id_repository(script_id, db)
