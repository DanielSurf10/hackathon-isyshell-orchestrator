from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ScriptORM(Base):
    __tablename__ = "scripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    allow_params: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    execution_logs: Mapped[list["ExecutionLogORM"]] = relationship(
        back_populates="script",
        cascade="all, delete-orphan",
    )


class ExecutionLogORM(Base):
    __tablename__ = "execution_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    script_id: Mapped[int] = mapped_column(
        ForeignKey("scripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_container: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    parameters_used: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    output_log: Mapped[str] = mapped_column(Text, nullable=False, default="")
    output_error_log: Mapped[str] = mapped_column(Text, nullable=False, default="")
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    script: Mapped[ScriptORM] = relationship(back_populates="execution_logs")
