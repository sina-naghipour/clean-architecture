from datetime import datetime
from typing import Optional, Dict, Any
import uuid
import logging
from decimal import Decimal
from dotenv import load_dotenv
import os


from database.database_models import ReferralDB, CommissionDB
from repositories.referrals_repository import ReferralRepository

load_dotenv()


class ReferralService:
    def __init__(self, referral_repo: ReferralRepository, logger: logging.Logger = None):
        self.referral_repo = referral_repo
        self.logger = logger or logging.getLogger(__name__)
        self.commission_rate = Decimal(os.getenv('REFERRAL_COMMISSION_RATE', '0.05'))

    async def create_referral(self, referrer_id: str, referred_id: str) -> str:
        if referrer_id == referred_id:
            raise ValueError("Cannot create self-referral")
        
        exists = await self.referral_repo.referral_exists(referrer_id, referred_id)
        if exists:
            raise ValueError(f"Referral already exists for {referrer_id} -> {referred_id}")
        
        code = f"REF_{uuid.uuid4().hex[:8].upper()}"
        referral = ReferralDB(
            referrer_id=referrer_id,
            referred_id=referred_id,
            referral_code=code
        )
        
        await self.referral_repo.create_referral(referral)
        self.logger.info(f"Created referral: {referrer_id} -> {referred_id} with code {code}")
        return code

    async def accrue_commission(self, order_id: str, customer_id: str, 
                              amount: float, referral_code: Optional[str] = None) -> Optional[CommissionDB]:
        if not referral_code:  # Guard 1 - no code
            self.logger.debug(f"No referral code for order {order_id}")
            return None

        referral = await self.referral_repo.get_referral_by_code(referral_code)  # Guard 2 - valid code
        if not referral:
            self.logger.warning(f"Invalid referral code: {referral_code}")
            return None

        if referral.referrer_id == customer_id:  # Guard 3 - self-referral
            self.logger.warning(f"Self-referral attempt blocked: {customer_id}")
            return None

        if referral.referred_id != customer_id:  # Guard 4 - customer mismatch
            self.logger.warning(
                f"Customer mismatch: referral for {referral.referred_id}, "
                f"payment from {customer_id}"
            )
            return None

        existing = await self.referral_repo.get_commission_by_order_id(order_id)  # Guard 5 - idempotency
        if existing:
            self.logger.info(f"Commission already exists for order {order_id}")
            return existing

        if amount < 1.00:  # Guard 6 - minimum amount
            self.logger.warning(f"Amount too low for commission: {amount}")
            return None

        commission_amount = Decimal(str(amount)) * self.commission_rate 
        
        audit_log = {
            'calculated_at': datetime.utcnow().isoformat(),
            'order_amount': float(amount),
            'customer_id': customer_id,
            'referrer_id': referral.referrer_id,
            'commission_rate': float(self.commission_rate),
            'fraud_checks_passed': True
        }

        commission = CommissionDB(
            referral_id=referral.id,
            order_id=order_id,
            amount=float(commission_amount),
            status='pending',
            audit_log=audit_log
        )

        try:
            created = await self.referral_repo.create_commission(commission)
            self.logger.info(
                f"Commission accrued: ${commission_amount:.2f} for order {order_id}, "
                f"referrer: {referral.referrer_id}"
            )
            return created
        except ValueError as e:
            self.logger.warning(f"Commission creation failed: {e}")
            return None

    async def get_report(self, referrer_id: str) -> Dict[str, Any]:
        commissions = await self.referral_repo.get_commissions_by_referrer(referrer_id)
        
        total_commissions = sum(c.amount for c in commissions)
        pending = sum(c.amount for c in commissions if c.status == 'pending')
        paid = sum(c.amount for c in commissions if c.status == 'paid')
        
        return {
            'referrer_id': referrer_id,
            'total_commissions': len(commissions),
            'total_amount': total_commissions,
            'pending_amount': pending,
            'paid_amount': paid,
            'commissions': [
                {
                    'id': str(c.id),
                    'order_id': c.order_id,
                    'amount': c.amount,
                    'status': c.status,
                    'created_at': c.created_at.isoformat()
                }
                for c in commissions
            ]
        }