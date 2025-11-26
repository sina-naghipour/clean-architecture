from typing import Any, Dict, List, Optional, Generic, TypeVar, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func as sql_func
from sqlalchemy.exc import SQLAlchemyError
import logging
from database.connection import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

logger = logging.getLogger(__name__)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db_session: AsyncSession):
        self.model = model
        self.db_session = db_session

    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        try:
            result = await self.db_session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} by ID {id}: {e}")
            return None

    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        order_by: Optional[Any] = None
    ) -> List[ModelType]:
        try:
            query = select(self.model)
            
            if order_by:
                query = query.order_by(order_by)
            else:
                if hasattr(self.model, 'created_at'):
                    query = query.order_by(self.model.created_at.desc())
                elif hasattr(self.model, 'id'):
                    query = query.order_by(self.model.id)
            
            query = query.offset(skip).limit(limit)
            
            result = await self.db_session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all {self.model.__name__}: {e}")
            return []

    async def create(self, obj_in: Union[Dict[str, Any], Any]) -> Optional[ModelType]:
        try:
            if isinstance(obj_in, dict):
                db_obj = self.model(**obj_in)
            else:
                db_obj = self.model(**obj_in.model_dump())
            
            self.db_session.add(db_obj)
            await self.db_session.commit()
            await self.db_session.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            return None

    async def update(
        self, 
        id: Any, 
        obj_in: Union[Dict[str, Any], Any]
    ) -> Optional[ModelType]:
        try:
            update_data = {}
            
            if isinstance(obj_in, dict):
                update_data = {k: v for k, v in obj_in.items() if v is not None}
            else:
                update_data = obj_in.model_dump(exclude_unset=True)
            
            if not update_data:
                return await self.get_by_id(id)
            
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            if not update_data:
                return await self.get_by_id(id)
            
            result = await self.db_session.execute(
                update(self.model)
                .where(self.model.id == id)
                .values(**update_data)
                .returning(self.model)
            )
            
            await self.db_session.commit()
            updated_obj = result.scalar_one_or_none()
            
            if updated_obj:
                await self.db_session.refresh(updated_obj)
            
            return updated_obj
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            logger.error(f"Error updating {self.model.__name__} {id}: {e}")
            return None

    async def delete(self, id: Any) -> bool:
        try:
            obj = await self.get_by_id(id)
            if not obj:
                return False
            
            await self.db_session.delete(obj)
            await self.db_session.commit()
            return True
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            logger.error(f"Error deleting {self.model.__name__} {id}: {e}")
            return False

    async def exists(self, id: Any) -> bool:
        try:
            result = await self.db_session.execute(
                select(self.model.id).where(self.model.id == id)
            )
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            logger.error(f"Error checking existence of {self.model.__name__} {id}: {e}")
            return False

    async def count(self) -> int:
        try:
            result = await self.db_session.execute(
                select(sql_func.count(self.model.id))
            )
            return result.scalar_one()
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            return 0

    async def get_multi_by_ids(self, ids: List[Any]) -> List[ModelType]:
        try:
            if not ids:
                return []
                
            result = await self.db_session.execute(select(self.model).where(self.model.id.in_(ids)))
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting multiple {self.model.__name__} by IDs: {e}")
            return []