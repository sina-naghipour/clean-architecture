import pytest
import pytest_asyncio
from unittest.mock import Mock
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from main import app
from services.cart_services import CartService
from database import models


class TestCartService:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest_asyncio.fixture
    async def mock_logger(self):
        return Mock()

    @pytest_asyncio.fixture
    async def mock_request(self):
        request = Mock(spec=Request)
        request.url = "http://testserver/api/cart"
        return request

    @pytest_asyncio.fixture
    async def cart_service(self, mock_logger):
        return CartService(logger=mock_logger)

    def test_client_initialization(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_cart_success(
        self, cart_service, mock_request
    ):
        # First create a cart by adding an item
        user_id = "test_user_1"
        item_data = models.CartItemRequest(
            product_id="prod_1",
            quantity=2
        )
        await cart_service.add_cart_item(mock_request, user_id, item_data)

        result = await cart_service.get_cart(
            mock_request, user_id
        )

        assert isinstance(result, models.CartResponse)
        assert result.user_id == user_id
        assert len(result.items) == 1
        assert result.items[0].product_id == "prod_1"
        
        cart_service.logger.info.assert_any_call(f"Cart retrieval attempt for user: {user_id}")
        cart_service.logger.info.assert_any_call(f"Cart retrieved successfully for user: {user_id}")

    @pytest.mark.asyncio
    async def test_get_cart_not_found(
        self, cart_service, mock_request
    ):
        result = await cart_service.get_cart(
            mock_request, "non_existent_user"
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_add_cart_item_success(
        self, cart_service, mock_request
    ):
        user_id = "test_user_2"
        item_data = models.CartItemRequest(
            product_id="prod_2",
            quantity=1
        )

        result = await cart_service.add_cart_item(
            mock_request, user_id, item_data
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 201
        
        # Verify cart was created
        cart_result = await cart_service.get_cart(mock_request, user_id)
        assert cart_result.user_id == user_id
        assert len(cart_result.items) == 1
        
        cart_service.logger.info.assert_any_call(f"Add item attempt for user: {user_id}, product: {item_data.product_id}")
        cart_service.logger.info.assert_any_call("Item added successfully to cart: item_1")

    @pytest.mark.asyncio
    async def test_add_cart_item_product_not_found(
        self, cart_service, mock_request
    ):
        user_id = "test_user_3"
        item_data = models.CartItemRequest(
            product_id="non_existent_product",
            quantity=1
        )

        result = await cart_service.add_cart_item(
            mock_request, user_id, item_data
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_add_cart_item_update_quantity(
        self, cart_service, mock_request
    ):
        user_id = "test_user_4"
        item_data = models.CartItemRequest(
            product_id="prod_1",
            quantity=1
        )

        # Add item first time
        await cart_service.add_cart_item(mock_request, user_id, item_data)
        
        # Add same item again
        result = await cart_service.add_cart_item(
            mock_request, user_id, item_data
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 201
        
        # Verify quantity was updated
        cart_result = await cart_service.get_cart(mock_request, user_id)
        assert len(cart_result.items) == 1
        assert cart_result.items[0].quantity == 2  # 1 + 1

    @pytest.mark.asyncio
    async def test_update_cart_item_success(
        self, cart_service, mock_request
    ):
        user_id = "test_user_5"
        item_data = models.CartItemRequest(
            product_id="prod_2",
            quantity=1
        )
        
        # First add an item
        add_result = await cart_service.add_cart_item(mock_request, user_id, item_data)
        item_id = "item_1"

        update_data = models.CartItemUpdate(
            quantity=5
        )

        result = await cart_service.update_cart_item(
            mock_request, user_id, item_id, update_data
        )

        assert isinstance(result, models.CartItemResponse)
        assert result.quantity == 5
        
        cart_service.logger.info.assert_any_call(f"Update item attempt for user: {user_id}, item: {item_id}")
        cart_service.logger.info.assert_any_call(f"Item updated successfully: {item_id}")

    @pytest.mark.asyncio
    async def test_update_cart_item_not_found(
        self, cart_service, mock_request
    ):
        user_id = "test_user_6"
        update_data = models.CartItemUpdate(quantity=2)

        result = await cart_service.update_cart_item(
            mock_request, user_id, "non_existent_item", update_data
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_remove_cart_item_success(
        self, cart_service, mock_request
    ):
        user_id = "test_user_7"
        item_data = models.CartItemRequest(
            product_id="prod_3",
            quantity=1
        )
        
        # First add an item
        add_result = await cart_service.add_cart_item(mock_request, user_id, item_data)
        item_id = "item_1"

        result = await cart_service.remove_cart_item(
            mock_request, user_id, item_id
        )

        assert result is None
        
        # Verify item is gone
        cart_result = await cart_service.get_cart(mock_request, user_id)
        assert len(cart_result.items) == 0
        
        cart_service.logger.info.assert_any_call(f"Remove item attempt for user: {user_id}, item: {item_id}")
        cart_service.logger.info.assert_any_call(f"Item removed successfully: {item_id}")

    @pytest.mark.asyncio
    async def test_clear_cart_success(
        self, cart_service, mock_request
    ):
        user_id = "test_user_8"
        
        # Add some items
        items = [
            models.CartItemRequest(product_id="prod_1", quantity=1),
            models.CartItemRequest(product_id="prod_2", quantity=2)
        ]
        
        for item in items:
            await cart_service.add_cart_item(mock_request, user_id, item)

        result = await cart_service.clear_cart(
            mock_request, user_id
        )

        assert result is None
        
        # Verify cart is empty
        cart_result = await cart_service.get_cart(mock_request, user_id)
        assert len(cart_result.items) == 0
        
        cart_service.logger.info.assert_any_call(f"Clear cart attempt for user: {user_id}")
        cart_service.logger.info.assert_any_call(f"Cart cleared successfully for user: {user_id}")

    @pytest.mark.asyncio
    async def test_list_carts_success(
        self, cart_service, mock_request
    ):
        # Create some test carts
        users = ["user_a", "user_b", "user_c"]
        for user_id in users:
            item_data = models.CartItemRequest(
                product_id="prod_1",
                quantity=1
            )
            await cart_service.add_cart_item(mock_request, user_id, item_data)

        query_params = models.CartQueryParams(
            page=1,
            page_size=20
        )

        result = await cart_service.list_carts(
            mock_request, query_params
        )

        assert isinstance(result, models.CartList)
        assert len(result.items) == 3
        assert result.total == 3
        assert result.page == 1
        assert result.page_size == 20

    @pytest.mark.asyncio
    async def test_cart_total_calculation(
        self, cart_service, mock_request
    ):
        user_id = "test_user_total"
        
        # Add multiple items with different quantities and prices
        items = [
            models.CartItemRequest(product_id="prod_1", quantity=2),
            models.CartItemRequest(product_id="prod_2", quantity=3),
            models.CartItemRequest(product_id="prod_3", quantity=1)
        ]
        
        for item in items:
            await cart_service.add_cart_item(mock_request, user_id, item)

        result = await cart_service.get_cart(mock_request, user_id)

        expected_total = 1999.98 + 89.97 + 79.99
        assert abs(result.total - expected_total) < 0.01  # Allow floating point precision

    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_logger):
        service = CartService(logger=mock_logger)

        assert service.logger == mock_logger
        assert service.carts == {}
        assert service.next_cart_id == 1
        assert service.next_item_id == 1
        assert "prod_1" in service.products
