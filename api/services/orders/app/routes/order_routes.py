import logging
import os
from fastapi import APIRouter, Request, Depends, Query, Header, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from services.order_services import OrderService
from database import pydantic_models
from decorators.order_routes_decorators import OrderErrorDecorators
from database.connection import get_db
from dotenv import load_dotenv
from typing import Optional


load_dotenv()


logger = logging.getLogger(__name__)

router = APIRouter(tags=['orders'])

DEFAULT_PAGE_SIZE = int(os.getenv('DEFAULT_PAGE_SIZE', '20'))
MAX_PAGE_SIZE = int(os.getenv('MAX_PAGE_SIZE', '100'))

def get_order_service(db_session: AsyncSession = Depends(get_db)) -> OrderService:
    return OrderService(logger=logger, db_session=db_session)

@router.post(
    '/',
    response_model=pydantic_models.OrderResponse,
    status_code=201,
    summary="Create order (checkout current cart)"
)
@OrderErrorDecorators.handle_create_errors
async def create_order(
    request: Request,
    order_data: pydantic_models.OrderCreate,
    order_service: OrderService = Depends(get_order_service),
    x_referral_code: Optional[str] = Header(None, alias="X-Referral-Code")
) -> pydantic_models.OrderResponse:
    referral_code = x_referral_code
    if not referral_code and hasattr(request.state, 'user'):
        referral_code = request.state.user.get('referral_code') 
    return await order_service.create_order(request, order_data, request.state.user['id'], referral_code)

@router.get(
    '/',
    response_model=pydantic_models.OrderList,
    summary="List user's orders (paginated)"
)
@OrderErrorDecorators.handle_list_errors
async def list_orders(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Page size"),
    order_service: OrderService = Depends(get_order_service),
) -> pydantic_models.OrderList:
    query_params = pydantic_models.OrderQueryParams(
        page=page,
        page_size=page_size
    )
    return await order_service.list_orders(request, request.state.user['id'], query_params)

@router.get(
    '/{order_id}',
    response_model=pydantic_models.OrderResponse,
    summary="Get order details"
)
@OrderErrorDecorators.handle_get_errors
async def get_order(
    request: Request,
    order_id: str,
    order_service: OrderService = Depends(get_order_service),
) -> pydantic_models.OrderResponse:
    return await order_service.get_order(request, order_id, request.state.user['id'])

@OrderErrorDecorators.handle_payment_webhook_errors
@router.post('/webhooks/payment-updates')
async def payment_webhook(
    request: Request,
    payment_data: dict = Body(...),
    api_key: str = Header(None, alias="X-API-Key"),
    order_service: OrderService = Depends(get_order_service)
):
    internal_key = os.getenv("INTERNAL_API_KEY", "default_internal_key")
    
    if not api_key or api_key != internal_key:
        raise HTTPException(
            status_code=403, 
            detail="Forbidden: Invalid or missing API key"
        )
    logger.info("Received payment webhook: %s", payment_data)
    return await order_service.handle_payment_webhook(request, payment_data)