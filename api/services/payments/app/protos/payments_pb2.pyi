from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class CreatePaymentRequest(_message.Message):
    __slots__ = ("order_id", "user_id", "amount", "currency", "payment_method_token", "metadata", "success_url", "cancel_url", "checkout_mode")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_FIELD_NUMBER: _ClassVar[int]
    PAYMENT_METHOD_TOKEN_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_URL_FIELD_NUMBER: _ClassVar[int]
    CANCEL_URL_FIELD_NUMBER: _ClassVar[int]
    CHECKOUT_MODE_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    user_id: str
    amount: float
    currency: str
    payment_method_token: str
    metadata: _containers.ScalarMap[str, str]
    success_url: str
    cancel_url: str
    checkout_mode: bool
    def __init__(self, order_id: _Optional[str] = ..., user_id: _Optional[str] = ..., amount: _Optional[float] = ..., currency: _Optional[str] = ..., payment_method_token: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., success_url: _Optional[str] = ..., cancel_url: _Optional[str] = ..., checkout_mode: bool = ...) -> None: ...

class GetPaymentRequest(_message.Message):
    __slots__ = ("payment_id",)
    PAYMENT_ID_FIELD_NUMBER: _ClassVar[int]
    payment_id: str
    def __init__(self, payment_id: _Optional[str] = ...) -> None: ...

class RefundRequest(_message.Message):
    __slots__ = ("payment_id", "amount", "reason")
    PAYMENT_ID_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    payment_id: str
    amount: float
    reason: str
    def __init__(self, payment_id: _Optional[str] = ..., amount: _Optional[float] = ..., reason: _Optional[str] = ...) -> None: ...

class PaymentResponse(_message.Message):
    __slots__ = ("payment_id", "order_id", "user_id", "amount", "status", "stripe_payment_intent_id", "payment_method_token", "currency", "client_secret", "checkout_url")
    PAYMENT_ID_FIELD_NUMBER: _ClassVar[int]
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    STRIPE_PAYMENT_INTENT_ID_FIELD_NUMBER: _ClassVar[int]
    PAYMENT_METHOD_TOKEN_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_FIELD_NUMBER: _ClassVar[int]
    CLIENT_SECRET_FIELD_NUMBER: _ClassVar[int]
    CHECKOUT_URL_FIELD_NUMBER: _ClassVar[int]
    payment_id: str
    order_id: str
    user_id: str
    amount: float
    status: str
    stripe_payment_intent_id: str
    payment_method_token: str
    currency: str
    client_secret: str
    checkout_url: str
    def __init__(self, payment_id: _Optional[str] = ..., order_id: _Optional[str] = ..., user_id: _Optional[str] = ..., amount: _Optional[float] = ..., status: _Optional[str] = ..., stripe_payment_intent_id: _Optional[str] = ..., payment_method_token: _Optional[str] = ..., currency: _Optional[str] = ..., client_secret: _Optional[str] = ..., checkout_url: _Optional[str] = ...) -> None: ...

class RefundResponse(_message.Message):
    __slots__ = ("refund_id", "status", "amount", "currency", "reason")
    REFUND_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    refund_id: str
    status: str
    amount: float
    currency: str
    reason: str
    def __init__(self, refund_id: _Optional[str] = ..., status: _Optional[str] = ..., amount: _Optional[float] = ..., currency: _Optional[str] = ..., reason: _Optional[str] = ...) -> None: ...
