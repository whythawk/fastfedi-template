from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi import Request
import bovine
from bovine.crypto.types import CryptographicIdentifier
import secrets
import json

from app.crud.base import CRUDBase
from app.core.config import settings
from app.utilities import regex
from app.models import Actor
from app.schemas import activitypubdantic, ActorLocalCreate, ActorLocalUpdate
from app.schema_types import ActorType

# from app.core.config import settings


class CRUDActor(CRUDBase[Actor, ActorLocalCreate, ActorLocalUpdate]):
    def create(self, db: Session, *, obj_in: ActorLocalCreate) -> Actor:
        if isinstance(obj_in, dict):
            obj_in = ActorLocalCreate(**obj_in)
        return super().create(db, obj_in=obj_in)

    # Mostly for locals ...
    def get_by_name(self, *, db: Session, preferredUsername: str, actortype: ActorType | str) -> Actor:
        if isinstance(actortype, str):
            try:
                actortype = ActorType(actortype)
            except ValueError:
                return None
        if not regex.matches(regex.actornameStrict, preferredUsername):
            return None
        return (
            db.query(self.model)
            .filter((self.model.preferredUsername == preferredUsername) & (self.model.type == actortype))
            .first()
        )

    def _get_actor_id(self, *, db_obj: Actor):
        return f"https://{db_obj.domain}/{db_obj.preferredUsername}"

    def _make_requests_id(self, *, db_obj: Actor):
        return f"https://{db_obj.domain}/{secrets.token_urlsafe(6)}"

    def _fetch_public_key(self, actor: bovine.BovineActor) -> CryptographicIdentifier:
        """
        Validate_signature takes `(method, url, headers, body)` as parameters and returns the owner if the http signature is valid.
        https://codeberg.org/bovine/bovine/src/commit/91ec9a0b77863c164c0598227e6e14b3d4cc005f/bovine/bovine/crypto/__init__.py#L105

        Use as:

            actor_fetch = fetch_public_key(actor)
            assert await bovine.crypto.build_validate_http_signature_raw(actor_fetch)(
                "post", str(request.url), request.headers, request.body)
            )
        """

        async def fetch_with_url(key_url: str):
            data = await actor.get(key_url, fail_silently=True)
            if data:
                return CryptographicIdentifier.from_public_key(data.get("publicKey", data))

        return fetch_with_url

    async def validate_http_signature(self, actor: bovine.BovineActor):
        return bovine.crypto.build_validate_http_signature_raw(self._fetch_public_key(actor))

    def get_wellknown_webfinger(self, *, db_obj: Actor):
        return bovine.utils.webfinger_response_json(
            f"acct:{db_obj.preferredUsername}@{db_obj.domain}", self._get_actor_id(db_obj=db_obj)
        )

    def get_wellknown_actor(self, *, db_obj: Actor):
        actor_id = self._get_actor_id(db_obj=db_obj)
        return bovine.activitystreams.Actor(
            id=actor_id,
            preferred_username=db_obj.preferredUsername,
            name=db_obj.name,
            inbox=db_obj.inbox,
            outbox=actor_id,
            public_key=db_obj.publicKey,
            public_key_name="main-key",
        ).build()

    def get_requests_actor(self, *, db_obj: Actor):
        actor_id = self._get_actor_id(db_obj=db_obj)
        return bovine.BovineActor(
            actor_id=actor_id,
            public_key_url=f"{actor_id}#main-key",
            secret=db_obj.privateKey,
        )

    def remove(self, db: Session, *, db_obj: Actor) -> None:
        db.delete(db_obj)
        db.commit()
        return None


actor = CRUDActor(Actor)
