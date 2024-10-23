from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, Any
from sqlalchemy.orm import Session

from app import schemas, crud
from app.api import deps

router = APIRouter(lifespan=deps.get_lifespan)
settings_SERVER_HOST = "https://4bcd-193-32-126-132.ngrok-free.app"


@router.get("/nodeinfo", response_model=schemas.NodeInfoRoot, response_model_exclude_none=True)
def read_nodeinfo_endpoint() -> Any:
    """
    Get wellknown nodeinfo endpoint.
    """
    return schemas.NodeInfoRoot(
        **{
            "links": [
                {
                    "rel": "http://nodeinfo.diaspora.software/ns/schema/2.1",
                    "href": f"https://{settings_SERVER_HOST}/nodeinfo/2.1",
                }
            ]
        }
    )


@router.get("/nodeinfo/2.1", response_model=schemas.NodeInfo, response_model_exclude_none=True)
def read_nodeinfo(*, db: Annotated[Session, Depends(deps.get_db)]) -> Any:
    """
    Get wellknown nodeinfo 2.1.
    """
    return crud.pub.get_wellknown_nodeinfo(db=db)


@router.get("/webfinger", response_model=schemas.WebFinger, response_model_exclude_none=True)
# @router.get("/webfinger")
def read_webfinger(
    *,
    db: Annotated[Session, Depends(deps.get_db)],
    resource: str = "",
) -> Any:
    """
    Get wellknown actor.
    """
    db_obj = crud.pub.get_actor_by_resource(db=db, resource=resource)
    if not resource or not db_obj:
        raise HTTPException(
            status_code=400,
            detail="Well-known actor unknown.",
        )
    return crud.pub.get_wellknown_webfinger(db_obj=db_obj)
