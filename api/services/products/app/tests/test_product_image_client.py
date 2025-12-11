import pytest
import httpx
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from fastapi import UploadFile
from io import BytesIO
import json
import logging
from dotenv import load_dotenv
import os

load_dotenv()
STATIC_SERVICE_URL = os.getenv('STATIC_SERVICE_URL', 'http://statics:8005/api/static')
from services.product_image_client import ProductImageClient, UploadResult


@pytest.fixture
def mock_httpx_client():
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def image_client(mock_httpx_client):
    client = ProductImageClient(base_url=STATIC_SERVICE_URL)
    client.client = mock_httpx_client
    yield client
    # Cleanup
    asyncio.run(client.close())


@pytest.fixture
def sample_image_file():
    """Create a mock UploadFile for testing"""
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.jpg"
    mock_file.read = AsyncMock(return_value=b"fake image content")
    mock_file.content_type = "image/jpeg"
    return mock_file


@pytest.fixture
def sample_upload_response():
    return {
        "id": "abc123",
        "url": f"{STATIC_SERVICE_URL}/files/abc123.jpg",
        "filename": "test.jpg"
    }


class TestUploadImage:
    @pytest.mark.asyncio
    async def test_upload_image_success(self, image_client, mock_httpx_client, sample_image_file, sample_upload_response):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = sample_upload_response
        mock_httpx_client.post.return_value = mock_response
        
        result = await image_client.upload_image(sample_image_file, subdirectory="products")
        
        assert result.success is True
        assert result.url == f"{STATIC_SERVICE_URL}/files/abc123.jpg"
        assert result.error is None
        
        mock_httpx_client.post.assert_called_once()
        call_args = mock_httpx_client.post.call_args
        assert call_args[0][0] == f"{STATIC_SERVICE_URL}/files"
        assert "files" in call_args[1]
        assert "params" in call_args[1]
        assert call_args[1]["params"]["subdirectory"] == "products"

    @pytest.mark.asyncio
    async def test_upload_image_with_metadata(self, image_client, mock_httpx_client, sample_image_file):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"url": "test.jpg"}
        mock_httpx_client.post.return_value = mock_response
        
        metadata = {"product_id": "123", "is_primary": True}
        result = await image_client.upload_image(
            sample_image_file, 
            subdirectory="products",
            metadata=metadata
        )
        
        assert result.success is True
        
        call_args = mock_httpx_client.post.call_args
        params = call_args[1]["params"]
        assert "custom_metadata" in params
        loaded_metadata = json.loads(params["custom_metadata"])
        assert loaded_metadata == metadata

    @pytest.mark.asyncio
    async def test_upload_image_failure_400(self, image_client, mock_httpx_client, sample_image_file):
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Invalid file type"}
        mock_httpx_client.post.return_value = mock_response
        
        result = await image_client.upload_image(sample_image_file)
        
        assert result.success is False
        assert result.error == "Invalid file type"
        assert result.url is None

    @pytest.mark.asyncio
    async def test_upload_image_failure_500(self, image_client, mock_httpx_client, sample_image_file):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal server error"}
        mock_httpx_client.post.return_value = mock_response
        
        result = await image_client.upload_image(sample_image_file)
        
        assert result.success is False
        assert result.error == "Internal server error"

    @pytest.mark.asyncio
    async def test_upload_image_exception(self, image_client, mock_httpx_client, sample_image_file):
        mock_httpx_client.post.side_effect = Exception("Network error")
        
        result = await image_client.upload_image(sample_image_file)
        
        assert result.success is False
        assert "Network error" in result.error


class TestUploadImages:
    @pytest.mark.asyncio
    async def test_upload_images_multiple(self, image_client, mock_httpx_client):
        # Setup mock responses
        mock_response1 = Mock()
        mock_response1.status_code = 201
        mock_response1.json.return_value = {"url": "img1.jpg"}
        
        mock_response2 = Mock()
        mock_response2.status_code = 201
        mock_response2.json.return_value = {"url": "img2.jpg"}
        
        mock_httpx_client.post.side_effect = [mock_response1, mock_response2]
        
        # Create mock files
        file1 = MagicMock(spec=UploadFile)
        file1.filename = "img1.jpg"
        file1.read = AsyncMock(return_value=b"content1")
        file1.content_type = "image/jpeg"
        
        file2 = MagicMock(spec=UploadFile)
        file2.filename = "img2.jpg"
        file2.read = AsyncMock(return_value=b"content2")
        file2.content_type = "image/jpeg"
        
        results = await image_client.upload_images([file1, file2])
        
        assert len(results) == 2
        assert all(r.success for r in results)
        assert results[0].url == "img1.jpg"
        assert results[1].url == "img2.jpg"
        
        # Should make 2 calls
        assert mock_httpx_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_upload_images_with_concurrency_limit(self, image_client, mock_httpx_client):
        image_client.max_concurrent = 2
        
        # Create 4 mock responses
        mock_responses = []
        for i in range(4):
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"url": f"img{i}.jpg"}
            mock_responses.append(mock_response)
        
        mock_httpx_client.post.side_effect = mock_responses
        
        # Create 4 mock files
        files = []
        for i in range(4):
            mock_file = MagicMock(spec=UploadFile)
            mock_file.filename = f"img{i}.jpg"
            mock_file.read = AsyncMock(return_value=b"content")
            mock_file.content_type = "image/jpeg"
            files.append(mock_file)
        
        results = await image_client.upload_images(files)
        
        assert len(results) == 4
        assert all(r.success for r in results)
        # Concurrency should be limited to max_concurrent (2)

    @pytest.mark.asyncio
    async def test_upload_images_with_metadata_list(self, image_client, mock_httpx_client):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"url": "test.jpg"}
        mock_httpx_client.post.return_value = mock_response
        
        file1 = MagicMock(spec=UploadFile)
        file1.filename = "img1.jpg"
        file1.read = AsyncMock(return_value=b"content1")
        file1.content_type = "image/jpeg"
        
        file2 = MagicMock(spec=UploadFile)
        file2.filename = "img2.jpg"
        file2.read = AsyncMock(return_value=b"content2")
        file2.content_type = "image/jpeg"
        
        metadata_list = [
            {"product_id": "123"},
            {"product_id": "456"}
        ]
        
        results = await image_client.upload_images(
            [file1, file2],
            metadata_list=metadata_list
        )
        
        assert len(results) == 2
        # Check that metadata was passed correctly
        assert mock_httpx_client.post.call_count == 2


class TestDeleteImage:
    @pytest.mark.asyncio
    async def test_delete_image_success(self, image_client, mock_httpx_client):
        mock_response = Mock()
        mock_response.status_code = 204
        mock_httpx_client.delete.return_value = mock_response
        
        result = await image_client.delete_image("file123")
        
        assert result is True
        mock_httpx_client.delete.assert_called_once_with(
            f"{STATIC_SERVICE_URL}/files/file123"
        )

    @pytest.mark.asyncio
    async def test_delete_image_not_found(self, image_client, mock_httpx_client):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_httpx_client.delete.return_value = mock_response
        
        result = await image_client.delete_image("file123")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_image_failure(self, image_client, mock_httpx_client):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_httpx_client.delete.return_value = mock_response
        
        result = await image_client.delete_image("file123")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_image_exception(self, image_client, mock_httpx_client):
        mock_httpx_client.delete.side_effect = Exception("Network error")
        
        result = await image_client.delete_image("file123")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_images_multiple(self, image_client, mock_httpx_client):
        mock_response = Mock()
        mock_response.status_code = 204
        mock_httpx_client.delete.return_value = mock_response
        
        results = await image_client.delete_images(["file1", "file2", "file3"])
        
        assert len(results) == 3
        assert all(results)
        assert mock_httpx_client.delete.call_count == 3


class TestValidateImage:
    @pytest.mark.asyncio
    async def test_validate_static_image_success(self, image_client, mock_httpx_client):
        mock_response = Mock()
        mock_response.status_code = 200
        # Change this:
        mock_httpx_client.get.return_value = mock_response  # Not .head()
        
        result = await image_client.validate_image("/static/img/products/abc123.jpg")
        assert result is True
        
        # Verify the right URL is called
        mock_httpx_client.get.assert_called_once_with("http://statics:8005/files/abc123")

    @pytest.mark.asyncio
    async def test_validate_static_image_not_found(self, image_client, mock_httpx_client):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_httpx_client.head.return_value = mock_response
        
        result = await image_client.validate_image(
            "/static/img/products/abc123.jpg"
        )
        
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_external_url_success(self, image_client, mock_httpx_client):
        mock_response = Mock()
        mock_response.status_code = 200
        
        mock_httpx_client.get.return_value = mock_response
        
        result = await image_client.validate_image(
            "https://example.com/image.jpg"
        )
        
        assert result is True
        mock_httpx_client.get.assert_called_once_with(
            "https://example.com/image.jpg",
            timeout=5.0
        )

    @pytest.mark.asyncio
    async def test_validate_invalid_url(self, image_client, mock_httpx_client):
        mock_httpx_client.head.side_effect = Exception("Connection failed")
        
        result = await image_client.validate_image("invalid-url")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_non_static_non_http(self, image_client):
        result = await image_client.validate_image("/some/local/path.jpg")
        
        assert result is False


class TestExtractFileId:
    def test_extract_file_id_from_static_url(self, image_client):
        url = "https://example.com/static/img/abc123-def456.jpg"
        file_id = image_client.extract_file_id(url)
        
        assert file_id == "abc123-def456"

    def test_extract_file_id_with_query_params(self, image_client):
        url = "https://example.com/static/img/abc123.jpg?width=300&height=200"
        file_id = image_client.extract_file_id(url)
        
        assert file_id == "abc123"

    def test_extract_file_id_no_static_path(self, image_client):
        url = "https://example.com/images/abc123.jpg"
        file_id = image_client.extract_file_id(url)
        
        assert file_id is None

    def test_extract_file_id_malformed_url(self, image_client):
        url = "not-a-url"
        file_id = image_client.extract_file_id(url)
        
        assert file_id is None


class TestCleanupUnusedImages:
    @pytest.mark.asyncio
    async def test_cleanup_success(self, image_client, mock_httpx_client):
        # Mock metadata response
        mock_metadata_response = Mock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = {
            "files": [
                {"id": "file1", "url": "/static/img/file1.jpg"},
                {"id": "file2", "url": "/static/img/file2.jpg"},
                {"id": "file3", "url": "/static/img/file3.jpg"}
            ]
        }
        
        # Mock delete responses
        mock_delete_responses = [
            Mock(status_code=204),  # file2 deleted
            Mock(status_code=204)   # file3 deleted
        ]
        
        mock_httpx_client.get.return_value = mock_metadata_response
        mock_httpx_client.delete.side_effect = mock_delete_responses
        
        used_urls = [
            f"{STATIC_SERVICE_URL}/files/file1.jpg"  # Only file1 is used
        ]
        
        deleted_ids = await image_client.cleanup_unused_images(
            used_urls,
            subdirectory="products"
        )
        
        assert sorted(deleted_ids) == ["file1", "file2"]
        
        # Verify metadata call
        mock_httpx_client.get.assert_called_once_with(
            "http://statics:8005/metadata",
            params={"subdirectory": "products"}
        )
        
        # Verify delete calls for unused files
        assert mock_httpx_client.delete.call_count == 3
        delete_calls = mock_httpx_client.delete.call_args_list
        assert delete_calls[0][0][0] == "http://statics:8005/files/file1"
        assert delete_calls[1][0][0] == "http://statics:8005/files/file2"

    @pytest.mark.asyncio
    async def test_cleanup_no_unused_images(self, image_client, mock_httpx_client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "files": [
                {"id": "file1", "url": "/static/img/file1.jpg"}
            ]
        }
        mock_httpx_client.get.return_value = mock_response
        
        used_urls = [
            "http://test.com/static/img/file1.jpg"
        ]
        
        deleted_ids = await image_client.cleanup_unused_images(used_urls)
        
        assert deleted_ids == []
        mock_httpx_client.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_cleanup_metadata_failure(self, image_client, mock_httpx_client):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_httpx_client.get.return_value = mock_response
        
        deleted_ids = await image_client.cleanup_unused_images([])
        
        assert deleted_ids == []
        mock_httpx_client.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_cleanup_exception(self, image_client, mock_httpx_client):
        mock_httpx_client.get.side_effect = Exception("Network error")
        
        deleted_ids = await image_client.cleanup_unused_images([])
        
        assert deleted_ids == []


class TestClientInitialization:
    def test_client_default_logger(self):
        client = ProductImageClient(base_url=STATIC_SERVICE_URL)
        assert client.logger is not None
        assert client.logger.name == "services.product_image_client"

    def test_client_custom_logger(self):
        custom_logger = logging.getLogger("custom")
        client = ProductImageClient(
            base_url=STATIC_SERVICE_URL,
            logger=custom_logger
        )
        assert client.logger == custom_logger

    def test_client_timeout_config(self):
        client = ProductImageClient(
            base_url=STATIC_SERVICE_URL,
            timeout=60.0,
            max_concurrent=5
        )
        assert client.timeout == 60.0
        assert client.max_concurrent == 5

    @pytest.mark.asyncio
    async def test_client_close(self, mock_httpx_client):
        mock_client = AsyncMock()
        with patch('httpx.AsyncClient', return_value=mock_client):
            client = ProductImageClient(base_url=STATIC_SERVICE_URL)
            await client.close()
            mock_client.aclose.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])