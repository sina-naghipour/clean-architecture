import pytest
import tempfile
import json
import os
import uuid
from pathlib import Path
from datetime import datetime, UTC
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.metadata_updater import MetadataUpdater
from fastapi import HTTPException


def test_metadata_updater_initialization():
    with tempfile.TemporaryDirectory() as tmp:
        metadata_file = Path(tmp) / "metadata.json"
        updater = MetadataUpdater(metadata_file)
        
        assert metadata_file.exists()
        assert metadata_file.parent.exists()
        
        with open(metadata_file, 'r') as f:
            data = json.load(f)
            assert data == {}


def test_add_file():
    with tempfile.TemporaryDirectory() as tmp:
        metadata_file = Path(tmp) / "metadata.json"
        updater = MetadataUpdater(metadata_file)
        
        file_id = str(uuid.uuid4())
        file_data = {
            "original_filename": "test.jpg",
            "safe_filename": f"{file_id}.jpg",
            "path": f"products/{file_id}.jpg",
            "full_path": f"/static/img/products/{file_id}.jpg",
            "size_bytes": 1024000,
            "mime_type": "image/jpeg",
            "uploaded_at": datetime.now(UTC).isoformat(),
            "custom_metadata": {}
        }
        
        result = updater.add_file(file_id, file_data)
        assert result is True
        
        with open(metadata_file, 'r') as f:
            data = json.load(f)
            assert "files" in data
            assert file_id in data["files"]
            assert data["files"][file_id]["original_filename"] == "test.jpg"
            assert data["files"][file_id]["size_bytes"] == 1024000


def test_add_multiple_files():
    with tempfile.TemporaryDirectory() as tmp:
        metadata_file = Path(tmp) / "metadata.json"
        updater = MetadataUpdater(metadata_file)
        
        file1_id = str(uuid.uuid4())
        file2_id = str(uuid.uuid4())
        
        file1_data = {
            "original_filename": "test1.jpg",
            "safe_filename": f"{file1_id}.jpg",
            "path": f"products/{file1_id}.jpg",
            "full_path": f"/static/img/products/{file1_id}.jpg",
            "size_bytes": 1024000,
            "mime_type": "image/jpeg",
            "uploaded_at": datetime.now(UTC).isoformat(),
            "custom_metadata": {}
        }
        
        file2_data = {
            "original_filename": "test2.png",
            "safe_filename": f"{file2_id}.png",
            "path": f"products/{file2_id}.png",
            "full_path": f"/static/img/products/{file2_id}.png",
            "size_bytes": 512000,
            "mime_type": "image/png",
            "uploaded_at": datetime.now(UTC).isoformat(),
            "custom_metadata": {"description": "Product image"}
        }
        
        updater.add_file(file1_id, file1_data)
        updater.add_file(file2_id, file2_data)
        
        with open(metadata_file, 'r') as f:
            data = json.load(f)
            assert len(data["files"]) == 2
            assert file1_id in data["files"]
            assert file2_id in data["files"]
            assert data["files"][file2_id]["custom_metadata"]["description"] == "Product image"


def test_remove_file():
    with tempfile.TemporaryDirectory() as tmp:
        metadata_file = Path(tmp) / "metadata.json"
        updater = MetadataUpdater(metadata_file)
        
        file_id = str(uuid.uuid4())
        file_data = {
            "original_filename": "test.jpg",
            "safe_filename": f"{file_id}.jpg",
            "path": f"products/{file_id}.jpg",
            "full_path": f"/static/img/products/{file_id}.jpg",
            "size_bytes": 1024000,
            "mime_type": "image/jpeg",
            "uploaded_at": datetime.now(UTC).isoformat(),
            "custom_metadata": {}
        }
        
        updater.add_file(file_id, file_data)
        
        with open(metadata_file, 'r') as f:
            data = json.load(f)
            assert file_id in data["files"]
        
        result = updater.remove_file(file_id)
        assert result is True
        
        with open(metadata_file, 'r') as f:
            data = json.load(f)
            assert "files" in data
            assert file_id not in data["files"]


def test_remove_nonexistent_file():
    with tempfile.TemporaryDirectory() as tmp:
        metadata_file = Path(tmp) / "metadata.json"
        updater = MetadataUpdater(metadata_file)
        
        result = updater.remove_file("nonexistent")
        assert result is True


def test_get_file():
    with tempfile.TemporaryDirectory() as tmp:
        metadata_file = Path(tmp) / "metadata.json"
        updater = MetadataUpdater(metadata_file)
        
        file_id = str(uuid.uuid4())
        file_data = {
            "original_filename": "test.jpg",
            "safe_filename": f"{file_id}.jpg",
            "path": f"products/{file_id}.jpg",
            "full_path": f"/static/img/products/{file_id}.jpg",
            "size_bytes": 1024000,
            "mime_type": "image/jpeg",
            "uploaded_at": datetime.now(UTC).isoformat(),
            "custom_metadata": {"width": 800, "height": 600}
        }
        
        updater.add_file(file_id, file_data)
        
        retrieved = updater.get_file(file_id)
        assert retrieved["original_filename"] == "test.jpg"
        assert retrieved["size_bytes"] == 1024000
        assert retrieved["custom_metadata"]["width"] == 800


def test_get_nonexistent_file():
    with tempfile.TemporaryDirectory() as tmp:
        metadata_file = Path(tmp) / "metadata.json"
        updater = MetadataUpdater(metadata_file)
        
        with pytest.raises(HTTPException) as exc_info:
            updater.get_file("nonexistent")
        
        assert exc_info.value.status_code == 404
        assert "File not found" in exc_info.value.detail


def test_list_files():
    with tempfile.TemporaryDirectory() as tmp:
        metadata_file = Path(tmp) / "metadata.json"
        updater = MetadataUpdater(metadata_file)
        
        file1_id = str(uuid.uuid4())
        file2_id = str(uuid.uuid4())
        
        file1_data = {"original_filename": "test1.jpg", "size_bytes": 1000}
        file2_data = {"original_filename": "test2.png", "size_bytes": 2000}
        
        updater.add_file(file1_id, file1_data)
        updater.add_file(file2_id, file2_data)
        
        files = updater.list_files()
        assert len(files) == 2
        assert file1_id in files
        assert file2_id in files
        assert files[file1_id]["original_filename"] == "test1.jpg"
        assert files[file2_id]["size_bytes"] == 2000


def test_list_files_empty():
    with tempfile.TemporaryDirectory() as tmp:
        metadata_file = Path(tmp) / "metadata.json"
        updater = MetadataUpdater(metadata_file)
        
        files = updater.list_files()
        assert files == {}


def test_add_product_reference():
    with tempfile.TemporaryDirectory() as tmp:
        metadata_file = Path(tmp) / "metadata.json"
        updater = MetadataUpdater(metadata_file)
        
        product_id = "prod_123"
        file_id = "img_456"
        
        result = updater.add_product_reference(product_id, file_id, "Test Product")
        assert result is True
        
        with open(metadata_file, 'r') as f:
            data = json.load(f)
            assert "products" in data
            assert product_id in data["products"]
            assert data["products"][product_id]["name"] == "Test Product"
            assert data["products"][product_id]["files"] == [file_id]


def test_add_multiple_files_to_product():
    with tempfile.TemporaryDirectory() as tmp:
        metadata_file = Path(tmp) / "metadata.json"
        updater = MetadataUpdater(metadata_file)
        
        product_id = "prod_123"
        
        updater.add_product_reference(product_id, "img_1", "Test Product")
        updater.add_product_reference(product_id, "img_2", "Test Product")
        
        with open(metadata_file, 'r') as f:
            data = json.load(f)
            assert len(data["products"][product_id]["files"]) == 2
            assert "img_1" in data["products"][product_id]["files"]
            assert "img_2" in data["products"][product_id]["files"]


def test_remove_product_reference():
    with tempfile.TemporaryDirectory() as tmp:
        metadata_file = Path(tmp) / "metadata.json"
        updater = MetadataUpdater(metadata_file)
        
        product_id = "prod_123"
        
        updater.add_product_reference(product_id, "img_1", "Test Product")
        updater.add_product_reference(product_id, "img_2", "Test Product")
        
        result = updater.remove_product_reference(product_id, "img_1")
        assert result is True
        
        with open(metadata_file, 'r') as f:
            data = json.load(f)
            assert len(data["products"][product_id]["files"]) == 1
            assert "img_2" in data["products"][product_id]["files"]
            assert "img_1" not in data["products"][product_id]["files"]


def test_remove_product_reference_last_file():
    with tempfile.TemporaryDirectory() as tmp:
        metadata_file = Path(tmp) / "metadata.json"
        updater = MetadataUpdater(metadata_file)
        
        product_id = "prod_123"
        
        updater.add_product_reference(product_id, "img_1", "Test Product")
        
        result = updater.remove_product_reference(product_id, "img_1")
        assert result is True
        
        with open(metadata_file, 'r') as f:
            data = json.load(f)
            assert "products" not in data or product_id not in data["products"]


def test_corrupted_metadata_file():
    with tempfile.TemporaryDirectory() as tmp:
        metadata_file = Path(tmp) / "metadata.json"
        
        with open(metadata_file, 'w') as f:
            f.write("invalid json {")
        
        updater = MetadataUpdater(metadata_file)
        
        with pytest.raises(HTTPException) as exc_info:
            updater.add_file("test_id", {"test": "data"})
        
        assert exc_info.value.status_code == 500
        assert "Failed to read metadata" in exc_info.value.detail


if __name__ == "__main__":
    print("Running MetadataUpdater tests...")
    test_metadata_updater_initialization()
    print("✓ test_metadata_updater_initialization")
    
    test_add_file()
    print("✓ test_add_file")
    
    test_add_multiple_files()
    print("✓ test_add_multiple_files")
    
    test_remove_file()
    print("✓ test_remove_file")
    
    test_get_file()
    print("✓ test_get_file")
    
    test_list_files()
    print("✓ test_list_files")
    
    test_add_product_reference()
    print("✓ test_add_product_reference")
    
    test_remove_product_reference()
    print("✓ test_remove_product_reference")
    
    print("\nAll MetadataUpdater tests passed! ✓")