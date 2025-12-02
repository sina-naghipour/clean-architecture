import pytest
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from database.connection import MongoDBConnection
from repositories.image_repository import ImageRepository
from database.database_models import ImageDB

from unittest.mock import AsyncMock, patch, MagicMock
import asyncio

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

@pytest.mark.asyncio
async def test_init_without_collection():
    repo = ImageRepository()
    assert repo.collection is None

@pytest.mark.asyncio
async def test__get_collection_lazy_loading():
    repo = ImageRepository()
    mock_collection = AsyncMock()
    with patch('repositories.image_repository.get_images_collection', AsyncMock(return_value=mock_collection)):
        result = await repo._get_collection()
        assert result == mock_collection
        assert repo.collection == mock_collection

@pytest.mark.asyncio
async def test_create_image_insert_failure(test_db_setup):
    repository, connection, collection = test_db_setup
    mock_collection = AsyncMock()
    mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id=None))
    repository.collection = mock_collection
    
    new_image = ImageDB(
        id="img_fail",
        product_id="prod_fail",
        filename="fail.jpg",
        original_name="fail.jpg",
        mime_type="image/jpeg",
        size=1000,
        width=100,
        height=100,
        is_primary=True
    )
    
    result = await repository.create_image(new_image)
    assert result is None

@pytest.mark.asyncio
async def test_get_image_by_id_malformed_data(test_db_setup):
    repository, connection, collection = test_db_setup
    bad_data = {"_id": "bad_img", "invalid": "data"}
    await collection.insert_one(bad_data)
    
    with pytest.raises(Exception):
        await repository.get_image_by_id("bad_img")

@pytest.mark.asyncio
async def test_update_image_no_changes(test_db_setup):
    repository, connection, collection = test_db_setup
    
    original = await repository.get_image_by_id("img_1")
    update_data = {"original_name": original.original_name}
    
    result = await repository.update_image("img_1", update_data)
    assert result is not None
    assert result.original_name == original.original_name

@pytest.mark.asyncio
async def test_set_primary_image_already_primary(test_db_setup):
    repository, connection, collection = test_db_setup
    
    result = await repository.set_primary_image("prod_1", "img_1")
    assert result is True

@pytest.mark.asyncio
async def test_set_primary_image_wrong_product(test_db_setup):
    repository, connection, collection = test_db_setup
    
    result = await repository.set_primary_image("prod_2", "img_1")
    assert result is False

@pytest.mark.asyncio
async def test_get_recent_images_limit_zero(test_db_setup):
    repository, connection, collection = test_db_setup
    
    images = await repository.get_recent_images(limit=0)
    assert len(images) == 0

@pytest.mark.asyncio
async def test_get_recent_images_large_limit(test_db_setup):
    repository, connection, collection = test_db_setup
    
    images = await repository.get_recent_images(limit=1000)
    assert len(images) == 3

@pytest.mark.asyncio
async def test_get_recent_images_negative_limit(test_db_setup):
    repository, connection, collection = test_db_setup

    with pytest.raises(ValueError, match="non-negative"):
        await repository.get_recent_images(limit=-1)

@pytest.mark.asyncio
async def test_count_images_by_product_id_large_collection(test_db_setup):
    repository, connection, collection = test_db_setup
    
    for i in range(10):
        image = ImageDB(
            id=f"bulk_{i}",
            product_id="prod_bulk",
            filename=f"bulk_{i}.jpg",
            original_name=f"bulk_{i}.jpg",
            mime_type="image/jpeg",
            size=1000,
            width=100,
            height=100,
            is_primary=False
        )
        await repository.create_image(image)
    
    count = await repository.count_images_by_product_id("prod_bulk")
    assert count == 10

@pytest.mark.asyncio
async def test_concurrent_set_primary_image(test_db_setup):
    repository, connection, collection = test_db_setup
    
    async def set_primary_task(image_id):
        return await repository.set_primary_image("prod_1", image_id)
    
    tasks = [set_primary_task("img_1"), set_primary_task("img_2")]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    primary_count = await collection.count_documents({"product_id": "prod_1", "is_primary": True})
    assert primary_count == 1

@pytest.mark.asyncio
async def test_update_image_with_empty_data(test_db_setup):
    repository, connection, collection = test_db_setup
    
    result = await repository.update_image("img_1", {})
    assert result is not None

@pytest.mark.asyncio
async def test_delete_image_already_deleted(test_db_setup):
    repository, connection, collection = test_db_setup
    
    await repository.delete_image("img_1")
    result = await repository.delete_image("img_1")
    assert result is False

@pytest.mark.asyncio
async def test_get_primary_image_no_primary(test_db_setup):
    repository, connection, collection = test_db_setup
    
    await collection.update_many({}, {"$set": {"is_primary": False}})
    
    result = await repository.get_primary_image_by_product_id("prod_1")
    assert result is None

@pytest.mark.asyncio
async def test_create_image_duplicate_id(test_db_setup):
    repository, connection, collection = test_db_setup
    
    duplicate_image = ImageDB(
        id="img_1",
        product_id="prod_duplicate",
        filename="duplicate.jpg",
        original_name="duplicate.jpg",
        mime_type="image/jpeg",
        size=1000,
        width=100,
        height=100,
        is_primary=True
    )
    
    with pytest.raises(Exception):
        await repository.create_image(duplicate_image)

@pytest.mark.asyncio
async def test_decorator_validation_failure(test_db_setup):
    repository, connection, collection = test_db_setup
    
    # Test get_image_by_id with empty string
    with pytest.raises(ValueError, match="Invalid image ID"):
        await repository.get_image_by_id("")
    
    # Test get_image_by_id with None
    with pytest.raises(ValueError, match="Invalid image ID"):
        await repository.get_image_by_id(None)
    
    # Test get_image_by_id with non-string
    with pytest.raises(ValueError, match="Invalid image ID"):
        await repository.get_image_by_id(123)
    
    # Test get_images_by_product_id with empty string  
    with pytest.raises(ValueError, match="Invalid product ID"):
        await repository.get_images_by_product_id("")
    
    # Test set_primary_image with empty product_id
    with pytest.raises(ValueError, match="Invalid product ID"):
        await repository.set_primary_image("", "img_1")
    
    # Test set_primary_image with empty image_id
    with pytest.raises(ValueError, match="Invalid image ID"):
        await repository.set_primary_image("prod_1", "")
    
    # Test set_primary_image with None values
    with pytest.raises(ValueError, match="Invalid product ID"):
        await repository.set_primary_image(None, "img_1")
    
    with pytest.raises(ValueError, match="Invalid image ID"):
        await repository.set_primary_image("prod_1", None)
    
    # Test get_primary_image_by_product_id with empty string
    with pytest.raises(ValueError, match="Invalid product ID"):
        await repository.get_primary_image_by_product_id("")
    
    # Test count_images_by_product_id with empty string
    with pytest.raises(ValueError, match="Invalid product ID"):
        await repository.count_images_by_product_id("")


@pytest.mark.asyncio
async def test_decorator_error_handling():
    mock_collection = AsyncMock()
    mock_collection.find_one = AsyncMock(side_effect=Exception("DB Error"))
    repo = ImageRepository(collection=mock_collection)
    
    with pytest.raises(Exception):
        await repo.get_image_by_id("valid_id")

@pytest.mark.asyncio
async def test_empty_string_fields(test_db_setup):
    repository, connection, collection = test_db_setup
    
    empty_image = ImageDB(
        id="img_empty",
        product_id="",
        filename="",
        original_name="",
        mime_type="",
        size=0,
        width=0,
        height=0,
        is_primary=False
    )
    
    result = await repository.create_image(empty_image)
    assert result is not None

@pytest.mark.asyncio
async def test_set_primary_image_twice_different_images(test_db_setup):
    repository, connection, collection = test_db_setup
    
    result1 = await repository.set_primary_image("prod_1", "img_2")
    assert result1 is True
    
    result2 = await repository.set_primary_image("prod_1", "img_1")
    assert result2 is True
    
    primary = await repository.get_primary_image_by_product_id("prod_1")
    assert primary.id == "img_1"

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