from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    oauth,
    creators,
    proxy,
    wellknown,
    root,
)

api_router = APIRouter()
api_router.include_router(creators.router, prefix="/creators", tags=["creators"])
api_router.include_router(proxy.router, prefix="/proxy", tags=["proxy"])

root_router = APIRouter()
root_router.include_router(oauth.router, prefix="/oauth", tags=["oauth"])
root_router.include_router(wellknown.router, prefix="/.well-known", tags=["wellknown"])
root_router.include_router(root.router, tags=["root"])
