import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from fastapi import Request
from fastapi.responses import JSONResponse
from services.product_services import ProductService
from database import pydantic_models
from database.database_models import ProductDB
from services.product_helpers import create_problem_response

@pytest.fixture
def mock_logger():
    return Mock()

@pytest.fixture
def mock_repository():
    repo = Mock()
    repo.create_product = AsyncMock()
    repo.get_product_by_id = AsyncMock()
    repo.get_product_by_name = AsyncMock()
    repo.list_products = AsyncMock()
    repo.count_products = AsyncMock()
    repo.update_product = AsyncMock()
    repo.delete_product = AsyncMock()
    repo.update_inventory = AsyncMock()
    return repo

@pytest.fixture
def product_service(mock_logger, mock_repository):
    service = ProductService(mock_logger)
    service.product_repository = mock_repository
    return service

@pytest.fixture
def mock_request():
    request = Mock(spec=Request)
    request.url = "http://testserver/api/products"
    return request

@pytest.mark.asyncio
class TestProductService:
    async def test_create_product_success(self, product_service, mock_request):
        product_data = pydantic_models.ProductRequest(
            name="Test Product",
            price=99.99,
            stock=10,
            description="Test Description"
        )
        
        mock_product = ProductDB(
            id="test_id_123",
            name="Test Product",
            price=99.99,
            stock=10,
            description="Test Description"
        )
        
        product_service.product_repository.create_product.return_value = mock_product
        
        result = await product_service.create_product(mock_request, product_data)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 201
        assert "Location" in result.headers
        assert "/api/products/test_id_123" in result.headers["Location"]
        
        product_service.product_repository.create_product.assert_called_once()
        product_service.logger.info.assert_called()

    async def test_create_product_duplicate_name(self, product_service, mock_request):
        product_data = pydantic_models.ProductRequest(
            name="Existing Product",
            price=99.99,
            stock=10,
            description="Test Description"
        )
        
        product_service.product_repository.create_product.return_value = None
        
        result = await product_service.create_product(mock_request, product_data)
        
        assert result.status_code == 409
        assert "Conflict" in result.body.decode()
        product_service.logger.info.assert_called()

    async def test_get_product_success(self, product_service, mock_request):
        mock_product = ProductDB(
            id="test_id_123",
            name="Test Product",
            price=99.99,
            stock=10,
            description="Test Description"
        )
        
        product_service.product_repository.get_product_by_id.return_value = mock_product
        
        result = await product_service.get_product(mock_request, "test_id_123")
        
        assert result.id == "test_id_123"
        assert result.name == "Test Product"
        assert result.price == 99.99
        product_service.product_repository.get_product_by_id.assert_called_once_with("test_id_123")

    async def test_get_product_not_found(self, product_service, mock_request):
        product_service.product_repository.get_product_by_id.return_value = None
        
        result = await product_service.get_product(mock_request, "non_existent_id")
        
        assert result.status_code == 404
        assert "Not Found" in result.body.decode()

    async def test_list_products_success(self, product_service, mock_request):
        mock_products = [
            ProductDB(
                id="prod_1",
                name="Product 1",
                price=99.99,
                stock=10,
                description="Description 1"
            ),
            ProductDB(
                id="prod_2",
                name="Product 2",
                price=199.99,
                stock=5,
                description="Description 2"
            )
        ]
        
        product_service.product_repository.list_products.return_value = mock_products
        product_service.product_repository.count_products.return_value = 2
        
        query_params = pydantic_models.ProductQueryParams(
            page=1,
            page_size=10,
            q=None
        )
        
        result = await product_service.list_products(mock_request, query_params)
        
        assert result.total == 2
        assert len(result.items) == 2
        assert result.page == 1
        assert result.page_size == 10
        assert result.items[0].name == "Product 1"
        assert result.items[1].name == "Product 2"

    async def test_list_products_with_search(self, product_service, mock_request):
        mock_products = [
            ProductDB(
                id="prod_1",
                name="Laptop",
                price=999.99,
                stock=5,
                description="Gaming laptop"
            )
        ]
        
        product_service.product_repository.list_products.return_value = mock_products
        product_service.product_repository.count_products.return_value = 1
        
        query_params = pydantic_models.ProductQueryParams(
            page=1,
            page_size=10,
            q="laptop"
        )
        
        result = await product_service.list_products(mock_request, query_params)
        
        assert result.total == 1
        assert result.items[0].name == "Laptop"
        product_service.product_repository.list_products.assert_called_with(
            skip=0, limit=10, search_query="laptop"
        )

    async def test_list_products_pagination(self, product_service, mock_request):
        product_service.product_repository.list_products.return_value = []
        product_service.product_repository.count_products.return_value = 50
        
        query_params = pydantic_models.ProductQueryParams(
            page=2,
            page_size=10,
            q=None
        )
        
        result = await product_service.list_products(mock_request, query_params)
        
        assert result.total == 50
        assert result.page == 2
        assert result.page_size == 10
        product_service.product_repository.list_products.assert_called_with(
            skip=10, limit=10, search_query=None
        )

    async def test_update_product_success(self, product_service, mock_request):
        mock_updated_product = ProductDB(
            id="test_id_123",
            name="Updated Product",
            price=149.99,
            stock=15,
            description="Updated Description"
        )
        
        product_service.product_repository.update_product.return_value = mock_updated_product
        
        update_data = pydantic_models.ProductRequest(
            name="Updated Product",
            price=149.99,
            stock=15,
            description="Updated Description"
        )
        
        result = await product_service.update_product(mock_request, "test_id_123", update_data)
        
        assert result.name == "Updated Product"
        assert result.price == 149.99
        assert result.stock == 15
        product_service.product_repository.update_product.assert_called_once()

    async def test_update_product_not_found(self, product_service, mock_request):
        product_service.product_repository.update_product.return_value = None
        
        update_data = pydantic_models.ProductRequest(
            name="Updated Product",
            price=149.99,
            stock=15,
            description="Updated Description"
        )
        
        result = await product_service.update_product(mock_request, "non_existent_id", update_data)
        
        assert result.status_code == 404
        assert "Not Found" in result.body.decode()

    async def test_patch_product_success(self, product_service, mock_request):
        mock_patched_product = ProductDB(
            id="test_id_123",
            name="Original Product",
            price=199.99,
            stock=25,
            description="Original Description"
        )
        
        product_service.product_repository.update_product.return_value = mock_patched_product
        
        patch_data = pydantic_models.ProductPatch(price=199.99)
        
        result = await product_service.patch_product(mock_request, "test_id_123", patch_data)
        
        assert result.price == 199.99
        assert result.name == "Original Product"
        product_service.product_repository.update_product.assert_called_once()

    async def test_patch_product_not_found(self, product_service, mock_request):
        product_service.product_repository.update_product.return_value = None
        
        patch_data = pydantic_models.ProductPatch(price=199.99)
        
        result = await product_service.patch_product(mock_request, "non_existent_id", patch_data)
        
        assert result.status_code == 404
        assert "Not Found" in result.body.decode()

    async def test_delete_product_success(self, product_service, mock_request):
        product_service.product_repository.delete_product.return_value = True
        
        result = await product_service.delete_product(mock_request, "test_id_123")
        
        assert result is None
        product_service.product_repository.delete_product.assert_called_once_with("test_id_123")
        product_service.logger.info.assert_called()

    async def test_delete_product_not_found(self, product_service, mock_request):
        product_service.product_repository.delete_product.return_value = False
        
        result = await product_service.delete_product(mock_request, "non_existent_id")
        
        assert result.status_code == 404
        assert "Not Found" in result.body.decode()

    async def test_update_inventory_success(self, product_service, mock_request):
        mock_updated_product = ProductDB(
            id="test_id_123",
            name="Test Product",
            price=99.99,
            stock=25,
            description="Test Description"
        )
        
        product_service.product_repository.update_inventory.return_value = mock_updated_product
        
        inventory_data = pydantic_models.InventoryUpdate(stock=25)
        
        result = await product_service.update_inventory(mock_request, "test_id_123", inventory_data)
        
        assert result.id == "test_id_123"
        assert result.stock == 25
        product_service.product_repository.update_inventory.assert_called_once_with("test_id_123", 25)

    async def test_update_inventory_not_found(self, product_service, mock_request):
        product_service.product_repository.update_inventory.return_value = None
        
        inventory_data = pydantic_models.InventoryUpdate(stock=25)
        
        result = await product_service.update_inventory(mock_request, "non_existent_id", inventory_data)
        
        assert result.status_code == 404
        assert "Not Found" in result.body.decode()

    async def test_error_handling_in_create_product(self, product_service, mock_request):
        product_data = pydantic_models.ProductRequest(
            name="Test Product",
            price=99.99,
            stock=10,
            description="Test Description"
        )
        
        product_service.product_repository.create_product.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            await product_service.create_product(mock_request, product_data)

    async def test_error_handling_in_list_products(self, product_service, mock_request):
        query_params = pydantic_models.ProductQueryParams(
            page=1,
            page_size=10,
            q=None
        )
        
        product_service.product_repository.list_products.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            await product_service.list_products(mock_request, query_params)

@pytest.mark.asyncio
class TestProductServiceIntegration:
    async def test_full_product_lifecycle(self, product_service, mock_request):
        create_data = pydantic_models.ProductRequest(
            name="Integration Test Product",
            price=299.99,
            stock=20,
            description="Integration Test"
        )
        
        mock_created_product = ProductDB(
            id="integration_id",
            name="Integration Test Product",
            price=299.99,
            stock=20,
            description="Integration Test"
        )
        
        product_service.product_repository.create_product.return_value = mock_created_product
        product_service.product_repository.get_product_by_id.return_value = mock_created_product
        product_service.product_repository.update_product.return_value = mock_created_product
        product_service.product_repository.delete_product.return_value = True
        
        create_result = await product_service.create_product(mock_request, create_data)
        assert create_result.status_code == 201
        
        get_result = await product_service.get_product(mock_request, "integration_id")
        assert get_result.name == "Integration Test Product"
        
        update_data = pydantic_models.ProductRequest(
            name="Updated Integration Product",
            price=399.99,
            stock=15,
            description="Updated Integration Test"
        )
        
        update_result = await product_service.update_product(mock_request, "integration_id", update_data)
        assert update_result.name == "Integration Test Product"
        
        delete_result = await product_service.delete_product(mock_request, "integration_id")
        assert delete_result is None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])