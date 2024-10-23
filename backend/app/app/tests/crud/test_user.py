from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import crud
from app.core.security import verify_password
from app.schemas.creator import CreatorCreate, CreatorUpdate
from app.tests.utils.utils import random_email, random_lower_string


def test_create_creator(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    creator_in = CreatorCreate(email=email, password=password)
    creator = crud.creator.create(db, obj_in=creator_in)
    assert creator.email == email
    assert hasattr(creator, "hashed_password")


def test_authenticate_creator(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    creator_in = CreatorCreate(email=email, password=password)
    creator = crud.creator.create(db, obj_in=creator_in)
    authenticated_creator = crud.creator.authenticate(db, email=email, password=password)
    assert authenticated_creator
    assert creator.email == authenticated_creator.email


def test_not_authenticate_creator(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    creator = crud.creator.authenticate(db, email=email, password=password)
    assert creator is None


def test_check_if_creator_is_active(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    creator_in = CreatorCreate(email=email, password=password)
    creator = crud.creator.create(db, obj_in=creator_in)
    is_active = crud.creator.is_active(creator)
    assert is_active is True


def test_check_if_creator_is_active_inactive(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    creator_in = CreatorCreate(email=email, password=password, disabled=True)
    creator = crud.creator.create(db, obj_in=creator_in)
    is_active = crud.creator.is_active(creator)
    assert is_active


def test_check_if_creator_is_admin(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    creator_in = CreatorCreate(email=email, password=password, is_admin=True)
    creator = crud.creator.create(db, obj_in=creator_in)
    is_admin = crud.creator.is_admin(creator)
    assert is_admin is True


def test_check_if_creator_is__normal_creator(db: Session) -> None:
    creatorname = random_email()
    password = random_lower_string()
    creator_in = CreatorCreate(email=creatorname, password=password)
    creator = crud.creator.create(db, obj_in=creator_in)
    is_admin = crud.creator.is_admin(creator)
    assert is_admin is False


def test_get_creator(db: Session) -> None:
    password = random_lower_string()
    creatorname = random_email()
    creator_in = CreatorCreate(email=creatorname, password=password, is_admin=True)
    creator = crud.creator.create(db, obj_in=creator_in)
    creator_2 = crud.creator.get(db, id=creator.id)
    assert creator_2
    assert creator.email == creator_2.email
    assert jsonable_encoder(creator) == jsonable_encoder(creator_2)


def test_update_creator(db: Session) -> None:
    password = random_lower_string()
    email = random_email()
    creator_in = CreatorCreate(email=email, password=password, is_admin=True)
    creator = crud.creator.create(db, obj_in=creator_in)
    new_password = random_lower_string()
    creator_in_update = CreatorUpdate(password=new_password, is_admin=True)
    crud.creator.update(db, db_obj=creator, obj_in=creator_in_update)
    creator_2 = crud.creator.get(db, id=creator.id)
    assert creator_2
    assert creator.email == creator_2.email
    assert verify_password(new_password, creator_2.hashed_password)
