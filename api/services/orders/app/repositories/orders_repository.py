# app/repositories/orders_repository.py
from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
import logging

from database.database_models import OrderDB, OrderStatus
from optl.trace_decorator import trace_repository_operation
from decorators.order_repository_decorators import OrderRepositoryDecorators
from cache.cache_decorators import cache_order, cache_user_orders, invalidate_order_cache
from cache.cache_service import cache_service

class OrderRepository:
    def __init__(self, session: AsyncSession, logger: logging.Logger = None):
        self.session = session
        self.logger = logger or logging.getLogger(__name__)
    
    @trace_repository_operation("create_order")
    @OrderRepositoryDecorators.handle_repository_operation("create_order")
    async def create_order(self, order_data: OrderDB) -> OrderDB:
        self.session.add(order_data)
        await self.session.commit()
        await self.session.refresh(order_data)
        
        if cache_service.enabled:
            await cache_service.delete_user_orders(order_data.user_id)
        
        return order_data
    
    @cache_order
    @trace_repository_operation("get_order_by_id")
    @OrderRepositoryDecorators.handle_repository_operation("get_order_by_id")
    async def get_order_by_id(self, order_id: UUID) -> Optional[OrderDB]:
        stmt = select(OrderDB).where(OrderDB.id == order_id)
        result = await self.session.execute(stmt)
        order = result.scalar_one_or_none()
        
        if order:
            return order
        return None
    
    @trace_repository_operation("update_order_payment_id")
    @OrderRepositoryDecorators.handle_repository_operation("update_order_payment_id")
    async def update_order_payment_id(self, order_id: UUID, payment_id: str) -> Optional[OrderDB]:
        stmt = update(OrderDB).where(OrderDB.id == order_id).values(payment_id=payment_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        if result.rowcount == 0:
            return None
        
        if cache_service.enabled:
            await cache_service.delete_order(str(order_id))
        
        return await self.get_order_by_id(order_id)
    
    @invalidate_order_cache
    @trace_repository_operation("update_order_status")
    @OrderRepositoryDecorators.handle_repository_operation("update_order_status")
    async def update_order_status(self, order_id: UUID, new_status: OrderStatus) -> Optional[OrderDB]:
        stmt = update(OrderDB).where(OrderDB.id == order_id).values(status=new_status)
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        if result.rowcount == 0:
            return None
        
        return await self.get_order_by_id(order_id)
    
    @invalidate_order_cache
    @trace_repository_operation("update_order_receipt_url")
    @OrderRepositoryDecorators.handle_repository_operation("update_order_receipt_url")
    async def update_order_receipt_url(self, order_id: UUID, receipt_url: str) -> Optional[OrderDB]:
        stmt = update(OrderDB).where(OrderDB.id == order_id).values(receipt_url=receipt_url)
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        if result.rowcount == 0:
            return None
        
        return await self.get_order_by_id(order_id)
    
    @cache_user_orders
    @trace_repository_operation("list_orders")
    @OrderRepositoryDecorators.handle_repository_operation("list_orders")
    async def list_orders(self, user_id: str, skip: int = 0, limit: int = 20) -> List[Dict]:
        stmt = select(OrderDB).where(
            OrderDB.user_id == user_id
        ).order_by(
            OrderDB.created_at.desc()
        ).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        orders = result.scalars().all()
        
        return [order.to_dict() for order in orders]
    
    @trace_repository_operation("count_orders")
    @OrderRepositoryDecorators.handle_repository_operation("count_orders")
    async def count_orders(self, user_id: Optional[str] = None) -> int:
        stmt = select(func.count(OrderDB.id))
        
        if user_id:
            stmt = stmt.where(OrderDB.user_id == user_id)
        
        result = await self.session.execute(stmt)
        return result.scalar_one()