from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging

from database.database_models import CommissionDB

class CommissionRepository:
    def __init__(self, session: AsyncSession, logger: logging.Logger = None):
        self.session = session
        self.logger = logger or logging.getLogger(__name__)

    async def get_commission_by_order_id(self, order_id: str) -> Optional[CommissionDB]:
        try:
            stmt = select(CommissionDB).where(CommissionDB.order_id == order_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching commission: {e}")
            raise

    async def create_commission(self, commission: CommissionDB) -> CommissionDB:
        try:
            self.session.add(commission)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(commission)
            return commission
        except IntegrityError:
            await self.session.rollback()
            raise ValueError(f"Commission already exists for order: {commission.order_id}")
        except SQLAlchemyError as e:
            self.logger.error(f"Error creating commission: {e}")
            await self.session.rollback()
            raise

    async def get_commissions_by_referrer(self, referrer_id: str) -> List[CommissionDB]:
        try:
            stmt = (
                select(CommissionDB)
                .where(CommissionDB.referrer_id == referrer_id)
                .order_by(CommissionDB.created_at.desc())
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching commissions: {e}")
            raise

    async def update_commission_status(self, commission_id: UUID, status: str) -> Optional[CommissionDB]:
        try:
            stmt = select(CommissionDB).where(CommissionDB.id == commission_id)
            result = await self.session.execute(stmt)
            commission = result.scalar_one_or_none()
            
            if commission:
                commission.status = status
                await self.session.commit()
                await self.session.refresh(commission)
            
            return commission
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating commission: {e}")
            await self.session.rollback()
            raise