from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from sqlalchemy import DateTime, UniqueConstraint
from sqlalchemy.sql import func
from ulid import ULID
from sqlalchemy.dialects.postgresql import ENUM

from app.db.base_class import Base
from app.schema_types import ActorType

if TYPE_CHECKING:
    from creator import Creator  # noqa: F401


class Actor(Base):
    id: Mapped[str] = mapped_column(primary_key=True, index=True, default=str(ULID()))
    # ACTIVITY
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    modified: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    fetched: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    # REQUIRED ACTIVITYSTREAMS PROPERTIES
    type: Mapped[ENUM[ActorType]] = mapped_column(ENUM(ActorType), nullable=False, default=ActorType.Person)
    name: Mapped[str] = mapped_column(index=True, nullable=True)
    preferredUsername: Mapped[str] = mapped_column(index=True, nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(index=True, nullable=True)
    # RECOMMENDED ACTIVITYSTREAMS PROPERTIES
    inbox: Mapped[str] = mapped_column(nullable=False)
    outbox: Mapped[str] = mapped_column(unique=True, nullable=False)
    sharedInbox: Mapped[Optional[str]] = mapped_column(nullable=True)
    following: Mapped[Optional[str]] = mapped_column(unique=True, nullable=True)
    followers: Mapped[Optional[str]] = mapped_column(unique=True, nullable=True)
    liked: Mapped[Optional[str]] = mapped_column(unique=True, nullable=True)
    # OPTIONAL ACTIVITYSTREAMS PROPERTIES
    URI: Mapped[Optional[str]] = mapped_column(index=True, unique=True, nullable=False)  # ActivityPub URI
    URL: Mapped[Optional[str]] = mapped_column(unique=True, nullable=True)  # Actor Profile URL
    # AUTHENTICATION AND PERSISTENCE
    privateKey: Mapped[Optional[str]] = mapped_column(unique=True, nullable=True)
    publicKey: Mapped[str] = mapped_column(unique=True, nullable=False)
    publicKeyURI: Mapped[str] = mapped_column(unique=True, nullable=False)
    # UNIQUENESS CONSTRAINT
    creator_id: Mapped[Optional[str]] = mapped_column(ForeignKey("creator.id"), nullable=True)
    creator: Mapped[Optional["Creator"]] = relationship(back_populates="actors", foreign_keys=[creator_id])
    UniqueConstraint("preferredUsername", "domain")
