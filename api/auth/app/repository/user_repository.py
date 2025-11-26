import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update as sql_update
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import uuid

from database.database_models import UserModel
from .base import BaseRepository
from database.pydantic_models import UserCreate, ProfileUpdateRequest

logger = logging.getLogger(__name__)

class UserRepository(BaseRepository[UserModel]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(UserModel, db_session)
        self.logger = logger

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        try:
            result = await self.db_session.execute(
                select(UserModel).where(
                    UserModel.email.ilike(email)
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Error getting user by email {email}: {e}")
            return None

    async def get_active_user_by_email(self, email: str) -> Optional[UserModel]:
        try:
            result = await self.db_session.execute(
                select(UserModel).where(
                    and_(
                        UserModel.email.ilike(email),
                        UserModel.is_active == True
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Error getting active user by email {email}: {e}")
            return None

    async def email_exists(self, email: str) -> bool:
        user = await self.get_by_email(email)
        return user is not None

    async def create_user(self, user_data: UserCreate) -> Optional[UserModel]:
        try:
            return await self.create(user_data)
        except IntegrityError:
            await self.db_session.rollback()
            raise ValueError("User with this email already exists")
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error creating user: {e}")
            raise

    async def update_last_login(self, user_id: uuid.UUID) -> bool:
        try:
            result = await self.db_session.execute(
                sql_update(UserModel)
                .where(UserModel.id == user_id)
                .values(last_login=datetime.utcnow())
            )
            await self.db_session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error updating last login for user {user_id}: {e}")
            return False

    async def update_password(self, user_id: uuid.UUID, new_password_hash: str) -> bool:
        try:
            result = await self.db_session.execute(
                sql_update(UserModel)
                .where(UserModel.id == user_id)
                .values(password=new_password_hash)
            )
            await self.db_session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error updating password for user {user_id}: {e}")
            return False

    async def activate_user(self, user_id: uuid.UUID) -> bool:
        try:
            result = await self.db_session.execute(
                sql_update(UserModel)
                .where(UserModel.id == user_id)
                .values(is_active=True)
            )
            await self.db_session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error activating user {user_id}: {e}")
            return False

    async def deactivate_user(self, user_id: uuid.UUID) -> bool:
        try:
            result = await self.db_session.execute(
                sql_update(UserModel)
                .where(UserModel.id == user_id)
                .values(is_active=False)
            )
            await self.db_session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error deactivating user {user_id}: {e}")
            return False

    async def update_profile(self, user_id: uuid.UUID, profile_data: ProfileUpdateRequest) -> Optional[UserModel]:
        update_data = profile_data.model_dump(exclude_unset=True)
        return await self.update(user_id, update_data)

    async def search_users(self, query: str, skip: int = 0, limit: int = 50) -> List[UserModel]:
        try:
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
        except Exception as e:
            self.logger.error(f"Error searching users with query '{query}': {e}")
            return []

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        try:
            result = await self.db_session.execute(
                select(UserModel)
                .where(UserModel.is_active == True)
                .offset(skip)
                .limit(limit)
                .order_by(UserModel.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            self.logger.error(f"Error getting active users: {e}")
            return []

    async def get_users_created_after(self, date: datetime) -> List[UserModel]:
        try:
            result = await self.db_session.execute(
                select(UserModel)
                .where(UserModel.created_at >= date)
                .order_by(UserModel.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            self.logger.error(f"Error getting users created after {date}: {e}")
            return []