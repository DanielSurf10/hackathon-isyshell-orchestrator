from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.database import SessionLocal
from ..db.models import ExecutionLogORM, ScriptORM


def _resolve_session(db: Session | None) -> tuple[Session, bool]:
    if db is not None:
        return db, False
    return SessionLocal(), True


def list_scripts(db: Session | None = None) -> list[ScriptORM]:
    session, should_close = _resolve_session(db)
    try:
        return list(session.scalars(select(ScriptORM).order_by(ScriptORM.id)))
    finally:
        if should_close:
            session.close()


def get_script_by_id(script_id: int, db: Session | None = None) -> ScriptORM | None:
    session, should_close = _resolve_session(db)
    try:
        return session.get(ScriptORM, script_id)
    finally:
        if should_close:
            session.close()


def create_script(
    *,
    name: str,
    description: str,
    path: str,
    allow_params: bool,
    is_active: bool = True,
    created_at: datetime | None = None,
    db: Session | None = None,
) -> ScriptORM:
    session, should_close = _resolve_session(db)
    try:
        script = ScriptORM(
            name=name,
            description=description,
            path=path,
            allow_params=allow_params,
            is_active=is_active,
            created_at=created_at or datetime.now(timezone.utc),
        )
        session.add(script)
        session.commit()
        session.refresh(script)
        return script
    finally:
        if should_close:
            session.close()


def update_script_status(script_id: int, is_active: bool, db: Session | None = None) -> ScriptORM | None:
    session, should_close = _resolve_session(db)
    try:
        script = session.get(ScriptORM, script_id)
        if script is None:
            return None

        script.is_active = is_active
        session.commit()
        session.refresh(script)
        return script
    finally:
        if should_close:
            session.close()


def create_execution_log(
    *,
    script_id: int,
    target_container: str,
    parameters_used: str,
    status: int,
    output_log: str,
    output_error_log: str,
    executed_at: datetime | None = None,
    db: Session | None = None,
) -> ExecutionLogORM:
    session, should_close = _resolve_session(db)
    try:
        execution_log = ExecutionLogORM(
            script_id=script_id,
            target_container=target_container,
            parameters_used=parameters_used,
            status=status,
            output_log=output_log,
            output_error_log=output_error_log,
            executed_at=executed_at or datetime.now(timezone.utc),
        )
        session.add(execution_log)
        session.commit()
        session.refresh(execution_log)
        return execution_log
    finally:
        if should_close:
            session.close()


def list_execution_logs(db: Session | None = None) -> list[ExecutionLogORM]:
    session, should_close = _resolve_session(db)
    try:
        return list(session.scalars(select(ExecutionLogORM).order_by(ExecutionLogORM.id)))
    finally:
        if should_close:
            session.close()


def list_execution_logs_by_container(target_container: str, db: Session | None = None) -> list[ExecutionLogORM]:
    session, should_close = _resolve_session(db)
    try:
        stmt = select(ExecutionLogORM).where(ExecutionLogORM.target_container == target_container)
        return list(session.scalars(stmt.order_by(ExecutionLogORM.id)))
    finally:
        if should_close:
            session.close()


def list_execution_logs_with_errors_by_container(
    target_container: str,
    db: Session | None = None,
) -> list[ExecutionLogORM]:
    session, should_close = _resolve_session(db)
    try:
        stmt = select(ExecutionLogORM).where(
            ExecutionLogORM.target_container == target_container,
            ExecutionLogORM.status != 0,
        )
        return list(session.scalars(stmt.order_by(ExecutionLogORM.id)))
    finally:
        if should_close:
            session.close()


def list_execution_logs_with_errors_by_script(script_id: int, db: Session | None = None) -> list[ExecutionLogORM]:
    session, should_close = _resolve_session(db)
    try:
        stmt = select(ExecutionLogORM).where(
            ExecutionLogORM.script_id == script_id,
            ExecutionLogORM.status != 0,
        )
        return list(session.scalars(stmt.order_by(ExecutionLogORM.id)))
    finally:
        if should_close:
            session.close()
