from typing import Annotated, Any, Union

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app import crud, models, schemas, schema_types
from app.schemas import activitypubdantic as ap
from app.api import deps
from app.core.config import settings
from app.core import security
import json
import orjson
from functools import wraps

from bovine.crypto.http_signature import HttpSignature
from bovine.crypto.signature import parse_signature_header
from bovine.crypto.types import CryptographicIdentifier

router = APIRouter(lifespan=deps.get_lifespan)
settings_SERVER_HOST = "https://4bcd-193-32-126-132.ngrok-free.app"


def verify_request_signature(endpoint):
    # https://stackoverflow.com/a/72312122/295606
    @wraps(endpoint)
    async def wrapper(*, db: Session, request: Request, **kwargs):
        # if request.headers.get("SECRET", None) != SECRET_KEY:
        #     raise HTTPException(status_code=401, detail="Invalid client secret")
        print("-------------------------------------------------")
        print(request.headers)
        http_signature = HttpSignature()
        # If it's not signed, then ...?
        parsed_signature = parse_signature_header(request.headers["signature"])
        signature_fields = parsed_signature.fields
        for field in signature_fields:
            if field == "keyId":
                print(request.headers[field])
            if field == "(request-target)":
                method = request.method.lower()
                path = request.url
                http_signature.with_field(field, f"{method} {path}")
            elif field == "host":
                http_signature.with_field(field, request.headers["x-forwarded-host"])
            else:
                http_signature.with_field(field, request.headers[field])
        # print(http_signature)
        print("-------------------------------------------------")
        # kwargs["db"] = db
        # kwargs["request"] = request
        # https://stackoverflow.com/a/42769789/295606
        return await endpoint(db=db, request=request, **kwargs)

    return wrapper


@router.get("/tester", response_model=schemas.Msg)
@verify_request_signature
def test_endpoint() -> Any:
    """
    Test current endpoint.
    """
    return {"msg": "Message returned ok."}


@router.post("/{actortype}/{actorname}/inbox", status_code=status.HTTP_202_ACCEPTED)
@verify_request_signature
async def post_to_actor_inbox(
    *,
    db: Annotated[Session, Depends(deps.get_db)],
    actortype: str,
    actorname: str,
    request: Request,
):
    """
    Post an activity to a local actor.
    """
    print("-------------------------------------------------")
    print(request.headers)
    print("-------------------------------------------------")
    body = await request.json()
    try:
        test = await request.body()
        ap.get_class(orjson.loads(test))
        print("-----------------------------")
        print(request.cookies)
        print(request.client)
        print(request.url)
        print(request.method)
        print(request.headers)
        print("-----------------------------")
    except Exception as e:
        print(e)
        print(test)
    # 1. Reject large requests
    if len(body) > settings.JSONLD_MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Payload data too large.",
        )
    # 2. Check if user or domain are blocked
    # 3. Get actor and check if they have blocked the poster
    db_obj = crud.actor.get_by_name(db=db, preferredUsername=actorname, actortype=actortype)
    if not db_obj:
        raise HTTPException(
            status_code=400,
            detail=f"{actortype} unknown.",
        )
    # 4. Verify the sender, and add to db if needed
    print("-----------------------------")
    validation_response = await crud.pub.validate_http_signature(db_obj=db_obj, request=request)
    if validation_response:
        raise HTTPException(
            status_code=400,
            detail=validation_response,
        )
    print(json.dumps(body, indent=2))
    print("-----------------------------")
    # 5. Convert body to an activitypub class
    # 6. Queue processing the activity


@router.get("/{actortype}/{actorname}")
# @verify_request_signature
async def read_actor(
    *,
    db: Annotated[Session, Depends(deps.get_db)],
    actortype: str,
    actorname: str,
    request: Request,
) -> Any:
    """
    Get an actor of a specified type.
    """
    db_obj = crud.actor.get_by_name(db=db, preferredUsername=actorname, actortype=actortype)
    if not db_obj:
        raise HTTPException(
            status_code=400,
            detail=f"{actortype} unknown.",
        )
    return crud.pub.get_wellknown_actor(db_obj=db_obj)
    wk = crud.pub.get_wellknown_actor(db_obj=db_obj)
    output_class = ap.get_class(wk)
    return output_class.data()
