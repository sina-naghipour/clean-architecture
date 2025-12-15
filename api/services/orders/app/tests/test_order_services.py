import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from fastapi import Request
from fastapi.responses import JSONResponse
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
            service = OrderService(logger=mock_logger, db_session=mock_db_session)
            service.order_repo = mock_repo_instance
            yield service

    @pytest_asyncio.fixture
    async def mock_request(self):
        request = Mock(spec=Request)
        request.url = "http://testserver/api/orders"
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

        result = await order_service.create_order(mock_request, order_data, user_id)

        assert isinstance(result, JSONResponse)
        assert result.status_code == 201
        order_service.order_repo.create_order.assert_called_once()

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
        order_service.order_repo.get_order_by_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_order_not_found(self, order_service, mock_request):
        user_id = "test_user_1"
        order_id = str(uuid4())
        
        order_service.order_repo.get_order_by_id.return_value = None

        result = await order_service.get_order(mock_request, order_id, user_id)

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_get_order_wrong_user(self, order_service, mock_request, sample_order_db):
        wrong_user_id = "different_user"
        order_id = str(sample_order_db.id)
        
        order_service.order_repo.get_order_by_id.return_value = sample_order_db

        result = await order_service.get_order(mock_request, order_id, wrong_user_id)

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_get_order_invalid_uuid(self, order_service, mock_request):
        user_id = "test_user_1"
        invalid_order_id = "not-a-uuid"

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
                items=[{"product_id": "prod_3", "name": "Keyboard", "quantity": 1, "unit_price": 50.00}]
            )
        ]
        orders_db[1].user_id = "test_user_1"
        
        order_service.order_repo.list_orders.return_value = orders_db

        query_params = pydantic_models.OrderQueryParams(
            page=1,
            page_size=20
        )

        result = await order_service.list_orders(mock_request, user_id, query_params)

        assert isinstance(result, pydantic_models.OrderList)
        assert len(result.items) == 2

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