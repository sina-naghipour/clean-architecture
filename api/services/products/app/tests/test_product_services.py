import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request
from fastapi.responses import JSONResponse

from services.product_services import ProductService
from database import pydantic_models
from database.database_models import ProductDB, ImageDB
from datetime import datetime
from services.product_helpers import create_problem_response

@pytest.fixture
def mock_logger():
    return Mock()

@pytest.fixture
def mock_product_repository():
    repo = Mock()
    repo.create_product = AsyncMock()
    repo.get_product_by_id = AsyncMock()
    repo.get_product_by_name = AsyncMock()
    repo.list_products = AsyncMock()
    repo.count_products = AsyncMock()
    repo.update_product = AsyncMock()
    repo.delete_product = AsyncMock()
    repo.update_inventory = AsyncMock()
    repo.add_image_to_product = AsyncMock()
    repo.remove_image_from_product = AsyncMock()
    repo.set_primary_image = AsyncMock()
    return repo

@pytest.fixture
def mock_image_repository():
    repo = Mock()
    repo.get_image_by_id = AsyncMock()
    return repo

@pytest.fixture
def product_service(mock_logger, mock_product_repository, mock_image_repository):
    service = ProductService(mock_logger)
    service.product_repository = mock_product_repository
    service.image_repository = mock_image_repository
    return service

@pytest.fixture
def mock_request():
    request = Mock(spec=Request)
    request.url = "http://testserver/api/products"
    return request

@pytest.fixture
def sample_product_db():
    return ProductDB(
        id="test_id_123",
        name="Test Product",
        price=99.99,
        stock=10,
        description="Test Description",
        tags=["electronics"],
        image_ids=["img_1", "img_2"],
        primary_image_id="img_1"
    )

@pytest.fixture
def sample_image_data():
    """Returns a proper ImageDB object for testing"""
    return ImageDB(
        id="img_1",
        product_id="test_id_123",
        filename="test_img.jpg",
        original_name="original.jpg",
        mime_type="image/jpeg",
        size=1024000,
        width=800,
        height=600,
        is_primary=True,
        uploaded_at=datetime.utcnow()
    )

@pytest.mark.asyncio
async def test_create_product_success(product_service, mock_request):
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
        description="Test Description",
        image_ids=[],
        primary_image_id=None
    )
    
    product_service.product_repository.create_product.return_value = mock_product
    
    result = await product_service.create_product(mock_request, product_data)
    
    assert isinstance(result, JSONResponse)
    assert result.status_code == 201
    
    product_service.product_repository.create_product.assert_called_once()
    product_service.logger.info.assert_called()

@pytest.mark.asyncio
async def test_get_product_success(product_service, mock_request, sample_product_db, sample_image_data):
    # Configure the mock to return the sample product
    product_service.product_repository.get_product_by_id.return_value = sample_product_db
    
    # Configure the image repository mock to return actual ImageDB objects
    # Use side_effect to return different values based on input
    async def get_image_side_effect(image_id):
        if image_id == "img_1":
            return sample_image_data
        elif image_id == "img_2":
            return ImageDB(
                id="img_2",
                product_id="test_id_123",
                filename="test_img2.jpg",
                original_name="original2.jpg",
                mime_type="image/jpeg",
                size=512000,
                width=400,
                height=300,
                is_primary=False,
                uploaded_at=datetime.utcnow()
            )
        return None
    
    product_service.image_repository.get_image_by_id.side_effect = get_image_side_effect
    
    result = await product_service.get_product(mock_request, "test_id_123")
    
    # Check result is ProductResponse (not JSONResponse for errors)
    assert hasattr(result, 'id')
    assert result.id == "test_id_123"
    assert result.name == "Test Product"
    assert result.price == 99.99
    assert result.images is not None
    assert len(result.images) == 2
    assert result.primary_image_id == "img_1"
    
    product_service.product_repository.get_product_by_id.assert_called_once_with("test_id_123")
    assert product_service.image_repository.get_image_by_id.call_count == 2

@pytest.mark.asyncio
async def test_get_product_no_images(product_service, mock_request):
    product_without_images = ProductDB(
        id="test_id_123",
        name="Test Product",
        price=99.99,
        stock=10,
        description="Test Description",
        image_ids=[],
        primary_image_id=None
    )
    
    product_service.product_repository.get_product_by_id.return_value = product_without_images
    
    result = await product_service.get_product(mock_request, "test_id_123")
    
    assert hasattr(result, 'id')
    assert result.id == "test_id_123"
    assert result.images == []
    assert result.primary_image_id is None
    
    product_service.image_repository.get_image_by_id.assert_not_called()

@pytest.mark.asyncio
async def test_get_product_image_not_found(product_service, mock_request, sample_product_db):
    product_service.product_repository.get_product_by_id.return_value = sample_product_db
    product_service.image_repository.get_image_by_id.return_value = None
    
    result = await product_service.get_product(mock_request, "test_id_123")
    
    assert hasattr(result, 'id')
    assert result.id == "test_id_123"
    assert result.images == []  # Should be empty since no images found
    assert result.primary_image_id == "img_1"

@pytest.mark.asyncio
async def test_get_product_not_found(product_service, mock_request):
    product_service.product_repository.get_product_by_id.return_value = None
    
    result = await product_service.get_product(mock_request, "non_existent_id")
    
    assert isinstance(result, JSONResponse)
    assert result.status_code == 404
    assert "Not Found" in result.body.decode()

@pytest.mark.asyncio
async def test_list_products_success(product_service, mock_request):
    mock_products = [
        ProductDB(
            id="prod_1",
            name="Product 1",
            price=99.99,
            stock=10,
            description="Description 1",
            image_ids=["img_1"],
            primary_image_id="img_1"
        ),
        ProductDB(
            id="prod_2",
            name="Product 2",
            price=199.99,
            stock=5,
            description="Description 2",
            image_ids=[],
            primary_image_id=None
        )
    ]
    
    mock_image = ImageDB(
        id="img_1",
        product_id="prod_1",
        filename="prod1_img.jpg",
        original_name="original.jpg",
        mime_type="image/jpeg",
        size=1024000,
        width=800,
        height=600,
        is_primary=True,
        uploaded_at=datetime.utcnow()
    )
    
    product_service.product_repository.list_products.return_value = mock_products
    product_service.product_repository.count_products.return_value = 2
    
    # Configure image repository to return the mock image
    async def get_image_side_effect(image_id):
        if image_id == "img_1":
            return mock_image
        return None
    
    product_service.image_repository.get_image_by_id.side_effect = get_image_side_effect
    
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
    assert len(result.items[0].images) == 1
    assert result.items[0].primary_image_id == "img_1"
    
    assert result.items[1].name == "Product 2"
    assert result.items[1].images == []
    assert result.items[1].primary_image_id is None
    
    product_service.product_repository.list_products.assert_called_with(
        skip=0, limit=10, search_query=None
    )

@pytest.mark.asyncio
async def test_list_products_with_search(product_service, mock_request):
    product_service.product_repository.list_products.return_value = []
    product_service.product_repository.count_products.return_value = 0
    
    query_params = pydantic_models.ProductQueryParams(
        page=1,
        page_size=10,
        q="laptop"
    )
    
    result = await product_service.list_products(mock_request, query_params)
    
    assert result.total == 0
    assert result.items == []
    
    product_service.product_repository.list_products.assert_called_with(
        skip=0, limit=10, search_query="laptop"
    )

@pytest.mark.asyncio
async def test_list_products_pagination(product_service, mock_request):
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

@pytest.mark.asyncio
async def test_update_product_success(product_service, mock_request, sample_product_db, sample_image_data):
    # Configure the product repository to return the updated product
    product_service.product_repository.update_product.return_value = sample_product_db
    
    # Configure the image repository to return actual ImageDB objects
    async def get_image_side_effect(image_id):
        if image_id == "img_1":
            return sample_image_data
        elif image_id == "img_2":
            return ImageDB(
                id="img_2",
                product_id="test_id_123",
                filename="test_img2.jpg",
                original_name="original2.jpg",
                mime_type="image/jpeg",
                size=512000,
                width=400,
                height=300,
                is_primary=False,
                uploaded_at=datetime.utcnow()
            )
        return None
    
    product_service.image_repository.get_image_by_id.side_effect = get_image_side_effect
    
    update_data = pydantic_models.ProductRequest(
        name="Updated Product",
        price=149.99,
        stock=15,
        description="Updated Description"
    )
    
    result = await product_service.update_product(mock_request, "test_id_123", update_data)
    
    # Check that we got a ProductResponse, not an error
    assert hasattr(result, 'name')
    assert result.name == "Test Product"  # Should be from sample_product_db
    assert result.price == 99.99
    assert result.stock == 10
    
    product_service.product_repository.update_product.assert_called_once()

@pytest.mark.asyncio
async def test_update_product_not_found(product_service, mock_request):
    product_service.product_repository.update_product.return_value = None
    
    update_data = pydantic_models.ProductRequest(
        name="Updated Product",
        price=149.99,
        stock=15,
        description="Updated Description"
    )
    
    result = await product_service.update_product(mock_request, "non_existent_id", update_data)
    
    assert isinstance(result, JSONResponse)
    assert result.status_code == 404
    assert "Not Found" in result.body.decode()

@pytest.mark.asyncio
async def test_patch_product_success(product_service, mock_request, sample_product_db, sample_image_data):
    # Configure the product repository to return the patched product
    product_service.product_repository.update_product.return_value = sample_product_db
    
    # Configure the image repository to return actual ImageDB objects
    async def get_image_side_effect(image_id):
        if image_id == "img_1":
            return sample_image_data
        elif image_id == "img_2":
            return ImageDB(
                id="img_2",
                product_id="test_id_123",
                filename="test_img2.jpg",
                original_name="original2.jpg",
                mime_type="image/jpeg",
                size=512000,
                width=400,
                height=300,
                is_primary=False,
                uploaded_at=datetime.utcnow()
            )
        return None
    
    product_service.image_repository.get_image_by_id.side_effect = get_image_side_effect
    
    patch_data = pydantic_models.ProductPatch(price=199.99)
    
    result = await product_service.patch_product(mock_request, "test_id_123", patch_data)
    
    assert hasattr(result, 'price')
    assert result.price == 99.99  # Should be from sample_product_db
    assert result.name == "Test Product"
    
    product_service.product_repository.update_product.assert_called_once()

@pytest.mark.asyncio
async def test_patch_product_not_found(product_service, mock_request):
    product_service.product_repository.update_product.return_value = None
    
    patch_data = pydantic_models.ProductPatch(price=199.99)
    
    result = await product_service.patch_product(mock_request, "non_existent_id", patch_data)
    
    assert isinstance(result, JSONResponse)
    assert result.status_code == 404
    assert "Not Found" in result.body.decode()

@pytest.mark.asyncio
async def test_delete_product_success(product_service, mock_request, sample_product_db):
    product_service.product_repository.get_product_by_id.return_value = sample_product_db
    product_service.product_repository.delete_product.return_value = True
    
    with patch('services.image_services.ImageService') as mock_image_service_class:
        mock_image_service = Mock()
        mock_image_service.delete_product_image = AsyncMock()
        mock_image_service_class.return_value = mock_image_service
        
        result = await product_service.delete_product(mock_request, "test_id_123")
        
        assert result is None
        product_service.product_repository.delete_product.assert_called_once_with("test_id_123")
        product_service.logger.info.assert_called()

@pytest.mark.asyncio
async def test_delete_product_not_found(product_service, mock_request):
    product_service.product_repository.delete_product.return_value = False
    
    result = await product_service.delete_product(mock_request, "non_existent_id")
    
    assert isinstance(result, JSONResponse)
    assert result.status_code == 404
    assert "Not Found" in result.body.decode()

@pytest.mark.asyncio
async def test_delete_product_with_images_error(product_service, mock_request, sample_product_db):
    product_service.product_repository.get_product_by_id.return_value = sample_product_db
    product_service.product_repository.delete_product.return_value = True
    
    with patch('services.image_services.ImageService') as mock_image_service_class:
        mock_image_service = Mock()
        mock_image_service.delete_product_image = AsyncMock(side_effect=Exception("Image delete failed"))
        mock_image_service_class.return_value = mock_image_service
        
        result = await product_service.delete_product(mock_request, "test_id_123")
        
        assert result is None
        product_service.logger.error.assert_called()

@pytest.mark.asyncio
async def test_update_inventory_success(product_service, mock_request):
    mock_updated_product = ProductDB(
        id="test_id_123",
        name="Test Product",
        price=99.99,
        stock=25,
        description="Test Description",
        image_ids=[],
        primary_image_id=None
    )
    
    product_service.product_repository.update_inventory.return_value = mock_updated_product
    
    inventory_data = pydantic_models.InventoryUpdate(stock=25)
    
    result = await product_service.update_inventory(mock_request, "test_id_123", inventory_data)
    
    assert result.id == "test_id_123"
    assert result.stock == 25
    
    product_service.product_repository.update_inventory.assert_called_once_with("test_id_123", 25)

@pytest.mark.asyncio
async def test_update_inventory_not_found(product_service, mock_request):
    product_service.product_repository.update_inventory.return_value = None
    
    inventory_data = pydantic_models.InventoryUpdate(stock=25)
    
    result = await product_service.update_inventory(mock_request, "non_existent_id", inventory_data)
    
    assert isinstance(result, JSONResponse)
    assert result.status_code == 404
    assert "Not Found" in result.body.decode()

@pytest.mark.asyncio
async def test_backward_compatibility_empty_image_fields(product_service, mock_request):
    product_without_image_fields = ProductDB(
        id="old_product",
        name="Old Product",
        price=50.0,
        stock=5,
        description="Old product without image fields"
    )
    
    product_service.product_repository.get_product_by_id.return_value = product_without_image_fields
    
    result = await product_service.get_product(mock_request, "old_product")
    
    assert hasattr(result, 'id')
    assert result.id == "old_product"
    assert result.images == []
    assert result.primary_image_id is None

@pytest.mark.asyncio
async def test_product_response_structure(product_service, mock_request, sample_product_db, sample_image_data):
    product_service.product_repository.get_product_by_id.return_value = sample_product_db
    product_service.image_repository.get_image_by_id.return_value = sample_image_data
    
    result = await product_service.get_product(mock_request, "test_id_123")
    
    assert hasattr(result, 'id')
    assert hasattr(result, 'name')
    assert hasattr(result, 'price')
    assert hasattr(result, 'stock')
    assert hasattr(result, 'description')
    assert hasattr(result, 'images')
    assert hasattr(result, 'primary_image_id')
    
    assert isinstance(result.images, list)
    if result.images:
        image = result.images[0]
        assert hasattr(image, 'id')
        assert hasattr(image, 'url')
        assert hasattr(image, 'is_primary')
        assert hasattr(image, 'width')
        assert hasattr(image, 'height')

if __name__ == "__main__":
    pytest.main([__file__, "-v"])