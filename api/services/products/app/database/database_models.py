from pymongo import IndexModel, ASCENDING, TEXT, DESCENDING
from datetime import datetime
import uuid
from typing import List, Optional

class ProductDB:
    def __init__(
        self,
        name: str,
        price: float,
        stock: int,
        description: str = None,
        tags: List[str] = None,
        images: List[str] = None,
        id: str = None,
        created_at: datetime = None,
        updated_at: datetime = None
    ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.price = price
        self.stock = stock
        self.description = description
        self.tags = tags or []
        self.images = images or []
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def to_dict(self):
        return {
            "_id": self.id,
            "name": self.name,
            "price": self.price,
            "stock": self.stock,
            "description": self.description,
            "tags": self.tags,
            "images": self.images,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return None
        return cls(
            id=data.get("_id"),
            name=data["name"],
            price=data["price"],
            stock=data["stock"],
            description=data.get("description"),
            tags=data.get("tags", []),
            images=data.get("images", []),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )

    COLLECTION_NAME = "products"
    
    @classmethod
    def get_indexes(cls):
        return [
            IndexModel([("name", ASCENDING)]),
            IndexModel([("name", TEXT)]),
            IndexModel([("price", ASCENDING)]),
            IndexModel([("stock", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("tags", ASCENDING)])
        ]