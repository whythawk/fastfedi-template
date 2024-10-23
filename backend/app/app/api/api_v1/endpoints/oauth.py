from typing import Annotated, Any, Union

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.utilities import (
    send_reset_password_email,
    send_magic_login_email,
)

router = APIRouter(lifespan=deps.get_lifespan)

"""
https://github.com/OWASP/CheatSheetSeries/blob/master/cheatsheets/Authentication_Cheat_Sheet.md
Specifies minimum criteria:
    - Change password must require current password verification to ensure that it's the legitimate creator.
    - Login page and all subsequent authenticated pages must be exclusively accessed over TLS or other strong transport.
    - An application should respond with a generic error message regardless of whether:
        - The creator ID or password was incorrect.
        - The account does not exist.
        - The account is locked or disabled.
    - Code should go through the same process, no matter what, allowing the application to return in approximately
      the same response time.
    - In the words of George Orwell, break these rules sooner than do something truly barbaric.

See `security.py` for other requirements.
"""


@router.post("/magic/{email}", response_model=schemas.WebToken)
def login_with_magic_link(*, db: Annotated[Session, Depends(deps.get_db)], email: str) -> Any:
    """
    First step of a 'magic link' login. Check if the creator exists and generate a magic link. Generates two short-duration
    jwt tokens, one for validation, one for email. Creates creator if not exist.
    """
    creator = crud.creator.get_by_email(db, email=email)
    if not creator:
        creator_in = schemas.CreatorCreate(**{"email": email})
        creator = crud.creator.create(db, obj_in=creator_in)
    if not crud.creator.is_active(creator):
        # Still permits a timed-attack, but does create ambiguity.
        raise HTTPException(status_code=400, detail="A link to activate your account has been emailed.")
    tokens = security.create_magic_tokens(subject=creator.id)
    if settings.emails_enabled and creator.email:
        # Send email with creator.email as subject
        send_magic_login_email(email_to=creator.email, token=tokens[0])
    return {"claim": tokens[1]}


@router.post("/claim", response_model=schemas.Token)
def validate_magic_link(
    *,
    db: Annotated[Session, Depends(deps.get_db)],
    obj_in: schemas.WebToken,
    magic_in: Annotated[bool, Depends(deps.get_magic_token)],
) -> Any:
    """
    Second step of a 'magic link' login.
    """
    claim_in = deps.get_magic_token(token=obj_in.claim)
    # Get the creator
    creator = crud.creator.get(db, id=magic_in.sub)
    # Test the claims
    if (
        (claim_in.sub == magic_in.sub)
        or (claim_in.fingerprint != magic_in.fingerprint)
        or not creator
        or not crud.creator.is_active(creator)
    ):
        raise HTTPException(status_code=400, detail="Login failed; invalid claim.")
    # Validate that the email is the creator's
    if not creator.email_validated:
        crud.creator.validate_email(db=db, db_obj=creator)
    # Check if totp active
    refresh_token = None
    force_totp = True
    if not creator.totp_secret:
        # No TOTP, so this concludes the login validation
        force_totp = False
        refresh_token = security.create_refresh_token(subject=creator.id)
        crud.token.create(db=db, obj_in=refresh_token, creator_obj=creator)
    return {
        "access_token": security.create_access_token(subject=creator.id, force_totp=force_totp),
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login", response_model=schemas.Token)
def login_with_oauth2(
    db: Annotated[Session, Depends(deps.get_db)], form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Any:
    """
    First step with OAuth2 compatible token login, get an access token for future requests.
    """
    creator = crud.creator.authenticate(db, email=form_data.username, password=form_data.password)
    if not form_data.password or not creator or not crud.creator.is_active(creator):
        raise HTTPException(status_code=400, detail="Login failed; incorrect email or password")
    # Check if totp active
    refresh_token = None
    force_totp = True
    scopes = SecurityScopes(["read", "write", "admin"])
    if not creator.totp_secret:
        # No TOTP, so this concludes the login validation
        force_totp = False
        refresh_token = security.create_refresh_token(subject=creator.id, security_scopes=scopes)
        crud.token.create(db=db, obj_in=refresh_token, creator_obj=creator)
    return {
        "access_token": security.create_access_token(subject=creator.id, force_totp=force_totp, security_scopes=scopes),
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/totp", response_model=schemas.Token)
def login_with_totp(
    *,
    db: Annotated[Session, Depends(deps.get_db)],
    totp_data: schemas.WebToken,
    current_creator: Annotated[models.Creator, Depends(deps.get_totp_creator)],
) -> Any:
    """
    Final validation step, using TOTP.
    """
    new_counter = security.verify_totp(
        token=totp_data.claim, secret=current_creator.totp_secret, last_counter=current_creator.totp_counter
    )
    if not new_counter:
        raise HTTPException(status_code=400, detail="Login failed; unable to verify TOTP.")
    # Save the new counter to prevent reuse
    scopes = SecurityScopes(["read", "write", "admin"])
    current_creator = crud.creator.update_totp_counter(db=db, db_obj=current_creator, new_counter=new_counter)
    refresh_token = security.create_refresh_token(subject=current_creator.id, security_scopes=scopes)
    crud.token.create(db=db, obj_in=refresh_token, creator_obj=current_creator)
    return {
        "access_token": security.create_access_token(subject=current_creator.id, security_scopes=scopes),
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.put("/totp", response_model=schemas.Msg)
def enable_totp_authentication(
    *,
    db: Annotated[Session, Depends(deps.get_db)],
    data_in: schemas.EnableTOTP,
    current_creator: Annotated[models.Creator, Depends(deps.get_current_active_creator)],
) -> Any:
    """
    For validation of token before enabling TOTP.
    """
    if current_creator.hashed_password:
        creator = crud.creator.authenticate(db, email=current_creator.email, password=data_in.password)
        if not data_in.password or not creator:
            raise HTTPException(status_code=400, detail="Unable to authenticate or activate TOTP.")
    totp_in = security.create_new_totp(label=current_creator.email, uri=data_in.uri)
    new_counter = security.verify_totp(
        token=data_in.claim, secret=totp_in.secret, last_counter=current_creator.totp_counter
    )
    if not new_counter:
        raise HTTPException(status_code=400, detail="Unable to authenticate or activate TOTP.")
    # Enable TOTP and save the new counter to prevent reuse
    current_creator = crud.creator.activate_totp(db=db, db_obj=current_creator, totp_in=totp_in)
    current_creator = crud.creator.update_totp_counter(db=db, db_obj=current_creator, new_counter=new_counter)
    return {"msg": "TOTP enabled. Do not lose your recovery code."}


@router.delete("/totp", response_model=schemas.Msg)
def disable_totp_authentication(
    *,
    db: Annotated[Session, Depends(deps.get_db)],
    data_in: schemas.CreatorUpdate,
    current_creator: Annotated[models.Creator, Depends(deps.get_current_active_creator)],
) -> Any:
    """
    Disable TOTP.
    """
    if current_creator.hashed_password:
        creator = crud.creator.authenticate(db, email=current_creator.email, password=data_in.original)
        if not data_in.original or not creator:
            raise HTTPException(status_code=400, detail="Unable to authenticate or deactivate TOTP.")
    crud.creator.deactivate_totp(db=db, db_obj=current_creator)
    return {"msg": "TOTP disabled."}


@router.post("/refresh", response_model=schemas.Token)
def refresh_token(
    db: Annotated[Session, Depends(deps.get_db)],
    current_creator: Annotated[models.Creator, Depends(deps.get_refresh_creator)],
) -> Any:
    """
    Refresh tokens for future requests
    """
    refresh_token = security.create_refresh_token(subject=current_creator.id)
    scopes = SecurityScopes(["read", "write", "admin"])
    crud.token.create(db=db, obj_in=refresh_token, creator_obj=current_creator, security_scopes=scopes)
    return {
        "access_token": security.create_access_token(subject=current_creator.id, security_scopes=scopes),
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/revoke", response_model=schemas.Msg)
def revoke_token(
    db: Annotated[Session, Depends(deps.get_db)],
    current_creator: Annotated[models.Creator, Depends(deps.get_refresh_creator)],
) -> Any:
    """
    Revoke a refresh token
    """
    return {"msg": "Token revoked"}


@router.post("/recover/{email}", response_model=Union[schemas.WebToken, schemas.Msg])
def recover_password(email: str, db: Annotated[Session, Depends(deps.get_db)]) -> Any:
    """
    Password Recovery
    """
    creator = crud.creator.get_by_email(db, email=email)
    if creator and crud.creator.is_active(creator):
        tokens = security.create_magic_tokens(subject=creator.id)
        if settings.emails_enabled:
            send_reset_password_email(email_to=creator.email, email=email, token=tokens[0])
            return {"claim": tokens[1]}
    return {"msg": "If that login exists, we'll send you an email to reset your password."}


@router.post("/reset", response_model=schemas.Msg)
def reset_password(
    *,
    db: Annotated[Session, Depends(deps.get_db)],
    new_password: str = Body(...),
    claim: str = Body(...),
    magic_in: Annotated[bool, Depends(deps.get_magic_token)],
) -> Any:
    """
    Reset password
    """
    claim_in = deps.get_magic_token(token=claim)
    # Get the creator
    creator = crud.creator.get(db, id=magic_in.sub)
    # Test the claims
    if (
        (claim_in.sub == magic_in.sub)
        or (claim_in.fingerprint != magic_in.fingerprint)
        or not creator
        or not crud.creator.is_active(creator)
    ):
        raise HTTPException(status_code=400, detail="Password update failed; invalid claim.")
    # Update the password
    hashed_password = security.get_password_hash(new_password)
    creator.hashed_password = hashed_password
    db.add(creator)
    db.commit()
    return {"msg": "Password updated successfully."}
