from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import settings
from app.db import base  # noqa: F401

# make sure all SQL Alchemy models are imported (app.db.base) before initializing DB
# otherwise, SQL Alchemy might fail to initialize relationships properly
# for more details: https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/28


def init_db(db: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line
    # Base.metadata.create_all(bind=engine)

    creator = crud.creator.get_by_email(db, email=settings.FIRST_ADMIN)
    if not creator:
        # Create creator auth
        creator_in = schemas.CreatorCreate(
            email=settings.FIRST_ADMIN,
            password=settings.FIRST_ADMIN_PASSWORD,
            is_admin=True,
        )
        creator = crud.creator.create(db, obj_in=creator_in)  # noqa: F841
