import pytest
import asyncio
from fastapi.testclient import TestClient
from fastapi import FastAPI, UploadFile
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from io import BytesIO
import json
from datetime import datetime

from services.product_services import ProductService
from database import pydantic_models
from database.database_models import ProductDB
from routes.product_routes import router, get_product_service
from services.product_image_client import UploadResult

app = FastAPI()
app.include_router(router, prefix="/api/products")

@pytest.fixture
def mock_product_service():
    service = Mock(spec=ProductService)
    
    # Make sure async methods return proper data, not AsyncMock objects
    # Use AsyncMock with return_value set to actual data
    service.create_product = AsyncMock()
    service.create_product_with_images = AsyncMock()
    service.get_product = AsyncMock()
    service.list_products = AsyncMock()
    service.update_product = AsyncMock()
    service.patch_product = AsyncMock()
    service.delete_product = AsyncMock()
    service.update_inventory = AsyncMock()
    service.add_product_images = AsyncMock()
    service.remove_product_image = AsyncMock()
    service.update_product_tags = AsyncMock()
    service.cleanup_product_images = AsyncMock()
    service.close = AsyncMock()
    return service

@pytest.fixture
def client(mock_product_service):
    app.dependency_overrides[get_product_service] = lambda: mock_product_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_product_data():
    return {
        "name": "Test Product",
        "price": 99.99,
        "stock": 10,
        "description": "Test Description",
        "tags": ["electronics", "test"],
        "images": ["http://example.com/image1.jpg"]
    }

@pytest.fixture
def sample_product_response():
    return {
        "id": "prod_123",
        "name": "Test Product",
        "price": 99.99,
        "stock": 10,
        "description": "Test Description",
        "tags": ["electronics", "test"],
        "images": ["http://example.com/image1.jpg"],
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }

@pytest.fixture
def sample_image_file():
    return ("test.jpg", BytesIO(b"fake image data"), "image/jpeg")

@pytest.fixture
def mock_upload_result():
    return UploadResult(success=True, url="http://example.com/static/img/test.jpg")

class TestProductRoutesContract:
    def test_create_product_success(self, client, mock_product_service, sample_product_data, sample_product_response):
        from fastapi.responses import JSONResponse
        
        # Create a proper JSONResponse with actual data
        json_response = JSONResponse(
            status_code=201,
            content=sample_product_response,
            headers={"Location": "/api/products/prod_123"}
        )
        
        # Set the mock to return the JSONResponse
        mock_product_service.create_product.return_value = json_response
        
        response = client.post("/api/products/", json=sample_product_data)
        
        assert response.status_code == 201
        assert response.json() == sample_product_response
        assert "Location" in response.headers
        assert "/api/products/prod_123" in response.headers["Location"]
        mock_product_service.create_product.assert_called_once()

    def test_create_product_success(self, client, mock_product_service, sample_product_data, sample_product_response):
        product_response = pydantic_models.ProductResponse(**sample_product_response)
        
        mock_product_service.create_product.return_value = product_response
        
        response = client.post("/api/products/", json=sample_product_data)
        
        assert response.status_code == 201
        assert response.json() == sample_product_response
        mock_product_service.create_product.assert_called_once()

    def test_get_product_success(self, client, mock_product_service, sample_product_response):
        product_response = pydantic_models.ProductResponse(**sample_product_response)
        
        mock_product_service.get_product.return_value = product_response
        
        response = client.get("/api/products/prod_123")
        
        assert response.status_code == 200
        assert response.json()["id"] == "prod_123"
        assert response.json()["name"] == "Test Product"
        mock_product_service.get_product.assert_called_once()

    def test_get_product_not_found(self, client, mock_product_service):
        from services.product_helpers import create_problem_response
        
        problem_response = create_problem_response(
            status_code=404,
            error_type="not-found",
            title="Not Found", 
            detail="Product not found",
            instance="/api/products/non_existent"
        )
        
        mock_product_service.get_product.return_value = problem_response
        
        response = client.get("/api/products/non_existent")
        
        assert response.status_code == 404
        assert "Not Found" in response.json()["title"]

    def test_list_products_success(self, client, mock_product_service, sample_product_response):
        # Create proper ProductList object
        product_list = pydantic_models.ProductList(
            items=[pydantic_models.ProductResponse(**sample_product_response)],
            total=1,
            page=1,
            page_size=20
        )
        
        # Set the mock to return the ProductList
        mock_product_service.list_products.return_value = product_list
        
        response = client.get("/api/products/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == "prod_123"
        mock_product_service.list_products.assert_called_once()

    def test_update_product_success(self, client, mock_product_service, sample_product_data, sample_product_response):
        # Create proper ProductResponse
        product_response = pydantic_models.ProductResponse(**sample_product_response)
        mock_product_service.update_product.return_value = product_response
        
        response = client.put("/api/products/prod_123", json=sample_product_data)
        
        assert response.status_code == 200
        assert response.json()["id"] == "prod_123"
        mock_product_service.update_product.assert_called_once()

    def test_patch_product_success(self, client, mock_product_service, sample_product_response):
        product_response = pydantic_models.ProductResponse(**sample_product_response)
        mock_product_service.patch_product.return_value = product_response
        
        patch_data = {"price": 149.99, "description": "Updated description"}
        
        response = client.patch("/api/products/prod_123", json=patch_data)
        
        assert response.status_code == 200
        mock_product_service.patch_product.assert_called_once()

    def test_add_product_images_success(self, client, mock_product_service, sample_image_file):
        # Return a proper dictionary, not a Mock
        mock_response = {
            "product_id": "prod_123",
            "added_count": 2,
            "failed_count": 0,
            "total_images": 3,
            "new_images": ["img1.jpg", "img2.jpg"]
        }
        mock_product_service.add_product_images.return_value = mock_response
        
        files = [('images', sample_image_file), ('images', sample_image_file)]
        
        response = client.post("/api/products/prod_123/images", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == "prod_123"
        assert data["added_count"] == 2
        mock_product_service.add_product_images.assert_called_once()

    def test_remove_product_image_success(self, client, mock_product_service):
        mock_response = {
            "product_id": "prod_123",
            "removed_image": "http://example.com/image.jpg",
            "remaining_images": ["img2.jpg"]
        }
        mock_product_service.remove_product_image.return_value = mock_response
        
        response = client.delete("/api/products/prod_123/images?image_url=http%3A%2F%2Fexample.com%2Fimage.jpg")
        
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == "prod_123"
        assert data["removed_image"] == "http://example.com/image.jpg"
        mock_product_service.remove_product_image.assert_called_once()

    def test_update_product_tags_success(self, client, mock_product_service):
        mock_response = {
            "product_id": "prod_123",
            "updated_tags": ["new_tag1", "new_tag2"]
        }
        mock_product_service.update_product_tags.return_value = mock_response
        
        tag_data = {"tags": ["new_tag1", "new_tag2"]}
        
        response = client.patch("/api/products/prod_123/tags", json=tag_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == "prod_123"
        assert data["updated_tags"] == ["new_tag1", "new_tag2"]
        mock_product_service.update_product_tags.assert_called_once()

    def test_cleanup_product_images_success(self, client, mock_product_service):
        mock_response = {
            "product_id": "prod_123",
            "valid_images": 2,
            "invalid_images_removed": 1,
            "invalid_image_urls": ["bad_image.jpg"]
        }
        mock_product_service.cleanup_product_images.return_value = mock_response
        
        response = client.post("/api/products/prod_123/images/cleanup")
        
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == "prod_123"
        assert data["invalid_images_removed"] == 1
        mock_product_service.cleanup_product_images.assert_called_once()

class TestProductRoutesValidation:
    def test_create_product_validation_errors(self, client):
        invalid_data = {"name": ""}  # Missing required fields
        
        response = client.post("/api/products/", json=invalid_data)
        
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("field required" in str(error).lower() for error in errors)

    def test_create_product_invalid_price(self, client):
        invalid_data = {
            "name": "Test Product",
            "price": -10.0,  # Price must be > 0
            "stock": 10,
            "tags": [],
            "images": []
        }
        
        response = client.post("/api/products/", json=invalid_data)
        
        assert response.status_code == 422

    def test_create_product_invalid_stock(self, client):
        invalid_data = {
            "name": "Test Product",
            "price": 99.99,
            "stock": -5,  # Stock must be >= 0
            "tags": [],
            "images": []
        }
        
        response = client.post("/api/products/", json=invalid_data)
        
        assert response.status_code == 422

    def test_create_product_invalid_tags(self, client, mock_product_service, sample_product_response):
        product_response = pydantic_models.ProductResponse(**sample_product_response)
        
        mock_product_service.create_product.return_value = product_response
        
        invalid_data = {
            "name": "Test Product",
            "price": 99.99,
            "stock": 10,
            "tags": ["", "  "],  # These get filtered to empty list
            "images": []
        }
        
        response = client.post("/api/products/", json=invalid_data)

        assert response.status_code == 201
        mock_product_service.create_product.assert_called_once()
        

    def test_patch_product_validation_errors(self, client):
        # Mock the service to return a valid response to avoid validation errors
        from fastapi.responses import JSONResponse
        mock_response = JSONResponse(
            status_code=200,
            content={"id": "prod_123", "name": "Test", "price": 149.99, "stock": 10, "tags": [], "images": [], "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"}
        )
        
        # We need to patch the dependency
        from routes.product_routes import get_product_service
        mock_service = Mock(spec=ProductService)
        mock_service.patch_product = AsyncMock(return_value=mock_response)
        
        app.dependency_overrides[get_product_service] = lambda: mock_service
        
        invalid_data = {"price": -10.0}  # Invalid price
        
        response = client.patch("/api/products/prod_123", json=invalid_data)
        
        # Should fail validation before hitting the service
        assert response.status_code == 422
        
        app.dependency_overrides.clear()

    def test_update_inventory_validation_error(self, client):
        invalid_data = {"stock": -5}  # Invalid stock
        
        response = client.patch("/api/products/prod_123/inventory", json=invalid_data)
        
        assert response.status_code == 422

    def test_update_product_tags_validation_error(self, client):
        invalid_data = {"tags": []}  # Empty tags list
        
        response = client.patch("/api/products/prod_123/tags", json=invalid_data)
        
        assert response.status_code == 422

    def test_invalid_page_parameter(self, client):
        response = client.get("/api/products/?page=0")  # Page should be >= 1
        
        assert response.status_code == 422

    def test_invalid_page_size_parameter(self, client):
        response = client.get("/api/products/?page_size=200")  # Exceeds MAX_PAGE_SIZE
        
        assert response.status_code == 422

if __name__ == "__main__":
    pytest.main([__file__, "-v"])