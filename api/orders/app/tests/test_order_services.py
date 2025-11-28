import pytest
import pytest_asyncio
from unittest.mock import Mock
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from main import app
from services.order_services import OrderService
from app.database import pydantic_models


class TestOrderService:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest_asyncio.fixture
    async def mock_logger(self):
        return Mock()

    @pytest_asyncio.fixture
    async def mock_request(self):
        request = Mock(spec=Request)
        request.url = "http://testserver/api/orders"
        return request

    @pytest_asyncio.fixture
    async def order_service(self, mock_logger):
        service = OrderService(logger=mock_logger)
        service._create_mock_cart("test_user_1")
        return service

    def test_client_initialization(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_order_success(
        self, order_service, mock_request
    ):
        user_id = "test_user_1"
        order_data = pydantic_models.OrderCreate(
            billing_address_id="addr_1",
            shipping_address_id="addr_1",
            payment_method_token="pm_tok_abc"
        )

        result = await order_service.create_order(
            mock_request, order_data, user_id
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 201
        
        order_service.logger.info.assert_any_call(f"Order creation attempt for user: {user_id}")
        order_service.logger.info.assert_any_call("Order created successfully: order_1")

    @pytest.mark.asyncio
    async def test_create_order_empty_cart(
        self, order_service, mock_request
    ):
        user_id = "user_with_empty_cart"
        order_data = pydantic_models.OrderCreate()

        result = await order_service.create_order(
            mock_request, order_data, user_id
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 400

    @pytest.mark.asyncio
    async def test_get_order_success(
        self, order_service, mock_request
    ):
        user_id = "test_user_1"
        order_data = pydantic_models.OrderCreate()
        
        create_result = await order_service.create_order(mock_request, order_data, user_id)
        order_id = "order_1"

        result = await order_service.get_order(
            mock_request, order_id, user_id
        )

        assert isinstance(result, pydantic_models.OrderResponse)
        assert result.id == order_id
        assert result.status == pydantic_models.OrderStatus.CREATED
        assert len(result.items) == 2
        
        order_service.logger.info.assert_any_call(f"Order retrieval attempt: {order_id}")
        order_service.logger.info.assert_any_call(f"Order retrieved successfully: {order_id}")

    @pytest.mark.asyncio
    async def test_get_order_not_found(
        self, order_service, mock_request
    ):
        user_id = "test_user_1"

        result = await order_service.get_order(
            mock_request, "non_existent_order", user_id
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_get_order_wrong_user(
        self, order_service, mock_request
    ):
        user_id = "test_user_1"
        order_data = pydantic_models.OrderCreate()
        
        await order_service.create_order(mock_request, order_data, user_id)
        order_id = "order_1"

        result = await order_service.get_order(
            mock_request, order_id, "different_user"
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_list_orders_success(
        self, order_service, mock_request
    ):
        user_id = "test_user_1"
        
        order_data = pydantic_models.OrderCreate()
        await order_service.create_order(mock_request, order_data, user_id)

        query_params = pydantic_models.OrderQueryParams(
            page=1,
            page_size=20
        )

        result = await order_service.list_orders(
            mock_request, user_id, query_params
        )

        assert isinstance(result, pydantic_models.OrderList)
        assert len(result.items) == 1
        assert result.total == 1
        assert result.page == 1
        assert result.page_size == 20
        
        order_service.logger.info.assert_any_call(f"Orders listing attempt for user: {user_id}")
        order_service.logger.info.assert_any_call(f"Orders listed successfully for user: {user_id}")

    @pytest.mark.asyncio
    async def test_list_orders_empty(
        self, order_service, mock_request
    ):
        user_id = "user_with_no_orders"

        query_params = pydantic_models.OrderQueryParams(
            page=1,
            page_size=20
        )

        result = await order_service.list_orders(
            mock_request, user_id, query_params
        )

        assert isinstance(result, pydantic_models.OrderList)
        assert len(result.items) == 0
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_order_total_calculation(
        self, order_service, mock_request
    ):
        user_id = "test_user_1"
        order_data = pydantic_models.OrderCreate()

        result = await order_service.create_order(mock_request, order_data, user_id)
        
        get_result = await order_service.get_order(mock_request, "order_1", user_id)

        expected_total = (1 * 999.99) + (2 * 29.99)
        assert abs(get_result.total - expected_total) < 0.01

    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_logger):
        service = OrderService(logger=mock_logger)

        assert service.logger == mock_logger
        assert service.orders == {}
        assert service.next_order_id == 1
        assert service.user_carts == {}
