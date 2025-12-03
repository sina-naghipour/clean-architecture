import pytest
import tempfile
import os
import uuid
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import UploadFile, HTTPException
import sys
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.file_upload_service import FileUploadService
from services.metadata_updater import MetadataUpdater


@pytest.fixture
def temp_upload_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def mock_metadata_updater():
    updater = Mock(spec=MetadataUpdater)
    updater.add_file = Mock(return_value=True)
    updater.get_file = Mock()
    updater.remove_file = Mock(return_value=True)
    updater.list_files = Mock(return_value={})
    return updater


@pytest.fixture
def file_upload_service(temp_upload_dir, mock_metadata_updater):
    return FileUploadService(
        upload_dir=temp_upload_dir,
        metadata_updater=mock_metadata_updater,
        max_file_size=5*1024*1024,
        allowed_mime_types=["image/jpeg", "image/png"]
    )


@pytest.fixture
def mock_upload_file():
    file = Mock(spec=UploadFile)
    file.filename = "test.jpg"
    file.read = AsyncMock(return_value=b"fake image data")
    return file


@pytest.mark.asyncio
async def test_upload_file_success(file_upload_service, mock_upload_file, mock_metadata_updater):
    with patch('utils.file_validator.FileValidator.validate_size') as mock_validate_size:
        with patch('utils.file_validator.FileValidator.validate_magic_number') as mock_validate_magic:
            with patch('utils.file_validator.FileValidator.validate_filename') as mock_validate_filename:
                mock_validate_size.return_value = True
                mock_validate_magic.return_value = "image/jpeg"
                mock_validate_filename.return_value = "test.jpg"
                
                with patch('utils.path_security.PathSecurity.create_safe_filename') as mock_create_filename:
                    mock_create_filename.return_value = "safe_test.jpg"
                    
                    with patch('utils.path_security.PathSecurity.validate_and_sanitize') as mock_validate_path:
                        mock_validate_path.return_value = file_upload_service.upload_dir / "safe_test.jpg"
                        
                        with patch('utils.atomic_writer.AtomicWriter.write_atomic'):
                            result = await file_upload_service.upload_file(mock_upload_file)
                            
                            assert "id" in result
                            assert result["filename"] == "safe_test.jpg"
                            assert result["original_filename"] == "test.jpg"
                            assert result["mime_type"] == "image/jpeg"
                            assert "url" in result
                            
                            mock_metadata_updater.add_file.assert_called_once()


@pytest.mark.asyncio 
async def test_upload_file_with_subdirectory(file_upload_service, mock_upload_file):
    with patch('utils.file_validator.FileValidator.validate_size') as mock_validate_size:
        with patch('utils.file_validator.FileValidator.validate_magic_number') as mock_validate_magic:
            with patch('utils.file_validator.FileValidator.validate_filename') as mock_validate_filename:
                mock_validate_size.return_value = True
                mock_validate_magic.return_value = "image/jpeg"
                mock_validate_filename.return_value = "test.jpg"
                
                with patch('utils.path_security.PathSecurity.create_safe_filename') as mock_create_filename:
                    mock_create_filename.return_value = "safe_test.jpg"
                    
                    with patch('utils.path_security.PathSecurity.validate_and_sanitize') as mock_validate_path:
                        expected_path = file_upload_service.upload_dir / "products" / "123" / "safe_test.jpg"
                        mock_validate_path.return_value = expected_path
                        
                        with patch('utils.atomic_writer.AtomicWriter.write_atomic'):
                            result = await file_upload_service.upload_file(
                                mock_upload_file, 
                                subdirectory="products/123"
                            )
                            
                            path = result["path"].replace("\\", "/")
                            assert "products/123" in path

@pytest.mark.asyncio
async def test_upload_file_size_exceeds_limit(file_upload_service, mock_upload_file):
    mock_upload_file.read.return_value = b"x" * (6 * 1024 * 1024)
    
    with patch('utils.file_validator.FileValidator.validate_size') as mock_validate_size:
        mock_validate_size.side_effect = HTTPException(status_code=413, detail="File too large")
        
        with pytest.raises(HTTPException) as exc_info:
            await file_upload_service.upload_file(mock_upload_file)
        
        assert exc_info.value.status_code == 413


@pytest.mark.asyncio
async def test_upload_file_invalid_mime_type(file_upload_service, mock_upload_file):
    with patch('utils.file_validator.FileValidator.validate_size') as mock_validate_size:
        with patch('utils.file_validator.FileValidator.validate_magic_number') as mock_validate_magic:
            mock_validate_size.return_value = True
            mock_validate_magic.side_effect = HTTPException(status_code=415, detail="Invalid type")
            
            with pytest.raises(HTTPException) as exc_info:
                await file_upload_service.upload_file(mock_upload_file)
            
            assert exc_info.value.status_code == 415


@pytest.mark.asyncio
async def test_upload_file_path_traversal(file_upload_service, mock_upload_file):
    with patch('utils.file_validator.FileValidator.validate_size') as mock_validate_size:
        with patch('utils.file_validator.FileValidator.validate_magic_number') as mock_validate_magic:
            with patch('utils.file_validator.FileValidator.validate_filename') as mock_validate_filename:
                mock_validate_size.return_value = True
                mock_validate_magic.return_value = "image/jpeg"
                mock_validate_filename.return_value = "test.jpg"
                
                with patch('utils.path_security.PathSecurity.validate_and_sanitize') as mock_validate_path:
                    mock_validate_path.side_effect = HTTPException(status_code=400, detail="Path traversal")
                    
                    with pytest.raises(HTTPException) as exc_info:
                        await file_upload_service.upload_file(mock_upload_file, subdirectory="../etc")
                    
                    assert exc_info.value.status_code == 400
                    assert "Path traversal" in exc_info.value.detail


@pytest.mark.asyncio
async def test_delete_file_success(file_upload_service, mock_metadata_updater):
    file_id = str(uuid.uuid4())
    
    mock_metadata_updater.get_file.return_value = {
        "path": f"{file_id}.jpg",
        "original_filename": "test.jpg"
    }
    
    with patch('utils.atomic_writer.AtomicWriter.delete_atomic') as mock_delete:
        mock_delete.return_value = True
        
        result = await file_upload_service.delete_file(file_id)
        
        assert result is True
        mock_metadata_updater.remove_file.assert_called_once_with(file_id)


@pytest.mark.asyncio
async def test_delete_file_not_found_in_metadata(file_upload_service, mock_metadata_updater):
    mock_metadata_updater.get_file.side_effect = HTTPException(status_code=404, detail="Not found")
    
    result = await file_upload_service.delete_file("nonexistent")
    
    assert result is False


@pytest.mark.asyncio
async def test_delete_file_delete_fails(file_upload_service, mock_metadata_updater):
    file_id = str(uuid.uuid4())
    
    mock_metadata_updater.get_file.return_value = {
        "path": f"{file_id}.jpg",
        "original_filename": "test.jpg"
    }
    
    with patch('utils.atomic_writer.AtomicWriter.delete_atomic') as mock_delete:
        mock_delete.return_value = False
        
        result = await file_upload_service.delete_file(file_id)
        
        assert result is False
        mock_metadata_updater.remove_file.assert_not_called()


def test_get_file_path(file_upload_service, mock_metadata_updater, temp_upload_dir):
    file_id = str(uuid.uuid4())
    
    mock_metadata_updater.get_file.return_value = {
        "path": f"products/{file_id}.jpg"
    }
    
    result = file_upload_service.get_file_path(file_id)
    
    assert result == temp_upload_dir / f"products/{file_id}.jpg"
    mock_metadata_updater.get_file.assert_called_once_with(file_id)


def test_get_file_path_not_found(file_upload_service, mock_metadata_updater):
    mock_metadata_updater.get_file.side_effect = HTTPException(status_code=404, detail="Not found")
    
    with pytest.raises(HTTPException) as exc_info:
        file_upload_service.get_file_path("nonexistent")
    
    assert exc_info.value.status_code == 404


def test_get_file_url(file_upload_service, mock_metadata_updater):
    file_id = str(uuid.uuid4())
    
    mock_metadata_updater.get_file.return_value = {
        "path": f"products/{file_id}.jpg"
    }
    
    result = file_upload_service.get_file_url(file_id)
    
    assert result == f"/static/img/products/{file_id}.jpg"


def test_get_file_url_not_found(file_upload_service, mock_metadata_updater):
    mock_metadata_updater.get_file.side_effect = HTTPException(status_code=404, detail="Not found")
    
    with pytest.raises(HTTPException) as exc_info:
        file_upload_service.get_file_url("nonexistent")
    
    assert exc_info.value.status_code == 404


def test_upload_directory_created(file_upload_service, temp_upload_dir):
    # Upload directory should be created during initialization
    assert temp_upload_dir.exists()


@pytest.mark.asyncio
async def test_upload_file_general_exception(file_upload_service, mock_upload_file):
    with patch('utils.file_validator.FileValidator.validate_size') as mock_validate_size:
        mock_validate_size.side_effect = Exception("Unexpected error")
        
        with pytest.raises(HTTPException) as exc_info:
            await file_upload_service.upload_file(mock_upload_file)
        
        assert exc_info.value.status_code == 500
        # Updated to match decorator message
        assert "Upload operation failed" in exc_info.value.detail
        assert "Unexpected error" in exc_info.value.detail


@pytest.mark.asyncio
async def test_delete_file_general_exception(file_upload_service, mock_metadata_updater):
    mock_metadata_updater.get_file.side_effect = Exception("Unexpected error")
    
    with pytest.raises(HTTPException) as exc_info:
        await file_upload_service.delete_file("test_id")
    
    assert exc_info.value.status_code == 500
    # Updated to match decorator message  
    assert "Delete operation failed" in exc_info.value.detail
    assert "Unexpected error" in exc_info.value.detail


if __name__ == "__main__":
    print("Running FileUploadService tests...")
    print("Note: These tests require mocking many dependencies")
    print("Run with: pytest tests/test_file_upload_service.py -v --asyncio-mode=auto")