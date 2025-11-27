import pytest
import pytest_asyncio
from unittest.mock import Mock
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from main import app
from services.product_services import ProductService
from app.database import pydantic_models


class TestProductService:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest_asyncio.fixture
    async def mock_logger(self):
        return Mock()

    @pytest_asyncio.fixture
    async def mock_request(self):
        request = Mock(spec=Request)
        request.url = "http://testserver/api/products"
        return request

    @pytest_asyncio.fixture
    async def product_service(self, mock_logger):
        return ProductService(logger=mock_logger)

    def test_client_initialization(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_product_success(
        self, product_service, mock_request
    ):
        product_data = pydantic_models.ProductRequest(
            name="Test Product",
            price=29.99,
            stock=100,
            description="Test description"
        )

        result = await product_service.create_product(
            mock_request, product_data
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 201
        assert "Location" in result.headers
        assert "/api/products/prod_1" in result.headers["Location"]
        
        product_service.logger.info.assert_any_call("Product creation attempt: Test Product")
        product_service.logger.info.assert_any_call("Product created successfully: prod_1")

    @pytest.mark.asyncio
    async def test_create_product_duplicate(
        self, product_service, mock_request
    ):
        # Create first product
        product_data = pydantic_models.ProductRequest(
            name="Duplicate Product",
            price=39.99,
            stock=50,
            description="First product"
        )
        await product_service.create_product(mock_request, product_data)

        # Try to create duplicate
        duplicate_data = pydantic_models.ProductRequest(
            name="Duplicate Product",
            price=49.99,
            stock=25,
            description="Duplicate product"
        )

        result = await product_service.create_product(
            mock_request, duplicate_data
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 409

    @pytest.mark.asyncio
    async def test_get_product_success(
        self, product_service, mock_request
    ):
        # First create a product
        product_data = pydantic_models.ProductRequest(
            name="Test Product for Get",
            price=59.99,
            stock=75,
            description="Test product for get"
        )
        create_result = await product_service.create_product(mock_request, product_data)
        product_id = "prod_1"

        result = await product_service.get_product(
            mock_request, product_id
        )

        assert isinstance(result, pydantic_models.ProductResponse)
        assert result.id == product_id
        assert result.name == "Test Product for Get"
        
        product_service.logger.info.assert_any_call(f"Product retrieval attempt: {product_id}")
        product_service.logger.info.assert_any_call(f"Product retrieved successfully: {product_id}")

    @pytest.mark.asyncio
    async def test_get_product_not_found(
        self, product_service, mock_request
    ):
        result = await product_service.get_product(
            mock_request, "non_existent_id"
        )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_list_products_success(
        self, product_service, mock_request
    ):
        # Create some test products
        for i in range(3):
            product_data = pydantic_models.ProductRequest(
                name=f"Test Product {i}",
                price=10 + i + .99,
                stock=10 * (i + 1),
                description=f"Test product {i}"
            )
            await product_service.create_product(mock_request, product_data)

        query_params = pydantic_models.ProductQueryParams(
            page=1,
            page_size=20
        )

        result = await product_service.list_products(
            mock_request, query_params
        )

        assert isinstance(result, pydantic_models.ProductList)
        assert len(result.items) == 3
        assert result.total == 3
        assert result.page == 1
        assert result.page_size == 20

    @pytest.mark.asyncio
    async def test_list_products_with_search(
        self, product_service, mock_request
    ):
        # Create test products
        product_data1 = pydantic_models.ProductRequest(
            name="Laptop Computer",
            price=999.99,
            stock=5,
            description="High-performance laptop"
        )
        product_data2 = pydantic_models.ProductRequest(
            name="Wireless Mouse",
            price=29.99,
            stock=20,
            description="Ergonomic wireless mouse"
        )
        
        await product_service.create_product(mock_request, product_data1)
        await product_service.create_product(mock_request, product_data2)

        query_params = pydantic_models.ProductQueryParams(
            page=1,
            page_size=20,
            q="laptop"
        )

        result = await product_service.list_products(
            mock_request, query_params
        )

        assert isinstance(result, pydantic_models.ProductList)
        assert len(result.items) == 1
        assert "Laptop" in result.items[0].name

    @pytest.mark.asyncio
    async def test_update_product_success(
        self, product_service, mock_request
    ):
        # First create a product
        product_data = pydantic_models.ProductRequest(
            name="Product to Update",
            price=79.99,
            stock=30,
            description="Original description"
        )
        await product_service.create_product(mock_request, product_data)
        product_id = "prod_1"

        update_data = pydantic_models.ProductRequest(
            name="Updated Product",
            price=89.99,
            stock=40,
            description="Updated description"
        )

        result = await product_service.update_product(
            mock_request, product_id, update_data
        )

        assert isinstance(result, pydantic_models.ProductResponse)
        assert result.name == "Updated Product"
        assert result.price == 89.99
        assert result.stock == 40
        
        product_service.logger.info.assert_any_call(f"Product update attempt: {product_id}")
        product_service.logger.info.assert_any_call(f"Product updated successfully: {product_id}")

    @pytest.mark.asyncio
    async def test_patch_product_success(
        self, product_service, mock_request
    ):
        # First create a product
        product_data = pydantic_models.ProductRequest(
            name="Product to Patch",
            price=99.99,
            stock=15,
            description="Original description"
        )
        await product_service.create_product(mock_request, product_data)
        product_id = "prod_1"

        patch_data = pydantic_models.ProductPatch(
            stock=25
        )

        result = await product_service.patch_product(
            mock_request, product_id, patch_data
        )

        assert isinstance(result, pydantic_models.ProductResponse)
        assert result.stock == 25
        assert result.name == "Product to Patch"  # Should remain unchanged

    @pytest.mark.asyncio
    async def test_delete_product_success(
        self, product_service, mock_request
    ):
        # First create a product
        product_data = pydantic_models.ProductRequest(
            name="Product to Delete",
            price=49.99,
            stock=10,
            description="To be deleted"
        )
        await product_service.create_product(mock_request, product_data)
        product_id = "prod_1"

        result = await product_service.delete_product(
            mock_request, product_id
        )

        assert result is None
        
        # Verify product is gone
        get_result = await product_service.get_product(mock_request, product_id)
        assert get_result.status_code == 404
        
        product_service.logger.info.assert_any_call(f"Product deletion attempt: {product_id}")
        product_service.logger.info.assert_any_call(f"Product deleted successfully: {product_id}")

    @pytest.mark.asyncio
    async def test_update_inventory_success(
        self, product_service, mock_request
    ):
        # First create a product
        product_data = pydantic_models.ProductRequest(
            name="Product for Inventory",
            price=69.99,
            stock=20,
            description="Inventory test"
        )
        await product_service.create_product(mock_request, product_data)
        product_id = "prod_1"

        inventory_data = pydantic_models.InventoryUpdate(
            stock=50
        )

        result = await product_service.update_inventory(
            mock_request, product_id, inventory_data
        )

        assert isinstance(result, pydantic_models.InventoryResponse)  # Check for model, not dict
        assert result.id == product_id
        assert result.stock == 50
        
        product_service.logger.info.assert_any_call(f"Inventory update attempt: {product_id}")
        product_service.logger.info.assert_any_call(f"Inventory updated successfully: {product_id} -> Stock: 50")

    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_logger):
        service = ProductService(logger=mock_logger)

        assert service.logger == mock_logger
        assert service.products == {}
        assert service.next_id == 1
