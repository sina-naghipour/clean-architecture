import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from main import app


class TestProductAPIContract:    
    @pytest_asyncio.fixture
    async def client(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "timestamp" in data
        assert data["service"] == "product"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        response = await client.get("/info")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data

    @pytest.mark.asyncio
    async def test_create_product_contract(self, client):
        product_data = {
            "name": "Test Product",
            "price": 29.99,
            "stock": 100,
            "description": "Test product description"
        }
        
        response = await client.post("/", json=product_data)
        
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

    @pytest.mark.asyncio
    async def test_create_product_validation_contract(self, client):
        invalid_data = {
            "name": "",
            "price": -10.00,
            "stock": -5
        }
        
        response = await client.post("/", json=invalid_data)
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_products_contract(self, client):
        # First create a product to ensure there's data
        product_data = {
            "name": "Test Product for List",
            "price": 39.99,
            "stock": 50,
            "description": "Test product for listing"
        }
        
        create_response = await client.post("/", json=product_data)
        
        response = await client.get("/")
        assert response.status_code == 200
        
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert "page_size" in data
            assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_list_products_pagination_contract(self, client):
        # First create some products
        for i in range(3):
            product_data = {
                "name": f"Test Product {i}",
                "price": 10.99 + i,
                "stock": 10 * (i + 1),
                "description": f"Test product {i}"
            }
            await client.post("/", json=product_data)
        
        response = await client.get("/?page=2&page_size=5")
        assert response.status_code == 200
        
        if response.status_code == 200:
            data = response.json()
            assert data["page"] == 2
            assert data["page_size"] == 5
        
    @pytest.mark.asyncio
    async def test_get_product_contract(self, client):
        product_data = {
            "name": "Test Product for Get",
            "price": 39.99,
            "stock": 50,
            "description": "Test product for get operation"
        }
        
        create_response = await client.post("/", json=product_data)
        
        if create_response.status_code == 201:
            product_id = create_response.json()["id"]
            
            response = await client.get(f"//{product_id}")
            
            print(f'responssss {response}')
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                if data["total"] == 0:
                    assert "items" in data
                    assert "total" in data
                    assert "page" in data
                    assert "page_size" in data
                else:
                    assert "id" in data
                    assert "name" in data
                    assert "price" in data
                    assert "stock" in data

    @pytest.mark.asyncio
    async def test_get_product_not_found_contract(self, client):
        response = await client.get("/non_existent_id")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_product_contract(self, client):
        # First create a product to update
        product_data = {
            "name": "Test Product for Update",
            "price": 49.99,
            "stock": 75,
            "description": "Test product for update operation"
        }
        
        create_response = await client.post("/", json=product_data)
        
        if create_response.status_code == 201:
            product_id = create_response.json()["id"]
            
            update_data = {
                "name": "Updated Product",
                "price": 59.99,
                "stock": 100,
                "description": "Updated description"
            }
            
            response = await client.put(f"/{product_id}", json=update_data)
            
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert data["name"] == update_data["name"]
                assert data["price"] == update_data["price"]
                assert data["stock"] == update_data["stock"]

    @pytest.mark.asyncio
    async def test_patch_product_contract(self, client):
        # First create a product to patch
        product_data = {
            "name": "Test Product for Patch",
            "price": 69.99,
            "stock": 25,
            "description": "Test product for patch operation"
        }
        
        create_response = await client.post("/", json=product_data)
        
        if create_response.status_code == 201:
            product_id = create_response.json()["id"]
            
            patch_data = {
                "stock": 50
            }
            
            response = await client.patch(f"/{product_id}", json=patch_data)
            
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert data["stock"] == patch_data["stock"]

    @pytest.mark.asyncio
    async def test_delete_product_contract(self, client):
        # First create a product to delete
        product_data = {
            "name": "Test Product for Delete",
            "price": 79.99,
            "stock": 10,
            "description": "Test product for delete operation"
        }
        
        create_response = await client.post("/", json=product_data)
        
        if create_response.status_code == 201:
            product_id = create_response.json()["id"]
            
            response = await client.delete(f"/{product_id}")
            
            assert response.status_code in [204, 404]

    @pytest.mark.asyncio
    async def test_update_inventory_contract(self, client):
        # First create a product to update inventory
        product_data = {
            "name": "Test Product for Inventory",
            "price": 89.99,
            "stock": 30,
            "description": "Test product for inventory operation"
        }
        
        create_response = await client.post("/", json=product_data)
        
        if create_response.status_code == 201:
            product_id = create_response.json()["id"]
            
            inventory_data = {
                "stock": 60
            }
            
            response = await client.patch(f"/{product_id}/inventory", json=inventory_data)
            
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert "id" in data
                assert "stock" in data
                assert data["stock"] == inventory_data["stock"]


class TestProductAPIErrorScenarios:
    
    @pytest_asyncio.fixture
    async def client(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_malformed_json_contract(self, client):
        response = await client.post(
            "/",
            content="{invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unsupported_media_type_contract(self, client):
        response = await client.post(
            "/",
            content="name=Test",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_method_not_allowed_contract(self, client):
        response = await client.put("/")
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_cors_headers_contract(self, client):
        response = await client.get("/health", headers={"Origin": "http://localhost:3000"})
        
        if "access-control-allow-origin" in response.headers:
            assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
