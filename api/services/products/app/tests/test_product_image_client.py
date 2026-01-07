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
    client.http_client.client = mock_httpx_client
    yield client
    asyncio.run(client.close())


@pytest.fixture
def sample_image_file():
    mock_file = MagicMock()
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
        
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
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
        
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
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
        
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
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
        
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
            result = await image_client.upload_image(sample_image_file)
        
        assert result.success is False
        assert result.error == "Internal server error"

    @pytest.mark.asyncio
    async def test_upload_image_exception(self, image_client, mock_httpx_client, sample_image_file):
        mock_httpx_client.post.side_effect = Exception("Network error")
        
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
            result = await image_client.upload_image(sample_image_file)
        
        assert result.success is False
        assert "Network error" in result.error


class TestUploadImages:
    @pytest.mark.asyncio
    async def test_upload_images_multiple(self, image_client, mock_httpx_client):
        mock_response1 = Mock()
        mock_response1.status_code = 201
        mock_response1.json.return_value = {"url": "img1.jpg"}
        
        mock_response2 = Mock()
        mock_response2.status_code = 201
        mock_response2.json.return_value = {"url": "img2.jpg"}
        
        mock_httpx_client.post.side_effect = [mock_response1, mock_response2]
        
        file1 = MagicMock()
        file1.filename = "img1.jpg"
        file1.read = AsyncMock(return_value=b"content1")
        file1.content_type = "image/jpeg"
        
        file2 = MagicMock()
        file2.filename = "img2.jpg"
        file2.read = AsyncMock(return_value=b"content2")
        file2.content_type = "image/jpeg"
        
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
            results = await image_client.upload_images([file1, file2])
        
        assert len(results) == 2
        assert all(r.success for r in results)
        assert results[0].url == "img1.jpg"
        assert results[1].url == "img2.jpg"
        
        assert mock_httpx_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_upload_images_with_concurrency_limit(self, image_client, mock_httpx_client):
        image_client.max_concurrent = 2
        
        mock_responses = []
        for i in range(4):
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"url": f"img{i}.jpg"}
            mock_responses.append(mock_response)
        
        mock_httpx_client.post.side_effect = mock_responses
        
        files = []
        for i in range(4):
            mock_file = MagicMock()
            mock_file.filename = f"img{i}.jpg"
            mock_file.read = AsyncMock(return_value=b"content")
            mock_file.content_type = "image/jpeg"
            files.append(mock_file)
        
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
            results = await image_client.upload_images(files)
        
        assert len(results) == 4
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_upload_images_with_metadata_list(self, image_client, mock_httpx_client):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"url": "test.jpg"}
        mock_httpx_client.post.return_value = mock_response
        
        file1 = MagicMock()
        file1.filename = "img1.jpg"
        file1.read = AsyncMock(return_value=b"content1")
        file1.content_type = "image/jpeg"
        
        file2 = MagicMock()
        file2.filename = "img2.jpg"
        file2.read = AsyncMock(return_value=b"content2")
        file2.content_type = "image/jpeg"
        
        metadata_list = [
            {"product_id": "123"},
            {"product_id": "456"}
        ]
        
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
            results = await image_client.upload_images(
                [file1, file2],
                metadata_list=metadata_list
            )
        
        assert len(results) == 2
        assert mock_httpx_client.post.call_count == 2


class TestDeleteImage:
    @pytest.mark.asyncio
    async def test_delete_image_success(self, image_client, mock_httpx_client):
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
            mock_response = Mock()
            mock_response.status_code = 204
            image_client.http_client.delete = AsyncMock(return_value=mock_response)
            
            result = await image_client.delete_image("file123")
        
        assert result is True
        image_client.http_client.delete.assert_called_once_with(
            f"{STATIC_SERVICE_URL}/files/file123"
        )

    @pytest.mark.asyncio
    async def test_delete_image_not_found(self, image_client, mock_httpx_client):
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
            mock_response = Mock()
            mock_response.status_code = 404
            image_client.http_client.delete = AsyncMock(return_value=mock_response)
            
            result = await image_client.delete_image("file123")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_image_failure(self, image_client, mock_httpx_client):
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
            mock_response = Mock()
            mock_response.status_code = 500
            image_client.http_client.delete = AsyncMock(return_value=mock_response)
            
            result = await image_client.delete_image("file123")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_image_exception(self, image_client, mock_httpx_client):
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
            image_client.http_client.delete = AsyncMock(side_effect=Exception("Network error"))
            
            result = await image_client.delete_image("file123")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_images_multiple(self, image_client, mock_httpx_client):
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
            mock_response = Mock()
            mock_response.status_code = 204
            image_client.delete_image = AsyncMock(return_value=True)
            
            results = await image_client.delete_images(["file1", "file2", "file3"])
        
        assert len(results) == 3
        assert all(results)


class TestValidateImage:
    @pytest.mark.asyncio
    async def test_validate_static_image_success(self, image_client, mock_httpx_client):
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
            mock_response = Mock()
            mock_response.status_code = 200
            image_client.http_client.get = AsyncMock(return_value=mock_response)
            
            result = await image_client.validate_image("/static/img/products/abc123.jpg")
        
        assert result is True
        
        image_client.http_client.get.assert_called_once_with(
            f"{STATIC_SERVICE_URL}/files/abc123"
        )

    @pytest.mark.asyncio
    async def test_validate_static_image_not_found(self, image_client, mock_httpx_client):
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
            mock_response = Mock()
            mock_response.status_code = 404
            image_client.http_client.get = AsyncMock(return_value=mock_response)
            
            result = await image_client.validate_image(
                "/static/img/products/abc123.jpg"
            )
        
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_external_url_success(self, image_client, mock_httpx_client):
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_httpx_client.get.return_value = mock_response
            
            result = await image_client.validate_image(
                "https://example.com/image.jpg"
            )
        
        assert result is True
        mock_httpx_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_invalid_url(self, image_client, mock_httpx_client):
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
            mock_httpx_client.get.side_effect = Exception("Connection failed")
            
            result = await image_client.validate_image("invalid-url")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_non_static_non_http(self, image_client):
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
            result = await image_client.validate_image("/some/local/path.jpg")
        
        assert result is False


class TestExtractFileId:
    def test_extract_file_id_from_static_url(self, image_client):
        import services.product_image_client
        original_method = services.product_image_client.ProductImageClient.extract_file_id
        
        try:
            if hasattr(original_method, '__wrapped__'):
                services.product_image_client.ProductImageClient.extract_file_id = original_method.__wrapped__
            
            url = "https://example.com/static/img/abc123-def456.jpg"
            file_id = image_client.extract_file_id(url)
            
            assert file_id == "abc123-def456"
        finally:
            services.product_image_client.ProductImageClient.extract_file_id = original_method

    def test_extract_file_id_with_query_params(self, image_client):
        import services.product_image_client
        original_method = services.product_image_client.ProductImageClient.extract_file_id
        
        try:
            if hasattr(original_method, '__wrapped__'):
                services.product_image_client.ProductImageClient.extract_file_id = original_method.__wrapped__
            
            url = "https://example.com/static/img/abc123.jpg?width=300&height=200"
            file_id = image_client.extract_file_id(url)
            
            assert file_id == "abc123"
        finally:
            services.product_image_client.ProductImageClient.extract_file_id = original_method

    def test_extract_file_id_no_static_path(self, image_client):
        import services.product_image_client
        original_method = services.product_image_client.ProductImageClient.extract_file_id
        
        try:
            if hasattr(original_method, '__wrapped__'):
                services.product_image_client.ProductImageClient.extract_file_id = original_method.__wrapped__
            
            url = "https://example.com/images/abc123.jpg"
            file_id = image_client.extract_file_id(url)
            
            assert file_id is None
        finally:
            services.product_image_client.ProductImageClient.extract_file_id = original_method

    def test_extract_file_id_malformed_url(self, image_client):
        import services.product_image_client
        original_method = services.product_image_client.ProductImageClient.extract_file_id
        
        try:
            if hasattr(original_method, '__wrapped__'):
                services.product_image_client.ProductImageClient.extract_file_id = original_method.__wrapped__
            
            url = "not-a-url"
            file_id = image_client.extract_file_id(url)
            
            assert file_id is None
        finally:
            services.product_image_client.ProductImageClient.extract_file_id = original_method


class TestCleanupUnusedImages:
    @pytest.mark.asyncio
    async def test_cleanup_success(self, image_client):
        mock_metadata_response = Mock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = {
            "files": [
                {"id": "file1"},
                {"id": "file2"},
                {"id": "file3"}
            ]
        }
        
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
            with patch.object(image_client.http_client, 'get', AsyncMock(return_value=mock_metadata_response)):
                with patch.object(image_client, 'extract_file_id') as mock_extract:
                    def extract_side_effect(url):
                        if 'file1' in url:
                            return 'file1'
                        elif 'file2' in url:
                            return 'file2'
                        elif 'file3' in url:
                            return 'file3'
                        return None
                    mock_extract.side_effect = extract_side_effect
                    
                    with patch.object(image_client, 'delete_image', AsyncMock(side_effect=[True, True])) as mock_delete:
                        used_urls = [f"/static/img/file1.jpg"]
                        
                        deleted_ids = await image_client.cleanup_unused_images(
                            used_urls,
                            subdirectory="products"
                        )
        
        assert set(deleted_ids) == {"file2", "file3"}
        assert mock_delete.call_count == 2

    @pytest.mark.asyncio
    async def test_cleanup_no_unused_images(self, image_client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "files": [
                {"id": "file1"}
            ]
        }
        
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
            with patch.object(image_client.http_client, 'get', AsyncMock(return_value=mock_response)):
                with patch.object(image_client, 'extract_file_id', return_value='file1'):
                    with patch.object(image_client, 'delete_image', AsyncMock()) as mock_delete:
                        used_urls = ["http://test.com/static/img/file1.jpg"]
                        
                        deleted_ids = await image_client.cleanup_unused_images(used_urls)
        
        assert deleted_ids == []
        assert mock_delete.call_count == 1

    @pytest.mark.asyncio
    async def test_cleanup_metadata_failure(self, image_client):
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
            with patch.object(image_client.http_client, 'get', AsyncMock(return_value=mock_response)):
                deleted_ids = await image_client.cleanup_unused_images([])
        
        assert deleted_ids == []

    @pytest.mark.asyncio
    async def test_cleanup_exception(self, image_client):
        with patch('optl.trace_decorator.trace_client_operation', lambda x: x):
            with patch.object(image_client.http_client, 'get', AsyncMock(side_effect=Exception("Network error"))):
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
        from utils.resilience_config import ResilienceConfig
        resilience_config = ResilienceConfig(timeout=60.0)
        
        client = ProductImageClient(
            base_url=STATIC_SERVICE_URL,
            resilience_config=resilience_config,
            max_concurrent=5
        )
        assert client.http_client.config.timeout == 60.0
        assert client.max_concurrent == 5

    @pytest.mark.asyncio
    async def test_client_close(self):
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            client = ProductImageClient(base_url=STATIC_SERVICE_URL)
            await client.close()
            mock_client.aclose.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])