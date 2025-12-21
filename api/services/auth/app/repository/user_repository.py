from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update as sql_update
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import uuid
import logging

from database.database_models import UserModel
from .base import BaseRepository
from optl.trace_decorator import trace_repository_operation 
from database.pydantic_models import UserCreate
from opentelemetry import trace

logger = logging.getLogger(__name__)

class UserRepository(BaseRepository[UserModel]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(UserModel, db_session)
        self.logger = logger

    @trace_repository_operation("get_by_email")
    async def get_by_email(self, email: str) -> Optional[UserModel]:
        result = await self.db_session.execute(
            select(UserModel).where(UserModel.email.ilike(email))
        )
        return result.scalar_one_or_none()

    @trace_repository_operation("get_active_user_by_email")
    async def get_active_user_by_email(self, email: str) -> Optional[UserModel]:
        result = await self.db_session.execute(
            select(UserModel).where(
                and_(
                    UserModel.email.ilike(email),
                    UserModel.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()

    @trace_repository_operation("email_exists")
    async def email_exists(self, email: str) -> bool:
        user = await self.get_by_email(email)
        return user is not None

    @trace_repository_operation("create_user")
    async def create_user(self, user_data: UserCreate) -> Optional[UserModel]:
        try:
            return await self.create(user_data)
        except IntegrityError:
            await self.db_session.rollback()
            self.logger.error(f"User with email {user_data.email} already exists")
            raise ValueError("User with this email already exists")

    @trace_repository_operation("update_last_login")
    async def update_last_login(self, user_id: uuid.UUID) -> bool:
        result = await self.db_session.execute(
            sql_update(UserModel)
            .where(UserModel.id == user_id)
            .values(last_login=datetime.utcnow())
        )
        await self.db_session.commit()
        return result.rowcount > 0

    @trace_repository_operation("update_password")
    async def update_password(self, user_id: uuid.UUID, new_password_hash: str) -> bool:
        result = await self.db_session.execute(
            sql_update(UserModel)
            .where(UserModel.id == user_id)
            .values(password=new_password_hash)
        )
        await self.db_session.commit()
        return result.rowcount > 0

    @trace_repository_operation("activate_user")
    async def activate_user(self, user_id: uuid.UUID) -> bool:
        result = await self.db_session.execute(
            sql_update(UserModel)
            .where(UserModel.id == user_id)
            .values(is_active=True)
        )
        await self.db_session.commit()
        return result.rowcount > 0

    @trace_repository_operation("deactivate_user")
    async def deactivate_user(self, user_id: uuid.UUID) -> bool:
        result = await self.db_session.execute(
            sql_update(UserModel)
            .where(UserModel.id == user_id)
            .values(is_active=False)
        )
        await self.db_session.commit()
        return result.rowcount > 0


    @trace_repository_operation("search_users")
    async def search_users(self, query: str, skip: int = 0, limit: int = 50) -> List[UserModel]:
        result = await self.db_session.execute(
            select(UserModel)
            .where(
                and_(
                    UserModel.is_active == True,
                    or_(
                        UserModel.name.ilike(f"%{query}%"),
                        UserModel.email.ilike(f"%{query}%")
                    )
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(UserModel.created_at.desc())
        )
        return result.scalars().all()

    @trace_repository_operation("get_active_users")
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        result = await self.db_session.execute(
            select(UserModel)
            .where(UserModel.is_active == True)
            .offset(skip)
            .limit(limit)
            .order_by(UserModel.created_at.desc())
        )
        return result.scalars().all()

    @trace_repository_operation("get_users_created_after")
    async def get_users_created_after(self, date: datetime) -> List[UserModel]:
        result = await self.db_session.execute(
            select(UserModel)
            .where(UserModel.created_at >= date)
            .order_by(UserModel.created_at.desc())
        )
        return result.scalars().all()