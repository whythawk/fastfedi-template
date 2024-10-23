from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from app.db.base_class import Base

if TYPE_CHECKING:
    from .creator import Creator  # noqa: F401


class Token(Base):
    token: Mapped[str] = mapped_column(primary_key=True, index=True)
    scopes: Mapped[Optional[str]] = mapped_column(nullable=True)
    authenticates_id: Mapped[str] = mapped_column(ForeignKey("creator.id"))
    authenticates: Mapped["Creator"] = relationship(back_populates="tokens")
