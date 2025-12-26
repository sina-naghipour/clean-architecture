from typing import Any, Dict, List, Optional, Generic, TypeVar, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func as sql_func
import logging
from database.connection import Base
from optl.trace_decorator import trace_repository_operation
ModelType = TypeVar("ModelType", bound=Base)

logger = logging.getLogger(__name__)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db_session: AsyncSession):
        self.model = model
        self.db_session = db_session

    @trace_repository_operation("get_by_id")
    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        result = await self.db_session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    @trace_repository_operation("get_all")
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        query = select(self.model)
        if hasattr(self.model, 'created_at'):
            query = query.order_by(self.model.created_at.desc())
        query = query.offset(skip).limit(limit)
        result = await self.db_session.execute(query)
        return result.scalars().all()

    @trace_repository_operation("create")
    async def create(self, obj_in: Union[Dict[str, Any], Any]) -> Optional[ModelType]:
        if isinstance(obj_in, dict):
            db_obj = self.model(**obj_in)
        else:
            db_obj = self.model(**obj_in.model_dump())
        
        self.db_session.add(db_obj)
        await self.db_session.flush()
        await self.db_session.commit()
        await self.db_session.refresh(db_obj)
        return db_obj

    @trace_repository_operation("update")
    async def update(self, id: Any, obj_in: Union[Dict[str, Any], Any]) -> Optional[ModelType]:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
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

    @trace_repository_operation("delete")
    async def delete(self, id: Any) -> bool:
        obj = await self.get_by_id(id)
        if not obj:
            return False
        await self.db_session.delete(obj)
        await self.db_session.commit()
        return True

    @trace_repository_operation("exists")
    async def exists(self, id: Any) -> bool:
        result = await self.db_session.execute(
            select(self.model.id).where(self.model.id == id)
        )
        return result.scalar_one_or_none() is not None

    @trace_repository_operation("count")
    async def count(self) -> int:
        result = await self.db_session.execute(
            select(sql_func.count(self.model.id))
        )
        return result.scalar_one()

    @trace_repository_operation("get_multi_by_ids")
    async def get_multi_by_ids(self, ids: List[Any]) -> List[ModelType]:
        if not ids:
            return []
        result = await self.db_session.execute(
            select(self.model).where(self.model.id.in_(ids))
        )
        return result.scalars().all()