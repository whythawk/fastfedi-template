from typing import Optional
from ulid import ULID
from pydantic import field_validator, StringConstraints, ConfigDict, BaseModel, Field, EmailStr
from typing_extensions import Annotated

from app.schemas.base_schema import BaseSchema, LocaleType


class CreatorLogin(BaseModel):
    username: str
    password: str


# Shared properties
class CreatorBase(BaseSchema):
    email: Optional[EmailStr] = None
    locale: Optional[LocaleType] = Field(
        None,
        description="Specify the language used by the creator. Controlled vocabulary defined by ISO 639-1, ISO 639-2 or ISO 639-3.",
    )
    is_active: Optional[bool] = True
    is_disabled: Optional[bool] = False
    is_approved: Optional[bool] = True
    is_moderator: Optional[bool] = False
    is_admin: Optional[bool] = False


# Properties to receive via API on creation
class CreatorCreate(CreatorBase):
    email: EmailStr
    password: Optional[Annotated[str, StringConstraints(min_length=8, max_length=64)]] = None


# Properties to receive via API on update
class CreatorUpdate(CreatorBase):
    original: Optional[Annotated[str, StringConstraints(min_length=8, max_length=64)]] = None
    password: Optional[Annotated[str, StringConstraints(min_length=8, max_length=64)]] = None


class CreatorInDBBase(CreatorBase):
    id: Optional[ULID] = None
    model_config = ConfigDict(from_attributes=True)


# Additional properties to return via API
class Creator(CreatorInDBBase):
    hashed_password: bool = Field(default=False, alias="password")
    totp_secret: bool = Field(default=False, alias="totp")
    model_config = ConfigDict(populate_by_name=True)

    @field_validator("hashed_password", mode="before")
    @classmethod
    def evaluate_hashed_password(cls, hashed_password):
        if hashed_password:
            return True
        return False

    @field_validator("totp_secret", mode="before")
    @classmethod
    def evaluate_totp_secret(cls, totp_secret):
        if totp_secret:
            return True
        return False


# Additional properties stored in DB
class CreatorInDB(CreatorInDBBase):
    hashed_password: Optional[str] = None
    totp_secret: Optional[str] = None
    totp_counter: Optional[int] = None
