from typing import Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.schemas.creator import CreatorCreate
from app.tests.utils.utils import random_email, random_lower_string


def test_get_creators__me(client: TestClient, _token_headers: Dict[str, str]) -> None:
    r = client.get(f"{settings.API_V1_STR}/creators/me", headers=_token_headers)
    current_creator = r.json()
    assert current_creator
    assert current_creator["is_active"] is True
    assert current_creator["is_admin"]
    assert current_creator["email"] == settings.FIRST_ADMIN


def test_get_creators_normal_creator_me(client: TestClient, normal_creator_token_headers: Dict[str, str]) -> None:
    r = client.get(f"{settings.API_V1_STR}/creators/me", headers=normal_creator_token_headers)
    current_creator = r.json()
    assert current_creator
    assert current_creator["is_active"] is True
    assert current_creator["is_admin"] is False
    assert current_creator["email"] == settings.EMAIL_TEST_USER


def test_create_creator_new_email(client: TestClient, _token_headers: dict, db: Session) -> None:
    creatorname = random_email()
    password = random_lower_string()
    data = {"email": creatorname, "password": password}
    r = client.post(
        f"{settings.API_V1_STR}/creators/",
        headers=_token_headers,
        json=data,
    )
    assert 200 <= r.status_code < 300
    created_creator = r.json()
    creator = crud.creator.get_by_email(db, email=creatorname)
    assert creator
    assert creator.email == created_creator["email"]


def test_get_existing_creator(client: TestClient, _token_headers: dict, db: Session) -> None:
    creatorname = random_email()
    password = random_lower_string()
    creator_in = CreatorCreate(email=creatorname, password=password)
    creator = crud.creator.create(db, obj_in=creator_in)
    creator_id = creator.id
    r = client.get(
        f"{settings.API_V1_STR}/creators/{creator_id}",
        headers=_token_headers,
    )
    assert 200 <= r.status_code < 300
    api_creator = r.json()
    existing_creator = crud.creator.get_by_email(db, email=creatorname)
    assert existing_creator
    assert existing_creator.email == api_creator["email"]


def test_create_creator_existing_creatorname(client: TestClient, _token_headers: dict, db: Session) -> None:
    creatorname = random_email()
    # creatorname = email
    password = random_lower_string()
    creator_in = CreatorCreate(email=creatorname, password=password)
    crud.creator.create(db, obj_in=creator_in)
    data = {"email": creatorname, "password": password}
    r = client.post(
        f"{settings.API_V1_STR}/creators/",
        headers=_token_headers,
        json=data,
    )
    created_creator = r.json()
    assert r.status_code == 400
    assert "_id" not in created_creator


def test_create_creator_by_normal_creator(client: TestClient, normal_creator_token_headers: Dict[str, str]) -> None:
    creatorname = random_email()
    password = random_lower_string()
    data = {"email": creatorname, "password": password}
    r = client.post(
        f"{settings.API_V1_STR}/creators/",
        headers=normal_creator_token_headers,
        json=data,
    )
    assert r.status_code == 400


def test_retrieve_creators(client: TestClient, _token_headers: dict, db: Session) -> None:
    creatorname = random_email()
    password = random_lower_string()
    creator_in = CreatorCreate(email=creatorname, password=password)
    crud.creator.create(db, obj_in=creator_in)

    creatorname2 = random_email()
    password2 = random_lower_string()
    creator_in2 = CreatorCreate(email=creatorname2, password=password2)
    crud.creator.create(db, obj_in=creator_in2)

    r = client.get(f"{settings.API_V1_STR}/creators/", headers=_token_headers)
    all_creators = r.json()

    assert len(all_creators) > 1
    for item in all_creators:
        assert "email" in item
