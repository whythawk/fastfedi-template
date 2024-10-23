from .crud_creator import creator  # noqa: F401
from .crud_token import token  # noqa: F401
from .crud_actor import actor  # noqa: F401
from .crud_pub import pub  # noqa: F401


# For a new basic set of CRUD operations you could just do

# from .base import CRUDBase
# from app.models.item import Item
# from app.schemas.item import ItemCreate, ItemUpdate

# item = CRUDBase[Item, ItemCreate, ItemUpdate](Item)
