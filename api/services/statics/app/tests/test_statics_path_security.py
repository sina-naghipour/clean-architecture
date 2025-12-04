import pytest
import tempfile
from pathlib import Path
from fastapi import HTTPException
from unittest.mock import patch
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.path_security import PathSecurity


def test_validate_and_sanitize_valid_path():
    with tempfile.TemporaryDirectory() as tmp:
        security = PathSecurity(Path(tmp))
        result = security.validate_and_sanitize("products/123")
        assert str(result).startswith(str(Path(tmp).resolve()))
        
        result_path = Path(result)
        assert result_path.parent.name == "123" or result_path.parent.name == "products"
        assert result_path.name == "" or result_path.name == "123"


def test_validate_and_sanitize_with_filename():
    with tempfile.TemporaryDirectory() as tmp:
        security = PathSecurity(Path(tmp))
        result = security.validate_and_sanitize("products", "test.jpg")
        assert str(result).startswith(str(Path(tmp).resolve()))
        
        result_path = Path(result)
        assert result_path.parent.name == "products"
        assert result_path.name == "test.jpg"


def test_validate_and_sanitize_path_traversal_double_dot():
    with tempfile.TemporaryDirectory() as tmp:
        security = PathSecurity(Path(tmp))
        with pytest.raises(HTTPException) as exc_info:
            security.validate_and_sanitize("../etc/passwd")
        assert exc_info.value.status_code == 400
        assert "Path traversal" in exc_info.value.detail


def test_validate_and_sanitize_path_traversal_encoded():
    with tempfile.TemporaryDirectory() as tmp:
        security = PathSecurity(Path(tmp))
        with pytest.raises(HTTPException) as exc_info:
            security.validate_and_sanitize("%2e%2e/etc/passwd")
        assert exc_info.value.status_code == 400
        assert "Encoded path traversal" in exc_info.value.detail


def test_validate_and_sanitize_absolute_path():
    with tempfile.TemporaryDirectory() as tmp:
        security = PathSecurity(Path(tmp))
        with pytest.raises(HTTPException) as exc_info:
            security.validate_and_sanitize("/etc/passwd")
        assert exc_info.value.status_code == 400
        assert "Absolute paths" in exc_info.value.detail


def test_validate_and_sanitize_windows_absolute_path():
    with tempfile.TemporaryDirectory() as tmp:
        security = PathSecurity(Path(tmp))
        with pytest.raises(HTTPException) as exc_info:
            security.validate_and_sanitize("C:\\Windows\\system32")
        assert exc_info.value.status_code == 400
        assert "Absolute paths" in exc_info.value.detail


def test_validate_and_sanitize_empty_path():
    with tempfile.TemporaryDirectory() as tmp:
        security = PathSecurity(Path(tmp))
        
        with pytest.raises(HTTPException) as exc_info:
            security.validate_and_sanitize("")
        
        assert "user_path cannot be empty string" in str(exc_info.value.detail)
        assert exc_info.value.status_code == 500
        
        with pytest.raises(HTTPException) as exc_info:
            security.validate_and_sanitize("", "test.jpg")
        
        assert "user_path cannot be empty string" in str(exc_info.value.detail)
        assert exc_info.value.status_code == 500

def test_validate_and_sanitize_path_outside_base():
    with tempfile.TemporaryDirectory() as tmp:
        security = PathSecurity(Path(tmp))
        # Create a symlink or try to escape - this test depends on system
        with pytest.raises(HTTPException) as exc_info:
            security.validate_and_sanitize("../../../etc")
        assert exc_info.value.status_code == 400


def test_create_safe_filename():
    with tempfile.TemporaryDirectory() as tmp:
        security = PathSecurity(Path(tmp))
        
        filename = security.create_safe_filename("test.jpg")
        assert filename.endswith(".jpg")
        assert len(filename) == 32 + 4  # 32 hex chars + .jpg
        
        filename2 = security.create_safe_filename("test.JPEG")
        assert filename2.endswith(".jpg")
        
        filename3 = security.create_safe_filename("test.png")
        assert filename3.endswith(".png")
        
        filename4 = security.create_safe_filename("test")
        assert filename4.endswith(".bin")


def test_base_directory_created():
    with tempfile.TemporaryDirectory() as tmp:
        new_dir = Path(tmp) / "new_subdir"
        assert not new_dir.exists()
        
        security = PathSecurity(new_dir)
        assert new_dir.exists()


if __name__ == "__main__":
    print("Running PathSecurity tests...")
    test_validate_and_sanitize_valid_path()
    print("✓ test_validate_and_sanitize_valid_path")
    
    test_validate_and_sanitize_with_filename()
    print("✓ test_validate_and_sanitize_with_filename")
    
    test_validate_and_sanitize_path_traversal_double_dot()
    print("✓ test_validate_and_sanitize_path_traversal_double_dot")
    
    test_validate_and_sanitize_path_traversal_encoded()
    print("✓ test_validate_and_sanitize_path_traversal_encoded")
    
    test_validate_and_sanitize_absolute_path()
    print("✓ test_validate_and_sanitize_absolute_path")
    
    test_validate_and_sanitize_empty_path()
    print("✓ test_validate_and_sanitize_empty_path")
    
    test_create_safe_filename()
    print("✓ test_create_safe_filename")
    
    test_base_directory_created()
    print("✓ test_base_directory_created")
    
    print("\nAll PathSecurity tests passed! ✓")