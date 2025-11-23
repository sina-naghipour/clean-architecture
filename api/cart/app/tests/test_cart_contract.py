import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from main import app


class TestCartAPIContract:    
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
        assert data["service"] == "cart"

    @pytest.mark.asyncio
    async def test_ready_endpoint(self, client):
        response = await client.get("/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["status"] == "ready"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
        assert "ready" in data

    @pytest.mark.asyncio
    async def test_get_cart_contract(self, client):
        # First add an item to create a cart
        item_data = {
            "product_id": "prod_4",
            "quantity": 2
        }
        
        await client.post("/api/cart/items", json=item_data, headers={"Authorization": "Bearer test_token"})
        
        response = await client.get("/api/cart", headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "user_id" in data
            assert "items" in data
            assert "total" in data
            assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_get_cart_not_found_contract(self, client):
        response = await client.get("/api/cart", headers={"Authorization": "Bearer unknown_user"})
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_add_cart_item_contract(self, client):
        item_data = {
            "product_id": "prod_1",
            "quantity": 1
        }
        
        response = await client.post("/api/cart/items", json=item_data, headers={"Authorization": "Bearer test_token"})
        print(f'here : {response.json()}')
        assert response.status_code in [201, 404]
        
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert "product_id" in data
            assert "name" in data
            assert "quantity" in data
            assert "unit_price" in data
            assert data["product_id"] == item_data["product_id"]
            assert data["quantity"] == item_data["quantity"]
            
            assert "Location" in response.headers
            assert "/api/cart/items/" in response.headers["Location"]

    @pytest.mark.asyncio
    async def test_add_cart_item_validation_contract(self, client):
        invalid_data = {
            "product_id": "",
            "quantity": 0
        }
        
        response = await client.post("/api/cart/items", json=invalid_data, headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_add_cart_item_product_not_found_contract(self, client):
        item_data = {
            "product_id": "non_existent_product",
            "quantity": 1
        }
        
        response = await client.post("/api/cart/items", json=item_data, headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_cart_item_contract(self, client):
        # First add an item
        item_data = {
            "product_id": "prod_2",
            "quantity": 1
        }
        
        add_response = await client.post("/api/cart/items", json=item_data, headers={"Authorization": "Bearer test_token"})
        
        if add_response.status_code == 201:
            item_id = add_response.json()["id"]
            
            update_data = {
                "quantity": 3
            }
            
            response = await client.patch(f"/api/cart/items/{item_id}", json=update_data, headers={"Authorization": "Bearer test_token"})
            
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert data["quantity"] == update_data["quantity"]

    @pytest.mark.asyncio
    async def test_update_cart_item_not_found_contract(self, client):
        update_data = {
            "quantity": 2
        }
        
        response = await client.patch("/api/cart/items/non_existent_item", json=update_data, headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_remove_cart_item_contract(self, client):
        # First add an item
        item_data = {
            "product_id": "prod_3",
            "quantity": 1
        }
        
        add_response = await client.post("/api/cart/items", json=item_data, headers={"Authorization": "Bearer test_token"})
        
        if add_response.status_code == 201:
            item_id = add_response.json()["id"]
            
            response = await client.delete(f"/api/cart/items/{item_id}", headers={"Authorization": "Bearer test_token"})
            
            assert response.status_code in [204, 404]

    @pytest.mark.asyncio
    async def test_clear_cart_contract(self, client):
        # First add some items
        items = [
            {"product_id": "prod_1", "quantity": 1},
            {"product_id": "prod_2", "quantity": 2}
        ]
        
        for item in items:
            await client.post("/api/cart/items", json=item, headers={"Authorization": "Bearer test_token"})
        
        response = await client.delete("/api/cart", headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code in [204, 404]


class TestCartAPIErrorScenarios:
    
    @pytest_asyncio.fixture
    async def client(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_malformed_json_contract(self, client):
        response = await client.post(
            "/api/cart/items",
            content="{invalid json",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer test_token"
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unsupported_media_type_contract(self, client):
        response = await client.post(
            "/api/cart/items",
            content="product_id=prod_1&quantity=1",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": "Bearer test_token"
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_method_not_allowed_contract(self, client):
        response = await client.put("/api/cart", headers={"Authorization": "Bearer test_token"})
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_unauthorized_access_contract(self, client):
        response = await client.get("/api/cart")
        assert response.status_code == 422  # Missing authorization header

    @pytest.mark.asyncio
    async def test_cors_headers_contract(self, client):
        response = await client.get("/health", headers={"Origin": "http://localhost:3000"})
        
        if "access-control-allow-origin" in response.headers:
            assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
