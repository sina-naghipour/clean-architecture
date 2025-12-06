import pytest
import asyncio
import os
import time
from motor.motor_asyncio import AsyncIOMotorClient
from database.connection import MongoDBConnection
from repositories.product_repository import ProductRepository
from database.database_models import ProductDB

TEST_DB_NAME = "test_product_db"
TEST_CONNECTION_STRING = os.getenv("TEST_MONGODB_URI", "mongodb://localhost:27017/")

@pytest.fixture(scope="function")
async def test_db_setup():
    connection = MongoDBConnection()
    await connection.connect(TEST_CONNECTION_STRING, TEST_DB_NAME)
    collection = connection.get_collection()
    
    await collection.delete_many({})
    
    test_products = [
        {
            "_id": "prod_1",
            "name": "Laptop",
            "description": "High-performance laptop",
            "price": 999.99,
            "stock": 10,
            "tags": ["electronics", "computers"],
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        },
        {
            "_id": "prod_2", 
            "name": "Mouse",
            "description": "Wireless mouse",
            "price": 29.99,
            "stock": 50,
            "tags": ["electronics", "accessories"],
            "created_at": "2023-01-02T00:00:00",
            "updated_at": "2023-01-02T00:00:00"
        },
        {
            "_id": "prod_3",
            "name": "Desk",
            "description": "Wooden desk",
            "price": 199.99,
            "stock": 5,
            "tags": ["furniture", "office"],
            "created_at": "2023-01-03T00:00:00", 
            "updated_at": "2023-01-03T00:00:00"
        }
    ]
    
    await collection.insert_many(test_products)
    
    repository = ProductRepository(collection=collection)
    
    yield repository, connection, collection
    
    await collection.delete_many({})
    await connection.close()

@pytest.mark.asyncio
async def test_create_product_success(test_db_setup):
    repository, connection, collection = test_db_setup
    
    new_product = ProductDB(
        id="prod_4",
        name="Keyboard",
        description="Mechanical keyboard",
        price=79.99,
        stock=25,
        tags=["electronics", "accessories"]
    )
    
    result = await repository.create_product(new_product)
    
    assert result is not None
    assert result.name == "Keyboard"
    assert result.price == 79.99
    
    fetched = await repository.get_product_by_id("prod_4")
    assert fetched.name == "Keyboard"

@pytest.mark.asyncio
async def test_create_product_duplicate_name(test_db_setup):
    repository, connection, collection = test_db_setup
    
    duplicate_product = ProductDB(
        id="prod_5",
        name="Laptop",
        description="Another laptop",
        price=899.99,
        stock=5
    )
    
    result = await repository.create_product(duplicate_product)
    assert result is None

@pytest.mark.asyncio
async def test_get_product_by_id_success(test_db_setup):
    repository, connection, collection = test_db_setup
    
    result = await repository.get_product_by_id("prod_1")
    
    assert result is not None
    assert result.id == "prod_1"
    assert result.name == "Laptop"
    assert result.price == 999.99

@pytest.mark.asyncio
async def test_get_product_by_id_not_found(test_db_setup):
    repository, connection, collection = test_db_setup
    
    result = await repository.get_product_by_id("non_existent")
    assert result is None

@pytest.mark.asyncio
async def test_get_product_by_name(test_db_setup):
    repository, connection, collection = test_db_setup
    
    result = await repository.get_product_by_name("Mouse")
    
    assert result is not None
    assert result.name == "Mouse"
    assert result.price == 29.99

@pytest.mark.asyncio
async def test_list_products_basic(test_db_setup):
    repository, connection, collection = test_db_setup
    
    products = await repository.list_products(skip=0, limit=2)
    
    assert len(products) == 2
    assert products[0].name == "Desk"
    assert products[1].name == "Mouse"

@pytest.mark.asyncio
async def test_list_products_with_search(test_db_setup):
    repository, connection, collection = test_db_setup
    
    products = await repository.list_products(
        skip=0, 
        limit=10, 
        search_query="laptop"
    )
    
    assert len(products) == 1
    assert products[0].name == "Laptop"

@pytest.mark.asyncio
async def test_list_products_with_tags(test_db_setup):
    repository, connection, collection = test_db_setup
    
    products = await repository.list_products(
        skip=0,
        limit=10,
        tags=["electronics"]
    )
    
    assert len(products) == 2
    product_names = [p.name for p in products]
    assert "Laptop" in product_names
    assert "Mouse" in product_names

@pytest.mark.asyncio
async def test_count_products(test_db_setup):
    repository, connection, collection = test_db_setup
    
    count = await repository.count_products()
    assert count == 3

@pytest.mark.asyncio
async def test_count_products_with_search(test_db_setup):
    repository, connection, collection = test_db_setup
    
    count = await repository.count_products(search_query="wireless")
    assert count == 1

@pytest.mark.asyncio
async def test_update_product_success(test_db_setup):
    repository, connection, collection = test_db_setup
    
    update_data = {
        "name": "Gaming Laptop",
        "price": 1299.99,
        "stock": 8
    }
    
    result = await repository.update_product("prod_1", update_data)
    
    assert result is not None
    assert result.name == "Gaming Laptop"
    assert result.price == 1299.99
    assert result.stock == 8

@pytest.mark.asyncio
async def test_update_product_not_found(test_db_setup):
    repository, connection, collection = test_db_setup
    
    result = await repository.update_product("non_existent", {"name": "Test"})
    assert result is None

@pytest.mark.asyncio
async def test_delete_product_success(test_db_setup):
    repository, connection, collection = test_db_setup
    
    result = await repository.delete_product("prod_1")
    assert result is True
    
    fetched = await repository.get_product_by_id("prod_1")
    assert fetched is None

@pytest.mark.asyncio
async def test_delete_product_not_found(test_db_setup):
    repository, connection, collection = test_db_setup
    
    result = await repository.delete_product("non_existent")
    assert result is False

@pytest.mark.asyncio
async def test_update_inventory(test_db_setup):
    repository, connection, collection = test_db_setup
    
    result = await repository.update_inventory("prod_1", 15)
    assert result is not None
    assert result.stock == 15

@pytest.mark.asyncio
async def test_get_products_by_tags(test_db_setup):
    repository, connection, collection = test_db_setup
    
    products = await repository.get_products_by_tags(["electronics"])
    assert len(products) == 2
    assert all("electronics" in product.tags for product in products)

@pytest.mark.asyncio
async def test_get_popular_tags(test_db_setup):
    repository, connection, collection = test_db_setup
    
    popular_tags = await repository.get_popular_tags(limit=5)
    assert len(popular_tags) > 0
    tag_names = [tag["tag"] for tag in popular_tags]
    assert "electronics" in tag_names

@pytest.mark.asyncio
async def test_tag_query_performance(test_db_setup):
    repository, connection, collection = test_db_setup
    
    await collection.create_index("tags")
    
    start_time = time.time()
    
    for _ in range(100):
        cursor = collection.find({"tags": "electronics"})
        results = await cursor.to_list(length=100)
    
    end_time = time.time()
    query_time = end_time - start_time
    
    print(f"Tag query time for 100 iterations: {query_time:.4f} seconds")
    assert query_time < 2.0

@pytest.mark.asyncio
async def test_search_query_performance(test_db_setup):
    repository, connection, collection = test_db_setup
    
    start_time = time.time()
    
    for _ in range(100):
        cursor = collection.find({
            "$or": [
                {"name": {"$regex": "laptop", "$options": "i"}},
                {"description": {"$regex": "wireless", "$options": "i"}}
            ]
        })
        results = await cursor.to_list(length=100)
    
    end_time = time.time()
    query_time = end_time - start_time
    
    print(f"Search query time for 100 iterations: {query_time:.4f} seconds")
    assert query_time < 2.0
@pytest.mark.asyncio
async def test_index_effectiveness(test_db_setup):
    repository, connection, collection = test_db_setup
    
    await collection.delete_many({})
    
    bulk_data = []
    for i in range(5000):
        bulk_data.append({
            "_id": f"prod_{i}",
            "name": f"Product {i}",
            "description": f"Description {i}",
            "price": i * 10.0,
            "stock": i % 100,
            "tags": ["electronics"] if i % 10 == 0 else ["furniture"],
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        })
    
    await collection.insert_many(bulk_data)
    
    await collection.drop_indexes()
    
    start_time = time.time()
    for _ in range(10):
        cursor = collection.find({"tags": "electronics"})
        results = await cursor.to_list(length=1000)
    time_without_index = time.time() - start_time
    
    await collection.create_index([("tags", 1)])
    
    start_time = time.time()
    for _ in range(10):
        cursor = collection.find({"tags": "electronics"})
        results = await cursor.to_list(length=1000)
    time_with_index = time.time() - start_time
    
    improvement = ((time_without_index - time_with_index) / time_without_index) * 100
    print(f"Without index: {time_without_index:.4f}s, With index: {time_with_index:.4f}s, Improvement: {improvement:.1f}%")
    
    assert time_with_index < time_without_index 
    
if __name__ == "__main__":
    import asyncio
    
    async def run_tests():
        connection = MongoDBConnection()
        await connection.connect(TEST_CONNECTION_STRING, TEST_DB_NAME)
        collection = connection.get_collection()
        await collection.delete_many({})
        
        repo = ProductRepository(collection=collection)
        
        test_product = ProductDB(
            id="manual_test_1",
            name="Test Product",
            description="Test Description",
            price=100.0,
            stock=10,
            tags=["test"]
        )
        
        result = await repo.create_product(test_product)
        print(f"Create product: {'SUCCESS' if result else 'FAILED'}")
        
        fetched = await repo.get_product_by_id("manual_test_1")
        print(f"Get product: {'SUCCESS' if fetched else 'FAILED'}")
        
        await collection.delete_many({})
        await connection.close()
    
    asyncio.run(run_tests())