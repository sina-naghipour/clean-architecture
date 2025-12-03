import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import FastAPI, UploadFile
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the actual app
from main import app
from routes.file_routes import get_file_service


@pytest.fixture
def mock_file_service():
    service = Mock()
    service.upload_file = AsyncMock()
    service.delete_file = AsyncMock()
    service.get_file_path = Mock()
    service.metadata_updater = Mock()
    return service


@pytest.fixture
def client(mock_file_service):
    # Override the dependency
    app.dependency_overrides[get_file_service] = lambda: mock_file_service
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up after test
    app.dependency_overrides.clear()


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "static"


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data


def test_upload_file_success(client, mock_file_service):
    mock_file_service.upload_file.return_value = {
        "id": "file_123",
        "filename": "safe_test.jpg",
        "original_filename": "test.jpg",
        "path": "products/123/safe_test.jpg",
        "size": 1024000,
        "mime_type": "image/jpeg",
        "url": "/static/img/products/123/safe_test.jpg"
    }
    
    files = {"file": ("test.jpg", b"fake image data", "image/jpeg")}
    response = client.post("/files", files=files)
    
    print(f"DEBUG - Response status: {response.status_code}")
    print(f"DEBUG - Response body: {response.text[:200]}")
    
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["id"] == "file_123"
    assert "Location" in response.headers


def test_upload_file_bad_request(client, mock_file_service):
    # Missing file
    response = client.post("/files")
    assert response.status_code == 422


def test_upload_file_service_error(client, mock_file_service):
    from fastapi import HTTPException
    mock_file_service.upload_file.side_effect = HTTPException(
        status_code=413, 
        detail="File too large"
    )
    
    files = {"file": ("test.jpg", b"fake image data", "image/jpeg")}
    response = client.post("/files", files=files)
    
    assert response.status_code == 413
    assert response.headers["content-type"] == "application/problem+json"
    data = response.json()
    # Check RFC 7807 format
    assert "type" in data
    assert "title" in data
    assert "status" in data
    assert "detail" in data
    assert "File too large" in data["detail"]


def test_batch_upload_success(client, mock_file_service):
    mock_file_service.upload_file.return_value = {
        "id": "file_123",
        "filename": "safe_test.jpg",
        "original_filename": "test.jpg",
        "path": "safe_test.jpg",
        "size": 1024000,
        "mime_type": "image/jpeg",
        "url": "/static/img/safe_test.jpg"
    }
    
    files = [
        ("files", ("test1.jpg", b"fake image data 1", "image/jpeg")),
        ("files", ("test2.jpg", b"fake image data 2", "image/jpeg"))
    ]
    
    response = client.post("/files/batch", files=files)
    
    assert response.status_code == 207
    data = response.json()
    # Check RFC 7807 multi-status format
    assert "type" in data
    assert "title" in data
    assert "status" in data
    assert "detail" in data
    assert "successful" in data
    assert "failed" in data
    assert data["successful_count"] == 2


def test_batch_upload_partial_success(client, mock_file_service):
    from fastapi import HTTPException
    
    # Mock needs complete return values
    mock_file_service.upload_file.side_effect = [
        {
            "id": "file_123", 
            "filename": "test1.jpg",
            "original_filename": "test1.jpg",
            "path": "test1.jpg",
            "size": 1000,
            "mime_type": "image/jpeg",
            "url": "/static/img/test1.jpg"
        },
        HTTPException(status_code=415, detail="Invalid type")
    ]
    
    files = [
        ("files", ("test1.jpg", b"fake data 1", "image/jpeg")),
        ("files", ("test2.gif", b"fake data 2", "image/gif"))
    ]
    
    response = client.post("/files/batch", files=files)
    
    assert response.status_code == 207
    data = response.json()
    assert data["successful_count"] == 1
    assert data["failed_count"] == 1
    assert len(data["successful"]) == 1
    assert len(data["failed"]) == 1
    # Check failed item has proper structure
    failed_item = data["failed"][0]
    assert "filename" in failed_item
    assert "error" in failed_item
    assert "status_code" in failed_item


def test_get_file_success(client, mock_file_service, tmp_path):
    test_file = tmp_path / "test.jpg"
    test_file.write_bytes(b"fake image data")
    
    mock_file_service.get_file_path.return_value = test_file
    
    response = client.get("/files/file_123")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert response.content == b"fake image data"


def test_get_file_not_found(client, mock_file_service):
    # Create a Mock that has exists() method returning False
    mock_path = Mock()
    mock_path.exists.return_value = False
    mock_file_service.get_file_path.return_value = mock_path
    
    response = client.get("/files/nonexistent")
    
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    data = response.json()
    assert "type" in data
    assert "title" in data
    assert "status" in data
    assert "detail" in data


def test_delete_file_success(client, mock_file_service):
    mock_file_service.delete_file.return_value = True
    
    response = client.delete("/files/file_123")
    
    assert response.status_code == 204
    assert response.content == b""


def test_delete_file_not_found(client, mock_file_service):
    mock_file_service.delete_file.return_value = False
    
    response = client.delete("/files/nonexistent")
    
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    data = response.json()
    assert "type" in data
    assert "title" in data
    assert "status" in data
    assert "detail" in data


def test_get_metadata(client, mock_file_service):
    mock_metadata_updater = Mock()
    mock_metadata_updater.list_files.return_value = {
        "file_1": {"filename": "test1.jpg", "size": 1000},
        "file_2": {"filename": "test2.png", "size": 2000}
    }
    mock_file_service.metadata_updater = mock_metadata_updater
    
    response = client.get("/metadata")
    
    assert response.status_code == 200
    data = response.json()
    assert data["files_count"] == 2
    assert "file_1" in data["files"]
    assert "file_2" in data["files"]


def test_nonexistent_endpoint(client):
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_method_not_allowed(client):
    response = client.post("/files/file_123")
    assert response.status_code == 405


def test_upload_file_with_subdirectory(client, mock_file_service):
    mock_file_service.upload_file.return_value = {
        "id": "file_123",
        "filename": "safe_test.jpg",
        "original_filename": "test.jpg",
        "path": "products/123/safe_test.jpg",
        "size": 1024000,
        "mime_type": "image/jpeg",
        "url": "/static/img/products/123/safe_test.jpg"
    }
    
    files = {"file": ("test.jpg", b"fake image data", "image/jpeg")}
    response = client.post("/files?subdirectory=products/123", files=files)
    
    assert response.status_code == 201
    mock_file_service.upload_file.assert_called_once()
    call_kwargs = mock_file_service.upload_file.call_args[1]
    assert call_kwargs.get("subdirectory") == "products/123"


def test_error_response_follows_rfc7807(client, mock_file_service):
    """Test that all error responses follow RFC 7807 problem details format."""
    from fastapi import HTTPException
    
    # Test different error types
    error_cases = [
        (413, "file-too-large", "File Too Large"),
        (415, "unsupported-media-type", "Unsupported Media Type"),
        (404, "not-found", "Not Found"),
        (422, "validation", "Validation Failed"),
    ]
    
    for status_code, error_type, title in error_cases:
        mock_file_service.upload_file.side_effect = HTTPException(
            status_code=status_code,
            detail=f"Test error {status_code}"
        )
        
        response = client.post("/files", files={"file": ("test.jpg", b"data", "image/jpeg")})
        
        assert response.status_code == status_code
        assert response.headers["content-type"] == "application/problem+json"
        
        data = response.json()
        # Check RFC 7807 required fields
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert "detail" in data
        assert data["status"] == status_code
        assert error_type in data["type"]


if __name__ == "__main__":
    print("Running contract tests...")
