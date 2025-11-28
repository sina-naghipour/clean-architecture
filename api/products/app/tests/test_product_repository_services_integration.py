import pytest
from unittest.mock import Mock
from fastapi import Request
from services.product_services import ProductService
from repositories.product_repository import ProductRepository
from database import pydantic_models
from database.database_models import ProductDB
from database.connection import get_products_collection

class TestProductServiceRepositoryIntegration:
    @pytest.fixture
    def mock_logger(self):
        return Mock()

    @pytest.fixture
    def mock_request(self):
        request = Mock(spec=Request)
        request.url = "http://test.com/api/products"
        return request

    @pytest.fixture
    def repository(self):
        collection = get_products_collection()
        collection.delete_many({})
        return ProductRepository(collection=collection)

    @pytest.fixture
    def service(self, mock_logger, repository):
        service = ProductService(mock_logger)
        service.product_repository = repository
        return service

    @pytest.mark.asyncio
    async def test_create_product_flow(self, service, mock_request, repository):
        product_data = pydantic_models.ProductRequest(
            name=f"Integration Test Product {id(self)}",
            price=99.99,
            stock=50,
            description="Integration test"
        )
        
        result = await service.create_product(mock_request, product_data)
        
        assert result.status_code == 201
        created_id = result.headers["Location"].split("/")[-1]
        
        retrieved = await repository.get_product_by_id(created_id)
        assert retrieved is not None
        assert retrieved.name == product_data.name
        assert retrieved.price == 99.99

    @pytest.mark.asyncio
    async def test_get_product_flow(self, service, mock_request, repository):
        product_db = ProductDB(
            name=f"Retrieval Test {id(self)}",
            price=49.99,
            stock=25,
            description="For retrieval test"
        )
        created = await repository.create_product(product_db)
        
        result = await service.get_product(mock_request, created.id)
        
        assert result.id == created.id
        assert result.name == product_db.name
        assert result.price == 49.99

    @pytest.mark.asyncio
    async def test_list_products_flow(self, service, mock_request, repository):
        for i in range(3):
            product = ProductDB(
                name=f"List Product {i} {id(self)}",
                price=10.0 * (i + 1),
                stock=i * 5
            )
            await repository.create_product(product)
        
        query_params = pydantic_models.ProductQueryParams(page=1, page_size=10)
        result = await service.list_products(mock_request, query_params)
        
        assert len(result.items) >= 3
        assert result.total >= 3
        assert result.page == 1

    @pytest.mark.asyncio
    async def test_update_product_flow(self, service, mock_request, repository):
        original = ProductDB(
            name=f"Original Name {id(self)}",
            price=25.0,
            stock=30
        )
        created = await repository.create_product(original)
        
        update_data = pydantic_models.ProductRequest(
            name=f"Updated Name {id(self)}",
            price=35.0,
            stock=40,
            description="Updated description"
        )
        
        result = await service.update_product(mock_request, created.id, update_data)
        
        assert result.name == update_data.name
        assert result.price == 35.0
        
        updated_in_db = await repository.get_product_by_id(created.id)
        assert updated_in_db.name == update_data.name
        assert updated_in_db.price == 35.0

    @pytest.mark.asyncio
    async def test_patch_product_flow(self, service, mock_request, repository):
        original = ProductDB(
            name=f"Patch Original {id(self)}",
            price=50.0,
            stock=100
        )
        created = await repository.create_product(original)
        
        patch_data = pydantic_models.ProductPatch(stock=75)
        
        result = await service.patch_product(mock_request, created.id, patch_data)
        
        assert result.stock == 75
        assert result.name == original.name
        
        patched_in_db = await repository.get_product_by_id(created.id)
        assert patched_in_db.stock == 75

    @pytest.mark.asyncio
    async def test_delete_product_flow(self, service, mock_request, repository):
        product = ProductDB(
            name=f"To Delete {id(self)}",
            price=15.0,
            stock=5
        )
        created = await repository.create_product(product)
        
        result = await service.delete_product(mock_request, created.id)
        
        assert result is None
        
        deleted = await repository.get_product_by_id(created.id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_update_inventory_flow(self, service, mock_request, repository):
        product = ProductDB(
            name=f"Inventory Test {id(self)}",
            price=20.0,
            stock=10
        )
        created = await repository.create_product(product)
        
        inventory_data = pydantic_models.InventoryUpdate(stock=50)
        
        result = await service.update_inventory(mock_request, created.id, inventory_data)
        
        assert result.stock == 50
        
        updated = await repository.get_product_by_id(created.id)
        assert updated.stock == 50

    @pytest.mark.asyncio
    async def test_error_propagation_from_repository(self, service, mock_request, repository):
        product1 = ProductDB(name=f"Duplicate Test {id(self)}", price=10.0, stock=5)
        await repository.create_product(product1)
        
        product_data = pydantic_models.ProductRequest(
            name=f"duplicate test {id(self)}",
            price=15.0,
            stock=10
        )
        
        result = await service.create_product(mock_request, product_data)
        
        assert result.status_code == 409

    @pytest.mark.asyncio
    async def test_search_flow(self, service, mock_request, repository):
        product1 = ProductDB(name=f"Apple iPhone {id(self)}", price=999.0, stock=10, description="Smartphone")
        product2 = ProductDB(name=f"Samsung Phone {id(self)}", price=899.0, stock=15, description="Android")
        product3 = ProductDB(name=f"Google Tablet {id(self)}", price=499.0, stock=8, description="Tablet")
        
        await repository.create_product(product1)
        await repository.create_product(product2)
        await repository.create_product(product3)
        
        query_params = pydantic_models.ProductQueryParams(page=1, page_size=10, q="phone")
        result = await service.list_products(mock_request, query_params)
        
        phone_products = [item for item in result.items if "phone" in item.name.lower()]
        assert len(phone_products) == 2