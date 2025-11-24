import logging
import os
from fastapi import APIRouter, Request, Depends, Header
from services.profile_services import ProfileService
from database import models
from decorators.profile_routes_decorators import ProfileErrorDecorators

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/profile', tags=['profile'])

def get_profile_service() -> ProfileService:
    return ProfileService(logger=logger)

def get_user_id(authorization: str = Header(...)) -> str:
    if authorization.startswith("Bearer "):
        return "user_123"
    raise ValueError("Invalid authorization header")

@router.get(
    '',
    response_model=models.UserResponse,
    summary="Get user profile"
)
@ProfileErrorDecorators.handle_get_errors
async def get_profile(
    request: Request,
    user_id: str = Depends(get_user_id),
    profile_service: ProfileService = Depends(get_profile_service),
) -> models.UserResponse:
    return await profile_service.get_profile(request, user_id)

@router.patch(
    '',
    response_model=models.UserResponse,
    summary="Partially update profile"
)
@ProfileErrorDecorators.handle_update_errors
async def update_profile(
    request: Request,
    profile_data: models.ProfileUpdate,
    user_id: str = Depends(get_user_id),
    profile_service: ProfileService = Depends(get_profile_service),
) -> models.UserResponse:
    return await profile_service.update_profile(request, profile_data, user_id)

@router.patch(
    '/password',
    summary="Change password"
)
@ProfileErrorDecorators.handle_password_errors
async def change_password(
    request: Request,
    password_data: models.PasswordChange,
    user_id: str = Depends(get_user_id),
    profile_service: ProfileService = Depends(get_profile_service),
):
    return await profile_service.change_password(request, password_data, user_id)

@router.get(
    '/addresses',
    response_model=list[models.AddressResponse],
    summary="List user addresses"
)
@ProfileErrorDecorators.handle_get_errors
async def list_addresses(
    request: Request,
    user_id: str = Depends(get_user_id),
    profile_service: ProfileService = Depends(get_profile_service),
) -> list[models.AddressResponse]:
    return await profile_service.list_addresses(request, user_id)

@router.post(
    '/addresses',
    response_model=models.AddressResponse,
    status_code=201,
    summary="Create new address"
)
@ProfileErrorDecorators.handle_address_errors
async def create_address(
    request: Request,
    address_data: models.AddressRequest,
    user_id: str = Depends(get_user_id),
    profile_service: ProfileService = Depends(get_profile_service),
) -> models.AddressResponse:
    return await profile_service.create_address(request, address_data, user_id)

@router.patch(
    '/addresses/{address_id}',
    response_model=models.AddressResponse,
    summary="Update address"
)
@ProfileErrorDecorators.handle_address_update_errors
async def update_address(
    request: Request,
    address_id: str,
    address_data: models.AddressRequest,
    user_id: str = Depends(get_user_id),
    profile_service: ProfileService = Depends(get_profile_service),
) -> models.AddressResponse:
    return await profile_service.update_address(request, address_id, address_data, user_id)

@router.delete(
    '/addresses/{address_id}',
    status_code=204,
    summary="Delete address"
)
@ProfileErrorDecorators.handle_address_delete_errors
async def delete_address(
    request: Request,
    address_id: str,
    user_id: str = Depends(get_user_id),
    profile_service: ProfileService = Depends(get_profile_service),
):
    return await profile_service.delete_address(request, address_id, user_id)
