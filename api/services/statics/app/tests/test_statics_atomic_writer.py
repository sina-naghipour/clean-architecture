import pytest
import tempfile
from pathlib import Path
import os
from fastapi import HTTPException
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.atomic_writer import AtomicWriter


def test_write_atomic_success():
    with tempfile.TemporaryDirectory() as tmp:
        target_path = Path(tmp) / "test.txt"
        test_content = b"Hello, World!"
        
        with AtomicWriter.write_atomic(target_path) as temp_path:
            with open(temp_path, 'wb') as f:
                f.write(test_content)
        
        assert target_path.exists()
        with open(target_path, 'rb') as f:
            assert f.read() == test_content


def test_write_atomic_creates_parent_directory():
    with tempfile.TemporaryDirectory() as tmp:
        target_path = Path(tmp) / "subdir" / "nested" / "test.txt"
        test_content = b"Hello, World!"
        
        assert not target_path.parent.exists()
        
        with AtomicWriter.write_atomic(target_path) as temp_path:
            with open(temp_path, 'wb') as f:
                f.write(test_content)
        
        assert target_path.parent.exists()
        assert target_path.exists()


def test_write_atomic_temp_file_removed_on_success():
    with tempfile.TemporaryDirectory() as tmp:
        target_path = Path(tmp) / "test.txt"
        test_content = b"Hello, World!"
        
        temp_file_path = None
        with AtomicWriter.write_atomic(target_path) as temp_path:
            temp_file_path = temp_path
            assert temp_file_path.exists()
            with open(temp_path, 'wb') as f:
                f.write(test_content)
        
        assert not temp_file_path.exists()
        assert target_path.exists()


def test_write_atomic_temp_file_removed_on_error():
    with tempfile.TemporaryDirectory() as tmp:
        target_path = Path(tmp) / "test.txt"
        temp_file_path = None
        
        try:
            with AtomicWriter.write_atomic(target_path) as temp_path:
                temp_file_path = temp_path
                with open(temp_path, 'w') as f:
                    f.write("test")
                raise RuntimeError("Simulated error")
        except HTTPException as e:
            assert e.status_code == 500
            assert "Failed to write file" in e.detail
        
        if temp_file_path:
            assert not temp_file_path.exists()
        assert not target_path.exists()



def test_write_atomic_exception_on_failure():
    with tempfile.TemporaryDirectory() as tmp:
        target_path = Path(tmp) / "test.txt"
        
        if os.name == 'nt':
            pytest.skip("Permission tests behave differently on Windows")
        
        target_path.parent.chmod(0o444)
        
        try:
            with pytest.raises(HTTPException) as exc_info:
                with AtomicWriter.write_atomic(target_path) as temp_path:
                    with open(temp_path, 'w') as f:
                        f.write("test")
            
            assert exc_info.value.status_code == 500
            assert "Failed to write file" in exc_info.value.detail
        finally:
            target_path.parent.chmod(0o755)

def test_read_atomic_success():
    with tempfile.TemporaryDirectory() as tmp:
        file_path = Path(tmp) / "test.txt"
        test_content = b"Hello, World!"
        
        with open(file_path, 'wb') as f:
            f.write(test_content)
        
        result = AtomicWriter.read_atomic(file_path)
        assert result == test_content


def test_read_atomic_file_not_found():
    with tempfile.TemporaryDirectory() as tmp:
        file_path = Path(tmp) / "nonexistent.txt"
        
        with pytest.raises(HTTPException) as exc_info:
            AtomicWriter.read_atomic(file_path)
        
        assert exc_info.value.status_code == 404
        assert "File not found" in exc_info.value.detail


def test_delete_atomic_success():
    with tempfile.TemporaryDirectory() as tmp:
        file_path = Path(tmp) / "test.txt"
        test_content = b"Hello, World!"
        
        with open(file_path, 'wb') as f:
            f.write(test_content)
        
        assert file_path.exists()
        result = AtomicWriter.delete_atomic(file_path)
        assert result is True
        assert not file_path.exists()


def test_delete_atomic_nonexistent():
    with tempfile.TemporaryDirectory() as tmp:
        file_path = Path(tmp) / "nonexistent.txt"
        
        assert not file_path.exists()
        result = AtomicWriter.delete_atomic(file_path)
        assert result is False


def test_delete_atomic_permission_error():
    with tempfile.TemporaryDirectory() as tmp:
        file_path = Path(tmp) / "test.txt"
        
        with open(file_path, 'w') as f:
            f.write("test")
        
        # Skip on Windows
        if os.name == 'nt':
            pytest.skip("Permission tests behave differently on Windows")
        
        # Make file read-only
        os.chmod(file_path, 0o444)
        try:
            with pytest.raises(HTTPException) as exc_info:
                AtomicWriter.delete_atomic(file_path)
            assert exc_info.value.status_code == 500
            assert "Failed to delete file" in exc_info.value.detail
        finally:
            os.chmod(file_path, 0o755)

def test_context_manager_yields_temp_path():
    with tempfile.TemporaryDirectory() as tmp:
        target_path = Path(tmp) / "test.txt"
        
        with AtomicWriter.write_atomic(target_path) as temp_path:
            assert temp_path.exists()
            assert temp_path != target_path
            assert temp_path.parent == target_path.parent
            assert temp_path.name.startswith(".tmp_")


if __name__ == "__main__":
    print("Running AtomicWriter tests...")
    test_write_atomic_success()
    print("✓ test_write_atomic_success")
    
    test_write_atomic_creates_parent_directory()
    print("✓ test_write_atomic_creates_parent_directory")
    
    test_write_atomic_temp_file_removed_on_success()
    print("✓ test_write_atomic_temp_file_removed_on_success")
    
    test_context_manager_yields_temp_path()
    print("✓ test_context_manager_yields_temp_path")
    
    test_read_atomic_success()
    print("✓ test_read_atomic_success")
    
    test_read_atomic_file_not_found()
    print("✓ test_read_atomic_file_not_found")
    
    test_delete_atomic_success()
    print("✓ test_delete_atomic_success")
    
    test_delete_atomic_nonexistent()
    print("✓ test_delete_atomic_nonexistent")
    
    print("\nNote: Some tests may fail on Windows due to permission differences")
    print("All basic AtomicWriter tests passed! ✓")