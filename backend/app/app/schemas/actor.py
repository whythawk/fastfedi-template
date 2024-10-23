from typing import Optional
from ulid import ULID
from pydantic import (
    field_validator,
    StringConstraints,
    ConfigDict,
    BaseModel,
    Field,
    EmailStr,
    HttpUrl,
    model_validator,
    AnyHttpUrl,
)
from typing_extensions import Annotated
from datetime import datetime
import bovine

from app.schemas.base_schema import BaseSchema, LocaleType
from app.schema_types import ActorType
from app.utilities import regex
from app.core.config import settings

settings_SERVER_HOST = "https://4bcd-193-32-126-132.ngrok-free.app"


# NOTE: this is to support the database, not ActivityPub
class ActorBase(BaseSchema):
    id: Optional[ULID] = None
    created: Optional[datetime] = Field(None, description="Automatically generated date actor was created.")
    modified: Optional[datetime] = Field(None, description="Automatically generated date actor was last modified.")
    fetched: Optional[datetime] = Field(
        None, description="Automatically generated date actor was last fetched (remote)."
    )
    # REQUIRED ACTIVITYSTREAMS PROPERTIES
    type: ActorType = Field(
        default=ActorType.Person, description="Defined ActivityPub Actor types, default is 'Person'."
    )
    preferredUsername: str = Field(
        ...,
        description="Username of the account, should just be a string of [a-zA-Z0-9_]. Can be added to domain to create the full username in the form ``[username]@[domain]`` eg., ``user_96@example.org``. Username and domain should be unique *with* each other.",
    )
    name: Optional[str] = Field(
        None,
        description="DisplayName for this account. Can be empty, then just the Username will be used for display purposes.",
    )
    domain: Optional[str] = Field(
        None,
        description="Domain of the account, will be null if this is a local account, otherwise something like ``example.org``. Should be unique with username.",
    )
    # RECOMMENDED ACTIVITYSTREAMS PROPERTIES
    inbox: HttpUrl = Field(
        ...,
        description="Address of this account's ActivityPub inbox, for sending activity to.",
    )
    outbox: HttpUrl = Field(
        ...,
        description="Address of this account's activitypub outbox.",
    )
    sharedInbox: Optional[HttpUrl] = Field(
        None,
        description="Address of this account's ActivityPub sharedInbox.",
    )
    following: Optional[HttpUrl] = Field(
        None,
        description="URI for getting the following list of this account.",
    )
    followers: Optional[HttpUrl] = Field(
        None,
        description="URI for getting the followers list of this account.",
    )
    liked: Optional[HttpUrl] = Field(
        None,
        description="URI for getting the favourites / likes list of this account.",
    )
    # featuredCollection: Optional[HttpUrl] = Field(
    #     None,
    #     description="URL for getting the featured collection list of this account.",
    # )
    # OPTIONAL ACTIVITYSTREAMS PROPERTIES
    URI: Optional[HttpUrl] = Field(
        None,
        description="ActivityPub URI for this account.",
    )
    URL: Optional[HttpUrl] = Field(
        None,
        description="Web URL for this account's profile.",
    )
    # AUTHENTICATION AND PERSISTENCE
    privateKey: Optional[str] = Field(
        None,
        description="Publickey for authorizing signed activitypub requests, will be defined for both local and remote accounts.",
    )
    publicKey: str = Field(
        ...,
        description="Privatekey for signing activitypub requests, will only be defined for local accounts.",
    )
    publicKeyURI: HttpUrl = Field(
        ...,
        description="Web-reachable location of this account's public key.",
    )
    # LOCAL
    creator_id: Optional[ULID] = None
    # locale: Optional[LocaleType] = Field(
    #     None,
    #     description="Specify the language used by the actor. Controlled vocabulary defined by ISO 639-1, ISO 639-2 or ISO 639-3.",
    # )
    # ADMINISTRATION AND MODERATION
    # locked: bool = Field(False, description="Does this account need an approval for new followers?")
    # discoverable: bool = Field(False, description="Should this account be shown in the instance's profile directory?")
    # memorial: bool = Field(False, description="Is this a memorial account, ie., has the user passed away?")
    # sensitizedAt: Optional[datetime] = Field(
    #     None, description="When was this account set to have all its media shown as sensitive?"
    # )
    # silencedAt: Optional[datetime] = Field(
    #     None, description="When was this account silenced (eg., statuses only visible to followers, not public)?"
    # )
    # suspendedAt: Optional[datetime] = Field(
    #     None,
    #     description="When was this account suspended (eg., don't allow it to log in/post, don't accept media/posts from this account)?",
    # )
    model_config = ConfigDict(from_attributes=True)


class ActorLocalCreate(ActorBase):
    preferredUsername: str = Field(
        ...,
        description="Username of the account, should just be a string of [a-zA-Z0-9_]. Can be added to domain to create the full username in the form ``[username]@[domain]`` eg., ``user_96@example.org``. Username and domain should be unique *with* each other.",
    )
    domain: Optional[str] = Field(
        None,
        description="Domain of the account, will be null if this is a local account, otherwise something like ``example.org``. Should be unique with username.",
    )
    # RECOMMENDED ACTIVITYSTREAMS PROPERTIES
    inbox: Optional[HttpUrl] = Field(
        None,
        description="Address of this account's ActivityPub inbox, for sending activity to.",
    )
    outbox: Optional[HttpUrl] = Field(
        None,
        description="Address of this account's activitypub outbox.",
    )
    # AUTHENTICATION AND PERSISTENCE
    publicKey: Optional[str] = Field(
        None,
        description="Privatekey for signing activitypub requests, will only be defined for local accounts.",
    )
    publicKeyURI: Optional[HttpUrl] = Field(
        None,
        description="Web-reachable location of this account's public key.",
    )

    @field_validator("preferredUsername")
    @classmethod
    def validate_preferredUsername(cls, v: str) -> str:
        if not regex.matches(regex.actornameStrict, v):
            raise ValueError("Must be a valid preferredUsername")
        return v

    @model_validator(mode="after")
    def generate_keys(self) -> "ActorLocalCreate":
        if not self.publicKey and not self.privateKey:
            self.publicKey, self.privateKey = bovine.crypto.generate_rsa_public_private_key()
        return self

    @model_validator(mode="after")
    def generate_endpoints(self) -> "ActorLocalCreate":
        if self.preferredUsername:
            # Settings
            domain = settings_SERVER_HOST
            if not isinstance(settings_SERVER_HOST, str):
                domain = str(settings_SERVER_HOST)
            if domain[-1] == "/":
                domain = domain[:-1]
            # URIs
            self.domain = regex.url_root(settings_SERVER_HOST)
            self.inbox = f"{domain}/{self.type.as_uri}/{self.preferredUsername}/{regex.inbox}"
            self.outbox = f"{domain}/{self.type.as_uri}/{self.preferredUsername}/{regex.outbox}"
            self.sharedInbox = f"{domain}/{regex.inbox}"
            self.following = f"{domain}/{self.type.as_uri}/{self.preferredUsername}/{regex.following}"
            self.followers = f"{domain}/{self.type.as_uri}/{self.preferredUsername}/{regex.followers}"
            self.liked = f"{domain}/{self.type.as_uri}/{self.preferredUsername}/{regex.liked}"
            # self.featuredCollection = f"{domain}/{self.type.as_uri}/{self.preferredUsername}/{regex.featured}"
            self.publicKeyURI = f"{domain}/{self.type.as_uri}/{self.preferredUsername}#{regex.publicKey}"
            self.URI = f"{domain}/{self.type.as_uri}/{self.preferredUsername}"
            self.URL = f"{domain}/@{self.preferredUsername}"
        return self


class ActorLocalUpdate(ActorBase):
    pass
