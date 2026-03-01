"""
Mixins reutilizables para modelos SQLAlchemy.

TimestampMixin:  agrega created_at / updated_at automáticos.
RepresentableMixin: __repr__ basado en id y tablename para debugging.
"""

import uuid
from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class TimestampMixin:
    """Agrega created_at y updated_at a cualquier modelo."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class RepresentableMixin:
    """__repr__ automático para debugging."""
    def __repr__(self) -> str:
        pk = getattr(self, "id", "?")
        return f"<{self.__class__.__name__}(id={pk})>"
