"""Todo feature database models."""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class PriorityEnum(str, PyEnum):
    """Priority levels for todos."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Todo(Base):
    """Todo item model."""

    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    priority: Mapped[PriorityEnum] = mapped_column(
        Enum(PriorityEnum),
        default=PriorityEnum.MEDIUM,
        nullable=False,
        index=True,
    )
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Composite index for common queries (filtering by completion and due date)
    __table_args__ = (Index("ix_todos_completed_due_date", "completed", "due_date"),)

    def __repr__(self) -> str:
        """String representation of Todo."""
        return f"<Todo(id={self.id}, title='{self.title}', completed={self.completed})>"
