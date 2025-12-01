import pytest
import asyncio
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import Mock, AsyncMock
from services.product_services import ProductService
from database import pydantic_models
from database.database_models import ProductDB
from routes.product_routes import router, get_product_service
import logging
from database.pydantic_models import ProductImage

app = FastAPI()
app.include_router(router, prefix="/api/products")

@pytest.fixture
def mock_product_service():
    service = Mock(spec=ProductService)
    service.create_product = AsyncMock()
    service.get_product = AsyncMock()
    service.list_products = AsyncMock()
    service.update_product = AsyncMock()
    service.patch_product = AsyncMock()
    service.delete_product = AsyncMock()
    service.update_inventory = AsyncMock()
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
        "description": "Test Description"
    }

@pytest.fixture
def sample_product_response():
    return {
        "id": "prod_123",
        "name": "Test Product",
        "price": 99.99,
        "stock": 10,
        "description": "Test Description",
        "images": [],
        "primary_image_id": None
    }

class TestProductRoutesContract:
    def test_create_product_success(self, client, mock_product_service, sample_product_data, sample_product_response):
        from fastapi.responses import JSONResponse
        
        create_response = sample_product_response.copy()
        del create_response["images"]
        del create_response["primary_image_id"]
        
        json_response = JSONResponse(
            status_code=201,
            content=create_response,
            headers={"Location": "/api/products/prod_123"}
        )
        mock_product_service.create_product.return_value = json_response
        
        response = client.post("/api/products/create", json=sample_product_data)
        
        assert response.status_code == 201
        assert response.json() == create_response
        assert "Location" in response.headers
        assert "/api/products/prod_123" in response.headers["Location"]
        mock_product_service.create_product.assert_called_once()

    def test_get_product_success(self, client, mock_product_service, sample_product_response):
        
        pydantic_models.ProductResponse.model_rebuild()
        
        mock_response = pydantic_models.ProductResponse(**sample_product_response)
        mock_product_service.get_product.return_value = mock_response
        
        response = client.get("/api/products/prod_123")
        
        assert response.status_code == 200
        assert response.json() == sample_product_response
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
        
        
        pydantic_models.ProductResponse.model_rebuild()
        pydantic_models.ProductList.model_rebuild()
        
        product_list = pydantic_models.ProductList(
            items=[pydantic_models.ProductResponse(**sample_product_response)],
            total=1,
            page=1,
            page_size=20
        )
        mock_product_service.list_products.return_value = product_list
        
        response = client.get("/api/products/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0] == sample_product_response
        mock_product_service.list_products.assert_called_once()

    def test_list_products_with_pagination(self, client, mock_product_service):
        
        
        pydantic_models.ProductResponse.model_rebuild()
        pydantic_models.ProductList.model_rebuild()
        
        product_list = pydantic_models.ProductList(
            items=[],
            total=0,
            page=2,
            page_size=5
        )
        mock_product_service.list_products.return_value = product_list
        
        response = client.get("/api/products/?page=2&page_size=5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 5

    def test_list_products_with_search(self, client, mock_product_service):
        
        
        pydantic_models.ProductResponse.model_rebuild()
        pydantic_models.ProductList.model_rebuild()
        
        product_list = pydantic_models.ProductList(
            items=[],
            total=0,
            page=1,
            page_size=20
        )
        mock_product_service.list_products.return_value = product_list
        
        response = client.get("/api/products/?q=laptop")
        
        assert response.status_code == 200
        mock_product_service.list_products.assert_called_once()

    def test_update_product_success(self, client, mock_product_service, sample_product_data, sample_product_response):
        
        
        pydantic_models.ProductResponse.model_rebuild()
        
        mock_response = pydantic_models.ProductResponse(**sample_product_response)
        mock_product_service.update_product.return_value = mock_response
        
        response = client.put("/api/products/prod_123", json=sample_product_data)
        
        assert response.status_code == 200
        assert response.json() == sample_product_response
        mock_product_service.update_product.assert_called_once()

    def test_patch_product_success(self, client, mock_product_service, sample_product_response):
        
        
        pydantic_models.ProductResponse.model_rebuild()
        
        mock_response = pydantic_models.ProductResponse(**sample_product_response)
        mock_product_service.patch_product.return_value = mock_response
        
        patch_data = {"price": 149.99}
        
        response = client.patch("/api/products/prod_123", json=patch_data)
        
        assert response.status_code == 200
        assert response.json() == sample_product_response
        mock_product_service.patch_product.assert_called_once()

    def test_delete_product_success(self, client, mock_product_service):
        mock_product_service.delete_product.return_value = None
        
        response = client.delete("/api/products/prod_123")
        
        assert response.status_code == 204
        mock_product_service.delete_product.assert_called_once()

    def test_update_inventory_success(self, client, mock_product_service):
        inventory_response = pydantic_models.InventoryResponse(
            id="prod_123",
            stock=25
        )
        mock_product_service.update_inventory.return_value = inventory_response
        
        inventory_data = {"stock": 25}
        
        response = client.patch("/api/products/prod_123/inventory", json=inventory_data)
        
        assert response.status_code == 200
        assert response.json() == {"id": "prod_123", "stock": 25}
        mock_product_service.update_inventory.assert_called_once()

    def test_update_inventory_validation_error(self, client):
        invalid_data = {"stock": -5}
        
        response = client.patch("/api/products/prod_123/inventory", json=invalid_data)
        
        assert response.status_code == 422

    def test_invalid_page_parameter(self, client):
        response = client.get("/api/products/?page=0")
        
        assert response.status_code == 422

    def test_invalid_page_size_parameter(self, client):
        response = client.get("/api/products/?page_size=200")
        
        assert response.status_code == 422

    def test_route_not_found(self, client):
        response = client.get("/api/products/nonexistent/route")
        
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        response = client.post("/api/products/prod_123") 
        
        assert response.status_code == 405

class TestProductRoutesErrorScenarios:
    def test_service_raises_exception(self, client, mock_product_service):
        mock_product_service.get_product.side_effect = Exception("Database error")
        
        response = client.get("/api/products/prod_123")
        
        assert response.status_code == 500

    def test_malformed_json(self, client):
        response = client.post("/api/products/create", data='{"malformed": json')
        
        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        incomplete_data = {"name": "Test"}
        
        response = client.post("/api/products/create", json=incomplete_data)
        
        assert response.status_code == 422

class TestProductRoutesEdgeCases:
    def test_empty_product_list(self, client, mock_product_service):
        
        
        pydantic_models.ProductResponse.model_rebuild()
        pydantic_models.ProductList.model_rebuild()
        
        product_list = pydantic_models.ProductList(
            items=[],
            total=0,
            page=1,
            page_size=20
        )
        mock_product_service.list_products.return_value = product_list
        
        response = client.get("/api/products/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_special_characters_in_search(self, client, mock_product_service):
        
        
        pydantic_models.ProductResponse.model_rebuild()
        pydantic_models.ProductList.model_rebuild()
        
        product_list = pydantic_models.ProductList(
            items=[],
            total=0,
            page=1,
            page_size=20
        )
        mock_product_service.list_products.return_value = product_list
        
        response = client.get("/api/products/?q=test%20product%20@%23")
        
        assert response.status_code == 200

    def test_long_product_id(self, client, mock_product_service, sample_product_response):
        
        
        pydantic_models.ProductResponse.model_rebuild()
        
        mock_response = pydantic_models.ProductResponse(**sample_product_response)
        mock_product_service.get_product.return_value = mock_response
        
        long_id = "a" * 100
        response = client.get(f"/api/products/{long_id}")
        
        assert response.status_code == 200

class TestProductRoutesContentTypes:
    def test_json_content_type(self, client, mock_product_service, sample_product_response):
        
        
        pydantic_models.ProductResponse.model_rebuild()
        
        mock_response = pydantic_models.ProductResponse(**sample_product_response)
        mock_product_service.get_product.return_value = mock_response
        
        response = client.get("/api/products/prod_123")
        
        assert response.headers["content-type"] == "application/json"

    def test_create_product_content_type(self, client, mock_product_service, sample_product_data, sample_product_response):
        
        
        pydantic_models.ProductResponse.model_rebuild()
        
        create_response = sample_product_response.copy()
        del create_response["images"]
        del create_response["primary_image_id"]
        
        mock_response = pydantic_models.ProductResponse(**create_response)
        mock_product_service.create_product.return_value = mock_response
        
        response = client.post(
            "/api/products/create", 
            json=sample_product_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 201

    def test_wrong_content_type(self, client):
        response = client.post(
            "/api/products/create",
            data="name=test",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 422

def setup_module():
    """Setup module to resolve Pydantic forward references"""
    
    pydantic_models.ProductResponse.model_rebuild()
    pydantic_models.ProductList.model_rebuild()

if __name__ == "__main__":
    setup_module()
    pytest.main([__file__, "-v"])