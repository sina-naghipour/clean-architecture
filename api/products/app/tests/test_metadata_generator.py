import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

from services.metadata_generator import MetadataGenerator

@pytest.fixture
def temp_storage():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def metadata_generator(temp_storage):
    return MetadataGenerator(base_storage_path=temp_storage)

@pytest.fixture
def sample_image_data():
    return {
        "id": "img_123",
        "url": "/static/img/products/prod_456/prod_456_abc123.jpg",
        "is_primary": True,
        "width": 800,
        "height": 600,
        "filename": "prod_456_abc123.jpg",
        "mime_type": "image/jpeg",
        "uploaded_at": "2023-10-01T12:00:00Z"
    }

@pytest.fixture
def sample_product_data():
    return {
        "id": "prod_456",
        "name": "Test Product",
        "images": [],
        "created_at": "2023-10-01T10:00:00Z",
        "updated_at": "2023-10-01T12:00:00Z"
    }

def test_init_creates_directory(temp_storage):
    generator = MetadataGenerator(base_storage_path=temp_storage)
    assert generator.base_storage_path.exists()
    assert generator.metadata_file.parent == generator.base_storage_path

def test_read_existing_metadata_empty(metadata_generator):
    metadata = metadata_generator._read_existing_metadata()
    assert metadata == {}

def test_read_existing_metadata_with_content(temp_storage):
    metadata_file = temp_storage / "metadata.json"
    test_data = {"test": "data"}
    
    with open(metadata_file, 'w') as f:
        json.dump(test_data, f)
    
    generator = MetadataGenerator(base_storage_path=temp_storage)
    metadata = generator._read_existing_metadata()
    
    assert metadata == test_data

def test_read_existing_metadata_invalid_json(temp_storage):
    metadata_file = temp_storage / "metadata.json"
    
    with open(metadata_file, 'w') as f:
        f.write("invalid json")
    
    generator = MetadataGenerator(base_storage_path=temp_storage)
    
    with pytest.raises(json.JSONDecodeError):
        generator._read_existing_metadata()

def test_write_metadata_atomic_success(metadata_generator):
    test_metadata = {"product_1": {"name": "Test", "images": []}}
    
    success = metadata_generator._write_metadata_atomic(test_metadata)
    
    assert success is True
    assert metadata_generator.metadata_file.exists()
    
    with open(metadata_generator.metadata_file, 'r') as f:
        loaded = json.load(f)
    
    assert loaded == test_metadata

def test_write_metadata_atomic_failure(metadata_generator):
    with patch('builtins.open', side_effect=IOError("Permission denied")):
        success = metadata_generator._write_metadata_atomic({"test": "data"})
        assert success is False

def test_generate_product_metadata_success(metadata_generator, sample_image_data):
    product_id = "prod_456"
    product_name = "Test Product"
    images = [sample_image_data]
    
    success = metadata_generator.generate_product_metadata(
        product_id=product_id,
        product_name=product_name,
        images=images
    )
    
    assert success is True
    
    metadata = metadata_generator._read_existing_metadata()
    assert product_id in metadata
    assert metadata[product_id]["name"] == product_name
    assert metadata[product_id]["images"] == images
    assert "updated_at" in metadata[product_id]

def test_update_product_images_add_operation(metadata_generator, sample_image_data):
    product_id = "prod_456"
    product_name = "Test Product"
    
    success = metadata_generator.update_product_images(
        product_id=product_id,
        product_name=product_name,
        image_data=sample_image_data,
        operation="add"
    )
    
    assert success is True
    
    metadata = metadata_generator._read_existing_metadata()
    assert product_id in metadata
    assert metadata[product_id]["name"] == product_name
    assert len(metadata[product_id]["images"]) == 1
    assert metadata[product_id]["images"][0] == sample_image_data

def test_update_product_images_remove_operation(metadata_generator, sample_image_data):
    product_id = "prod_456"
    product_name = "Test Product"
    
    metadata_generator.update_product_images(
        product_id=product_id,
        product_name=product_name,
        image_data=sample_image_data,
        operation="add"
    )
    
    success = metadata_generator.update_product_images(
        product_id=product_id,
        product_name=product_name,
        image_data={"id": "img_123"},
        operation="remove"
    )
    
    assert success is True
    
    metadata = metadata_generator._read_existing_metadata()
    assert len(metadata[product_id]["images"]) == 0

def test_update_product_images_update_primary_operation(metadata_generator):
    product_id = "prod_456"
    product_name = "Test Product"
    
    image1 = {"id": "img_1", "url": "/img1.jpg", "is_primary": True}
    image2 = {"id": "img_2", "url": "/img2.jpg", "is_primary": False}
    
    metadata_generator.update_product_images(
        product_id=product_id,
        product_name=product_name,
        image_data=image1,
        operation="add"
    )
    
    metadata_generator.update_product_images(
        product_id=product_id,
        product_name=product_name,
        image_data=image2,
        operation="add"
    )
    
    metadata_generator.update_product_images(
        product_id=product_id,
        product_name=product_name,
        image_data={"id": "img_2"},
        operation="update_primary"
    )
    
    metadata = metadata_generator._read_existing_metadata()
    images = metadata[product_id]["images"]
    
    assert len(images) == 2
    assert images[0]["is_primary"] is False
    assert images[1]["is_primary"] is True

def test_remove_product_success(metadata_generator):
    product_id = "prod_456"
    product_name = "Test Product"
    
    metadata_generator.update_product_images(
        product_id=product_id,
        product_name=product_name,
        image_data={"id": "img_1", "url": "/img1.jpg", "is_primary": True},
        operation="add"
    )
    
    success = metadata_generator.remove_product(product_id)
    
    assert success is True
    
    metadata = metadata_generator._read_existing_metadata()
    assert product_id not in metadata

def test_remove_product_not_found(metadata_generator):
    success = metadata_generator.remove_product("non_existent")
    assert success is True

def test_get_product_metadata(metadata_generator):
    product_id = "prod_456"
    product_name = "Test Product"
    
    metadata_generator.update_product_images(
        product_id=product_id,
        product_name=product_name,
        image_data={"id": "img_1", "url": "/img1.jpg", "is_primary": True},
        operation="add"
    )
    
    metadata = metadata_generator.get_product_metadata(product_id)
    
    assert metadata["id"] == product_id
    assert metadata["name"] == product_name
    assert len(metadata["images"]) == 1

def test_get_product_metadata_not_found(metadata_generator):
    metadata = metadata_generator.get_product_metadata("non_existent")
    assert metadata == {}

def test_get_all_metadata(metadata_generator):
    metadata_generator.update_product_images(
        product_id="prod_1",
        product_name="Product 1",
        image_data={"id": "img_1", "url": "/img1.jpg", "is_primary": True},
        operation="add"
    )
    
    metadata_generator.update_product_images(
        product_id="prod_2",
        product_name="Product 2",
        image_data={"id": "img_2", "url": "/img2.jpg", "is_primary": True},
        operation="add"
    )
    
    all_metadata = metadata_generator.get_all_metadata()
    
    assert len(all_metadata) == 2
    assert "prod_1" in all_metadata
    assert "prod_2" in all_metadata

def test_validate_metadata_schema_valid(metadata_generator):
    valid_metadata = {
        "prod_1": {
            "id": "prod_1",
            "name": "Product 1",
            "images": [
                {"id": "img_1", "url": "/img1.jpg", "is_primary": True}
            ],
            "updated_at": "2023-10-01T12:00:00Z"
        }
    }
    
    with open(metadata_generator.metadata_file, 'w') as f:
        json.dump(valid_metadata, f)
    
    is_valid = metadata_generator.validate_metadata_schema()
    assert is_valid is True

def test_validate_metadata_schema_missing_field(metadata_generator):
    invalid_metadata = {
        "prod_1": {
            "id": "prod_1",
            "name": "Product 1",
            "images": [
                {"id": "img_1", "url": "/img1.jpg"}  # Missing is_primary
            ],
            "updated_at": "2023-10-01T12:00:00Z"
        }
    }
    
    with open(metadata_generator.metadata_file, 'w') as f:
        json.dump(invalid_metadata, f)
    
    is_valid = metadata_generator.validate_metadata_schema()
    assert is_valid is False

def test_validate_metadata_schema_invalid_json(metadata_generator):
    with open(metadata_generator.metadata_file, 'w') as f:
        f.write("invalid json")
    
    is_valid = metadata_generator.validate_metadata_schema()
    assert is_valid is False

def test_atomic_write_preserves_data(temp_storage):
    generator = MetadataGenerator(base_storage_path=temp_storage)
    
    initial_data = {"prod_1": {"name": "Test", "images": []}}
    
    generator._write_metadata_atomic(initial_data)
    
    assert generator.metadata_file.exists()
    
    with open(generator.metadata_file, 'r') as f:
        loaded = json.load(f)
    
    assert loaded == initial_data
    
    updated_data = {"prod_1": {"name": "Updated", "images": []}}
    generator._write_metadata_atomic(updated_data)
    
    with open(generator.metadata_file, 'r') as f:
        loaded = json.load(f)
    
    assert loaded == updated_data
    assert loaded != initial_data

if __name__ == "__main__":
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Testing MetadataGenerator with temp directory: {tmpdir}")
        
        generator = MetadataGenerator(base_storage_path=Path(tmpdir))
        
        test_data = {"test": "success"}
        result = generator._write_metadata_atomic(test_data)
        
        print(f"Write metadata: {'SUCCESS' if result else 'FAILED'}")
        
        metadata = generator._read_existing_metadata()
        print(f"Read metadata: {metadata}")
        
        print("Metadata generator tests completed!")