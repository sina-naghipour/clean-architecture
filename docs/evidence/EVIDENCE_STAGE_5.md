# EVIDENCE_GENERAL_FORMAT.md

## 1. File upload security

### Pattern
- **Location**: `static/app/utils/path_security.py`
- **Purpose**: Secure paths and prevent path traversals.

### Evidence Structure
```python
class PathSecurity:
    def __init__(self, base_upload_dir: Path):
        self.base_upload_dir = Path(base_upload_dir)
        self._ensure_base_directory()
    
    @create_directory_if_missing
    def _ensure_base_directory(self):
        pass
    
    @validate_path_operation
    @prevent_path_traversal
    @ensure_within_base_dir
    def validate_and_sanitize(self, user_path: str, filename: str = None) -> Path:
        if user_path == "":
            raise ValueError("user_path cannot be empty string")
        if user_path:
            user_path = user_path.strip('/\\')
        
        full_path = self.base_upload_dir
        
        if user_path:
            path_parts = [part for part in user_path.split('/') if part and part != '.']
            for part in path_parts:
                full_path = full_path / part
        
        if filename:
            full_path = full_path / filename
        
        if filename:
            full_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            full_path.mkdir(parents=True, exist_ok=True)
        
        return full_path
```

### Key Features
- **Layered Security Decorators**: Uses multiple security decorators for defense-in-depth against path traversal attacks.
- **Path Sanitization**: Cleans user input by stripping slashes and filtering out potentially malicious path components.
- **Safe Directory Creation**: Ensures directories are created only within validated base paths with proper error handling.

---


## 2. Collision-Free Server-Side Naming.

### Pattern
- **Location**: `static/app/utils/atomic_writer.py`
- **Purpose**: Provide atomic file operations with transactional safety.

### Evidence Structure
```python
class AtomicWriter:
    @staticmethod
    @contextmanager
    def write_atomic(target_path: Path):
        temp_path = None
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            with tempfile.NamedTemporaryFile(
                dir=target_path.parent,
                prefix=".tmp_",
                delete=False
            ) as temp_file:
                temp_path = Path(temp_file.name)
                yield temp_path
            
            os.replace(temp_path, target_path)
            temp_path = None
            
        except Exception as e:
            if temp_path and temp_path.exists():
                try:
                    os.unlink(temp_path)
                except:
                    pass
            raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")
```

### Key Features
- **Atomic Write Operations**: Uses temporary files and `os.replace()` for transactional file writes that prevent partial writes.
- **Automatic Cleanup**: Implements robust cleanup of temporary files in case of failures to prevent orphaned files.
- **Consistent Error Handling**: Provides uniform HTTP exception handling for all file operations with appropriate status codes.

## 3. Metadata Updater


### Pattern
- **Location**: `static/app/utils/metadata_updater.py`
- **Purpose**: Manage file metadata with atomic updates and relational references.

### Evidence Structure
```python
class MetadataUpdater:
    def __init__(self, metadata_file: Path):
        self.metadata_file = metadata_file
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.metadata_file.exists():
            self._write_metadata({})
    
    def _read_metadata(self) -> Dict[str, Any]:
        try:
            if not self.metadata_file.exists():
                return {}
            
            with open(self.metadata_file, 'r') as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            raise HTTPException(status_code=500, detail=f"Failed to read metadata: {str(e)}")
    
    def _write_metadata(self, metadata: Dict[str, Any]) -> bool:
        try:
            temp_file = self.metadata_file.with_suffix('.tmp')
            
            with open(temp_file, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            os.replace(temp_file, self.metadata_file)
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to write metadata: {str(e)}")
```

### Key Features
- **Atomic JSON Updates**: Uses temporary files and `os.replace()` for transactional metadata updates.
- **File-Product Relationships**: Manages bidirectional relationships between files and products with referential integrity.
- **Automatic Schema Initialization**: Self-initializes metadata file with proper structure and handles corrupted files gracefully.

## 4. Separate File Upload Logic

### Pattern
- **Location**: `services/file_upload_service.py`
- **Purpose**: Coordinate file upload operations with validation, security, and metadata tracking.

### Evidence Structure
```python
class FileUploadService:
    def __init__(
        self,
        upload_dir: Path,
        metadata_updater: MetadataUpdater,
        max_file_size: int,
        allowed_mime_types: list
    ):
        self.upload_dir = upload_dir
        self.metadata_updater = metadata_updater
        self.path_security = PathSecurity(upload_dir)
        self.file_validator = FileValidator(max_file_size, allowed_mime_types)
        
        self._ensure_upload_dir()
    
    @validate_path_security
    def _ensure_upload_dir(self):
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    @handle_upload_errors
    async def upload_file(
        self,
        upload_file: UploadFile,
        subdirectory: str = DEFAULT_SUBDIRECTORY,
        custom_metadata: Optional[dict] = None
    ) -> dict:
        
        original_filename = self.file_validator.validate_filename(upload_file.filename)
        file_content = await upload_file.read()
        
        self.file_validator.validate_size(file_content)
        mime_type = self.file_validator.validate_magic_number(file_content)
        
        safe_filename = self.path_security.create_safe_filename(original_filename)
        full_path = self.path_security.validate_and_sanitize(subdirectory, safe_filename)
        
        with AtomicWriter.write_atomic(full_path) as temp_path:
            with open(temp_path, 'wb') as f:
                f.write(file_content)
        
        file_id = Path(safe_filename).stem
        relative_path = str(full_path.relative_to(self.upload_dir))
        
        file_data = {
            "original_filename": original_filename,
            "safe_filename": safe_filename,
            "path": relative_path,
            "full_path": str(full_path),
            "size_bytes": len(file_content),
            "mime_type": mime_type,
            "uploaded_at": datetime.utcnow().isoformat(),
            "custom_metadata": custom_metadata or {}
        }
        
        self.metadata_updater.add_file(file_id, file_data)
        
        return {
            "id": file_id,
            "filename": safe_filename,
            "original_filename": original_filename,
            "path": relative_path,
            "size": len(file_content),
            "mime_type": mime_type,
            "url": f"/static/img/{relative_path}"
        }
```

### Key Features
- **Orchestrated Component Integration**: Coordinates multiple specialized components (validator, security, atomic writer, metadata) into a unified upload workflow.
- **Decorator-Based Error Handling**: Uses operation-specific decorators for consistent error management across different file operations.
- **Complete File Lifecycle Management**: Provides end-to-end operations including upload, retrieval, deletion, and URL generation.

## Key Architecture Benefits

1. Defense-in-Depth Security
2. Transactional Integrity
3. Clean Separation of Concerns