import pytest
from fastapi.testclient import TestClient
from main import app


class TestProductAPIContract:    
    @pytest.fixture
    def client(self):
        with TestClient(app) as client:
            yield client

    def test_health_endpoint(self, client):
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "timestamp" in data
        assert data["service"] == "product"

    def test_root_endpoint(self, client):
        response = client.get("/info")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data

    def test_create_product_contract(self, client):
        product_data = {
            "name": f"Test Product {id(self)}",
            "price": 29.99,
            "stock": 100,
            "description": "Test product description"
        }
        
        response = client.post("/create", json=product_data)
        
        assert response.status_code in [201, 409]
        
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert "name" in data
            assert "price" in data
            assert "stock" in data
            assert "description" in data
            assert data["name"] == product_data["name"]
            assert data["price"] == product_data["price"]
            assert data["stock"] == product_data["stock"]
            
            assert "Location" in response.headers
            assert "/" in response.headers["Location"]

    def test_create_product_validation_contract(self, client):
        invalid_data = {
            "name": "",
            "price": -10.00,
            "stock": -5
        }
        
        response = client.post("/create", json=invalid_data)
        
        assert response.status_code == 422

    def test_list_products_contract(self, client):
        product_data = {
            "name": f"Test Product for List {id(self)}",
            "price": 39.99,
            "stock": 50,
            "description": "Test product for listing"
        }
        
        create_response = client.post("/create", json=product_data)
        
        response = client.get("/")
        assert response.status_code == 200
        
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert "page_size" in data
            assert isinstance(data["items"], list)

    def test_list_products_pagination_contract(self, client):
        for i in range(3):
            product_data = {
                "name": f"Test Product {i} {id(self)}",
                "price": 10.99 + i,
                "stock": 10 * (i + 1),
                "description": f"Test product {i}"
            }
            client.post("/create", json=product_data)
        
        response = client.get("/?page=2&page_size=5")
        assert response.status_code == 200
        
        if response.status_code == 200:
            data = response.json()
            assert data["page"] == 2
            assert data["page_size"] == 5
        
    def test_get_product_contract(self, client):
        product_data = {
            "name": f"Test Product for Get {id(self)}",
            "price": 39.99,
            "stock": 50,
            "description": "Test product for get operation"
        }
        
        create_response = client.post("/create", json=product_data)
        
        if create_response.status_code == 201:
            product_id = create_response.json()["id"]
            
            response = client.get(f"/{product_id}")
            
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert "id" in data
                assert "name" in data
                assert "price" in data
                assert "stock" in data
                assert "description" in data

    def test_get_product_not_found_contract(self, client):
        response = client.get("/non_existent_id")
        
        assert response.status_code == 404

    def test_update_product_contract(self, client):
        product_data = {
            "name": f"Test Product for Update {id(self)}",
            "price": 49.99,
            "stock": 75,
            "description": "Test product for update operation"
        }
        
        create_response = client.post("/create", json=product_data)
        
        if create_response.status_code == 201:
            product_id = create_response.json()["id"]
            
            update_data = {
                "name": f"Updated Product {id(self)}",
                "price": 59.99,
                "stock": 100,
                "description": "Updated description"
            }
            
            response = client.put(f"/{product_id}", json=update_data)
            
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert data["name"] == update_data["name"]
                assert data["price"] == update_data["price"]
                assert data["stock"] == update_data["stock"]

    def test_patch_product_contract(self, client):
        product_data = {
            "name": f"Test Product for Patch {id(self)}",
            "price": 69.99,
            "stock": 25,
            "description": "Test product for patch operation"
        }
        
        create_response = client.post("/create", json=product_data)
        
        if create_response.status_code == 201:
            product_id = create_response.json()["id"]
            
            patch_data = {
                "stock": 50
            }
            
            response = client.patch(f"/{product_id}", json=patch_data)
            
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert data["stock"] == patch_data["stock"]

    def test_delete_product_contract(self, client):
        product_data = {
            "name": f"Test Product for Delete {id(self)}",
            "price": 79.99,
            "stock": 10,
            "description": "Test product for delete operation"
        }
        
        create_response = client.post("/create", json=product_data)
        
        if create_response.status_code == 201:
            product_id = create_response.json()["id"]
            
            response = client.delete(f"/{product_id}")
            
            assert response.status_code in [204, 404]

    def test_update_inventory_contract(self, client):
        product_data = {
            "name": f"Test Product for Inventory {id(self)}",
            "price": 89.99,
            "stock": 30,
            "description": "Test product for inventory operation"
        }
        
        create_response = client.post("/create", json=product_data)
        
        if create_response.status_code == 201:
            product_id = create_response.json()["id"]
            
            inventory_data = {
                "stock": 60
            }
            
            response = client.patch(f"/{product_id}/inventory", json=inventory_data)
            
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert "id" in data
                assert "stock" in data
                assert data["stock"] == inventory_data["stock"]


class TestProductAPIErrorScenarios:
    
    @pytest.fixture
    def client(self):
        with TestClient(app) as client:
            yield client

    def test_malformed_json_contract(self, client):
        response = client.post(
            "/create",
            content="{invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_unsupported_media_type_contract(self, client):
        response = client.post(
            "/create",
            content="name=Test",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 422

    def test_method_not_allowed_contract(self, client):
        response = client.put("/")
        assert response.status_code == 405

    def test_cors_headers_contract(self, client):
        response = client.get("/health", headers={"Origin": "http://localhost:3000"})
        
        if "access-control-allow-origin" in response.headers:
            assert response.headers["access-control-allow-origin"] == "http://localhost:3000"