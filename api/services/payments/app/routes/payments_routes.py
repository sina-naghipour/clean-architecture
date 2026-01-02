import logging
import os
from fastapi import APIRouter, Request, Depends, Body, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from services.payments_service import PaymentService
from database import pydantic_models
from database.connection import get_db
from services.stripe_service import StripeService
from services.payments_service import PaymentService
from typing import Optional


logger = logging.getLogger(__name__)

router = APIRouter(tags=['payments'])

def get_payment_service(db_session: AsyncSession = Depends(get_db)) -> PaymentService:
    stripe_service = StripeService(logger)
    return PaymentService(logger=logger, db_session=db_session, stripe_service=stripe_service)

@router.get(
    '/checkout_success',
    summary="Handle successful Stripe Checkout redirect",
    # response_model=pydantic_models.PaymentResponse
)
async def checkout_success(
    request: Request,
    payment_service: PaymentService = Depends(get_payment_service)
):
    return await payment_service.handle_checkout_success(request)

@router.get(
    '/checkout_cancel',
    summary="Handle cancelled Stripe Checkout redirect",
    # response_model=pydantic_models.PaymentResponse
)
async def checkout_cancel(
    request: Request,
    payment_service: PaymentService = Depends(get_payment_service)
):
    return await payment_service.handle_checkout_cancel(request)

def get_payment_service(db_session: AsyncSession = Depends(get_db)) -> PaymentService:
    stripe_service = StripeService(logger)
    return PaymentService(logger=logger, db_session=db_session, stripe_service=stripe_service)
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


    