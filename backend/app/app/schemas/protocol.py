from typing import Optional
from pydantic import Field, AnyHttpUrl, RootModel

from app.schemas.base_schema import BaseSchema
from app.core.config import settings


class ProtocolLink(BaseSchema):
    rel: str = Field(..., description="URI or registered relation type identifies the type of the link relation.")
    type: Optional[str] = Field(None, description="Media type of the target resource.")
    href: Optional[AnyHttpUrl] = Field(None, description="URI pointing to the target resource.")


class WebFinger(BaseSchema):
    # https://en.wikipedia.org/wiki/WebFinger
    subject: str = Field(..., description="URI identifying an ActivityPub actor.")
    aliases: Optional[list[AnyHttpUrl]] = Field(
        [], description="Zero or more URI strings identifying the same 'subject' actor."
    )
    links: Optional[list[ProtocolLink]] = Field(
        [], description="Links of member objects with further information on the 'subject' actor."
    )


class NodeSoftwareVersion(BaseSchema):
    name: str = Field(settings.SOFTWARE_NAME, description="The canonical name of this server software.")
    version: str = Field(settings.SOFTWARE_VERSION, description="The version of this server software.")
    repository: Optional[AnyHttpUrl] = Field(
        settings.SOFTWARE_REPOSITORY, description="The url of the source code repository of this server software."
    )
    homepage: Optional[AnyHttpUrl] = Field(
        settings.SOFTWARE_HOMEPAGE, description="The url of the homepage of this server software."
    )


class NodeServices(BaseSchema):
    inbound: Optional[list[str]] = Field(
        [],
        description="The third party sites this server can retrieve messages from for combined display with regular traffic.",
    )
    outbound: Optional[list[str]] = Field(
        [],
        description="The third party sites this server can publish messages to on the behalf of a user.",
    )


class NodeUsers(BaseSchema):
    total: int = Field(0, description="The total amount of on this server registered users.")
    activeMonth: int = Field(0, description="The amount of users that signed in at least once in the last 30 days.")
    activeHalfyear: int = Field(0, description="The amount of users that signed in at least once in the last 180 days.")


class NodeUsage(BaseSchema):
    users: NodeUsers = Field(..., description="Statistics about the users of this server.")
    localPosts: Optional[int] = Field(
        None, description="The amount of posts that were made by users that are registered on this server."
    )
    localComments: Optional[int] = Field(
        None, description="The amount of comments that were made by users that are registered on this server."
    )


class NodeInfo(BaseSchema):
    # https://nodeinfo.diaspora.software/docson/index.html#/ns/schema/2.1
    version: str = Field("2.1", description="The schema version, must be 2.1.")
    software: NodeSoftwareVersion = Field(NodeSoftwareVersion(), description="Metadata about server software in use.")
    protocols: list[str] = Field(["activitypub"], description="The protocols supported on this server.")
    services: NodeServices = Field(
        NodeServices(), description="The third party sites this server can connect to via their application API."
    )
    openRegistrations: bool = Field(
        settings.OPEN_REGISTRATION, description="Whether this server allows open self-registration."
    )
    usage: NodeUsage = Field(..., description="Usage statistics for this server.")
    metadata: Optional[RootModel[dict[str, str]]] = Field(
        None,
        description="Free form key value pairs for software specific values. Clients should not rely on any specific key present.",
    )


class NodeInfoRoot(BaseSchema):
    links: Optional[list[ProtocolLink]] = Field(
        [], description="Links of member objects with further information on the NodeInfo endpoint."
    )
