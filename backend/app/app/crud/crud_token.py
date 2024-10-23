from __future__ import annotations
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import Creator, Token
from app.schemas import TokenCreate, TokenUpdate
from app.core.config import settings


class CRUDToken(CRUDBase[Token, TokenCreate, TokenUpdate]):
    # Everything is creator-dependent
    def create(self, db: Session, *, obj_in: str, creator_obj: Creator) -> Token:
        db_obj = db.query(self.model).filter(self.model.token == obj_in).first()
        if db_obj and db_obj.authenticates != creator_obj:
            raise ValueError("Token mismatch between key and creator.")
        obj_in = TokenCreate(**{"token": obj_in, "authenticates_id": creator_obj.id})
        return super().create(db=db, obj_in=obj_in)

    def get(self, db: Session, token: str) -> Token:
        return db.query(self.model).filter(self.model.token == token).first()

    def get_by_creator(self, *, creator: Creator, token: str) -> Token:
        return creator.tokens.filter(self.model.token == token).first()

    def get_multi(self, *, creator: Creator, page: int = 0, page_break: bool = False) -> list[Token]:
        db_objs = creator.tokens
        if not page_break:
            if page > 0:
                db_objs = db_objs.offset(page * settings.MULTI_MAX)
            db_objs = db_objs.limit(settings.MULTI_MAX)
        return db_objs.all()

    def remove(self, db: Session, *, db_obj: Token) -> None:
        db.delete(db_obj)
        db.commit()
        return None


token = CRUDToken(Token)
