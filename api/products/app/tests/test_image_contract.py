import pytest
import asyncio
from fastapi.testclient import TestClient
from fastapi import FastAPI, UploadFile
from unittest.mock import Mock, AsyncMock, patch
from io import BytesIO
import json

from services.image_services import ImageService
from database import pydantic_models
from routes.image_routes import router, get_image_service

app = FastAPI()
app.include_router(router)

@pytest.fixture
def mock_image_service():
    service = Mock(spec=ImageService)
    service.upload_product_image = AsyncMock()
    service.get_product_images = AsyncMock()
    service.delete_product_image = AsyncMock()
    service.set_primary_image = AsyncMock()
    return service

@pytest.fixture
def client(mock_image_service):
    app.dependency_overrides[get_image_service] = lambda: mock_image_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_image_response():
    return {
        "id": "img_123",
        "product_id": "prod_456",
        "filename": "prod_456_abc123.jpg",
        "original_name": "test.jpg",
        "mime_type": "image/jpeg",
        "size": 1024000,
        "width": 800,
        "height": 600,
        "is_primary": True,
        "url": "/static/img/products/prod_456/prod_456_abc123.jpg",
        "uploaded_at": "2023-10-01T12:00:00Z"
    }

@pytest.fixture
def mock_image_file():
    return ("test.jpg", BytesIO(b"fake image content"), "image/jpeg")

class TestImageRoutesContract:
    def test_upload_product_image_success(self, client, mock_image_service, sample_image_response):
        mock_image_service.upload_product_image.return_value = pydantic_models.ProductImage(**sample_image_response)
        
        files = {"file": ("test.jpg", b"fake image content", "image/jpeg")}
        data = {"is_primary": "true"}
        
        response = client.post(
            "/images/products/prod_456",
            files=files,
            data=data
        )
        
        assert response.status_code == 201
        assert response.json() == sample_image_response
        mock_image_service.upload_product_image.assert_called_once()

    def test_upload_product_image_missing_file(self, client):
        response = client.post(
            "/images/products/prod_456",
            data={"is_primary": "false"}
        )
        
        assert response.status_code == 422

    def test_list_product_images_success(self, client, mock_image_service, sample_image_response):
        mock_image = pydantic_models.ProductImage(**sample_image_response)
        mock_image_service.get_product_images.return_value = [mock_image]
        
        response = client.get("/images/products/prod_456")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0] == sample_image_response
        assert data["total"] == 1
        mock_image_service.get_product_images.assert_called_once_with("prod_456")

    def test_get_product_image_success(self, client, mock_image_service, sample_image_response):
        mock_image = pydantic_models.ProductImage(**sample_image_response)
        mock_image_service.get_product_images.return_value = [mock_image]
        
        response = client.get("/images/products/prod_456/img_123")
        
        assert response.status_code == 200
        assert response.json() == sample_image_response
        mock_image_service.get_product_images.assert_called_once_with("prod_456")

    def test_get_product_image_not_found(self, client, mock_image_service):
        mock_image_service.get_product_images.return_value = []
        
        response = client.get("/images/products/prod_456/non_existent")
        
        assert response.status_code == 404
        assert "Not Found" in response.json()["title"]

    def test_delete_product_image_success(self, client, mock_image_service):
        mock_image_service.delete_product_image.return_value = True
        
        response = client.delete("/images/products/prod_456/img_123")
        
        assert response.status_code == 204
        mock_image_service.delete_product_image.assert_called_once_with("prod_456", "img_123")

    def test_delete_product_image_not_found(self, client, mock_image_service):
        mock_image_service.delete_product_image.return_value = False
        
        response = client.delete("/images/products/prod_456/non_existent")
        
        assert response.status_code == 404
        assert "Not Found" in response.json()["title"]

    def test_set_primary_image_success(self, client, mock_image_service, sample_image_response):
        mock_image = pydantic_models.ProductImage(**sample_image_response)
        mock_image_service.set_primary_image.return_value = mock_image
        
        response = client.patch("/images/products/prod_456/img_123/primary")
        
        assert response.status_code == 200
        assert response.json() == sample_image_response
        mock_image_service.set_primary_image.assert_called_once_with("prod_456", "img_123")

    def test_set_primary_image_not_found(self, client, mock_image_service):
        mock_image_service.set_primary_image.side_effect = Exception("Image not found")
        
        response = client.patch("/images/products/prod_456/non_existent/primary")
        
        assert response.status_code == 500

    def test_invalid_product_id_format(self, client):
        response = client.get("/images/products/invalid@id")
        
        assert response.status_code == 200

    def test_invalid_image_id_format(self, client, mock_image_service):
        mock_image_service.get_product_images.return_value = []
        
        response = client.get("/images/products/prod_456/invalid@id")
        
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        response = client.post("/images/products/prod_456/img_123")
        
        assert response.status_code == 405

    def test_route_not_found(self, client):
        response = client.get("/images/nonexistent/route")
        
        assert response.status_code == 404

class TestImageRoutesErrorScenarios:
    def test_upload_file_too_large(self, client, mock_image_service):
        mock_image_service.upload_product_image.side_effect = Exception("File too large")
        
        files = {"file": ("large.jpg", b"x" * 10000000, "image/jpeg")}
        
        response = client.post("/images/products/prod_456", files=files)
        
        assert response.status_code == 500

    def test_upload_invalid_file_type(self, client, mock_image_service):
        mock_image_service.upload_product_image.side_effect = Exception("Invalid file type")
        
        files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}
        
        response = client.post("/images/products/prod_456", files=files)
        
        assert response.status_code == 500

    def test_product_not_found_upload(self, client, mock_image_service):
        mock_image_service.upload_product_image.side_effect = Exception("Product not found")
        
        files = {"file": ("test.jpg", b"fake content", "image/jpeg")}
        
        response = client.post("/images/products/non_existent", files=files)
        
        assert response.status_code == 500

    def test_service_raises_exception(self, client, mock_image_service):
        mock_image_service.get_product_images.side_effect = Exception("Database error")
        
        response = client.get("/images/products/prod_456")
        
        assert response.status_code == 500

class TestImageRoutesContentTypes:
    def test_json_content_type(self, client, mock_image_service, sample_image_response):
        mock_image = pydantic_models.ProductImage(**sample_image_response)
        mock_image_service.get_product_images.return_value = [mock_image]
        
        response = client.get("/images/products/prod_456")
        
        assert response.headers["content-type"] == "application/json"

    def test_upload_multipart_form_data(self, client, mock_image_service, sample_image_response):
        mock_image = pydantic_models.ProductImage(**sample_image_response)
        mock_image_service.upload_product_image.return_value = mock_image
        
        files = {"file": ("test.jpg", b"fake image content", "image/jpeg")}
        
        response = client.post(
            "/images/products/prod_456",
            files=files
        )
        
        assert response.status_code == 201
        assert response.json() == sample_image_response

    def test_wrong_content_type_upload(self, client):
        response = client.post(
            "/images/products/prod_456",
            json={"file": "base64encoded"},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422

if __name__ == "__main__":
    import asyncio
    
    async def run_tests():
        print("Running image routes tests...")
        
        mock_service = Mock(spec=ImageService)
        
        app.dependency_overrides[get_image_service] = lambda: mock_service
        
        with TestClient(app) as test_client:
            response = test_client.get("/images/products/test_id")
            print(f"GET /images/products/test_id: {response.status_code}")
            
            response = test_client.post(
                "/images/products/test_id",
                files={"file": ("test.jpg", b"fake", "image/jpeg")}
            )
            print(f"POST /images/products/test_id: {response.status_code}")
        
        app.dependency_overrides.clear()
        print("Image routes tests completed!")
    
    asyncio.run(run_tests())