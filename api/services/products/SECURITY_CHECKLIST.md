# Image Upload Service - Security Checklist

## Threat Model & Mitigations

### 1. File Upload Threats

| Threat | Risk | Mitigation | Status |
|--------|------|------------|--------|
| **Path Traversal** | High - Could overwrite system files | • Validate file paths against base directory<br>• Reject paths with `..`, absolute paths<br>• Use `Path.resolve()` to check containment | ✅ Implemented |
| **File Overwrite** | Medium - Could replace existing files | • Use UUID-based server-side filenames<br>• Check for existing files before write | ✅ Implemented |
| **Denial of Service (Storage)** | Medium - Could fill disk space | • Enforce 5MB file size limit<br>• Monitor storage usage | ✅ Implemented |
| **Malicious File Upload** | High - Could upload executables, scripts | • Magic number validation (not extensions)<br>• Whitelist: JPEG, PNG, WebP only<br>• Content-type verification | ✅ Implemented |

### 2. File Content Threats

| Threat | Risk | Mitigation | Status |
|--------|------|------------|--------|
| **Fake Images** | Medium - Malformed images could crash processors | • Use `python-magic` for MIME detection<br>• Validate with PIL after upload | ✅ Implemented |
| **EXIF Data Leaks** | Low - Could leak GPS, camera info | • Strip EXIF metadata (future enhancement)<br>• Sanitize before storage | ⏳ Planned |
| **Malware in Images** | Low - Steganography, embedded payloads | • Scan with antivirus (future enhancement)<br>• Use trusted image processing libraries | ⏳ Planned |

### 3. Application Layer Threats

| Threat | Risk | Mitigation | Status |
|--------|------|------------|--------|
| **CSRF Attacks** | Medium - Unauthorized uploads | • FastAPI CSRF protection<br>• Authentication required for uploads | ✅ Implemented |
| **IDOR (Insecure Direct Object Reference)** | Medium - Access other users' images | • Validate product ownership<br>• Check `product_id` matches image ownership | ✅ Implemented |
| **Brute Force Uploads** | Low - Many failed attempts | • Rate limiting per IP/user<br>• Request throttling | ⏳ Planned |

### 4. Storage & Infrastructure Threats

| Threat | Risk | Mitigation | Status |
|--------|------|------------|--------|
| **Insecure File Permissions** | High - Could allow unauthorized access | • Set restrictive permissions (600 for files, 755 for dirs)<br>• Run service with minimal privileges | ✅ Implemented |
| **Race Conditions** | Medium - Concurrent upload issues | • Atomic writes (temp file → rename)<br>• Database transactions for metadata | ✅ Implemented |
| **Metadata Corruption** | Low - JSON file corruption | • Atomic metadata updates<br>• Backup mechanism<br>• Schema validation | ✅ Implemented |

### 5. Docusaurus Integration Threats

| Threat | Risk | Mitigation | Status |
|--------|------|------------|--------|
| **Invalid Metadata Format** | Medium - Could break Docusaurus | • Schema validation before write<br>• JSON linting | ✅ Implemented |
| **Path Injection in URLs** | Low - Malicious URLs in metadata | • URL sanitization<br>• Validate paths are under `/static/img/` | ✅ Implemented |

## Implementation Details

### Magic Number Validation
```python
# Uses python-magic to detect actual file type
mime = magic.Magic(mime=True)
mime_type = mime.from_buffer(file_content)
if mime_type not in ["image/jpeg", "image/png", "image/webp"]:
    raise HTTPException(415, "Invalid image format")
```

### Path Safety
```python
def _validate_file_path(self, filepath: Path) -> bool:
    absolute_path = filepath.resolve()
    allowed_path = self.base_storage_path.resolve()
    
    # Must be within allowed directory
    if not str(absolute_path).startswith(str(allowed_path)):
        return False
    
    # No traversal attempts
    if ".." in str(filepath) or filepath.is_absolute():
        return False
    
    return True
```

### Atomic Writes
```python
# 1. Write to temp file
temp_file_path = file_path.with_suffix(".tmp")
with open(temp_file_path, "wb") as f:
    f.write(file_content)

# 2. Atomically rename
os.rename(temp_file_path, file_path)
```

## Testing Coverage

### Security Tests Required
- [x] Path traversal attempts (`../`, encoded variants)
- [x] Fake image files (correct extension, wrong content)
- [x] Oversized file uploads (>5MB)
- [x] Invalid MIME types (PDF, EXE, etc.)
- [x] Concurrent upload tests
- [x] Unauthorized access attempts
- [ ] EXIF data sanitization
- [ ] Rate limiting tests

### Monitoring & Logging
- All file operations logged with timestamps
- Failed upload attempts logged with reason
- Storage usage monitoring
- Access pattern analysis

## Dependencies Security

| Dependency | Purpose | Security Notes |
|------------|---------|----------------|
| `python-magic` | File type detection | Uses libmagic, well-maintained |
| `Pillow` | Image processing | Actively maintained, security-focused |
| `FastAPI` | Web framework | Built-in security features |

## Deployment Checklist
- [ ] Set proper file permissions on `/static/img/`
- [ ] Configure reverse proxy limits (client_max_body_size)
- [ ] Enable HTTPS only
- [ ] Set up monitoring alerts
- [ ] Regular security updates
- [ ] Backup `/static/img/` and `metadata.json`

## Incident Response
1. **Detection**: Monitor logs for failed upload attempts
2. **Containment**: Block suspicious IPs, revoke tokens
3. **Investigation**: Check file system, review metadata
4. **Recovery**: Restore from backups, fix vulnerabilities
5. **Prevention**: Update security measures, retest

---

*Last Updated: 2025-12-01*  
*Maintainer: Sina Naghipour*