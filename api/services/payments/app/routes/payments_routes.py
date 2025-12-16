import logging
import os
from fastapi import APIRouter, Request, Depends, Body, Header
from sqlalchemy.ext.asyncio import AsyncSession
from services.payments_service import PaymentService
from database import pydantic_models
from database.connection import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=['payments'])

def get_payment_service(db_session: AsyncSession = Depends(get_db)) -> PaymentService:
    return PaymentService(logger=logger, db_session=db_session)

@router.post(
    '/',
    response_model=pydantic_models.PaymentResponse,
    status_code=201,
    summary="Create payment for order"
)
async def create_payment(
    request: Request,
    payment_data: pydantic_models.PaymentCreate,
    payment_service: PaymentService = Depends(get_payment_service),
):
    return await payment_service.create_payment(request, payment_data)

@router.get(
    '/{payment_id}',
    response_model=pydantic_models.PaymentResponse,
    summary="Get payment details"
)
async def get_payment(
    request: Request,
    payment_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
):
    return await payment_service.get_payment(request, payment_id)

@router.post(
    '/webhooks/stripe',
    summary="Stripe webhook endpoint"
)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(..., alias="Stripe-Signature"),
    payment_service: PaymentService = Depends(get_payment_service),
):
    payload = await request.body()
    return await payment_service.process_webhook(request, payload, stripe_signature)

@router.post(
    '/{payment_id}/refund',
    summary="Refund payment"
)
async def refund_payment(
    request: Request,
    payment_id: str,
    refund_data: pydantic_models.RefundRequest,
    payment_service: PaymentService = Depends(get_payment_service),
):
    return await payment_service.create_refund(request, payment_id, refund_data)