import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4
from fastapi import Request
from datetime import datetime
from services.order_services import OrderService
from database import pydantic_models
from database.database_models import OrderDB, OrderStatus

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
                mock_payment_instance.create_payment = AsyncMock(return_value=mock_payment_response)
                mock_payment_instance.get_payment = AsyncMock(return_value={
                    "id": "payment_123",
                    "status": "succeeded",
                    "client_secret": "pi_secret_123"
                })
                mock_payment_class.return_value = mock_payment_instance
                
                service = OrderService(logger=mock_logger, db_session=mock_db_session)
                service.order_repo = mock_repo_instance
                service.payment_client = mock_payment_instance
                yield service

    @pytest_asyncio.fixture
    async def mock_request(self):
        request = Mock(spec=Request)
        request.url = "http://testserver/api/orders"
        request.method = "POST"
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
            ]
        )
        order.user_id = "test_user_1"
        order.created_at = datetime.utcnow()
        return order

    @pytest.mark.asyncio
    async def test_create_order_success(self, order_service, mock_request, sample_order_db):
        user_id = "test_user_1"
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
        
        result = await order_service.create_order(mock_request, order_data, user_id)

        assert isinstance(result, pydantic_models.OrderResponse)
        assert result.id == str(sample_order_db.id)
        assert result.status == OrderStatus.PENDING
        assert result.payment_id == "payment_123"
        assert result.client_secret == "pi_secret_123"
        
        order_service.order_repo.create_order.assert_called_once()
        order_service.payment_client.create_payment.assert_called_once_with(
            order_id=str(sample_order_db.id),
            amount=sample_order_db.total,
            user_id=user_id,
            payment_method_token=order_data.payment_method_token
        )
        order_service.order_repo.update_order_payment_id.assert_called_once_with(sample_order_db.id, "payment_123")
        order_service.order_repo.update_order_status.assert_called_once_with(sample_order_db.id, OrderStatus.PENDING)

    @pytest.mark.asyncio
    async def test_create_order_payment_failure(self, order_service, mock_request, sample_order_db):
        user_id = "test_user_1"
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
        
        order_service._create_payment = AsyncMock(side_effect=Exception("Payment failed"))
        
        from fastapi.responses import JSONResponse
        result = await order_service.create_order(mock_request, order_data, user_id)

        assert isinstance(result, JSONResponse)
        assert result.status_code == 503
        
        order_service.order_repo.create_order.assert_called_once()
        order_service.order_repo.update_order_status.assert_called_once_with(sample_order_db.id, OrderStatus.FAILED)

    @pytest.mark.asyncio
    async def test_create_order_empty_items(self, order_service, mock_request):
        user_id = "test_user_1"
        order_data = pydantic_models.OrderCreate(
            items=[],
            billing_address_id="addr_1",
            shipping_address_id="addr_1",
            payment_method_token="pm_tok_abc"
        )
        
        result = await order_service.create_order(mock_request, order_data, user_id)

        from fastapi.responses import JSONResponse
        assert isinstance(result, JSONResponse)
        assert result.status_code == 400
        order_service.order_repo.create_order.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_order_success(self, order_service, mock_request, sample_order_db):
        user_id = "test_user_1"
        order_id = str(sample_order_db.id)
        
        order_service.order_repo.get_order_by_id.return_value = sample_order_db

        result = await order_service.get_order(mock_request, order_id, user_id)

        assert isinstance(result, pydantic_models.OrderResponse)
        assert result.id == order_id
        assert result.payment_id == "pay_123"
        order_service.order_repo.get_order_by_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_order_not_found(self, order_service, mock_request):
        user_id = "test_user_1"
        order_id = str(uuid4())
        
        order_service.order_repo.get_order_by_id.return_value = None

        from fastapi.responses import JSONResponse
        result = await order_service.get_order(mock_request, order_id, user_id)

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_get_order_wrong_user(self, order_service, mock_request, sample_order_db):
        wrong_user_id = "different_user"
        order_id = str(sample_order_db.id)
        
        order_service.order_repo.get_order_by_id.return_value = sample_order_db

        from fastapi.responses import JSONResponse
        result = await order_service.get_order(mock_request, order_id, wrong_user_id)

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_get_order_invalid_uuid(self, order_service, mock_request):
        user_id = "test_user_1"
        invalid_order_id = "not-a-uuid"

        from fastapi.responses import JSONResponse
        result = await order_service.get_order(mock_request, invalid_order_id, user_id)

        assert isinstance(result, JSONResponse)
        assert result.status_code == 400

    @pytest.mark.asyncio
    async def test_list_orders_success(self, order_service, mock_request, sample_order_db):
        user_id = "test_user_1"
        
        orders_db = [
            sample_order_db,
            OrderDB(
                id=uuid4(),
                status=OrderStatus.PAID,
                total=50.00,
                billing_address_id="addr_2",
                shipping_address_id="addr_2",
                payment_method_token="pm_tok_xyz",
                payment_id="pay_456",
                items=[{"product_id": "prod_3", "name": "Keyboard", "quantity": 1, "unit_price": 50.00}]
            )
        ]
        orders_db[1].user_id = "test_user_1"
        orders_db[1].created_at = datetime.utcnow()
        
        order_service.order_repo.list_orders.return_value = orders_db

        query_params = pydantic_models.OrderQueryParams(
            page=1,
            page_size=20
        )

        result = await order_service.list_orders(mock_request, user_id, query_params)

        assert isinstance(result, pydantic_models.OrderList)
        assert len(result.items) == 2
        assert result.items[0].payment_id == "pay_123"
        assert result.items[1].payment_id == "pay_456"

    @pytest.mark.asyncio
    async def test_list_orders_empty(self, order_service, mock_request):
        user_id = "user_with_no_orders"
        
        order_service.order_repo.list_orders.return_value = []

        query_params = pydantic_models.OrderQueryParams(
            page=1,
            page_size=20
        )

        result = await order_service.list_orders(mock_request, user_id, query_params)

        assert isinstance(result, pydantic_models.OrderList)
        assert len(result.items) == 0
        assert result.total == 0