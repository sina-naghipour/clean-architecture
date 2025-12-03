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
    assert data["total"] == 2
    assert data["successful_count"] == 2


def test_batch_upload_partial_success(client, mock_file_service):
    from fastapi import HTTPException
    
    mock_file_service.upload_file.side_effect = [
        {"id": "file_123", "filename": "test1.jpg"},
        HTTPException(status_code=415, detail="Invalid type")
    ]
    
    files = [
        ("files", ("test1.jpg", b"fake data 1", "image/jpeg")),
        ("files", ("test2.gif", b"fake data 2", "image/gif"))
    ]
    
    response = client.post("/files/batch", files=files)
    
    assert response.status_code == 207
    data = response.json()
    assert data["total"] == 2
    assert data["successful_count"] == 1


def test_get_file_success(client, mock_file_service, tmp_path):
    test_file = tmp_path / "test.jpg"
    test_file.write_bytes(b"fake image data")
    
    mock_file_service.get_file_path.return_value = test_file
    
    response = client.get("/files/file_123")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert response.content == b"fake image data"


def test_get_file_not_found(client, mock_file_service):
    mock_file_service.get_file_path.return_value = Mock(exists=Mock(return_value=False))
    
    response = client.get("/files/nonexistent")
    
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    data = response.json()
    assert data["title"] == "File Not Found"


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
    assert data["title"] == "File Not Found"


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
        "path": "products/123/safe_test.jpg"
    }
    
    files = {"file": ("test.jpg", b"fake image data", "image/jpeg")}
    response = client.post("/files?subdirectory=products/123", files=files)
    
    assert response.status_code == 201
    mock_file_service.upload_file.assert_called_once()
    call_kwargs = mock_file_service.upload_file.call_args[1]
    assert call_kwargs.get("subdirectory") == "products/123"


if __name__ == "__main__":
    print("Running contract tests...")