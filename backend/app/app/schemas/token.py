from typing import Optional
from pydantic import ConfigDict, BaseModel
from ulid import ULID


class Token(BaseModel):
    token: str
    authenticates_id: ULID
    scopes: Optional[str] = ""
    model_config = ConfigDict(from_attributes=True)


class TokenCreate(Token):
    authenticates_id: ULID


class TokenUpdate(Token):
    pass


class TokenData(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    scopes: Optional[str] = None
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[ULID] = None
    refresh: Optional[bool] = False
    scopes: Optional[list[str]] = []
    totp: Optional[bool] = False


class MagicTokenPayload(BaseModel):
    sub: Optional[ULID] = None
    fingerprint: Optional[ULID] = None


class WebToken(BaseModel):
    claim: str
