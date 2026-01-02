from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime

from database.database_models import PaymentDB, PaymentStatus
from optl.trace_decorator import trace_repository_operation

class PaymentRepository:
    def __init__(self, session: AsyncSession, logger: logging.Logger = None):
        self.session = session
        self.model = PaymentDB  # Add this for decorator
        self.logger = logger or logging.getLogger(__name__).getChild("PaymentRepository")

    @trace_repository_operation("create_payment")
    async def create_payment(self, payment_data: PaymentDB) -> Optional[PaymentDB]:
        try:
            self.logger.info(f"Creating payment for order: {payment_data.order_id}")
            
            self.session.add(payment_data)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(payment_data)

            self.logger.info(f"Payment created successfully: {payment_data.id}")
            return payment_data
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error creating payment: {e}")
            await self.session.rollback()
            raise

    @trace_repository_operation("get_payment_by_id")
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

    @trace_repository_operation("get_payment_by_order_id")
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

    @trace_repository_operation("get_payment_by_stripe_id")
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

    @trace_repository_operation("update_payment_status")
    async def update_payment_status(self, payment_id: UUID, new_status: PaymentStatus) -> Optional[PaymentDB]:
        if new_status == PaymentStatus.CREATED:
            self.logger.info('Did not change to created, payment already exists.')
            return
        try:
            self.logger.info(f"Updating payment status: {payment_id} -> {new_status}")
            
            stmt = (
                update(PaymentDB)
                .where(PaymentDB.id == payment_id)
                .values(status=new_status, updated_at=datetime.utcnow())
            )
            result = await self.session.execute(stmt)
            await self.session.flush()
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

    @trace_repository_operation("update_payment_stripe_id")
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
            await self.session.flush()
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

    @trace_repository_operation("update_payment_client_secret")
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
            await self.session.flush()
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
    
    @trace_repository_operation("update_payment_checkout_url")
    async def update_payment_checkout_url(self, payment_id: UUID, checkout_url: str) -> Optional[PaymentDB]:
        try:
            self.logger.info(f"Updating payment checkout URL: {payment_id}")
            
            stmt = (
                update(PaymentDB)
                .where(PaymentDB.id == payment_id)
                .values(
                    checkout_url=checkout_url,
                    updated_at=datetime.utcnow()
                )
            )
            result = await self.session.execute(stmt)
            await self.session.flush()
            await self.session.commit()
            
            if result.rowcount > 0:
                self.logger.info(f"Payment checkout URL updated successfully: {payment_id}")
                return await self.get_payment_by_id(payment_id)
            else:
                self.logger.info(f"No payment found for checkout URL update: {payment_id}")
                return None
                
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating payment checkout URL {payment_id}: {e}")
            await self.session.rollback()
            raise

    @trace_repository_operation("list_payments_by_user")
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

    @trace_repository_operation("count_payments")
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

    @trace_repository_operation("get_payment_by_stripe_id")
    async def get_payment_by_stripe_id(self, stripe_id: str) -> Optional[PaymentDB]:
        """
        Find payment by Stripe ID (payment_intent_id or session_id).
        Searches in both stripe_payment_intent_id and stripe_session_id fields.
        """
        try:
            self.logger.info(f"Fetching payment by Stripe ID: {stripe_id}")
            
            # First try to find by stripe_payment_intent_id
            stmt = select(PaymentDB).where(PaymentDB.stripe_payment_intent_id == stripe_id)
            result = await self.session.execute(stmt)
            payment = result.scalar_one_or_none()
            
            # If not found, try to find by stripe_session_id
            if not payment:
                stmt = select(PaymentDB).where(PaymentDB.stripe_session_id == stripe_id)
                result = await self.session.execute(stmt)
                payment = result.scalar_one_or_none()
            
            if payment:
                self.logger.info(f"Payment found for Stripe ID: {stripe_id}")
            else:
                self.logger.info(f"No payment found for Stripe ID: {stripe_id}")
                
            return payment
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching payment for Stripe ID {stripe_id}: {e}")
            raise

    @trace_repository_operation("update_stripe_metadata")
    async def update_stripe_metadata(self, payment_id: UUID, metadata: dict) -> Optional[PaymentDB]:
        """
        Update Stripe-specific metadata for a payment.
        Merges new metadata with existing metadata if it exists.
        """
        try:
            self.logger.info(f"Updating Stripe metadata for payment: {payment_id}")
            
            # First get the current payment to check existing metadata
            payment = await self.get_payment_by_id(payment_id)
            if not payment:
                self.logger.warning(f"No payment found for metadata update: {payment_id}")
                return None
            
            # Prepare the updated metadata
            current_metadata = payment.metadata or {}
            updated_metadata = {**current_metadata, **metadata}
            
            # Update the payment with new metadata
            stmt = (
                update(PaymentDB)
                .where(PaymentDB.id == payment_id)
                .values(
                    metadata=updated_metadata,
                    updated_at=datetime.utcnow()
                )
            )
            result = await self.session.execute(stmt)
            await self.session.flush()
            await self.session.commit()
            
            if result.rowcount > 0:
                self.logger.info(f"Stripe metadata updated successfully for payment: {payment_id}")
                # Refresh and return the updated payment
                await self.session.refresh(payment)
                return payment
            else:
                self.logger.info(f"No payment updated for metadata: {payment_id}")
                return None
                
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating Stripe metadata for payment {payment_id}: {e}")
            await self.session.rollback()
            raise