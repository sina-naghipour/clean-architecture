import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import Request
from fastapi.responses import JSONResponse
from services.product_services import ProductService
from database import pydantic_models
from database.database_models import ProductDB

class TestProductService:
    @pytest.fixture
    def mock_logger(self):
        return Mock()

    @pytest.fixture
    def mock_repository(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_logger, mock_repository):
        service = ProductService(mock_logger)
        service.product_repository = mock_repository
        return service

    @pytest.fixture
    def mock_request(self):
        request = Mock(spec=Request)
        request.url = "http://test.com/api/products"
        return request

    @pytest.fixture
    def sample_product_request(self):
        return pydantic_models.ProductRequest(
            name="Test Product",
            price=29.99,
            stock=100,
            description="Test Description"
        )

    @pytest.fixture
    def sample_product_db(self):
        return ProductDB(
            name="Test Product",
            price=29.99,
            stock=100,
            description="Test Description"
        )

    @pytest.mark.asyncio
    async def test_create_product_success(self, service, mock_request, sample_product_request, sample_product_db):
        service.product_repository.create_product.return_value = sample_product_db
        
        result = await service.create_product(mock_request, sample_product_request)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 201
        service.product_repository.create_product.assert_called_once()
        service.logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_create_product_duplicate_name(self, service, mock_request, sample_product_request):
        service.product_repository.create_product.return_value = None
        
        result = await service.create_product(mock_request, sample_product_request)
        
        assert result.status_code == 409
        service.product_repository.create_product.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_product_success(self, service, mock_request, sample_product_db):
        service.product_repository.get_product_by_id.return_value = sample_product_db
        
        result = await service.get_product(mock_request, "test_id")
        
        assert result.id == sample_product_db.id
        assert result.name == sample_product_db.name
        service.product_repository.get_product_by_id.assert_called_once_with("test_id")

    @pytest.mark.asyncio
    async def test_get_product_not_found(self, service, mock_request):
        service.product_repository.get_product_by_id.return_value = None
        
        result = await service.get_product(mock_request, "nonexistent_id")
        
        assert result.status_code == 404
        service.product_repository.get_product_by_id.assert_called_once_with("nonexistent_id")

    @pytest.mark.asyncio
    async def test_list_products_success(self, service, mock_request):
        products_db = [
            ProductDB(name="Product 1", price=10.0, stock=5, description="Desc 1"),
            ProductDB(name="Product 2", price=20.0, stock=10, description="Desc 2")
        ]
        service.product_repository.list_products.return_value = products_db
        service.product_repository.count_products.return_value = 2
        
        query_params = pydantic_models.ProductQueryParams(page=1, page_size=20)
        result = await service.list_products(mock_request, query_params)
        
        assert len(result.items) == 2
        assert result.total == 2
        assert result.page == 1
        service.product_repository.list_products.assert_called_once_with(skip=0, limit=20, search_query=None)
        service.product_repository.count_products.assert_called_once_with(search_query=None)

    @pytest.mark.asyncio
    async def test_list_products_with_search(self, service, mock_request):
        products_db = [ProductDB(name="Found Product", price=15.0, stock=8, description="Matching")]
        service.product_repository.list_products.return_value = products_db
        service.product_repository.count_products.return_value = 1
        
        query_params = pydantic_models.ProductQueryParams(page=1, page_size=10, q="Found")
        result = await service.list_products(mock_request, query_params)
        
        assert len(result.items) == 1
        service.product_repository.list_products.assert_called_once_with(skip=0, limit=10, search_query="Found")
        service.product_repository.count_products.assert_called_once_with(search_query="Found")

    @pytest.mark.asyncio
    async def test_update_product_success(self, service, mock_request):
        updated_product_db = ProductDB(
            name="Updated Product",
            price=39.99,
            stock=50,
            description="Updated Description"
        )
        service.product_repository.update_product.return_value = updated_product_db
        
        update_data = pydantic_models.ProductRequest(
            name="Updated Product",
            price=39.99,
            stock=50,
            description="Updated Description"
        )
        
        result = await service.update_product(mock_request, "test_id", update_data)
        
        assert result.name == "Updated Product"
        assert result.price == 39.99
        service.product_repository.update_product.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_product_not_found(self, service, mock_request):
        service.product_repository.update_product.return_value = None
        
        update_data = pydantic_models.ProductRequest(
            name="Updated Product",
            price=39.99,
            stock=50,
            description="Updated Description"
        )
        
        result = await service.update_product(mock_request, "nonexistent_id", update_data)
        
        assert result.status_code == 404
        service.product_repository.update_product.assert_called_once()

    @pytest.mark.asyncio
    async def test_patch_product_success(self, service, mock_request, sample_product_db):
        service.product_repository.patch_product.return_value = sample_product_db
        
        patch_data = pydantic_models.ProductPatch(stock=200, price=19.99)
        
        result = await service.patch_product(mock_request, "test_id", patch_data)
        
        assert result.stock == 100
        assert result.price == 29.99
        service.product_repository.patch_product.assert_called_once()

    @pytest.mark.asyncio
    async def test_patch_product_not_found(self, service, mock_request):
        service.product_repository.patch_product.return_value = None
        
        patch_data = pydantic_models.ProductPatch(stock=200)
        
        result = await service.patch_product(mock_request, "nonexistent_id", patch_data)
        
        assert result.status_code == 404
        service.product_repository.patch_product.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_product_success(self, service, mock_request):
        service.product_repository.delete_product.return_value = True
        
        result = await service.delete_product(mock_request, "test_id")
        
        assert result is None
        service.product_repository.delete_product.assert_called_once_with("test_id")

    @pytest.mark.asyncio
    async def test_delete_product_not_found(self, service, mock_request):
        service.product_repository.delete_product.return_value = False
        
        result = await service.delete_product(mock_request, "nonexistent_id")
        
        assert result.status_code == 404
        service.product_repository.delete_product.assert_called_once_with("nonexistent_id")

    @pytest.mark.asyncio
    async def test_update_inventory_success(self, service, mock_request, sample_product_db):
        service.product_repository.update_inventory.return_value = sample_product_db
        
        inventory_data = pydantic_models.InventoryUpdate(stock=150)
        
        result = await service.update_inventory(mock_request, "test_id", inventory_data)
        
        assert result.stock == 100
        service.product_repository.update_inventory.assert_called_once_with("test_id", 150)

    @pytest.mark.asyncio
    async def test_update_inventory_not_found(self, service, mock_request):
        service.product_repository.update_inventory.return_value = None
        
        inventory_data = pydantic_models.InventoryUpdate(stock=150)
        
        result = await service.update_inventory(mock_request, "nonexistent_id", inventory_data)
        
        assert result.status_code == 404
        service.product_repository.update_inventory.assert_called_once_with("nonexistent_id", 150)