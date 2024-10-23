from typing import Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.models.creator import Creator
from app.schemas.creator import CreatorCreate, CreatorUpdate
from app.tests.utils.utils import random_email, random_lower_string


def creator_authentication_headers(*, client: TestClient, email: str, password: str) -> Dict[str, str]:
    data = {"username": email, "password": password}

    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=data)
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


def create_random_creator(db: Session) -> Creator:
    email = random_email()
    password = random_lower_string()
    creator_in = CreatorCreate(username=email, email=email, password=password)
    creator = crud.creator.create(db=db, obj_in=creator_in)
    return creator


def authentication_token_from_email(*, client: TestClient, email: str, db: Session) -> Dict[str, str]:
    """
    Return a valid token for the creator with given email.

    If the creator doesn't exist it is created first.
    """
    password = random_lower_string()
    creator = crud.creator.get_by_email(db, email=email)
    if not creator:
        creator_in_create = CreatorCreate(username=email, email=email, password=password)
        creator = crud.creator.create(db, obj_in=creator_in_create)
    else:
        creator_in_update = CreatorUpdate(password=password)
        creator = crud.creator.update(db, db_obj=creator, obj_in=creator_in_update)

    return creator_authentication_headers(client=client, email=email, password=password)
