import logging
import os
from fastapi import APIRouter, Request, Depends, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from services.order_services import OrderService
from database import pydantic_models
from decorators.order_routes_decorators import OrderErrorDecorators
from database.connection import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=['orders'])

DEFAULT_PAGE_SIZE = int(os.getenv('DEFAULT_PAGE_SIZE', '20'))
MAX_PAGE_SIZE = int(os.getenv('MAX_PAGE_SIZE', '100'))

def get_order_service(db_session: AsyncSession = Depends(get_db)) -> OrderService:
    return OrderService(logger=logger, db_session=db_session)

def get_user_id(authorization: str = Header(...)) -> str:
    if authorization.startswith("Bearer "):
        return "user_123"
    raise ValueError("Invalid authorization header")

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
    user_id: str = Depends(get_user_id),
    order_service: OrderService = Depends(get_order_service),
) -> pydantic_models.OrderResponse:
    return await order_service.create_order(request, order_data, user_id)

@router.get(
    '/',
    response_model=pydantic_models.OrderList,
    summary="List user's orders (paginated)"
)
@OrderErrorDecorators.handle_list_errors
async def list_orders(
    request: Request,
    user_id: str = Depends(get_user_id),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Page size"),
    order_service: OrderService = Depends(get_order_service),
) -> pydantic_models.OrderList:
    query_params = pydantic_models.OrderQueryParams(
        page=page,
        page_size=page_size
    )
    return await order_service.list_orders(request, user_id, query_params)

@router.get(
    '/{order_id}',
    response_model=pydantic_models.OrderResponse,
    summary="Get order details"
)
@OrderErrorDecorators.handle_get_errors
async def get_order(
    request: Request,
    order_id: str,
    user_id: str = Depends(get_user_id),
    order_service: OrderService = Depends(get_order_service),
) -> pydantic_models.OrderResponse:
    return await order_service.get_order(request, order_id, user_id)