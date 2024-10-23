from typing import Generator, Annotated
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core.config import settings
from app.db.session import SessionLocal


scope_scheme = {
    "read": "Read",
    "write": "Write",
    "admin": "Admin",
}
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/oauth/login", scopes=scope_scheme)


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@asynccontextmanager
async def get_lifespan(_: FastAPI) -> AsyncIterator[None]:
    # https://github.com/long2ice/fastapi-cache?tab=readme-ov-file
    redis = aioredis.from_url(
        f"redis://{settings.DOCKER_IMAGE_CACHE}", password=settings.REDIS_PASSWORD, decode_responses=False
    )
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    yield


def get_token_payload(token: str) -> schemas.TokenPayload:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGO])
        token_data = schemas.TokenPayload(**payload)
    except (jwt.InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials.",
        )
    return token_data


def get_credentials_exception(detail: str, security_scopes: SecurityScopes = SecurityScopes([])) -> HTTPException:
    if security_scopes and security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": authenticate_value},
    )


def get_current_creator(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)],
    security_scopes: SecurityScopes = SecurityScopes([]),
) -> models.Creator:
    token_data = get_token_payload(token)
    if token_data.refresh or token_data.totp:
        # Refresh token is not a valid access token and TOTP True can only be used to validate TOTP
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    # Now test for scopes
    creator = crud.creator.get(db, id=token_data.sub)
    if not settings.USE_REFRESH_TOKEN:
        # If not using refresh tokens, need to check that this is a valid token
        if not models.token.get_by_creator(token=token, creator=creator):
            creator = None
    if not creator:
        raise get_credentials_exception(detail="Creator not found.", security_scopes=security_scopes)
    if security_scopes:
        for scope in security_scopes.scopes:
            if scope not in token_data.scopes:
                raise get_credentials_exception(detail="Not enough permissions.", security_scopes=security_scopes)
    return creator


def get_totp_creator(
    db: Annotated[Session, Depends(get_db)], token: Annotated[str, Depends(oauth2_scheme)]
) -> models.Creator:
    token_data = get_token_payload(token)
    if token_data.refresh or not token_data.totp:
        # Refresh token is not a valid access token and TOTP False cannot be used to validate TOTP
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials.",
        )
    creator = crud.creator.get(db, id=token_data.sub)
    if not creator:
        raise get_credentials_exception(detail="Could not validate credentials.")
    return creator


def get_magic_token(token: Annotated[str, Depends(oauth2_scheme)]) -> schemas.MagicTokenPayload:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGO])
        token_data = schemas.MagicTokenPayload(**payload)
    except (jwt.InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials.",
        )
    return token_data


def get_refresh_creator(
    db: Annotated[Session, Depends(get_db)], token: Annotated[str, Depends(oauth2_scheme)]
) -> models.Creator:
    token_data = get_token_payload(token)
    if not token_data.refresh:
        # Access token is not a valid refresh token
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials.",
        )
    creator = crud.creator.get(db, id=token_data.sub)
    if not creator:
        raise get_credentials_exception(detail="Creator not found.")
    if not crud.creator.is_active(creator):
        raise get_credentials_exception(detail="Inactive creator.")
    # Check and revoke this refresh token
    token_obj = crud.token.get_by_creator(token=token, creator=creator)
    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials.",
        )
    # TODO: Fix this ... need to preserve scopes and this can't happen here
    # crud.token.remove(db, db_obj=token_obj)
    return creator


def get_current_active_creator(
    current_creator: Annotated[models.Creator, Depends(get_current_creator)],
) -> models.Creator:
    if not crud.creator.is_active(current_creator):
        raise get_credentials_exception(detail="Inactive creator.")
    return current_creator


def get_current_active_admin(
    current_creator: Annotated[models.Creator, Depends(get_current_creator)],
) -> models.Creator:
    if not crud.creator.is_active(current_creator) or not crud.creator.is_admin(current_creator):
        raise get_credentials_exception(detail="Not enough permissions.")
    return current_creator


def get_active_websocket_creator(
    *, db: Session, token: str, security_scopes: SecurityScopes = SecurityScopes([])
) -> models.Creator:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGO])
        token_data = schemas.TokenPayload(**payload)
    except (jwt.InvalidTokenError, ValidationError):
        raise ValidationError("Could not validate credentials.")
    if token_data.refresh:
        # Refresh token is not a valid access token
        raise ValidationError("Could not validate credentials.")
    creator = crud.creator.get(db, id=token_data.sub)
    if not creator:
        raise ValidationError("Creator not found.")
    if not crud.creator.is_active(creator):
        raise ValidationError("Inactive creator.")
    if security_scopes:
        for scope in security_scopes.scopes:
            if scope not in token_data.scopes:
                raise ValidationError("Not enough permissions.")
    return creator
