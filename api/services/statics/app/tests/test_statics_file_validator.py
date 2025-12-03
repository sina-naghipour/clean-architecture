import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch
import filetype
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.file_validator import FileValidator


def test_validate_size_within_limit():
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=[])
    small_file = b"x" * (1024 * 1024)
    assert validator.validate_size(small_file) == True


def test_validate_size_exceeds_limit():
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=[])
    large_file = b"x" * (6 * 1024 * 1024)
    with pytest.raises(HTTPException) as exc_info:
        validator.validate_size(large_file)
    assert exc_info.value.status_code == 413
    assert "exceeds maximum" in exc_info.value.detail


@patch('magic.Magic')
def test_validate_magic_number_valid(mock_magic):
    mock_instance = Mock()
    mock_instance.from_buffer.return_value = "image/jpeg"
    mock_magic.return_value = mock_instance
    
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=["image/jpeg"])
    jpeg_magic = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    
    result = validator.validate_magic_number(jpeg_magic)
    assert result == "image/jpeg"


@patch('filetype.guess')
def test_validate_magic_number_invalid_type(mock_guess):
    mock_guess.return_value = None
    
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=["image/jpeg"])
    pdf_magic = b'%PDF-1.5'
    
    with pytest.raises(HTTPException) as exc_info:
        validator.validate_magic_number(pdf_magic)
    
    assert exc_info.value.status_code == 400
    assert "Could not determine" in exc_info.value.detail

def test_validate_magic_number_detection_fails():
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=["image/jpeg"])
    
    with patch('magic.Magic', side_effect=Exception("Magic error")):
        with pytest.raises(HTTPException) as exc_info:
            validator.validate_magic_number(b"test")
        assert exc_info.value.status_code == 400
        assert "Could not determine" in exc_info.value.detail


def test_validate_filename_valid():
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=[])
    result = validator.validate_filename("test.jpg")
    assert result == "test.jpg"


def test_validate_filename_empty():
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=[])
    with pytest.raises(HTTPException) as exc_info:
        validator.validate_filename("")
    assert exc_info.value.status_code == 400
    assert "cannot be empty" in exc_info.value.detail


def test_validate_filename_whitespace():
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=[])
    with pytest.raises(HTTPException) as exc_info:
        validator.validate_filename("   ")
    assert exc_info.value.status_code == 400
    assert "cannot be empty" in exc_info.value.detail


def test_validate_filename_too_long():
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=[])
    long_name = "a" * 300
    with pytest.raises(HTTPException) as exc_info:
        validator.validate_filename(long_name)
    assert exc_info.value.status_code == 400
    assert "too long" in exc_info.value.detail


def test_validate_filename_strips_whitespace():
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=[])
    result = validator.validate_filename("  test.jpg  ")
    assert result == "test.jpg"


if __name__ == "__main__":
    print("Running FileValidator tests...")
    test_validate_size_within_limit()
    print("✓ test_validate_size_within_limit")
    
    test_validate_size_exceeds_limit()
    print("✓ test_validate_size_exceeds_limit")
    
    test_validate_filename_valid()
    print("✓ test_validate_filename_valid")
    
    test_validate_filename_empty()
    print("✓ test_validate_filename_empty")
    
    test_validate_filename_whitespace()
    print("✓ test_validate_filename_whitespace")
    
    test_validate_filename_too_long()
    print("✓ test_validate_filename_too_long")
    
    test_validate_filename_strips_whitespace()
    print("✓ test_validate_filename_strips_whitespace")
    
    print("\nNote: Magic number tests require mocking")
    print("All basic tests passed! ✓")