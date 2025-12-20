from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
import logging

from database.database_models import OrderDB, OrderStatus
from optl.trace_decorator import trace_repository_operation

class OrderRepository:
    def __init__(self, session: AsyncSession, logger: logging.Logger = None):
        self.session = session
        self.logger = logger or logging.getLogger(__name__).getChild("OrderRepository")

    @trace_repository_operation("create_order")
    async def create_order(self, order_data: OrderDB) -> Optional[OrderDB]:
        try:
            self.logger.info(f"Creating order with ID: {order_data.id}")
            
            self.session.add(order_data)
            await self.session.commit()
            await self.session.refresh(order_data)
            
            self.logger.info(f"Order created successfully: {order_data.id}")
            return order_data
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error creating order: {e}")
            await self.session.rollback()
            raise

    @trace_repository_operation("get_order_by_id")
    async def get_order_by_id(self, order_id: UUID) -> Optional[OrderDB]:
        try:
            self.logger.info(f"Fetching order by ID: {order_id}")
            
            stmt = select(OrderDB).where(OrderDB.id == order_id)
            result = await self.session.execute(stmt)
            order = result.scalar_one_or_none()
            
            if order:
                self.logger.info(f"Order found: {order_id}")
            else:
                self.logger.info(f"Order not found: {order_id}")
                
            return order
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching order {order_id}: {e}")
            raise

    @trace_repository_operation("update_order_payment_id")
    async def update_order_payment_id(self, order_id: UUID, payment_id: str) -> Optional[OrderDB]:
        try:
            self.logger.info(f"Updating order payment ID: {order_id} -> {payment_id}")
            
            stmt = update(OrderDB).where(OrderDB.id == order_id).values(payment_id=payment_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            if result.rowcount > 0:
                self.logger.info(f"Order payment ID updated successfully: {order_id}")
                return await self.get_order_by_id(order_id)
            else:
                self.logger.info(f"No order found for payment ID update: {order_id}")
                return None
                
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating order payment ID {order_id}: {e}")
            await self.session.rollback()
            raise

    @trace_repository_operation("update_order_status")
    async def update_order_status(self, order_id: UUID, new_status: OrderStatus) -> Optional[OrderDB]:
        self.logger.info('calleddddddddddddddddddd')
        try:            
            stmt = update(OrderDB).where(OrderDB.id == order_id).values(status=new_status)
            
            result = await self.session.execute(stmt)
            
            await self.session.commit()
            
            if result.rowcount > 0:
                self.logger.info(f"Order status updated successfully: {order_id}")
                updated_order = await self.get_order_by_id(order_id)
                self.logger.info(f"Fetched updated order, status: {updated_order.status if updated_order else 'None'}")
                return updated_order
            else:
                self.logger.info(f"No order found for status update: {order_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error updating order status {order_id}: {e}", exc_info=True)
            await self.session.rollback()
            raise

    @trace_repository_operation("update_order_receipt_url")
    async def update_order_receipt_url(self, order_id: UUID, receipt_url: str) -> Optional[OrderDB]:
        try:            
            stmt = update(OrderDB).where(OrderDB.id == order_id).values(receipt_url=receipt_url)
            
            result = await self.session.execute(stmt)
            
            await self.session.commit()
            
            if result.rowcount > 0:
                self.logger.info(f"Order status updated successfully: {order_id}")
                updated_order = await self.get_order_by_id(order_id)
                self.logger.info(f"Fetched updated order, status: {updated_order.status if updated_order else 'None'}")
                return updated_order
            else:
                self.logger.info(f"No order found for status update: {order_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error updating order status {order_id}: {e}", exc_info=True)
            await self.session.rollback()
            raise

    @trace_repository_operation("list_orders")
    async def list_orders(self, skip: int = 0, limit: int = 20) -> List[OrderDB]:
        try:
            self.logger.info(f"Listing orders - skip: {skip}, limit: {limit}")
            
            stmt = select(OrderDB).order_by(OrderDB.created_at.desc()).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            orders = result.scalars().all()
            
            self.logger.info(f"Found {len(orders)} orders")
            return list(orders)
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error listing orders: {e}")
            raise

    @trace_repository_operation("count_orders")
    async def count_orders(self) -> int:
        try:
            self.logger.debug("Counting total orders")
            
            stmt = select(OrderDB)
            result = await self.session.execute(stmt)
            count = len(result.scalars().all())
            
            self.logger.debug(f"Total orders: {count}")
            return count
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error counting orders: {e}")
            raise