import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import Request, UploadFile
from fastapi.responses import JSONResponse
from io import BytesIO
import json
from datetime import datetime

from services.product_services import ProductService, get_image_client
from database import pydantic_models
from database.database_models import ProductDB
from services.product_image_client import UploadResult

@pytest.fixture
def mock_logger():
    return Mock()

@pytest.fixture
def mock_repository():
    repo = Mock()
    repo.create_product = AsyncMock()
    repo.get_product_by_id = AsyncMock()
    repo.list_products = AsyncMock()
    repo.count_products = AsyncMock()
    repo.update_product = AsyncMock()
    repo.delete_product = AsyncMock()
    repo.update_inventory = AsyncMock()
    repo.update_product_images = AsyncMock()
    return repo

@pytest.fixture
def mock_image_client():
    client = Mock()
    client.upload_images = AsyncMock()
    client.validate_image = AsyncMock()
    client.extract_file_id = Mock()
    client.delete_image = AsyncMock()
    client.close = AsyncMock()
    return client

@pytest.fixture
def product_service(mock_logger, mock_repository, mock_image_client):
    service = ProductService(mock_logger)
    service.product_repository = mock_repository
    service.image_client = mock_image_client
    return service

@pytest.fixture
def mock_request():
    request = Mock(spec=Request)
    request.url = "http://testserver/api/products"
    return request

@pytest.fixture
def sample_upload_file():
    """Create a mock UploadFile for testing"""
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.jpg"
    mock_file.file = BytesIO(b"fake image content")
    mock_file.read = AsyncMock(return_value=b"fake image content")
    mock_file.content_type = "image/jpeg"
    return mock_file

@pytest.fixture
def mock_product():
    return ProductDB(
        id="test_id_123",
        name="Test Product",
        price=99.99,
        stock=10,
        description="Test Description",
        tags=["electronics", "test"],
        images=["http://test.com/static/img/img1.jpg"],
        created_at=datetime(2024, 1, 1, 0, 0, 0),
        updated_at=datetime(2024, 1, 1, 0, 0, 0)
    )

@pytest.mark.asyncio
class TestProductService:
    async def test_create_product_success(self, product_service, mock_request):
        product_data = pydantic_models.ProductRequest(
            name="Test Product",
            price=99.99,
            stock=10,
            description="Test Description",
            tags=["electronics"],
            images=[]
        )
        
        # Use actual datetime objects
        created_at = datetime(2024, 1, 1, 0, 0, 0)
        updated_at = datetime(2024, 1, 1, 0, 0, 0)
        
        mock_product = ProductDB(
            id="test_id_123",
            name="Test Product",
            price=99.99,
            stock=10,
            description="Test Description",
            tags=["electronics"],
            images=[],
            created_at=created_at,
            updated_at=updated_at
        )
        
        product_service.product_repository.create_product.return_value = mock_product
        
        result = await product_service.create_product(mock_request, product_data)
        
        assert isinstance(result, pydantic_models.ProductResponse)
        assert result.id == "test_id_123"
        assert result.name == "Test Product"
        assert result.price == 99.99
        assert result.stock == 10
        
        product_service.product_repository.create_product.assert_called_once()
        product_service.logger.info.assert_called()

    async def test_create_product_with_images_success(self, product_service, mock_request):
        product_data = pydantic_models.ProductRequest(
            name="Test Product",
            price=99.99,
            stock=10,
            description="Test Description",
            tags=[],
            images=[]
        )
        
        mock_product = ProductDB(
            id="test_id_123",
            name="Test Product",
            price=99.99,
            stock=10,
            description="Test Description",
            tags=[],
            images=["http://test.com/static/img/img1.jpg", "http://test.com/static/img/img2.jpg"],
            created_at=datetime(2024, 1, 1, 0, 0, 0),
            updated_at=datetime(2024, 1, 1, 0, 0, 0)
        )
        
        product_service.product_repository.create_product.return_value = mock_product
        product_service.image_client.upload_images.return_value = [
            UploadResult(success=True, url="http://test.com/static/img/img1.jpg"),
            UploadResult(success=True, url="http://test.com/static/img/img2.jpg")
        ]
        
        # Create mock upload files properly
        file1 = MagicMock(spec=UploadFile)
        file1.filename = "img1.jpg"
        file1.file = BytesIO(b"content1")
        file1.read = AsyncMock(return_value=b"content1")
        file1.content_type = "image/jpeg"
        
        file2 = MagicMock(spec=UploadFile)
        file2.filename = "img2.jpg"
        file2.file = BytesIO(b"content2")
        file2.read = AsyncMock(return_value=b"content2")
        file2.content_type = "image/jpeg"
        
        result = await product_service.create_product_with_images(
            mock_request, 
            product_data, 
            [file1, file2]
        )
        
        assert isinstance(result, pydantic_models.ProductResponse)
        assert result.id == "test_id_123"
        assert len(result.images) == 2
        assert "http://test.com/static/img/img1.jpg" in result.images
        assert "http://test.com/static/img/img2.jpg" in result.images
        
        product_service.image_client.upload_images.assert_called_once()
        product_service.logger.info.assert_called()

    async def test_create_product_with_images_partial_failure(self, product_service, mock_request):
        product_data = pydantic_models.ProductRequest(
            name="Test Product",
            price=99.99,
            stock=10,
            description="Test Description",
            tags=[],
            images=[]
        )
        
        mock_product = ProductDB(
            id="test_id_123",
            name="Test Product",
            price=99.99,
            stock=10,
            description="Test Description",
            tags=[],
            images=["http://test.com/static/img/img1.jpg"],
            created_at=datetime(2024, 1, 1, 0, 0, 0),
            updated_at=datetime(2024, 1, 1, 0, 0, 0)
        )
        
        product_service.product_repository.create_product.return_value = mock_product
        product_service.image_client.upload_images.return_value = [
            UploadResult(success=True, url="http://test.com/static/img/img1.jpg"),
            UploadResult(success=False, error="Upload failed")
        ]
        
        # Create mock upload files properly
        file1 = MagicMock(spec=UploadFile)
        file1.filename = "img1.jpg"
        file1.file = BytesIO(b"content1")
        file1.read = AsyncMock(return_value=b"content1")
        file1.content_type = "image/jpeg"
        
        file2 = MagicMock(spec=UploadFile)
        file2.filename = "img2.jpg"
        file2.file = BytesIO(b"content2")
        file2.read = AsyncMock(return_value=b"content2")
        file2.content_type = "image/jpeg"
        
        result = await product_service.create_product_with_images(
            mock_request, 
            product_data, 
            [file1, file2]
        )
        
        assert isinstance(result, pydantic_models.ProductResponse)
        assert result.id == "test_id_123"
        assert len(result.images) == 1
        assert "http://test.com/static/img/img1.jpg" in result.images
        
        # Should create product even if some images fail
        product_service.product_repository.create_product.assert_called_once()
    async def test_get_product_success_with_valid_images(self, product_service, mock_request, mock_product):
        product_service.product_repository.get_product_by_id.return_value = mock_product
        product_service.image_client.validate_image.return_value = True
        
        result = await product_service.get_product(mock_request, "test_id_123")
        
        assert hasattr(result, 'id')
        assert result.id == "test_id_123"
        assert result.name == "Test Product"
        product_service.product_repository.get_product_by_id.assert_called_once_with("test_id_123")
        product_service.image_client.validate_image.assert_called_once_with(
            "http://test.com/static/img/img1.jpg"
        )
        product_service.product_repository.update_product_images.assert_not_called()

    async def test_get_product_success_with_invalid_images(self, product_service, mock_request, mock_product):
        product_service.product_repository.get_product_by_id.return_value = mock_product
        product_service.image_client.validate_image.return_value = False
        
        result = await product_service.get_product(mock_request, "test_id_123")
        
        assert result.id == "test_id_123"
        product_service.image_client.validate_image.assert_called_once()
        product_service.product_repository.update_product_images.assert_called_once_with(
            "test_id_123", []
        )

    async def test_get_product_not_found(self, product_service, mock_request):
        product_service.product_repository.get_product_by_id.return_value = None
        
        result = await product_service.get_product(mock_request, "non_existent_id")
        
        # Returns a problem response
        assert hasattr(result, 'status_code')
        assert result.status_code == 404
        assert "Not Found" in result.body.decode()

    async def test_list_products_success(self, product_service, mock_request):
        mock_products = [
            ProductDB(
                id="prod_1",
                name="Product 1",
                price=99.99,
                stock=10,
                description="Description 1",
                tags=["tag1"],
                images=["img1.jpg"],
                created_at=datetime(2024, 1, 1, 0, 0, 0),
                updated_at=datetime(2024, 1, 1, 0, 0, 0)
            ),
            ProductDB(
                id="prod_2",
                name="Product 2",
                price=199.99,
                stock=5,
                description="Description 2",
                tags=["tag2"],
                images=["img2.jpg"],
                created_at=datetime(2024, 1, 1, 0, 0, 0),
                updated_at=datetime(2024, 1, 1, 0, 0, 0)
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

    async def test_update_product_success(self, product_service, mock_request):
        mock_updated_product = ProductDB(
            id="test_id_123",
            name="Updated Product",
            price=149.99,
            stock=15,
            description="Updated Description",
            tags=["updated"],
            images=["updated.jpg"],
            created_at=datetime(2024, 1, 1, 0, 0, 0),
            updated_at=datetime(2024, 1, 1, 0, 0, 0)
        )
        
        product_service.product_repository.update_product.return_value = mock_updated_product
        
        update_data = pydantic_models.ProductRequest(
            name="Updated Product",
            price=149.99,
            stock=15,
            description="Updated Description",
            tags=["updated"],
            images=["updated.jpg"]
        )
        
        result = await product_service.update_product(mock_request, "test_id_123", update_data)
        
        assert result.name == "Updated Product"
        assert result.price == 149.99
        assert result.stock == 15
        product_service.product_repository.update_product.assert_called_once()

    async def test_delete_product_success_with_images(self, product_service, mock_request, mock_product):
        product_service.product_repository.get_product_by_id.return_value = mock_product
        product_service.product_repository.delete_product.return_value = True
        product_service.image_client.extract_file_id.return_value = "img1"
        product_service.image_client.delete_image.return_value = True
        
        result = await product_service.delete_product(mock_request, "test_id_123")
        
        assert result is None
        product_service.product_repository.delete_product.assert_called_once_with("test_id_123")
        product_service.image_client.delete_image.assert_called_once_with("img1")
        product_service.logger.info.assert_called()

    async def test_delete_product_no_images(self, product_service, mock_request, mock_product):
        mock_product.images = []
        product_service.product_repository.get_product_by_id.return_value = mock_product
        product_service.product_repository.delete_product.return_value = True
        
        result = await product_service.delete_product(mock_request, "test_id_123")
        
        assert result is None
        product_service.image_client.delete_image.assert_not_called()

    async def test_add_product_images_success(self, product_service, mock_request, mock_product):
        product_service.product_repository.get_product_by_id.return_value = mock_product
        product_service.image_client.upload_images.return_value = [
            UploadResult(success=True, url="http://test.com/static/img/new1.jpg"),
            UploadResult(success=True, url="http://test.com/static/img/new2.jpg")
        ]
        product_service.product_repository.update_product_images.return_value = True
        
        # Create mock upload files properly
        file1 = MagicMock(spec=UploadFile)
        file1.filename = "new1.jpg"
        file1.file = BytesIO(b"content1")
        file1.read = AsyncMock(return_value=b"content1")
        file1.content_type = "image/jpeg"
        
        file2 = MagicMock(spec=UploadFile)
        file2.filename = "new2.jpg"
        file2.file = BytesIO(b"content2")
        file2.read = AsyncMock(return_value=b"content2")
        file2.content_type = "image/jpeg"
        
        result = await product_service.add_product_images(
            mock_request, 
            "test_id_123", 
            [file1, file2]
        )
        
        assert result["product_id"] == "test_id_123"
        assert result["added_count"] == 2
        assert result["failed_count"] == 0
        assert result["total_images"] == 3  # original 1 + new 2
        product_service.image_client.upload_images.assert_called_once()
        product_service.product_repository.update_product_images.assert_called_once()

    async def test_add_product_images_product_not_found(self, product_service, mock_request):
        product_service.product_repository.get_product_by_id.return_value = None
        
        # Create mock upload file properly
        file = MagicMock(spec=UploadFile)
        file.filename = "test.jpg"
        file.file = BytesIO(b"content")
        file.read = AsyncMock(return_value=b"content")
        file.content_type = "image/jpeg"
        
        result = await product_service.add_product_images(
            mock_request, 
            "non_existent_id", 
            [file]
        )
        
        assert hasattr(result, 'status_code')
        assert result.status_code == 404

    async def test_remove_product_image_success(self, product_service, mock_request, mock_product):
        product_service.product_repository.get_product_by_id.return_value = mock_product
        product_service.product_repository.update_product_images.return_value = True
        product_service.image_client.extract_file_id.return_value = "img1"
        product_service.image_client.delete_image.return_value = True
        
        result = await product_service.remove_product_image(
            mock_request, 
            "test_id_123", 
            "http://test.com/static/img/img1.jpg"
        )
        
        assert result["product_id"] == "test_id_123"
        assert result["removed_image"] == "http://test.com/static/img/img1.jpg"
        product_service.product_repository.update_product_images.assert_called_once()
        product_service.image_client.delete_image.assert_called_once_with("img1")

    async def test_remove_product_image_not_in_product(self, product_service, mock_request, mock_product):
        product_service.product_repository.get_product_by_id.return_value = mock_product
        
        result = await product_service.remove_product_image(
            mock_request, 
            "test_id_123", 
            "http://test.com/static/img/nonexistent.jpg"
        )
        
        assert hasattr(result, 'status_code')
        assert result.status_code == 404

    async def test_update_product_tags_success(self, product_service, mock_request):
        mock_updated_product = ProductDB(
            id="test_id_123",
            name="Test Product",
            price=99.99,
            stock=10,
            tags=["new_tag1", "new_tag2"],
            images=[],
            created_at=datetime(2024, 1, 1, 0, 0, 0),
            updated_at=datetime(2024, 1, 1, 0, 0, 0)
        )
        
        product_service.product_repository.update_product.return_value = mock_updated_product
        
        tag_data = pydantic_models.ProductTagUpdate(tags=["new_tag1", "new_tag2"])
        
        result = await product_service.update_product_tags(mock_request, "test_id_123", tag_data)
        
        assert result["product_id"] == "test_id_123"
        assert result["updated_tags"] == ["new_tag1", "new_tag2"]
        product_service.product_repository.update_product.assert_called_once()

    async def test_cleanup_product_images_success(self, product_service, mock_request, mock_product):
        mock_product.images = [
            "http://test.com/static/img/valid.jpg",
            "http://test.com/static/img/invalid.jpg"
        ]
        product_service.product_repository.get_product_by_id.return_value = mock_product
        product_service.image_client.validate_image.side_effect = [True, False]
        product_service.product_repository.update_product_images.return_value = True
        
        result = await product_service.cleanup_product_images(mock_request, "test_id_123")
        
        assert result["product_id"] == "test_id_123"
        assert result["valid_images"] == 1
        assert result["invalid_images_removed"] == 1
        assert "http://test.com/static/img/invalid.jpg" in result["invalid_image_urls"]
        assert product_service.image_client.validate_image.call_count == 2
        product_service.product_repository.update_product_images.assert_called_once_with(
            "test_id_123", ["http://test.com/static/img/valid.jpg"]
        )

    async def test_update_inventory_success(self, product_service, mock_request):
        mock_updated_product = ProductDB(
            id="test_id_123",
            name="Test Product",
            price=99.99,
            stock=25,
            description="Test Description",
            created_at=datetime(2024, 1, 1, 0, 0, 0),
            updated_at=datetime(2024, 1, 1, 0, 0, 0)
        )
        
        product_service.product_repository.update_inventory.return_value = mock_updated_product
        
        inventory_data = pydantic_models.InventoryUpdate(stock=25)
        
        result = await product_service.update_inventory(mock_request, "test_id_123", inventory_data)
        
        assert result.id == "test_id_123"
        assert result.stock == 25
        product_service.product_repository.update_inventory.assert_called_once_with("test_id_123", 25)

    async def test_service_close(self, product_service):
        await product_service.close()
        product_service.image_client.close.assert_called_once()

@pytest.mark.asyncio
class TestImageClientIntegration:
    @patch('services.product_services.ProductImageClient')
    async def test_get_image_client_from_env(self, MockImageClient):
        with patch.dict('os.environ', {
            'STATIC_SERVICE_URL': 'http://localhost:8005/api/static',
            'IMAGE_CLIENT_TIMEOUT': '60.0',
            'IMAGE_CLIENT_MAX_CONCURRENT': '5'
        }):
            client = get_image_client()
            MockImageClient.assert_called_once()
            call_kwargs = MockImageClient.call_args.kwargs
            assert call_kwargs['base_url'] == 'http://static-service:8000'
            assert call_kwargs['timeout'] == 60.0
            assert call_kwargs['max_concurrent'] == 5

    @patch('services.product_services.ProductImageClient')
    async def test_get_image_client_defaults(self, MockImageClient):
        with patch.dict('os.environ', {}, clear=True):
            client = get_image_client()
            MockImageClient.assert_called_once()
            call_kwargs = MockImageClient.call_args.kwargs
            assert call_kwargs['base_url'] == 'http://localhost:8005/api/static'
            assert call_kwargs['timeout'] == 30.0
            assert call_kwargs['max_concurrent'] == 10

@pytest.mark.asyncio
class TestProductServiceErrorScenarios:
    async def test_create_product_duplicate_name(self, product_service, mock_request):
        product_data = pydantic_models.ProductRequest(
            name="Existing Product",
            price=99.99,
            stock=10,
            description="Test Description",
            tags=[],
            images=[]
        )
        
        product_service.product_repository.create_product.return_value = None
        
        result = await product_service.create_product(mock_request, product_data)
        
        assert hasattr(result, 'status_code')
        assert result.status_code == 409
        assert "Conflict" in result.body.decode()

    async def test_update_product_not_found(self, product_service, mock_request):
        product_service.product_repository.update_product.return_value = None
        
        update_data = pydantic_models.ProductRequest(
            name="Updated Product",
            price=149.99,
            stock=15,
            description="Updated Description",
            tags=[],
            images=[]
        )
        
        result = await product_service.update_product(mock_request, "non_existent_id", update_data)
        
        assert hasattr(result, 'status_code')
        assert result.status_code == 404
        assert "Not Found" in result.body.decode()

    async def test_patch_product_not_found(self, product_service, mock_request):
        product_service.product_repository.update_product.return_value = None
        
        patch_data = pydantic_models.ProductPatch(price=199.99)
        
        result = await product_service.patch_product(mock_request, "non_existent_id", patch_data)
        
        assert hasattr(result, 'status_code')
        assert result.status_code == 404
        assert "Not Found" in result.body.decode()

    async def test_delete_product_not_found(self, product_service, mock_request):
        product_service.product_repository.delete_product.return_value = False
        
        result = await product_service.delete_product(mock_request, "non_existent_id")
        
        assert hasattr(result, 'status_code')
        assert result.status_code == 404
        assert "Not Found" in result.body.decode()

    async def test_update_inventory_not_found(self, product_service, mock_request):
        product_service.product_repository.update_inventory.return_value = None
        
        inventory_data = pydantic_models.InventoryUpdate(stock=25)
        
        result = await product_service.update_inventory(mock_request, "non_existent_id", inventory_data)
        
        assert hasattr(result, 'status_code')
        assert result.status_code == 404
        assert "Not Found" in result.body.decode()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])