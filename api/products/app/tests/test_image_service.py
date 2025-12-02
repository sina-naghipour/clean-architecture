import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import UploadFile, HTTPException
from pathlib import Path
import io

from services.image_services import ImageService
from repositories.image_repository import ImageRepository
from repositories.product_repository import ProductRepository
from database.database_models import ProductDB, ImageDB
from database import pydantic_models


@pytest.fixture
def mock_image_repository():
    repo = Mock(spec=ImageRepository)
    repo.create_image = AsyncMock()
    repo.get_image_by_id = AsyncMock()
    repo.get_images_by_product_id = AsyncMock()
    repo.set_primary_image = AsyncMock()
    repo.delete_image = AsyncMock()
    return repo


@pytest.fixture
def mock_product_repository():
    repo = Mock(spec=ProductRepository)
    repo.get_product_by_id = AsyncMock()
    repo.add_image_to_product = AsyncMock()
    repo.remove_image_from_product = AsyncMock()
    repo.set_primary_image = AsyncMock()
    return repo


@pytest.fixture
def image_service(mock_image_repository, mock_product_repository):
    """Fixture for ImageService with mocked dependencies"""
    with patch('services.image_services.magic.Magic') as mock_magic:
        mock_magic_instance = Mock()
        mock_magic_instance.from_buffer.return_value = "image/jpeg"
        mock_magic.return_value = mock_magic_instance
        
        service = ImageService(
            image_repository=mock_image_repository,
            product_repository=mock_product_repository
        )
        yield service


@pytest.fixture
def sample_jpeg_content():
    return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01' + b'a' * 1000


@pytest.fixture
def mock_upload_file(sample_jpeg_content):
    file = Mock(spec=UploadFile)
    file.filename = "test.jpg"
    file.read = AsyncMock(return_value=sample_jpeg_content)
    return file


@pytest.fixture
def mock_product():
    return ProductDB(
        id="prod_123",
        name="Test Product",
        price=99.99,
        stock=10,
        description="Test Description",
        tags=["electronics"],
        image_ids=[],
        primary_image_id=None
    )


@pytest.fixture
def mock_image():
    return ImageDB(
        id="img_456",
        product_id="prod_123",
        filename="prod_123_abc123.jpg",
        original_name="test.jpg",
        mime_type="image/jpeg",
        size=1024000,
        width=800,
        height=600,
        is_primary=True
    )


@pytest.mark.asyncio
async def test_upload_product_image_success(image_service, mock_product_repository, mock_image_repository, mock_upload_file, mock_product, mock_image):
    mock_product_repository.get_product_by_id.return_value = mock_product
    mock_image_repository.create_image.return_value = mock_image
    mock_image_repository.set_primary_image.return_value = True
    
    mock_img = Mock()
    mock_img.size = (800, 600)
    
    with patch('PIL.Image.open') as mock_open:
        mock_open.return_value.__enter__.return_value = mock_img
        
        with patch('builtins.open'):
            with patch('os.rename'):
                with patch.object(Path, 'mkdir'):
                    result = await image_service.upload_product_image(
                        "prod_123", mock_upload_file, is_primary=True
                    )
    
    assert result is not None
    assert result.id == "img_456"
    assert result.product_id == "prod_123"
    assert result.is_primary == True
    
    mock_product_repository.get_product_by_id.assert_called_once_with("prod_123")
    mock_product_repository.add_image_to_product.assert_called_once_with("prod_123", "img_456")
    mock_product_repository.set_primary_image.assert_called_once_with("prod_123", "img_456")
    mock_image_repository.set_primary_image.assert_called_once_with("prod_123", "img_456")
    
    
    mock_product_repository.get_product_by_id.assert_called_once_with("prod_123")
    mock_product_repository.add_image_to_product.assert_called_once_with("prod_123", "img_456")
    mock_product_repository.set_primary_image.assert_called_once_with("prod_123", "img_456")
    mock_image_repository.set_primary_image.assert_called_once_with("prod_123", "img_456")


@pytest.mark.asyncio
async def test_upload_product_image_product_not_found(image_service, mock_product_repository, mock_upload_file):
    """Test image upload when product doesn't exist"""
    mock_product_repository.get_product_by_id.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await image_service.upload_product_image("prod_999", mock_upload_file)
    
    assert exc_info.value.status_code == 404
    assert "Product not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_upload_product_image_file_too_large(image_service, mock_product_repository, mock_product, mock_upload_file):
    """Test image upload with file exceeding size limit"""
    mock_product_repository.get_product_by_id.return_value = mock_product
    
    large_content = b'a' * (6 * 1024 * 1024)
    mock_upload_file.read.return_value = large_content
    
    with pytest.raises(HTTPException) as exc_info:
        await image_service.upload_product_image("prod_123", mock_upload_file)
    
    assert exc_info.value.status_code == 413
    assert "File size exceeds" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_upload_product_image_invalid_format(image_service, mock_product_repository, mock_product, mock_upload_file):
    """Test image upload with non-image file"""
    mock_product_repository.get_product_by_id.return_value = mock_product
    
    with patch('services.image_services.magic.Magic') as mock_magic:
        mock_magic_instance = Mock()
        mock_magic_instance.from_buffer.return_value = "application/pdf"
        mock_magic.return_value = mock_magic_instance
        
        with pytest.raises(HTTPException) as exc_info:
            await image_service.upload_product_image("prod_123", mock_upload_file)
    
    assert exc_info.value.status_code == 415
    assert "Invalid image format" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_product_images_success(image_service, mock_product_repository, mock_image_repository, mock_product, mock_image):
    """Test retrieving product images successfully"""
    mock_product_repository.get_product_by_id.return_value = mock_product
    mock_image_repository.get_images_by_product_id.return_value = [mock_image]
    
    results = await image_service.get_product_images("prod_123")
    
    assert len(results) == 1
    assert results[0].id == "img_456"
    assert results[0].url == "/static/img/products/prod_123/prod_123_abc123.jpg"
    
    mock_product_repository.get_product_by_id.assert_called_once_with("prod_123")
    mock_image_repository.get_images_by_product_id.assert_called_once_with("prod_123")


@pytest.mark.asyncio
async def test_get_product_images_product_not_found(image_service, mock_product_repository):
    """Test retrieving images for non-existent product"""
    mock_product_repository.get_product_by_id.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await image_service.get_product_images("prod_999")
    
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_product_image_success(image_service, mock_product_repository, mock_image_repository, mock_product, mock_image):
    """Test successful image deletion"""
    mock_product_repository.get_product_by_id.return_value = mock_product
    mock_image_repository.get_image_by_id.return_value = mock_image
    mock_image_repository.delete_image.return_value = True
    
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'unlink'):
            result = await image_service.delete_product_image("prod_123", "img_456")
    
    assert result is True
    mock_product_repository.remove_image_from_product.assert_called_once_with("prod_123", "img_456")


@pytest.mark.asyncio
async def test_delete_product_image_product_not_found(image_service, mock_product_repository):
    """Test image deletion for non-existent product"""
    mock_product_repository.get_product_by_id.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await image_service.delete_product_image("prod_999", "img_456")
    
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_product_image_image_not_found(image_service, mock_product_repository, mock_image_repository, mock_product):
    """Test deletion of non-existent image"""
    mock_product_repository.get_product_by_id.return_value = mock_product
    mock_image_repository.get_image_by_id.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await image_service.delete_product_image("prod_123", "img_999")
    
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_product_image_wrong_product(image_service, mock_product_repository, mock_image_repository, mock_product):
    """Test deletion of image belonging to different product"""
    mock_product_repository.get_product_by_id.return_value = mock_product
    
    wrong_product_image = ImageDB(
        id="img_456",
        product_id="prod_999",
        filename="wrong.jpg",
        original_name="wrong.jpg",
        mime_type="image/jpeg",
        size=1024000,
        width=800,
        height=600,
        is_primary=False
    )
    mock_image_repository.get_image_by_id.return_value = wrong_product_image
    
    with pytest.raises(HTTPException) as exc_info:
        await image_service.delete_product_image("prod_123", "img_456")
    
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_set_primary_image_success(image_service, mock_product_repository, mock_image_repository, mock_product, mock_image):
    """Test successful setting of primary image"""
    updated_product = ProductDB(
        id="prod_123",
        name="Test Product",
        price=99.99,
        stock=10,
        description="Test Description",
        tags=["electronics"],
        image_ids=["img_456", "img_789"],
        primary_image_id=None
    )
    
    mock_product_repository.get_product_by_id.return_value = updated_product
    mock_image_repository.set_primary_image.return_value = True
    mock_image_repository.get_image_by_id.return_value = mock_image
    
    result = await image_service.set_primary_image("prod_123", "img_456")
    
    assert result is not None
    assert result.id == "img_456"
    assert result.is_primary is True
    
    mock_product_repository.set_primary_image.assert_called_once_with("prod_123", "img_456")
    mock_image_repository.set_primary_image.assert_called_once_with("prod_123", "img_456")


@pytest.mark.asyncio
async def test_set_primary_image_product_not_found(image_service, mock_product_repository):
    """Test setting primary image for non-existent product"""
    mock_product_repository.get_product_by_id.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await image_service.set_primary_image("prod_999", "img_456")
    
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_set_primary_image_image_not_in_product(image_service, mock_product_repository, mock_product):
    """Test setting non-product image as primary"""
    mock_product_repository.get_product_by_id.return_value = mock_product
    
    with pytest.raises(HTTPException) as exc_info:
        await image_service.set_primary_image("prod_123", "img_999")
    
    assert exc_info.value.status_code == 400
    assert "Image does not belong" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_set_primary_image_failed(image_service, mock_product_repository, mock_image_repository, mock_product):
    """Test failed primary image setting"""
    updated_product = ProductDB(
        id="prod_123",
        name="Test Product",
        price=99.99,
        stock=10,
        description="Test Description",
        tags=["electronics"],
        image_ids=["img_456"],
        primary_image_id=None
    )
    
    mock_product_repository.get_product_by_id.return_value = updated_product
    mock_image_repository.set_primary_image.return_value = False
    
    with pytest.raises(HTTPException) as exc_info:
        await image_service.set_primary_image("prod_123", "img_456")
    
    assert exc_info.value.status_code == 400
    assert "Failed to set primary image" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_validate_file_path_security(image_service):
    """Test file path validation for security"""
    image_service.base_storage_path = Path("/static/img")
    
    valid_path = Path("/static/img/products/prod_123/test.jpg")
    assert image_service._validate_file_path(valid_path) is True
    
    traversal_path = Path("/static/img/products/prod_123/../other/test.jpg")
    assert image_service._validate_file_path(traversal_path) is False
    
    absolute_path = Path("C:\\windows\\system32\\file.jpg")
    assert image_service._validate_file_path(absolute_path) is False


def test_generate_server_filename(image_service):
    """Test server filename generation"""
    product_id = "prod_123"
    mime_type = "image/jpeg"
    
    filename = image_service._generate_server_filename(product_id, mime_type)
    
    assert filename.startswith("prod_123_")
    assert filename.endswith(".jpg")
    assert len(filename) > len("prod_123_.jpg")


def test_allowed_mime_types(image_service):
    """Test allowed MIME types configuration"""
    assert "image/jpeg" in image_service.allowed_mime_types
    assert "image/png" in image_service.allowed_mime_types
    assert "image/webp" in image_service.allowed_mime_types
    assert image_service.allowed_mime_types["image/jpeg"] == ".jpg"
    assert image_service.allowed_mime_types["image/png"] == ".png"
    assert image_service.allowed_mime_types["image/webp"] == ".webp"


def test_max_file_size(image_service):
    """Test maximum file size configuration"""
    assert image_service.max_file_size == 5 * 1024 * 1024

@pytest.mark.asyncio
async def test_upload_product_images_batch_success(image_service, mock_product_repository, mock_image_repository):
    """Test batch upload with all files successful."""
    product_id = "prod123"
    mock_product = MagicMock()
    mock_product.id = product_id
    mock_product_repository.get_product_by_id.return_value = mock_product
    
    mock_file1 = MagicMock()
    mock_file1.filename = "test1.jpg"
    mock_file1.read = AsyncMock(return_value=b"fake image data 1")
    
    mock_file2 = MagicMock()
    mock_file2.filename = "test2.png"
    mock_file2.read = AsyncMock(return_value=b"fake image data 2")
    
    mock_image = MagicMock()
    mock_image.id = "img123"
    mock_image.filename = "generated.jpg"
    mock_image.url = "/static/img/generated.jpg"
    mock_image.is_primary = False
    mock_image.uploaded_at = "2023-01-01T00:00:00"
    
    image_service.upload_product_image = AsyncMock(return_value=mock_image)
    
    result = await image_service.upload_product_images_batch(
        product_id=product_id,
        upload_files=[mock_file1, mock_file2],
        make_primary_first=True
    )
    
    assert result["total"] == 2
    assert result["successful_count"] == 2
    assert len(result["success"]) == 2
    assert len(result["failed"]) == 0
    assert image_service.upload_product_image.call_args_list[0][1]['is_primary'] == True
    assert image_service.upload_product_image.call_args_list[1][1]['is_primary'] == False

@pytest.mark.asyncio
async def test_upload_product_images_batch_partial_failure(image_service, mock_product_repository):
    """Test batch upload with some files failing."""
    product_id = "prod123"
    mock_product = MagicMock()
    mock_product.id = product_id
    mock_product_repository.get_product_by_id.return_value = mock_product
    
    mock_file1 = MagicMock()
    mock_file1.filename = "test1.jpg"
    mock_file1.read = AsyncMock(return_value=b"fake image data 1")
    
    mock_file2 = MagicMock()
    mock_file2.filename = "test2.gif"
    mock_file2.read = AsyncMock(return_value=b"fake image data 2")
    
    mock_image = MagicMock()
    mock_image.id = "img123"
    
    from fastapi import HTTPException
    image_service.upload_product_image = AsyncMock(side_effect=[
        mock_image,
        HTTPException(status_code=415, detail="Invalid image format")
    ])
    
    result = await image_service.upload_product_images_batch(
        product_id=product_id,
        upload_files=[mock_file1, mock_file2]
    )
    
    assert result["total"] == 2
    assert result["successful_count"] == 1
    assert len(result["success"]) == 1
    assert len(result["failed"]) == 1
    assert result["failed"][0]["filename"] == "test2.gif"
    assert result["failed"][0]["error"] == "Invalid image format"

@pytest.mark.asyncio
async def test_upload_product_images_batch_product_not_found(image_service, mock_product_repository):
    """Test batch upload for non-existent product."""
    product_id = "nonexistent"
    mock_product_repository.get_product_by_id.return_value = None
    
    mock_file = MagicMock()
    mock_file.filename = "test.jpg"
    
    result = await image_service.upload_product_images_batch(
            product_id=product_id,
            upload_files=[mock_file]
    )
    assert result["successful_count"] == 0
    assert len(result["failed"]) == 1
    assert result["failed"][0]["status_code"] == 404
    
@pytest.mark.asyncio
async def test_upload_product_images_batch_empty_files(image_service):
    """Test batch upload with empty file list."""
    result = await image_service.upload_product_images_batch(
        product_id="prod123",
        upload_files=[]
    )
    
    assert result["total"] == 0
    assert result["successful_count"] == 0
    assert len(result["success"]) == 0
    assert len(result["failed"]) == 0
