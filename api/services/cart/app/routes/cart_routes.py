import logging
import os
from fastapi import APIRouter, Request, Depends, Query, Header
from services.cart_services import CartService
from database import models
from decorators.cart_routes_decorators import CartErrorDecorators

logger = logging.getLogger(__name__)

router = APIRouter(tags=['cart'])

DEFAULT_PAGE_SIZE = int(os.getenv('DEFAULT_PAGE_SIZE', '20'))
MAX_PAGE_SIZE = int(os.getenv('MAX_PAGE_SIZE', '100'))

# Dependency injection functions
def get_cart_service() -> CartService:
    return CartService(logger=logger)

def get_user_id(authorization: str = Header(...)) -> str:
    # For now, extract user ID from header
    # this would validate JWT token
    if authorization.startswith("Bearer "):
        return "user_123"  # Default user for testing
    raise ValueError("Invalid authorization header")

@router.get(
    '/',
    response_model=models.CartResponse,
    summary="Get current user's cart"
)
@CartErrorDecorators.handle_get_cart_errors
async def get_cart(
    request: Request,
    user_id: str = Depends(get_user_id),
    cart_service: CartService = Depends(get_cart_service),
) -> models.CartResponse:
    print(f'here user_id : {user_id}')
    return await cart_service.get_cart(request, user_id)

@router.delete(
    '/',
    status_code=204,
    summary="Clear cart"
)
@CartErrorDecorators.handle_clear_cart_errors
async def clear_cart(
    request: Request,
    user_id: str = Depends(get_user_id),
    cart_service: CartService = Depends(get_cart_service),
) -> None:
    return await cart_service.clear_cart(request, user_id)

@router.post(
    '/items',
    response_model=models.CartItemResponse,
    status_code=201,
    summary="Add item to cart"
)
@CartErrorDecorators.handle_add_item_errors
async def add_cart_item(
    request: Request,
    item_data: models.CartItemRequest,
    user_id: str = Depends(get_user_id),
    cart_service: CartService = Depends(get_cart_service),
) -> models.CartItemResponse:
    return await cart_service.add_cart_item(request, user_id, item_data)

@router.patch(
    '/items/{item_id}',
    response_model=models.CartItemResponse,
    summary="Update cart item quantity"
)
@CartErrorDecorators.handle_update_item_errors
async def update_cart_item(
    request: Request,
    item_id: str,
    update_data: models.CartItemUpdate,
    user_id: str = Depends(get_user_id),
    cart_service: CartService = Depends(get_cart_service),
) -> models.CartItemResponse:
    return await cart_service.update_cart_item(request, user_id, item_id, update_data)

@router.delete(
    '/items/{item_id}',
    status_code=204,
    summary="Remove cart item"
)
@CartErrorDecorators.handle_remove_item_errors
async def remove_cart_item(
    request: Request,
    item_id: str,
    user_id: str = Depends(get_user_id),
    cart_service: CartService = Depends(get_cart_service),
) -> None:
    return await cart_service.remove_cart_item(request, user_id, item_id)

