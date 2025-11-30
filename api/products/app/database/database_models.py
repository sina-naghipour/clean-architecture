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
        image_ids: List[str] = None,
        primary_image_id: str = None,
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
        self.image_ids = image_ids or []
        self.primary_image_id = primary_image_id
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
            "image_ids": self.image_ids,
            "primary_image_id": self.primary_image_id,
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
            image_ids=data.get("image_ids", []),
            primary_image_id=data.get("primary_image_id"),
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
            IndexModel([("tags", ASCENDING)]),
            IndexModel([("image_ids", ASCENDING)])
        ]


class ImageDB:
    def __init__(
        self,
        product_id: str,
        filename: str,
        original_name: str,
        mime_type: str,
        size: int,
        width: int,
        height: int,
        is_primary: bool = False,
        id: str = None,
        uploaded_at: datetime = None
    ):
        self.id = id or str(uuid.uuid4())
        self.product_id = product_id
        self.filename = filename
        self.original_name = original_name
        self.mime_type = mime_type
        self.size = size
        self.width = width
        self.height = height
        self.is_primary = is_primary
        self.uploaded_at = uploaded_at or datetime.utcnow()

    def to_dict(self):
        return {
            "_id": self.id,
            "product_id": self.product_id,
            "filename": self.filename,
            "original_name": self.original_name,
            "mime_type": self.mime_type,
            "size": self.size,
            "width": self.width,
            "height": self.height,
            "is_primary": self.is_primary,
            "uploaded_at": self.uploaded_at
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return None
        return cls(
            id=data.get("_id"),
            product_id=data["product_id"],
            filename=data["filename"],
            original_name=data["original_name"],
            mime_type=data["mime_type"],
            size=data["size"],
            width=data["width"],
            height=data["height"],
            is_primary=data.get("is_primary", False),
            uploaded_at=data.get("uploaded_at")
        )

    COLLECTION_NAME = "product_images"
    
    @classmethod
    def get_indexes(cls):
        return [
            IndexModel([("product_id", ASCENDING)]),
            IndexModel([("is_primary", ASCENDING)]),
            IndexModel([("uploaded_at", DESCENDING)]),
            IndexModel([("mime_type", ASCENDING)]),
            IndexModel([("product_id", ASCENDING), ("is_primary", ASCENDING)])
        ]