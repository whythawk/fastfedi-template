from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime
from sqlalchemy.sql import func
from sqlalchemy_utils import LocaleType
from babel import Locale
from ulid import ULID

from app.db.base_class import Base

if TYPE_CHECKING:
    from token import Token  # noqa: F401
    from actor import Actor  # noqa: F401


class Creator(Base):
    id: Mapped[str] = mapped_column(primary_key=True, index=True, default=str(ULID()))
    # ACTIVITY
    # https://github.com/sqlalchemy/sqlalchemy/discussions/10189
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    modified: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )
    # METADATA
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(nullable=True)
    locale: Mapped[Locale] = mapped_column(LocaleType, nullable=True)
    # AUTHENTICATION AND PERSISTENCE
    totp_secret: Mapped[Optional[str]] = mapped_column(nullable=True)
    totp_counter: Mapped[Optional[int]] = mapped_column(nullable=True)
    email_validated: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_disabled: Mapped[bool] = mapped_column(default=False)
    is_approved: Mapped[bool] = mapped_column(default=True)
    is_moderator: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False)
    tokens: Mapped[list["Token"]] = relationship(
        foreign_keys="[Token.authenticates_id]", back_populates="authenticates", lazy="dynamic"
    )
    # ACTIVITYPUB ACTORS
    actors: Mapped[list["Actor"]] = relationship(order_by="Actor.created", back_populates="creator", lazy="dynamic")
