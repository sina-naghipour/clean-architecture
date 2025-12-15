from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
import logging

from database.database_models import OrderDB, OrderStatus

class OrderRepository:
    def __init__(self, session: AsyncSession, logger: logging.Logger = None):
        self.session = session
        self.logger = logger or logging.getLogger(__name__).getChild("OrderRepository")

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

    async def update_order_status(self, order_id: UUID, new_status: OrderStatus) -> Optional[OrderDB]:
        try:
            self.logger.info(f"Updating order status: {order_id} -> {new_status}")
            
            stmt = update(OrderDB).where(OrderDB.id == order_id).values(status=new_status)
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            if result.rowcount > 0:
                self.logger.info(f"Order status updated successfully: {order_id}")
                return await self.get_order_by_id(order_id)
            else:
                self.logger.info(f"No order found for status update: {order_id}")
                return None
                
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating order status {order_id}: {e}")
            await self.session.rollback()
            raise

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