from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi import Request
import bovine
from bovine.crypto.types import CryptographicIdentifier
import secrets
from datetime import date, timedelta

# from app.crud.base import CRUDBase
from app.core.config import settings
from app.models import Actor
from app.schemas import activitypubdantic, NodeInfo
from app.utilities import regex

# from app.schemas import TokenCreate, TokenUpdate
# from app.core.config import settings


class CRUDActivityPub:

    def get_actor_by_resource(self, *, db: Session, resource: str) -> Actor:
        # Check if the resource encapsulates a webfinger query
        preferredUsername, domain = bovine.utils.parse_fediverse_handle(resource)
        if preferredUsername and domain:
            return (
                db.query(Actor)
                .filter((Actor.preferredUsername == preferredUsername) & (Actor.domain == domain))
                .first()
            )
        # Check if the resource is the actor URL
        if regex.url_validates(resource):
            return db.query(Actor).filter(Actor.URL == resource).first()
        return None

    def _make_requests_id(self, *, db_obj: Actor):
        return f"{db_obj.domain}{secrets.token_urlsafe(6)}"

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

    async def validate_http_signature(self, *, db_obj: Actor, request: Request, method: str = "post") -> str | None:
        # returns an error message, or None
        # 1. Reject large requests
        body = await request.json()
        if len(body) > settings.JSONLD_MAX_SIZE:
            return "Payload data too large."
        # 2. Check if user or domain are blocked
        # 3. Get actor and check if they have blocked the poster
        actor = self.get_requests_actor(db_obj=db_obj)
        await actor.init()
        # verify = crud.actor.validate_http_signature(actor)
        verify = bovine.crypto.build_validate_http_signature_raw(self._fetch_public_key(actor))
        # assert await verify(method, str(request.url), request.headers, request.body)
        try:
            claimed_owner = await verify(method, str(request.url), request.headers, request.body)
        except Exception as e:
            print(e)
            return "HTTP Signature validation failed."
        print("-----------------------------")
        print("CLAIMED: ", claimed_owner)
        print("-----------------------------")
        await actor.session.close()
        return None

    def get_requests_actor(self, *, db_obj: Actor):
        return bovine.BovineActor(
            actor_id=db_obj.URI,
            public_key_url=db_obj.publicKeyURI,
            secret=db_obj.privateKey,
        )

    def get_wellknown_webfinger(self, *, db_obj: Actor):
        return bovine.utils.webfinger_response_json(f"acct:{db_obj.preferredUsername}@{db_obj.domain}", db_obj.URI)

    def get_wellknown_actor(self, *, db_obj: Actor):
        return bovine.activitystreams.Actor(
            id=db_obj.URI,
            preferred_username=db_obj.preferredUsername,
            name=db_obj.name,
            inbox=db_obj.inbox,
            outbox=db_obj.outbox,
            public_key=db_obj.publicKey,
            public_key_name="main-key",
        ).build()

    def get_wellknown_nodeinfo(self, *, db: Session) -> NodeInfo:
        # Get usage and return defaults
        activeMonth = date.today() - timedelta(30)
        activeHalf = date.today() - timedelta(180)
        usage = {
            "users": {
                "total": db.query(Actor).count(),
                "activeMonth": db.query(Actor).filter(Actor.fetched >= activeMonth).count(),
                "activeHalfyear": db.query(Actor).filter(Actor.fetched >= activeHalf).count(),
            },
            "localPosts": 0,
        }
        return NodeInfo(**{"usage": usage})


pub = CRUDActivityPub()
