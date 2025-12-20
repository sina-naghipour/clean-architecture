import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch
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


def test_validate_magic_number_valid():
    with patch('utils.file_validator.magic.from_buffer') as mock_from_buffer:
        mock_from_buffer.return_value = "image/jpeg"
        
        validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=["image/jpeg"])
        jpeg_magic = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        
        result = validator.validate_magic_number(jpeg_magic)
        assert result == "image/jpeg"


def test_validate_magic_number_invalid_type():
    with patch('utils.file_validator.magic.from_buffer') as mock_from_buffer:
        mock_from_buffer.return_value = "application/pdf"
        
        validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=["image/jpeg"])
        pdf_magic = b'%PDF-1.5'
        
        with pytest.raises(HTTPException) as exc_info:
            validator.validate_magic_number(pdf_magic)
        
        assert exc_info.value.status_code == 415


def test_validate_magic_number_detection_fails():
    with patch('utils.file_validator.magic.from_buffer') as mock_from_buffer:
        mock_from_buffer.side_effect = Exception("Magic error")
        
        validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=["image/jpeg"])
        
        with pytest.raises(HTTPException) as exc_info:
            validator.validate_magic_number(b"test")
        
        assert exc_info.value.status_code == 415


def test_validate_magic_number_magic_exception():
    import magic
    with patch('utils.file_validator.magic.from_buffer') as mock_from_buffer:
        mock_from_buffer.side_effect = magic.MagicException("Magic library error")
        
        validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=["image/jpeg"])
        
        with pytest.raises(HTTPException) as exc_info:
            validator.validate_magic_number(b"test")
        
        assert exc_info.value.status_code == 415


def test_validate_filename_valid():
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=[])
    result = validator.validate_filename("test.jpg")
    assert result == "test.jpg"


def test_validate_filename_empty():
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=[])
    with pytest.raises(HTTPException) as exc_info:
        validator.validate_filename("")
    assert exc_info.value.status_code == 422 
    assert "cannot be empty" in exc_info.value.detail.lower()


def test_validate_filename_whitespace():
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=[])
    with pytest.raises(HTTPException) as exc_info:
        validator.validate_filename("   ")
    assert exc_info.value.status_code == 422
    assert "cannot be empty" in exc_info.value.detail.lower()


def test_validate_filename_too_long():
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=[])
    long_name = "a" * 300
    with pytest.raises(HTTPException) as exc_info:
        validator.validate_filename(long_name)
    assert exc_info.value.status_code == 422
    assert "too long" in exc_info.value.detail.lower()


def test_validate_filename_strips_whitespace():
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=[])
    result = validator.validate_filename("  test.jpg  ")
    assert result == "test.jpg"


def test_validate_filename_dangerous_characters():
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=[])
    
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\0']
    
    for char in dangerous_chars:
        filename = f"test{char}file.jpg"
        with pytest.raises(HTTPException) as exc_info:
            validator.validate_filename(filename)
        assert exc_info.value.status_code == 422
        assert "invalid character" in exc_info.value.detail.lower() or "contains" in exc_info.value.detail.lower()


def test_validate_filename_path_traversal():
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=[])
    
    with pytest.raises(HTTPException) as exc_info:
        validator.validate_filename("../../../etc/passwd")
    assert exc_info.value.status_code == 422
    assert "path traversal" in exc_info.value.detail.lower() or "contains" in exc_info.value.detail.lower()


def test_validate_filename_reserved_names():
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=[])
    
    reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'LPT1']
    
    for name in reserved_names:
        filename = f"{name}.jpg"
        with pytest.raises(HTTPException) as exc_info:
            validator.validate_filename(filename)
        assert exc_info.value.status_code == 422
        assert "reserved" in exc_info.value.detail.lower()


def test_validate_extension_valid():
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=[])
    result = validator.validate_extension("test.jpg", [".jpg", ".png"])
    assert result == ".jpg"


def test_validate_extension_invalid():
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=[])
    with pytest.raises(HTTPException) as exc_info:
        validator.validate_extension("test.gif", [".jpg", ".png"])
    assert exc_info.value.status_code == 422
    assert "not allowed" in exc_info.value.detail.lower()


def test_validate_extension_no_extension():
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=[])
    
    with pytest.raises(HTTPException) as exc_info:
        validator.validate_extension("test", [".jpg", ".png"])
    
    assert exc_info.value.status_code == 422
    assert "File extension '' is not allowed" in exc_info.value.detail


def test_validate_input_not_none():
    validator = FileValidator(max_size=5*1024*1024, allowed_mime_types=[])
    
    with pytest.raises(HTTPException) as exc_info:
        validator.validate_filename(None)
    assert exc_info.value.status_code == 422
    assert "cannot be none" in exc_info.value.detail.lower()
    
    with pytest.raises(HTTPException) as exc_info:
        validator.validate_size(None)
    assert exc_info.value.status_code == 422
    assert "cannot be none" in exc_info.value.detail.lower()


if __name__ == "__main__":
    print("Running FileValidator tests...")
    
    tests = [
        ("test_validate_size_within_limit", test_validate_size_within_limit),
        ("test_validate_size_exceeds_limit", test_validate_size_exceeds_limit),
        ("test_validate_filename_valid", test_validate_filename_valid),
        ("test_validate_filename_empty", test_validate_filename_empty),
        ("test_validate_filename_whitespace", test_validate_filename_whitespace),
        ("test_validate_filename_too_long", test_validate_filename_too_long),
        ("test_validate_filename_strips_whitespace", test_validate_filename_strips_whitespace),
        ("test_validate_filename_dangerous_characters", test_validate_filename_dangerous_characters),
        ("test_validate_filename_path_traversal", test_validate_filename_path_traversal),
        ("test_validate_filename_reserved_names", test_validate_filename_reserved_names),
        ("test_validate_extension_valid", test_validate_extension_valid),
        ("test_validate_extension_invalid", test_validate_extension_invalid),
        ("test_validate_extension_no_extension", test_validate_extension_no_extension),
    ]
    
    passed = 0
    failed = []
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✓ {test_name}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_name}: {str(e)}")
            failed.append(test_name)
    
    print(f"\nPassed: {passed}/{len(tests)}")
    if failed:
        print(f"Failed: {', '.join(failed)}")
    
    print("\nNote: Magic number tests require mocking and may need adjustment")
    print("based on your exact FileValidator implementation.")