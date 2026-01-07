import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4
from fastapi import Request
from datetime import datetime
from services.order_services import OrderService
from database import pydantic_models
from database.database_models import OrderDB, OrderStatus
import json

class TestOrderService:
    @pytest_asyncio.fixture
    async def mock_logger(self):
        return Mock()

    @pytest_asyncio.fixture
    async def mock_db_session(self):
        return AsyncMock()

    @pytest_asyncio.fixture
    async def order_service(self, mock_logger, mock_db_session):
        with patch('services.order_services.OrderRepository') as mock_repo_class:
            mock_repo_instance = AsyncMock()
            mock_repo_class.return_value = mock_repo_instance
            
            with patch('services.order_services.PaymentGRPCClient') as mock_payment_class:
                mock_payment_instance = AsyncMock()
                
                mock_payment_response = MagicMock()
                mock_payment_response.payment_id = "payment_123"
                mock_payment_response.client_secret = "pi_secret_123"
                mock_payment_response.checkout_url = "https://checkout.stripe.com/pay/test"
                mock_payment_instance.create_payment = AsyncMock(return_value=mock_payment_response)
                mock_payment_instance.get_payment = AsyncMock()
                mock_payment_instance.initialize = AsyncMock()
                mock_payment_instance.close = AsyncMock()
                mock_payment_class.return_value = mock_payment_instance
                
                with patch('cache.cache_service.cache_service'):
                    service = OrderService(logger=mock_logger, db_session=mock_db_session)
                    service.order_repo = mock_repo_instance
                    service.payment_client = mock_payment_instance
                    service._payment_failure_count = 0
                    service._circuit_open = False
                    service._processed_keys = set()
                    yield service

    @pytest_asyncio.fixture
    async def mock_request(self):
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/orders"
        request.method = "POST"
        request.state = Mock()
        request.state.user = {"id": "test_user_1", "referrer_id": None}
        return request

    @pytest_asyncio.fixture
    def sample_order_db(self):
        order = OrderDB(
            id=uuid4(),
            status=OrderStatus.CREATED,
            total=1059.97,
            billing_address_id="addr_1",
            shipping_address_id="addr_1",
            payment_method_token="pm_tok_abc",
            payment_id="pay_123",
            items=[
                {
                    "product_id": "prod_1",
                    "name": "Laptop",
                    "quantity": 1,
                    "unit_price": 999.99
                },
                {
                    "product_id": "prod_2",
                    "name": "Mouse",
                    "quantity": 2,
                    "unit_price": 29.99
                }
            ],
            user_id="test_user_1",
            created_at=datetime.utcnow(),
            receipt_url=None,
            checkout_url="https://checkout.stripe.com/pay/test"
        )
        return order

    @pytest.mark.asyncio
    async def test_create_order_success(self, order_service, mock_request, sample_order_db):
        order_data = pydantic_models.OrderCreate(
            items=[
                pydantic_models.OrderItemCreate(
                    product_id="prod_1",
                    name="Laptop",
                    quantity=1,
                    unit_price=999.99
                ),
                pydantic_models.OrderItemCreate(
                    product_id="prod_2",
                    name="Mouse",
                    quantity=2,
                    unit_price=29.99
                )
            ],
            billing_address_id="addr_1",
            shipping_address_id="addr_1",
            payment_method_token="pm_tok_abc"
        )
        
        order_service.order_repo.create_order.return_value = sample_order_db
        order_service.order_repo.update_order_payment_id = AsyncMock()
        order_service.order_repo.update_order_status = AsyncMock()
        order_service.order_repo.update_order_checkout_url = AsyncMock()
        
        result = await order_service.create_order(mock_request, order_data, "test_user_1")

        assert isinstance(result, pydantic_models.OrderResponse)
        assert result.id == str(sample_order_db.id)
        assert result.status == OrderStatus.PENDING
        assert result.payment_id == "payment_123"
        assert result.client_secret == "pi_secret_123"
        assert result.checkout_url == "https://checkout.stripe.com/pay/test"
        
        order_service.order_repo.create_order.assert_called_once()
        order_service.payment_client.create_payment.assert_called_once()
        order_service.order_repo.update_order_payment_id.assert_called_once_with(sample_order_db.id, "payment_123")
        order_service.order_repo.update_order_status.assert_called_once_with(sample_order_db.id, OrderStatus.PENDING)

    @pytest.mark.asyncio
    async def test_create_order_payment_failure(self, order_service, mock_request, sample_order_db):
        order_data = pydantic_models.OrderCreate(
            items=[
                pydantic_models.OrderItemCreate(
                    product_id="prod_1",
                    name="Laptop",
                    quantity=1,
                    unit_price=999.99
                )
            ],
            billing_address_id="addr_1",
            shipping_address_id="addr_1",
            payment_method_token="pm_tok_abc"
        )
        
        order_service.order_repo.create_order.return_value = sample_order_db
        order_service.order_repo.update_order_status = AsyncMock()
        
        with patch.object(order_service, '_create_payment', side_effect=Exception("Payment processing error")):
            from fastapi.responses import JSONResponse
            result = await order_service.create_order(mock_request, order_data, "test_user_1")

            assert isinstance(result, JSONResponse)
            content = json.loads(result.body)
            assert content["status"] == 503
            assert "Payment processing error" in content["detail"]
            
            order_service.order_repo.create_order.assert_called_once()
            order_service.order_repo.update_order_status.assert_called_once_with(sample_order_db.id, OrderStatus.FAILED)

    @pytest.mark.asyncio
    async def test_create_order_empty_items(self, order_service, mock_request):
        order_data = pydantic_models.OrderCreate(
            items=[],
            billing_address_id="addr_1",
            shipping_address_id="addr_1",
            payment_method_token="pm_tok_abc"
        )
        
        from fastapi.responses import JSONResponse
        result = await order_service.create_order(mock_request, order_data, "test_user_1")

        assert isinstance(result, JSONResponse)
        content = json.loads(result.body)
        assert content["status"] == 400
        assert "empty items" in content["detail"].lower()
        order_service.order_repo.create_order.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_order_success(self, order_service, mock_request, sample_order_db):
        order_id = str(sample_order_db.id)
        
        order_service.order_repo.get_order_by_id.return_value = sample_order_db

        result = await order_service.get_order(mock_request, order_id, "test_user_1")

        assert isinstance(result, pydantic_models.OrderResponse)
        assert result.id == order_id
        assert result.status == OrderStatus.CREATED
        assert result.payment_id == "pay_123"
        order_service.order_repo.get_order_by_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_order_not_found(self, order_service, mock_request):
        order_id = str(uuid4())
        
        order_service.order_repo.get_order_by_id.return_value = None

        from fastapi.responses import JSONResponse
        result = await order_service.get_order(mock_request, order_id, "test_user_1")

        assert isinstance(result, JSONResponse)
        content = json.loads(result.body)
        assert content["status"] == 404
        assert "not found" in content["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_order_wrong_user(self, order_service, mock_request, sample_order_db):
        order_id = str(sample_order_db.id)
        
        order_service.order_repo.get_order_by_id.return_value = sample_order_db

        from fastapi.responses import JSONResponse
        result = await order_service.get_order(mock_request, order_id, "different_user")

        assert isinstance(result, JSONResponse)
        content = json.loads(result.body)
        assert content["status"] == 404
        assert "not found" in content["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_order_invalid_uuid(self, order_service, mock_request):
        invalid_order_id = "not-a-uuid"

        from fastapi.responses import JSONResponse
        result = await order_service.get_order(mock_request, invalid_order_id, "test_user_1")

        assert isinstance(result, JSONResponse)
        content = json.loads(result.body)
        assert content["status"] == 400
        assert "invalid order id" in content["detail"].lower()

    @pytest.mark.asyncio
    async def test_list_orders_success(self, order_service, mock_request, sample_order_db):
        orders_db = [sample_order_db]
        
        order_service.order_repo.list_orders.return_value = [order.to_dict() for order in orders_db]
        order_service.order_repo.count_orders.return_value = 1

        query_params = pydantic_models.OrderQueryParams(
            page=1,
            page_size=20
        )

        result = await order_service.list_orders(mock_request, "test_user_1", query_params)

        assert isinstance(result, pydantic_models.OrderList)
        assert len(result.items) == 1
        assert result.items[0].id == str(sample_order_db.id)
        assert result.total == 1
        assert result.page == 1
        assert result.page_size == 20

    @pytest.mark.asyncio
    async def test_list_orders_empty(self, order_service, mock_request):
        order_service.order_repo.list_orders.return_value = []
        order_service.order_repo.count_orders.return_value = 0

        query_params = pydantic_models.OrderQueryParams(
            page=1,
            page_size=20
        )

        result = await order_service.list_orders(mock_request, "user_with_no_orders", query_params)

        assert isinstance(result, pydantic_models.OrderList)
        assert len(result.items) == 0
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_handle_payment_webhook_success(self, order_service, mock_request, sample_order_db):
        order_id = str(sample_order_db.id)
        payment_data = {
            "order_id": order_id,
            "status": "succeeded",
            "receipt_url": "https://receipt.example.com/123",
            "checkout_url": "https://checkout.stripe.com/pay/updated"
        }
        
        order_service.order_repo.get_order_by_id.return_value = sample_order_db
        order_service.order_repo.update_order_status = AsyncMock()
        order_service.order_repo.update_order_receipt_url = AsyncMock()
        order_service.order_repo.update_order_checkout_url = AsyncMock()
        
        result = await order_service.handle_payment_webhook(mock_request, payment_data)
        
        assert isinstance(result, dict)
        assert result["status"] == "success"
        assert result["order_id"] == order_id
        assert result["updated_status"] == "paid"
        
        order_service.order_repo.get_order_by_id.assert_called_once()
        order_service.order_repo.update_order_status.assert_called_once_with(sample_order_db.id, OrderStatus.PAID)
        order_service.order_repo.update_order_receipt_url.assert_called_once_with(sample_order_db.id, "https://receipt.example.com/123")
        order_service.order_repo.update_order_checkout_url.assert_called_once_with(sample_order_db.id, "https://checkout.stripe.com/pay/updated")

    @pytest.mark.asyncio
    async def test_handle_payment_webhook_missing_fields(self, order_service, mock_request):
        payment_data = {"status": "succeeded"}
        
        from fastapi.responses import JSONResponse
        result = await order_service.handle_payment_webhook(mock_request, payment_data)
        
        assert isinstance(result, JSONResponse)
        content = json.loads(result.body)
        assert content["status"] == 400
        assert "missing order_id" in content["detail"].lower()

    @pytest.mark.asyncio
    async def test_handle_payment_webhook_order_not_found(self, order_service, mock_request):
        order_id = str(uuid4())
        payment_data = {
            "order_id": order_id,
            "status": "succeeded"
        }
        
        order_service.order_repo.get_order_by_id.return_value = None
        
        from fastapi.responses import JSONResponse
        result = await order_service.handle_payment_webhook(mock_request, payment_data)
        
        assert isinstance(result, JSONResponse)
        content = json.loads(result.body)
        assert content["status"] == 404
        assert "order not found" in content["detail"].lower()

    @pytest.mark.asyncio
    async def test_handle_payment_webhook_unknown_status(self, order_service, mock_request, sample_order_db):
        order_id = str(sample_order_db.id)
        payment_data = {
            "order_id": order_id,
            "status": "unknown_status"
        }
        
        order_service.order_repo.get_order_by_id.return_value = sample_order_db
        
        from fastapi.responses import JSONResponse
        result = await order_service.handle_payment_webhook(mock_request, payment_data)
        
        assert isinstance(result, JSONResponse)
        content = json.loads(result.body)
        assert content["status"] == 400
        assert "unknown status" in content["detail"].lower()

    @pytest.mark.asyncio
    async def test_handle_payment_webhook_duplicate_request(self, order_service, mock_request, sample_order_db):
        order_id = str(sample_order_db.id)
        payment_data = {
            "order_id": order_id,
            "status": "succeeded"
        }
        
        idempotency_key = "test_key"
        mock_request.headers = {"X-Idempotency-Key": idempotency_key}
        
        order_service._processed_keys = {idempotency_key}
        order_service.order_repo.get_order_by_id.return_value = sample_order_db
        
        result = await order_service.handle_payment_webhook(mock_request, payment_data)
        
        assert isinstance(result, dict)
        assert result["status"] == "ignored"
        assert result["reason"] == "duplicate"
        order_service.order_repo.get_order_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_payment_webhook_already_in_state(self, order_service, mock_request, sample_order_db):
        order_id = str(sample_order_db.id)
        sample_order_db.status = OrderStatus.PAID
        payment_data = {
            "order_id": order_id,
            "status": "succeeded"
        }
        
        order_service.order_repo.get_order_by_id.return_value = sample_order_db
        
        result = await order_service.handle_payment_webhook(mock_request, payment_data)
        
        assert isinstance(result, dict)
        assert result["status"] == "ignored"
        assert result["reason"] == "already_in_state"
        order_service.order_repo.update_order_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_build_order_response(self, order_service, sample_order_db):
        order_dict = sample_order_db.to_dict()
        
        result = order_service._build_order_response(order_dict)
        
        assert isinstance(result, pydantic_models.OrderResponse)
        assert result.id == str(sample_order_db.id)
        assert result.status == OrderStatus.CREATED
        assert result.total == 1059.97
        assert len(result.items) == 2
        assert result.items[0].product_id == "prod_1"
        assert result.items[1].product_id == "prod_2"
        assert result.checkout_url == "https://checkout.stripe.com/pay/test"

    @pytest.mark.asyncio
    async def test_create_payment_success(self, order_service, sample_order_db):
        order_service.payment_client.create_payment.return_value = MagicMock(
            payment_id="payment_123",
            client_secret="pi_secret_123",
            checkout_url="https://checkout.stripe.com/pay/test"
        )
        
        result = await order_service._create_payment(
            order_id=str(sample_order_db.id),
            amount=sample_order_db.total,
            user_id="test_user_1",
            payment_method_token="pm_tok_abc"
        )
        
        assert result.payment_id == "payment_123"
        assert result.client_secret == "pi_secret_123"
        order_service.payment_client.create_payment.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_payment_with_referrer(self, order_service, sample_order_db):
        order_service.payment_client.create_payment.return_value = MagicMock(
            payment_id="payment_123",
            client_secret="pi_secret_123",
            checkout_url="https://checkout.stripe.com/pay/test"
        )
        
        result = await order_service._create_payment(
            order_id=str(sample_order_db.id),
            amount=sample_order_db.total,
            user_id="test_user_1",
            payment_method_token="pm_tok_abc",
            referrer_id="ref_123"
        )
        
        order_service.payment_client.create_payment.assert_called_once()
        call_kwargs = order_service.payment_client.create_payment.call_args.kwargs
        assert call_kwargs.get('referrer_id') == "ref_123"

    @pytest.mark.asyncio
    async def test_idempotency_handler_methods(self, order_service):
        key = "test_key_123"
        
        is_duplicate = await order_service._is_duplicate_request(key)
        assert is_duplicate == False
        
        await order_service._store_idempotency_key(key)
        
        is_duplicate = await order_service._is_duplicate_request(key)
        assert is_duplicate == True

    @pytest.mark.asyncio
    async def test_handle_payment_webhook_invalid_transition(self, order_service, mock_request, sample_order_db):
        order_id = str(sample_order_db.id)
        sample_order_db.status = OrderStatus.PAID
        payment_data = {
            "order_id": order_id,
            "status": "pending"
        }
        
        order_service.order_repo.get_order_by_id.return_value = sample_order_db
        
        result = await order_service.handle_payment_webhook(mock_request, payment_data)
        
        assert isinstance(result, dict)
        assert result["status"] == "ignored"
        assert result["reason"] == "invalid_transition"
        order_service.order_repo.update_order_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_orders_with_pagination(self, order_service, mock_request, sample_order_db):
        orders_db = [sample_order_db]
        
        order_service.order_repo.list_orders.return_value = [order.to_dict() for order in orders_db]
        order_service.order_repo.count_orders.return_value = 10

        query_params = pydantic_models.OrderQueryParams(
            page=2,
            page_size=5
        )

        result = await order_service.list_orders(mock_request, "test_user_1", query_params)

        assert isinstance(result, pydantic_models.OrderList)
        assert result.total == 10
        assert result.page == 2
        assert result.page_size == 5
        assert len(result.items) == 1