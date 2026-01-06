from datetime import datetime
from typing import Optional, Dict, Any
import uuid
import logging
from decimal import Decimal
from dotenv import load_dotenv
import os

from database.database_models import CommissionDB
from repositories.commissions_repository import CommissionRepository

load_dotenv()


class CommissionService:
    def __init__(self, commission_repo: CommissionRepository, logger: logging.Logger = None):
        self.commission_repo = commission_repo
        self.logger = logger or logging.getLogger(__name__)
        self.commission_rate = Decimal(os.getenv('REFERRAL_COMMISSION_RATE', '0.05'))


    async def accrue_commission(self, order_id: str, customer_id: str, 
                              amount: float, referrer_id: Optional[str] = None) -> Optional[CommissionDB]:
        self.logger.debug(f"referrer_id: {referrer_id}, customer_id: {customer_id}, order_id: {order_id}, amount: {amount}")
        print(f"referrer_id: {referrer_id}, customer_id: {customer_id}, order_id: {order_id}, amount: {amount}")
        if not referrer_id:  # Guard 1 - no referrer
            self.logger.debug(f"No referrer_id for order {order_id}")
            return None

        if referrer_id == customer_id:  # Guard 2 - self-referral
            self.logger.warning(f"Self-referral attempt blocked: {customer_id}")
            return None

        existing = await self.commission_repo.get_commission_by_order_id(order_id)  # Guard 3 - idempotency
        if existing:
            self.logger.info(f"Commission already exists for order {order_id}")
            return existing

        if amount < 1.00:  # Guard 4 - minimum amount
            self.logger.warning(f"Amount too low for commission: {amount}")
            return None

        commission_amount = Decimal(str(amount)) * self.commission_rate 
        
        audit_log = {
            'calculated_at': datetime.utcnow().isoformat(),
            'order_amount': float(amount),
            'customer_id': customer_id,
            'referrer_id': referrer_id,
            'commission_rate': float(self.commission_rate),
            'fraud_checks_passed': True
        }

        commission = CommissionDB(
            referrer_id=referrer_id,
            order_id=order_id,
            amount=float(commission_amount),
            status='pending',
            audit_log=audit_log
        )

        try:
            created = await self.commission_repo.create_commission(commission)
            self.logger.info(
                f"Commission accrued: ${commission_amount:.2f} for order {order_id}, "
                f"referrer: {referrer_id}"
            )
            return created
        except ValueError as e:
            self.logger.warning(f"Commission creation failed: {e}")
            return None

    async def get_report(self, referrer_id: str) -> Dict[str, Any]:
        commissions = await self.commission_repo.get_commissions_by_referrer(referrer_id)
        
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

    async def mark_commission_paid(self, commission_id: str) -> Optional[CommissionDB]:
        try:
            return await self.commission_repo.update_commission_status(uuid.UUID(commission_id), 'paid')
        except Exception as e:
            self.logger.error(f"Failed to mark commission as paid: {e}")
            return None