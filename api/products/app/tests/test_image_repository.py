import pytest
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from database.connection import MongoDBConnection
from repositories.image_repository import ImageRepository
from database.database_models import ImageDB

TEST_DB_NAME = "test_product_db"
TEST_CONNECTION_STRING = os.getenv("TEST_MONGODB_URI", "mongodb://localhost:27017/")

@pytest.fixture(scope="function")
async def test_db_setup():
    connection = MongoDBConnection()
    await connection.connect(TEST_CONNECTION_STRING, TEST_DB_NAME)
    collection = connection.get_images_collection()
    
    await collection.delete_many({})
    
    test_images = [
        {
            "_id": "img_1",
            "product_id": "prod_1",
            "filename": "prod_1_img1.jpg",
            "original_name": "laptop_front.jpg",
            "mime_type": "image/jpeg",
            "size": 1024000,
            "width": 800,
            "height": 600,
            "is_primary": True,
            "uploaded_at": "2023-01-01T10:00:00"
        },
        {
            "_id": "img_2",
            "product_id": "prod_1",
            "filename": "prod_1_img2.jpg",
            "original_name": "laptop_back.jpg",
            "mime_type": "image/jpeg",
            "size": 980000,
            "width": 800,
            "height": 600,
            "is_primary": False,
            "uploaded_at": "2023-01-01T10:05:00"
        },
        {
            "_id": "img_3",
            "product_id": "prod_2",
            "filename": "prod_2_img1.jpg",
            "original_name": "mouse.jpg",
            "mime_type": "image/jpeg",
            "size": 512000,
            "width": 600,
            "height": 400,
            "is_primary": True,
            "uploaded_at": "2023-01-02T09:00:00"
        }
    ]
    
    await collection.insert_many(test_images)
    
    repository = ImageRepository(collection=collection)
    
    yield repository, connection, collection
    
    await collection.delete_many({})
    await connection.close()

@pytest.mark.asyncio
async def test_create_image_success(test_db_setup):
    repository, connection, collection = test_db_setup
    
    new_image = ImageDB(
        id="img_4",
        product_id="prod_3",
        filename="prod_3_img1.jpg",
        original_name="keyboard.jpg",
        mime_type="image/jpeg",
        size=750000,
        width=700,
        height=500,
        is_primary=True
    )
    
    result = await repository.create_image(new_image)
    
    assert result is not None
    assert result.filename == "prod_3_img1.jpg"
    assert result.product_id == "prod_3"
    
    fetched = await repository.get_image_by_id("img_4")
    assert fetched.filename == "prod_3_img1.jpg"

@pytest.mark.asyncio
async def test_get_image_by_id_success(test_db_setup):
    repository, connection, collection = test_db_setup
    
    result = await repository.get_image_by_id("img_1")
    
    assert result is not None
    assert result.id == "img_1"
    assert result.product_id == "prod_1"
    assert result.is_primary == True

@pytest.mark.asyncio
async def test_get_image_by_id_not_found(test_db_setup):
    repository, connection, collection = test_db_setup
    
    result = await repository.get_image_by_id("non_existent")
    assert result is None

@pytest.mark.asyncio
async def test_get_images_by_product_id(test_db_setup):
    repository, connection, collection = test_db_setup
    
    images = await repository.get_images_by_product_id("prod_1")
    
    assert len(images) == 2
    image_ids = [img.id for img in images]
    assert "img_1" in image_ids
    assert "img_2" in image_ids

@pytest.mark.asyncio
async def test_get_images_by_product_id_empty(test_db_setup):
    repository, connection, collection = test_db_setup
    
    images = await repository.get_images_by_product_id("prod_999")
    assert len(images) == 0

@pytest.mark.asyncio
async def test_get_primary_image_by_product_id_success(test_db_setup):
    repository, connection, collection = test_db_setup
    
    result = await repository.get_primary_image_by_product_id("prod_1")
    
    assert result is not None
    assert result.id == "img_1"
    assert result.is_primary == True

@pytest.mark.asyncio
async def test_get_primary_image_by_product_id_not_found(test_db_setup):
    repository, connection, collection = test_db_setup
    
    result = await repository.get_primary_image_by_product_id("prod_999")
    assert result is None

@pytest.mark.asyncio
async def test_update_image_success(test_db_setup):
    repository, connection, collection = test_db_setup
    
    update_data = {
        "original_name": "updated_laptop.jpg",
        "is_primary": False
    }
    
    result = await repository.update_image("img_1", update_data)
    
    assert result is not None
    assert result.original_name == "updated_laptop.jpg"
    assert result.is_primary == False

@pytest.mark.asyncio
async def test_update_image_not_found(test_db_setup):
    repository, connection, collection = test_db_setup
    
    result = await repository.update_image("non_existent", {"original_name": "test.jpg"})
    assert result is None

@pytest.mark.asyncio
async def test_delete_image_success(test_db_setup):
    repository, connection, collection = test_db_setup
    
    result = await repository.delete_image("img_1")
    assert result is True
    
    fetched = await repository.get_image_by_id("img_1")
    assert fetched is None

@pytest.mark.asyncio
async def test_delete_image_not_found(test_db_setup):
    repository, connection, collection = test_db_setup
    
    result = await repository.delete_image("non_existent")
    assert result is False

@pytest.mark.asyncio
async def test_set_primary_image_success(test_db_setup):
    repository, connection, collection = test_db_setup
    
    result = await repository.set_primary_image("prod_1", "img_2")
    
    assert result is True
    
    primary_image = await repository.get_primary_image_by_product_id("prod_1")
    assert primary_image.id == "img_2"
    
    old_primary = await repository.get_image_by_id("img_1")
    assert old_primary.is_primary == False

@pytest.mark.asyncio
async def test_set_primary_image_not_found(test_db_setup):
    repository, connection, collection = test_db_setup
    
    result = await repository.set_primary_image("prod_999", "img_999")
    assert result is False

@pytest.mark.asyncio
async def test_count_images_by_product_id(test_db_setup):
    repository, connection, collection = test_db_setup
    
    count = await repository.count_images_by_product_id("prod_1")
    assert count == 2
    
    count_empty = await repository.count_images_by_product_id("prod_999")
    assert count_empty == 0

@pytest.mark.asyncio
async def test_get_recent_images(test_db_setup):
    repository, connection, collection = test_db_setup
    
    recent_images = await repository.get_recent_images(limit=2)
    
    assert len(recent_images) == 2
    assert recent_images[0].id == "img_3"
    assert recent_images[1].id == "img_2"

if __name__ == "__main__":
    import asyncio
    
    async def run_tests():
        connection = MongoDBConnection()
        await connection.connect(TEST_CONNECTION_STRING, TEST_DB_NAME)
        collection = connection.get_images_collection()
        await collection.delete_many({})
        
        repo = ImageRepository(collection=collection)
        
        test_image = ImageDB(
            id="test_img_1",
            product_id="test_prod_1",
            filename="test_image.jpg",
            original_name="test.jpg",
            mime_type="image/jpeg",
            size=1000000,
            width=800,
            height=600,
            is_primary=True
        )
        
        result = await repo.create_image(test_image)
        print(f"Create image: {'SUCCESS' if result else 'FAILED'}")
        
        fetched = await repo.get_image_by_id("test_img_1")
        print(f"Get image: {'SUCCESS' if fetched else 'FAILED'}")
        
        await collection.delete_many({})
        await connection.close()
    
    asyncio.run(run_tests())