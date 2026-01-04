from datetime import datetime
from typing import Optional
import uuid
from uuid import UUID
import logging

from database.database_models import ReferralDB, CommissionDB
from repositories.referrals_repository import ReferralRepository

class ReferralService:
    def __init__(self, referral_repo: ReferralRepository, logger: logging.Logger = None):
        self.referral_repo = referral_repo
        self.logger = logger or logging.getLogger(__name__)

    async def create_referral(self, referrer_id: str, referred_id: str) -> str:
        code = f"REF_{uuid.uuid4().hex[:8].upper()}"
        referral = ReferralDB(
            referrer_id=referrer_id,
            referred_id=referred_id,
            referral_code=code
        )
        await self.referral_repo.create_referral(referral) 
        return code

    async def accrue_commission(self, order_id: str, customer_id: str, 
                              amount: float, referral_code: Optional[str] = None) -> Optional[CommissionDB]:
        if not referral_code:
            return None

        referral = await self.referral_repo.get_referral_by_code(referral_code)
        if not referral:
            return None

        if referral.referrer_id == customer_id:
            return None

        existing = await self.referral_repo.get_commission_by_order_id(order_id)
        if existing:
            return existing

        commission_amount = amount * 0.10

        commission = CommissionDB(
            referral_id=referral.id,
            order_id=order_id,
            amount=commission_amount,
            status='pending',
            audit_log={
                'calculated_at': datetime.utcnow().isoformat(),
                'order_amount': amount,
                'customer_id': customer_id,
                'rate': 0.10
            }
        )

        return await self.referral_repo.create_commission(commission)

    async def get_report(self, referrer_id: str):
        return await self.referral_repo.get_commissions_by_referrer(referrer_id)