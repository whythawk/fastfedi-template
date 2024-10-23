from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.creator import Creator
from app.schemas.creator import CreatorCreate, CreatorInDB, CreatorUpdate
from app.schemas.totp import NewTOTP


class CRUDCreator(CRUDBase[Creator, CreatorCreate, CreatorUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[Creator]:
        return db.query(Creator).filter(Creator.email == email).first()

    def create(self, db: Session, *, obj_in: CreatorCreate) -> Creator:
        db_obj = Creator(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password) if obj_in.password is not None else None,
            is_admin=obj_in.is_admin,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: Creator, obj_in: Union[CreatorUpdate, Dict[str, Any]]) -> Creator:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        if update_data.get("password"):
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        if update_data.get("email") and db_obj.email != update_data["email"]:
            update_data["email_validated"] = False
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[Creator]:
        creator = self.get_by_email(db, email=email)
        if not creator:
            return None
        if not verify_password(plain_password=password, hashed_password=creator.hashed_password):
            return None
        return creator

    def validate_email(self, db: Session, *, db_obj: Creator) -> Creator:
        obj_in = CreatorUpdate(**CreatorInDB.model_validate(db_obj).model_dump())
        obj_in.email_validated = True
        return self.update(db=db, db_obj=db_obj, obj_in=obj_in)

    def activate_totp(self, db: Session, *, db_obj: Creator, totp_in: NewTOTP) -> Creator:
        obj_in = CreatorUpdate(**CreatorInDB.model_validate(db_obj).model_dump())
        obj_in = obj_in.model_dump(exclude_unset=True)
        obj_in["totp_secret"] = totp_in.secret
        return self.update(db=db, db_obj=db_obj, obj_in=obj_in)

    def deactivate_totp(self, db: Session, *, db_obj: Creator) -> Creator:
        obj_in = CreatorUpdate(**CreatorInDB.model_validate(db_obj).model_dump())
        obj_in = obj_in.model_dump(exclude_unset=True)
        obj_in["totp_secret"] = None
        obj_in["totp_counter"] = None
        return self.update(db=db, db_obj=db_obj, obj_in=obj_in)

    def update_totp_counter(self, db: Session, *, db_obj: Creator, new_counter: int) -> Creator:
        obj_in = CreatorUpdate(**CreatorInDB.model_validate(db_obj).model_dump())
        obj_in = obj_in.model_dump(exclude_unset=True)
        obj_in["totp_counter"] = new_counter
        return self.update(db=db, db_obj=db_obj, obj_in=obj_in)

    def toggle_creator_state(self, db: Session, *, obj_in: Union[CreatorUpdate, Dict[str, Any]]) -> Creator:
        db_obj = self.get_by_email(db, email=obj_in.email)
        if not db_obj:
            return None
        return self.update(db=db, db_obj=db_obj, obj_in=obj_in)

    def has_password(self, creator: Creator) -> bool:
        if creator.hashed_password:
            return True
        return False

    def is_active(self, creator: Creator) -> bool:
        return creator.is_active

    def is_admin(self, creator: Creator) -> bool:
        return creator.is_admin

    def is_email_validated(self, creator: Creator) -> bool:
        return creator.email_validated


creator = CRUDCreator(Creator)
