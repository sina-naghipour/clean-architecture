from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
import logging

from database.database_models import ReferralDB, CommissionDB

class ReferralRepository:
    def __init__(self, session: AsyncSession, logger: logging.Logger = None):
        self.session = session
        self.logger = logger or logging.getLogger(__name__)

    async def get_referral_by_code(self, referral_code: str) -> Optional[ReferralDB]:
        try:
            stmt = select(ReferralDB).where(ReferralDB.referral_code == referral_code)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching referral: {e}")
            raise

    async def create_referral(self, referral: ReferralDB) -> ReferralDB:
        try:
            self.session.add(referral)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(referral)
            return referral
        except SQLAlchemyError as e:
            self.logger.error(f"Error creating referral: {e}")
            await self.session.rollback()
            raise

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
        except SQLAlchemyError as e:
            self.logger.error(f"Error creating commission: {e}")
            await self.session.rollback()
            raise

    async def get_commissions_by_referrer(self, referrer_id: str) -> List[CommissionDB]:
        try:
            stmt = (
                select(CommissionDB)
                .join(ReferralDB)
                .where(ReferralDB.referrer_id == referrer_id)
                .order_by(CommissionDB.created_at.desc())
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching commissions: {e}")
            raise