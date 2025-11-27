import pytest
import os
from datetime import datetime
from app.repositories.product_repository import ProductRepository
from app.database.database_models import ProductDB
from app.database.connection import MongoDBConnection

class TestProductRepositoryIntegration:
    
    @pytest.fixture(scope="class")
    def test_db_connection(self):
        connection = MongoDBConnection()
        test_connection_string = os.getenv("MONGODB_TEST_URI", "mongodb://localhost:27017/")
        test_db_name = os.getenv("MONGODB_TEST_DB_NAME", "product_test_db")
        
        try:
            connection.connect(connection_string=test_connection_string, db_name=test_db_name)
            connection.client.admin.command('ping')
            yield connection
        except Exception as e:
            pytest.skip(f"Could not connect to test database: {e}")
        finally:
            connection.close()

    @pytest.fixture
    def repository(self, test_db_connection):
        collection = test_db_connection.db["products"]
        collection.delete_many({})
        return ProductRepository(collection=collection)

    @pytest.fixture
    def sample_product(self):
        return ProductDB(
            name=f"Integration Test Product {datetime.utcnow().timestamp()}",
            price=99.99,
            stock=50,
            description="Integration test product description"
        )

    @pytest.mark.asyncio
    async def test_create_and_retrieve_product(self, repository, sample_product):
        created_product = await repository.create_product(sample_product)
        assert created_product is not None
        assert created_product.name == sample_product.name
        assert created_product.price == sample_product.price
        
        retrieved_product = await repository.get_product_by_id(created_product.id)
        assert retrieved_product is not None
        assert retrieved_product.id == created_product.id
        assert retrieved_product.name == sample_product.name
        assert retrieved_product.price == sample_product.price
        assert retrieved_product.stock == sample_product.stock

    @pytest.mark.asyncio
    async def test_duplicate_product_name_prevention(self, repository):
        product1 = ProductDB(
            name="Unique Product Name",
            price=49.99,
            stock=25,
            description="First product"
        )
        
        product2 = ProductDB(
            name="UNIQUE PRODUCT NAME",
            price=39.99,
            stock=30,
            description="Second product"
        )
        
        first_product = await repository.create_product(product1)
        assert first_product is not None
        
        second_product = await repository.create_product(product2)
        assert second_product is None

    @pytest.mark.asyncio
    async def test_update_product(self, repository):
        original_product = ProductDB(
            name="Original Product",
            price=99.99,
            stock=50,
            description="Original description"
        )
        
        created_product = await repository.create_product(original_product)
        assert created_product is not None
        
        update_data = {
            "name": "Updated Product Name",
            "price": 149.99,
            "stock": 75,
            "description": "Updated description"
        }
        
        updated_product = await repository.update_product(created_product.id, update_data)
        assert updated_product is not None
        assert updated_product.name == "Updated Product Name"
        assert updated_product.price == 149.99
        assert updated_product.stock == 75
        assert updated_product.description == "Updated description"

    @pytest.mark.asyncio
    async def test_patch_product(self, repository):
        original_product = ProductDB(
            name="Patch Test Product",
            price=100.0,
            stock=100,
            description="Original description"
        )
        
        created_product = await repository.create_product(original_product)
        assert created_product is not None
        
        patch_data = {"stock": 200, "price": 79.99}
        patched_product = await repository.patch_product(created_product.id, patch_data)
        
        assert patched_product is not None
        assert patched_product.stock == 200
        assert patched_product.price == 79.99
        assert patched_product.name == "Patch Test Product"

    @pytest.mark.asyncio
    async def test_delete_product(self, repository):
        product = ProductDB(
            name="Product To Delete",
            price=50.0,
            stock=10,
            description="Will be deleted"
        )
        
        created_product = await repository.create_product(product)
        assert created_product is not None
        
        delete_result = await repository.delete_product(created_product.id)
        assert delete_result is True
        
        deleted_product = await repository.get_product_by_id(created_product.id)
        assert deleted_product is None

    @pytest.mark.asyncio
    async def test_list_products_pagination(self, repository):
        for i in range(5):
            product = ProductDB(
                name=f"Pagination Product {i}",
                price=10.0 * (i + 1),
                stock=i * 10,
                description=f"Description {i}"
            )
            await repository.create_product(product)
        
        first_page = await repository.list_products(skip=0, limit=2)
        assert len(first_page) == 2
        
        second_page = await repository.list_products(skip=2, limit=2)
        assert len(second_page) == 2
        
        third_page = await repository.list_products(skip=4, limit=2)
        assert len(third_page) == 1

    @pytest.mark.asyncio
    async def test_search_products(self, repository):
        product1 = ProductDB(
            name="Apple iPhone",
            price=999.99,
            stock=10,
            description="Smartphone from Apple"
        )
        
        product2 = ProductDB(
            name="Samsung Galaxy",
            price=899.99,
            stock=15,
            description="Android smartphone"
        )
        
        product3 = ProductDB(
            name="Google Pixel",
            price=799.99,
            stock=8,
            description="Google's smartphone"
        )
        
        await repository.create_product(product1)
        await repository.create_product(product2)
        await repository.create_product(product3)
        
        apple_results = await repository.list_products(search_query="Apple")
        assert len(apple_results) == 1
        assert apple_results[0].name == "Apple iPhone"
        
        phone_results = await repository.list_products(search_query="phone")
        assert len(phone_results) == 3
        
        android_results = await repository.list_products(search_query="Android")
        assert len(android_results) == 1
        assert android_results[0].name == "Samsung Galaxy"

    @pytest.mark.asyncio
    async def test_update_inventory(self, repository):
        product = ProductDB(
            name="Inventory Test Product",
            price=50.0,
            stock=100,
            description="Inventory test"
        )
        
        created_product = await repository.create_product(product)
        assert created_product is not None
        
        updated_product = await repository.update_inventory(created_product.id, 150)
        assert updated_product is not None
        assert updated_product.stock == 150
        assert updated_product.name == "Inventory Test Product"
        assert updated_product.price == 50.0

    @pytest.mark.asyncio
    async def test_count_products(self, repository):
        initial_count = await repository.count_products()
        
        for i in range(3):
            product = ProductDB(
                name=f"Count Test Product {i}",
                price=10.0 * (i + 1),
                stock=i * 5
            )
            await repository.create_product(product)
        
        final_count = await repository.count_products()
        assert final_count == initial_count + 3
        
        search_count = await repository.count_products(search_query="Count Test")
        assert search_count == 3

    @pytest.mark.asyncio
    async def test_product_persistence(self, repository, test_db_connection):
        product = ProductDB(
            name="Persistence Test Product",
            price=75.0,
            stock=25,
            description="Persistence test"
        )
        
        created_product = await repository.create_product(product)
        assert created_product is not None
        
        new_collection = test_db_connection.db["products"]
        new_repository = ProductRepository(collection=new_collection)
        persisted_product = await new_repository.get_product_by_id(created_product.id)
        
        assert persisted_product is not None
        assert persisted_product.id == created_product.id
        assert persisted_product.name == created_product.name
        assert persisted_product.price == created_product.price
        assert persisted_product.stock == created_product.stock