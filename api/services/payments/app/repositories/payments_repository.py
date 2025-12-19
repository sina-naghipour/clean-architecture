from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime

from database.database_models import PaymentDB, PaymentStatus

class PaymentRepository:
    def __init__(self, session: AsyncSession, logger: logging.Logger = None):
        self.session = session
        self.logger = logger or logging.getLogger(__name__).getChild("PaymentRepository")

    async def create_payment(self, payment_data: PaymentDB) -> Optional[PaymentDB]:
        try:
            self.logger.info(f"Creating payment for order: {payment_data.order_id}")
            
            self.session.add(payment_data)
            await self.session.commit()
            await self.session.refresh(payment_data)

            self.logger.info(f"Payment created successfully: {payment_data.id}")
            return payment_data
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error creating payment: {e}")
            await self.session.rollback()
            raise

    async def get_payment_by_id(self, payment_id: UUID) -> Optional[PaymentDB]:
        try:
            self.logger.info(f"Fetching payment by ID: {payment_id}")
            
            stmt = select(PaymentDB).where(PaymentDB.id == payment_id)
            result = await self.session.execute(stmt)
            payment = result.scalar_one_or_none()
            
            if payment:
                self.logger.info(f"Payment found: {payment_id}")
            else:
                self.logger.info(f"Payment not found: {payment_id}")
                
            return payment
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching payment {payment_id}: {e}")
            raise

    async def get_payment_by_order_id(self, order_id: str) -> Optional[PaymentDB]:
        try:
            self.logger.info(f"Fetching payment by order ID: {order_id}")
            
            stmt = select(PaymentDB).where(PaymentDB.order_id == order_id)
            result = await self.session.execute(stmt)
            payment = result.scalar_one_or_none()
            
            if payment:
                self.logger.info(f"Payment found for order: {order_id}")
            else:
                self.logger.info(f"No payment found for order: {order_id}")
                
            return payment
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching payment for order {order_id}: {e}")
            raise

    async def get_payment_by_stripe_id(self, stripe_payment_intent_id: str) -> Optional[PaymentDB]:
        try:
            self.logger.info(f"Fetching payment by Stripe ID: {stripe_payment_intent_id}")
            
            stmt = select(PaymentDB).where(PaymentDB.stripe_payment_intent_id == stripe_payment_intent_id)
            result = await self.session.execute(stmt)
            payment = result.scalar_one_or_none()
            
            if payment:
                self.logger.info(f"Payment found for Stripe ID: {stripe_payment_intent_id}")
            else:
                self.logger.info(f"No payment found for Stripe ID: {stripe_payment_intent_id}")
                
            return payment
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching payment for Stripe ID {stripe_payment_intent_id}: {e}")
            raise

    async def update_payment_status(self, payment_id: UUID, new_status: PaymentStatus) -> Optional[PaymentDB]:
        try:
            self.logger.info(f"Updating payment status: {payment_id} -> {new_status}")
            
            stmt = (
                update(PaymentDB)
                .where(PaymentDB.id == payment_id)
                .values(status=new_status, updated_at=datetime.utcnow())
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            if result.rowcount > 0:
                self.logger.info(f"Payment status updated successfully: {payment_id}")
                return await self.get_payment_by_id(payment_id)
            else:
                self.logger.info(f"No payment found for status update: {payment_id}")
                return None
                
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating payment status {payment_id}: {e}")
            await self.session.rollback()
            raise

    async def update_payment_stripe_id(self, payment_id: UUID, stripe_payment_intent_id: str) -> Optional[PaymentDB]:
        try:
            self.logger.info(f"Updating payment Stripe ID: {payment_id} -> {stripe_payment_intent_id}")
            
            stmt = (
                update(PaymentDB)
                .where(PaymentDB.id == payment_id)
                .values(
                    stripe_payment_intent_id=stripe_payment_intent_id,
                    updated_at=datetime.utcnow()
                )
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            if result.rowcount > 0:
                self.logger.info(f"Payment Stripe ID updated successfully: {payment_id}")
                return await self.get_payment_by_id(payment_id)
            else:
                self.logger.info(f"No payment found for Stripe ID update: {payment_id}")
                return None
                
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating payment Stripe ID {payment_id}: {e}")
            await self.session.rollback()
            raise

    async def update_payment_metadata(self, payment_id: UUID, metadata: dict) -> Optional[PaymentDB]:
        try:
            self.logger.info(f"Updating payment metadata: {payment_id}")
            
            stmt = (
                update(PaymentDB)
                .where(PaymentDB.id == payment_id)
                .values(payment_metadata=metadata, updated_at=datetime.utcnow())
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            if result.rowcount > 0:
                self.logger.info(f"Payment metadata updated successfully: {payment_id}")
                return await self.get_payment_by_id(payment_id)
            else:
                self.logger.info(f"No payment found for metadata update: {payment_id}")
                return None
                
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating payment metadata {payment_id}: {e}")
            await self.session.rollback()
            raise

    async def update_payment_client_secret(self, payment_id: UUID, client_secret: str) -> Optional[PaymentDB]:
        try:
            self.logger.info(f"Updating payment client secret: {payment_id}")
            
            stmt = (
                update(PaymentDB)
                .where(PaymentDB.id == payment_id)
                .values(
                    client_secret=client_secret,
                    updated_at=datetime.now()
                )
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            if result.rowcount > 0:
                self.logger.info(f"Payment client secret updated successfully: {payment_id}")
                return await self.get_payment_by_id(payment_id)
            else:
                self.logger.info(f"No payment found for client secret update: {payment_id}")
                return None
                
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating payment client secret {payment_id}: {e}")
            await self.session.rollback()
            raise

    async def list_payments_by_user(self, user_id: str, skip: int = 0, limit: int = 20) -> List[PaymentDB]:
        try:
            self.logger.info(f"Listing payments for user: {user_id}")
            
            stmt = (
                select(PaymentDB)
                .where(PaymentDB.user_id == user_id)
                .order_by(PaymentDB.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            payments = result.scalars().all()
            
            self.logger.info(f"Found {len(payments)} payments for user: {user_id}")
            return list(payments)
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error listing payments for user {user_id}: {e}")
            raise

    async def count_payments(self) -> int:
        try:
            self.logger.debug("Counting total payments")
            
            stmt = select(PaymentDB)
            result = await self.session.execute(stmt)
            count = len(result.scalars().all())
            
            self.logger.debug(f"Total payments: {count}")
            return count
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error counting payments: {e}")
            raise