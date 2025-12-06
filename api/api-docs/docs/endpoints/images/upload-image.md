# POST /files

**Upload Product Image** - Upload and associate an image with a product (Admin Only)

**Tags:** Product Images

**Authentication:** Required (Bearer Token with Admin privileges)

---

## Description
Upload an image file to associate with a product. Images can be set as primary for the product and are automatically processed (resized, optimized, and stored securely). Supported formats: JPEG, PNG, WebP. Maximum file size: 5MB.

## Authentication
**Required:** Bearer Token with Admin role

### Headers
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

## Request

### Form Data

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `file` | file | ✓ | Max 5MB, JPEG/PNG/WebP | Image file to upload |
| `productId` | string | ✓ | Existing product ID | Product to associate image with |
| `is_primary` | boolean | No | Default: `false` | Set as primary product image |
| `alt_text` | string | No | ≤ 255 chars | Alternative text for accessibility |
| `caption` | string | No | ≤ 500 chars | Image caption/description |
| `order` | integer | No | ≥ 0 | Display order (lower numbers first) |
| `tags` | string[] | No | ≤ 10 tags | Image tags for categorization |
| `metadata` | JSON | No | - | Additional metadata as JSON string |

## Responses

### 201 Created - Image uploaded successfully
**Headers:**
- `Location`: `/files/{imageId}` (URI to created image resource)
- `X-Image-ID`: `img_12345678-1234-5678-1234-567812345678`

**Body:**
```json
{
  "id": "img_12345678-1234-5678-1234-567812345678",
  "productId": "prod_789",
  "filename": "prod_789_abc123def456.jpg",
  "originalName": "product-image.jpg",
  "mimeType": "image/jpeg",
  "size": 2457600,
  "dimensions": {
    "width": 1200,
    "height": 800,
    "aspectRatio": "3:2"
  },
  "variants": {
    "original": "/static/img/products/prod_789/prod_789_abc123def456.jpg",
    "large": "/static/img/products/prod_789/large/prod_789_abc123def456.jpg",
    "medium": "/static/img/products/prod_789/medium/prod_789_abc123def456.jpg",
    "thumbnail": "/static/img/products/prod_789/thumb/prod_789_abc123def456.jpg",
    "webp": "/static/img/products/prod_789/webp/prod_789_abc123def456.webp"
  },
  "isPrimary": true,
  "altText": "Premium wireless keyboard on wooden desk",
  "caption": "Main product shot showing design details",
  "order": 0,
  "tags": ["lifestyle", "desk", "keyboard"],
  "metadata": {
    "camera": "Canon EOS R5",
    "lens": "RF 24-70mm f/2.8",
    "colorProfile": "sRGB"
  },
  "uploadedAt": "2024-01-15T10:30:00Z",
  "uploadedBy": "admin_user",
  "processingStatus": "completed",
  "storage": {
    "location": "s3://product-images/prod_789/",
    "bucket": "product-images",
    "region": "us-east-1"
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique image identifier (UUID) |
| `productId` | string | Associated product ID |
| `filename` | string | Server-generated filename |
| `originalName` | string | Original client filename |
| `mimeType` | string | MIME type of uploaded file |
| `size` | integer | File size in bytes |
| `dimensions` | object | Image dimensions and aspect ratio |
| `variants` | object | URLs to different image sizes/formats |
| `isPrimary` | boolean | Whether this is primary product image |
| `altText` | string | Alternative text for accessibility |
| `caption` | string | Image caption/description |
| `order` | integer | Display order |
| `tags` | string[] | Image tags |
| `metadata` | object | Additional metadata |
| `uploadedAt` | string | Upload timestamp |
| `uploadedBy` | string | User who uploaded the image |
| `processingStatus` | string | Status of image processing |
| `storage` | object | Storage location information |

### 400 Bad Request - Invalid input
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/bad-request",
  "title": "Bad Request",
  "status": 400,
  "detail": "Missing required field: productId.",
  "instance": "/files"
}
```

### 401 Unauthorized - Missing or invalid token
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/unauthorized",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Missing or invalid Authorization header.",
  "instance": "/files"
}
```

### 403 Forbidden - Insufficient permissions
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "Insufficient permissions to upload product images.",
  "instance": "/files"
}
```

### 404 Not Found - Product not found
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/not-found",
  "title": "Not Found",
  "status": 404,
  "detail": "Product with ID 'prod_999' not found.",
  "instance": "/files"
}
```

### 413 Payload Too Large - File too large
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/file-too-large",
  "title": "File Too Large",
  "status": 413,
  "detail": "File size exceeds maximum allowed size of 5MB.",
  "instance": "/files",
  "maxSize": 5242880,
  "actualSize": 6291456
}
```

### 415 Unsupported Media Type - Invalid file type
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/unsupported-media-type",
  "title": "Unsupported Media Type",
  "status": 415,
  "detail": "Only JPEG, PNG, and WebP images are supported.",
  "instance": "/files",
  "allowedTypes": ["image/jpeg", "image/png", "image/webp"],
  "receivedType": "application/pdf"
}
```

### 422 Unprocessable Entity - Validation error
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/validation",
  "title": "Validation failed",
  "status": 422,
  "detail": "Image dimensions too small. Minimum: 300x300 pixels.",
  "instance": "/files",
  "errors": [
    {
      "field": "file",
      "message": "Image dimensions must be at least 300x300 pixels"
    }
  ]
}
```

### 500 Internal Server Error
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/internal",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "Failed to process uploaded image.",
  "instance": "/files"
}
```

## Examples

### Basic cURL Request
```bash
# Upload a simple product image
curl -X POST "http://localhost:8000/api/files" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "file=@/path/to/image.jpg" \
  -F "productId=prod_789"
```

### Complete cURL Request
```bash
curl -X POST "http://localhost:8000/api/files" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "file=@keyboard-main.jpg" \
  -F "productId=prod_789" \
  -F "is_primary=true" \
  -F "alt_text=Premium wireless keyboard on wooden desk" \
  -F "caption=Main product shot showing design details" \
  -F "order=0" \
  -F "tags=lifestyle" \
  -F "tags=desk" \
  -F "tags=keyboard" \
  -F "metadata={\"camera\": \"Canon EOS R5\", \"lens\": \"RF 24-70mm f/2.8\"}"
```

### JavaScript (Fetch) with Progress Tracking
```javascript
/**
 * Advanced image upload service with progress tracking and validation
 */
class ImageUploader {
  constructor(apiUrl = 'http://localhost:8000/api') {
    this.apiUrl = apiUrl;
    this.uploadQueue = new Map();
    this.maxFileSize = 5 * 1024 * 1024; // 5MB
    this.allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
    this.minDimensions = { width: 300, height: 300 };
  }
  
  /**
   * Upload product image with comprehensive features
   */
  async uploadImage(file, productId, options = {}, accessToken) {
    const {
      isPrimary = false,
      altText = '',
      caption = '',
      order = 0,
      tags = [],
      metadata = {},
      onProgress = null,
      onComplete = null,
      onError = null
    } = options;
    
    // Validate file before upload
    const validation = this.validateFile(file);
    if (!validation.valid) {
      throw new ImageValidationError('File validation failed', validation.errors);
    }
    
    // Validate product exists
    await this.validateProduct(productId, accessToken);
    
    // Create FormData
    const formData = new FormData();
    formData.append('file', file);
    formData.append('productId', productId);
    
    if (isPrimary) formData.append('is_primary', 'true');
    if (altText) formData.append('alt_text', altText);
    if (caption) formData.append('caption', caption);
    if (order > 0) formData.append('order', order.toString());
    
    tags.forEach(tag => formData.append('tags[]', tag));
    
    if (Object.keys(metadata).length > 0) {
      formData.append('metadata', JSON.stringify(metadata));
    }
    
    // Generate upload ID for tracking
    const uploadId = this.generateUploadId(file, productId);
    
    // Add to upload queue
    this.uploadQueue.set(uploadId, {
      file,
      productId,
      status: 'uploading',
      progress: 0,
      startedAt: new Date()
    });
    
    try {
      // Create XMLHttpRequest for progress tracking
      const xhr = new XMLHttpRequest();
      
      // Set up progress tracking
      if (onProgress) {
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const progress = Math.round((event.loaded / event.total) * 100);
            this.updateUploadProgress(uploadId, progress);
            onProgress(progress, uploadId);
          }
        });
      }
      
      // Make request
      const result = await new Promise((resolve, reject) => {
        xhr.open('POST', `${this.apiUrl}/files`);
        xhr.setRequestHeader('Authorization', `Bearer ${accessToken}`);
        
        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const response = JSON.parse(xhr.responseText);
              this.updateUploadStatus(uploadId, 'completed', response);
              
              // Trigger completion callback
              if (onComplete) {
                onComplete(response, uploadId);
              }
              
              // Update product cache
              this.updateProductCache(productId, response);
              
              // Trigger events
              this.triggerImageUploadedEvent(productId, response);
              
              resolve(response);
            } catch (error) {
              reject(new ImageUploadError('Failed to parse response', xhr.status, error));
            }
          } else {
            const error = this.parseUploadError(xhr);
            this.updateUploadStatus(uploadId, 'failed', error);
            
            if (onError) {
              onError(error, uploadId);
            }
            
            reject(error);
          }
        };
        
        xhr.onerror = () => {
          const error = new ImageUploadError('Network error during upload', null);
          this.updateUploadStatus(uploadId, 'failed', error);
          
          if (onError) {
            onError(error, uploadId);
          }
          
          reject(error);
        };
        
        xhr.send(formData);
      });
      
      return result;
      
    } catch (error) {
      // Update queue status
      this.updateUploadStatus(uploadId, 'failed', error);
      throw error;
    }
  }
  
  /**
   * Upload multiple images
   */
  async uploadMultipleImages(files, productId, accessToken, options = {}) {
    const {
      concurrency = 3,
      onBatchProgress = null,
      stopOnError = false
    } = options;
    
    const results = {
      successful: [],
      failed: [],
      total: files.length
    };
    
    // Process in batches for concurrency control
    for (let i = 0; i < files.length; i += concurrency) {
      const batch = files.slice(i, i + concurrency);
      const batchPromises = batch.map((file, index) =>
        this.uploadImage(file, productId, {
          order: i + index,
          ...options
        }, accessToken)
          .then(result => ({ success: true, file, result }))
          .catch(error => ({ success: false, file, error }))
      );
      
      const batchResults = await Promise.all(batchPromises);
      
      batchResults.forEach(result => {
        if (result.success) {
          results.successful.push({
            file: result.file.name,
            result: result.result
          });
        } else {
          results.failed.push({
            file: result.file.name,
            error: result.error
          });
          
          if (stopOnError) {
            throw new BatchUploadError('Batch upload stopped due to error', results);
          }
        }
      });
      
      // Batch progress callback
      if (onBatchProgress) {
        const processed = results.successful.length + results.failed.length;
        onBatchProgress(processed, files.length);
      }
    }
    
    return results;
  }
  
  /**
   * Upload with drag and drop
   */
  async uploadFromDropZone(dropZoneElement, productId, accessToken, options = {}) {
    return new Promise((resolve, reject) => {
      dropZoneElement.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZoneElement.classList.add('dragover');
      });
      
      dropZoneElement.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZoneElement.classList.remove('dragover');
      });
      
      dropZoneElement.addEventListener('drop', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZoneElement.classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files);
        const imageFiles = files.filter(file => 
          this.allowedTypes.includes(file.type)
        );
        
        if (imageFiles.length === 0) {
          reject(new ImageValidationError('No valid image files found'));
          return;
        }
        
        try {
          const results = await this.uploadMultipleImages(
            imageFiles,
            productId,
            accessToken,
            options
          );
          resolve(results);
        } catch (error) {
          reject(error);
        }
      });
    });
  }
  
  /**
   * Upload with preview and editing
   */
  async uploadWithPreview(fileInput, productId, accessToken, options = {}) {
    const files = Array.from(fileInput.files);
    const previews = [];
    
    // Create previews
    for (const file of files) {
      const preview = await this.createImagePreview(file);
      previews.push({
        file,
        preview,
        metadata: {
          altText: options.altText || '',
          caption: options.caption || '',
          tags: options.tags || []
        }
      });
    }
    
    // Show preview UI (implementation depends on your UI framework)
    this.showPreviewUI(previews, async (editedPreviews) => {
      // Upload edited previews
      const uploadPromises = editedPreviews.map(preview =>
        this.uploadImage(preview.file, productId, {
          ...options,
          altText: preview.metadata.altText,
          caption: preview.metadata.caption,
          tags: preview.metadata.tags
        }, accessToken)
      );
      
      return Promise.all(uploadPromises);
    });
  }
  
  /**
   * Validate file before upload
   */
  validateFile(file) {
    const errors = [];
    
    // Check file type
    if (!this.allowedTypes.includes(file.type)) {
      errors.push({
        field: 'type',
        message: `File type not supported. Allowed: ${this.allowedTypes.join(', ')}`
      });
    }
    
    // Check file size
    if (file.size > this.maxFileSize) {
      errors.push({
        field: 'size',
        message: `File too large. Maximum: ${this.formatBytes(this.maxFileSize)}`,
        maxSize: this.maxFileSize,
        actualSize: file.size
      });
    }
    
    // Check file name
    if (!file.name || file.name.length > 255) {
      errors.push({
        field: 'name',
        message: 'File name must be between 1 and 255 characters'
      });
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
  
  /**
   * Validate product exists
   */
  async validateProduct(productId, accessToken) {
    try {
      const response = await fetch(`${this.apiUrl}/products/${productId}`, {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      });
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new ProductNotFoundError(`Product ${productId} not found`);
        }
        throw new Error(`Failed to validate product: ${response.status}`);
      }
    } catch (error) {
      if (error instanceof ProductNotFoundError) {
        throw error;
      }
      throw new ValidationError(`Product validation failed: ${error.message}`);
    }
  }
  
  /**
   * Create image preview
   */
  createImagePreview(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
          resolve({
            url: e.target.result,
            width: img.width,
            height: img.height,
            aspectRatio: img.width / img.height,
            file: file
          });
        };
        img.onerror = () => reject(new Error('Failed to load image'));
        img.src = e.target.result;
      };
      
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsDataURL(file);
    });
  }
  
  /**
   * Parse upload error
   */
  parseUploadError(xhr) {
    let detail = 'Upload failed';
    let errors = [];
    
    try {
      const errorData = JSON.parse(xhr.responseText);
      detail = errorData.detail || detail;
      
      if (errorData.errors) {
        errors = errorData.errors;
      }
    } catch {
      detail = xhr.statusText || `HTTP ${xhr.status}`;
    }
    
    if (xhr.status === 413) {
      return new FileTooLargeError(detail, errors);
    } else if (xhr.status === 415) {
      return new UnsupportedTypeError(detail, errors);
    } else if (xhr.status === 422) {
      return new ImageValidationError(detail, errors);
    } else {
      return new ImageUploadError(detail, xhr.status, errors);
    }
  }
  
  /**
   * Update upload progress in queue
   */
  updateUploadProgress(uploadId, progress) {
    const upload = this.uploadQueue.get(uploadId);
    if (upload) {
      upload.progress = progress;
      this.uploadQueue.set(uploadId, upload);
    }
  }
  
  /**
   * Update upload status in queue
   */
  updateUploadStatus(uploadId, status, data) {
    const upload = this.uploadQueue.get(uploadId);
    if (upload) {
      upload.status = status;
      upload.completedAt = new Date();
      
      if (status === 'completed') {
        upload.result = data;
      } else if (status === 'failed') {
        upload.error = data;
      }
      
      this.uploadQueue.set(uploadId, upload);
    }
  }
  
  /**
   * Update product cache with new image
   */
  updateProductCache(productId, imageData) {
    // Implementation depends on your caching strategy
    console.log(`Updated cache for product ${productId} with image ${imageData.id}`);
  }
  
  /**
   * Trigger image uploaded event
   */
  triggerImageUploadedEvent(productId, imageData) {
    const event = new CustomEvent('imageUploaded', {
      detail: {
        productId,
        image: imageData,
        timestamp: new Date().toISOString()
      }
    });
    
    window.dispatchEvent(event);
    
    // Analytics
    if (window.gtag) {
      window.gtag('event', 'upload_image', {
        product_id: productId,
        image_id: imageData.id,
        file_size: imageData.size,
        is_primary: imageData.isPrimary
      });
    }
  }
  
  /**
   * Show preview UI (simplified)
   */
  showPreviewUI(previews, onConfirm) {
    // In a real implementation, this would show a modal or preview component
    console.log('Showing preview for', previews.length, 'images');
    
    // Simulate user confirmation after 1 second
    setTimeout(() => {
      onConfirm(previews);
    }, 1000);
  }
  
  /**
   * Helper methods
   */
  generateUploadId(file, productId) {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substr(2, 9);
    return `upload_${productId}_${timestamp}_${random}`;
  }
  
  formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }
  
  getUploadStatus(uploadId) {
    return this.uploadQueue.get(uploadId);
  }
  
  clearCompletedUploads() {
    for (const [id, upload] of this.uploadQueue) {
      if (upload.status === 'completed' || upload.status === 'failed') {
        const age = new Date() - upload.completedAt;
        if (age > 24 * 60 * 60 * 1000) { // 24 hours
          this.uploadQueue.delete(id);
        }
      }
    }
  }
}

// Custom Error Classes
class ImageValidationError extends Error {
  constructor(message, errors = []) {
    super(message);
    this.name = 'ImageValidationError';
    this.errors = errors;
  }
}

class ImageUploadError extends Error {
  constructor(message, statusCode = null, details = null) {
    super(message);
    this.name = 'ImageUploadError';
    this.status = statusCode;
    this.details = details;
  }
}

class FileTooLargeError extends ImageUploadError {
  constructor(message, errors = []) {
    super(message, 413, errors);
    this.name = 'FileTooLargeError';
  }
}

class UnsupportedTypeError extends ImageUploadError {
  constructor(message, errors = []) {
    super(message, 415, errors);
    this.name = 'UnsupportedTypeError';
  }
}

class ProductNotFoundError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ProductNotFoundError';
  }
}

class ValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ValidationError';
  }
}

class BatchUploadError extends Error {
  constructor(message, results = null) {
    super(message);
    this.name = 'BatchUploadError';
    this.results = results;
  }
}

// Usage Examples
async function demonstrateImageUpload() {
  const uploader = new ImageUploader();
  const accessToken = localStorage.getItem('accessToken');
  const productId = 'prod_789';
  
  try {
    // Example 1: Single image upload with progress
    console.log('Example 1: Uploading single image...');
    
    // Simulate file input
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*';
    
    // Listen for file selection
    fileInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      
      if (!file) return;
      
      try {
        const result = await uploader.uploadImage(file, productId, {
          isPrimary: true,
          altText: 'Product main image',
          caption: 'High-quality product photography',
          tags: ['main', 'product'],
          onProgress: (progress, uploadId) => {
            console.log(`Upload progress: ${progress}%`);
          },
          onComplete: (imageData, uploadId) => {
            console.log('Upload completed:', imageData);
          }
        }, accessToken);
        
        console.log('Image uploaded successfully:', result.id);
        
      } catch (error) {
        console.error('Upload failed:', error);
        
        if (error instanceof ImageValidationError) {
          error.errors.forEach(err => {
            console.error(`  - ${err.field}: ${err.message}`);
          });
        }
      }
    });
    
    // Trigger file selection (in real usage, user would click)
    // fileInput.click();
    
    // Example 2: Multiple image upload
    console.log('\nExample 2: Uploading multiple images...');
    
    const files = [
      // Simulated files - in real usage these would come from file input
    ];
    
    if (files.length > 0) {
      const results = await uploader.uploadMultipleImages(
        files,
        productId,
        accessToken,
        {
          concurrency: 3,
          onBatchProgress: (processed, total) => {
            console.log(`Batch progress: ${processed}/${total}`);
          }
        }
      );
      
      console.log(`Batch upload complete. Successful: ${results.successful.length}, Failed: ${results.failed.length}`);
    }
    
    // Example 3: Check upload status
    console.log('\nExample 3: Checking upload status...');
    
    // Get status of a specific upload
    const uploadId = 'upload_prod_789_1234567890_abc123';
    const status = uploader.getUploadStatus(uploadId);
    
    if (status) {
      console.log(`Upload ${uploadId}: ${status.status}, Progress: ${status.progress}%`);
    }
    
  } catch (error) {
    console.error('Demo error:', error);
  }
}
```

### React Component for Image Upload
```jsx
import React, { useState, useRef, useCallback } from 'react';
import ImagePreview from './ImagePreview';
import UploadProgress from './UploadProgress';

function ProductImageUpload({ productId, onUploadComplete }) {
  const [files, setFiles] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState({});
  const [errors, setErrors] = useState([]);
  const [metadata, setMetadata] = useState({});
  
  const fileInputRef = useRef(null);
  
  // Handle file selection
  const handleFileSelect = useCallback((event) => {
    const selectedFiles = Array.from(event.target.files);
    
    // Validate files
    const validFiles = [];
    const validationErrors = [];
    
    selectedFiles.forEach((file, index) => {
      // Basic validation
      if (!file.type.startsWith('image/')) {
        validationErrors.push({
          file: file.name,
          message: 'Not an image file'
        });
        return;
      }
      
      if (file.size > 5 * 1024 * 1024) {
        validationErrors.push({
          file: file.name,
          message: 'File too large (max 5MB)'
        });
        return;
      }
      
      validFiles.push(file);
    });
    
    if (validationErrors.length > 0) {
      setErrors(prev => [...prev, ...validationErrors]);
    }
    
    if (validFiles.length > 0) {
      // Create previews
      const newPreviews = validFiles.map(file => ({
        file,
        previewUrl: URL.createObjectURL(file),
        metadata: {
          altText: '',
          caption: '',
          tags: [],
          order: files.length + validFiles.indexOf(file),
          isPrimary: files.length + validFiles.indexOf(file) === 0
        }
      }));
      
      setPreviews(prev => [...prev, ...newPreviews]);
      setFiles(prev => [...prev, ...validFiles]);
    }
    
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [files.length]);
  
  // Handle drag and drop
  const handleDrop = useCallback((event) => {
    event.preventDefault();
    event.stopPropagation();
    
    const droppedFiles = Array.from(event.dataTransfer.files);
    const fileInputEvent = { target: { files: droppedFiles } };
    handleFileSelect(fileInputEvent);
  }, [handleFileSelect]);
  
  const handleDragOver = useCallback((event) => {
    event.preventDefault();
    event.stopPropagation();
  }, []);
  
  // Update metadata for a specific file
  const updateFileMetadata = useCallback((index, updates) => {
    setPreviews(prev => prev.map((preview, i) => 
      i === index ? { ...preview, metadata: { ...preview.metadata, ...updates } } : preview
    ));
  }, []);
  
  // Remove file from list
  const removeFile = useCallback((index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
    setPreviews(prev => {
      const removedPreview = prev[index];
      if (removedPreview?.previewUrl) {
        URL.revokeObjectURL(removedPreview.previewUrl);
      }
      return prev.filter((_, i) => i !== index);
    });
    
    // Update order for remaining files
    setPreviews(prev => prev.map((preview, i) => ({
      ...preview,
      metadata: { ...preview.metadata, order: i }
    })));
  }, []);
  
  // Upload files
  const handleUpload = useCallback(async () => {
    if (files.length === 0 || uploading) return;
    
    setUploading(true);
    setErrors([]);
    
    const accessToken = localStorage.getItem('accessToken');
    const uploadResults = [];
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const fileMetadata = previews[i]?.metadata || {};
      
      try {
        // Create FormData
        const formData = new FormData();
        formData.append('file', file);
        formData.append('productId', productId);
        
        if (fileMetadata.isPrimary) {
          formData.append('is_primary', 'true');
        }
        
        if (fileMetadata.altText) {
          formData.append('alt_text', fileMetadata.altText);
        }
        
        if (fileMetadata.caption) {
          formData.append('caption', fileMetadata.caption);
        }
        
        if (fileMetadata.order !== undefined) {
          formData.append('order', fileMetadata.order.toString());
        }
        
        if (fileMetadata.tags?.length > 0) {
          fileMetadata.tags.forEach(tag => formData.append('tags[]', tag));
        }
        
        // Create XMLHttpRequest for progress tracking
        const xhr = new XMLHttpRequest();
        
        // Track progress
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const progressPercent = Math.round((event.loaded / event.total) * 100);
            setProgress(prev => ({ ...prev, [i]: progressPercent }));
          }
        });
        
        // Make request
        const result = await new Promise((resolve, reject) => {
          xhr.open('POST', `http://localhost:8000/api/files`);
          xhr.setRequestHeader('Authorization', `Bearer ${accessToken}`);
          
          xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              try {
                const response = JSON.parse(xhr.responseText);
                resolve(response);
              } catch {
                reject(new Error('Failed to parse response'));
              }
            } else {
              reject(new Error(`Upload failed: ${xhr.status}`));
            }
          };
          
          xhr.onerror = () => reject(new Error('Network error'));
          xhr.send(formData);
        });
        
        uploadResults.push({
          success: true,
          file: file.name,
          result
        });
        
      } catch (error) {
        uploadResults.push({
          success: false,
          file: file.name,
          error: error.message
        });
        
        setErrors(prev => [...prev, {
          file: file.name,
          message: error.message
        }]);
      }
    }
    
    setUploading(false);
    setProgress({});
    
    // Notify parent component
    if (onUploadComplete) {
      onUploadComplete(uploadResults);
    }
    
    // Clear files on successful upload
    const allSuccessful = uploadResults.every(r => r.success);
    if (allSuccessful) {
      setFiles([]);
      setPreviews([]);
      
      // Clean up object URLs
      previews.forEach(preview => {
        if (preview.previewUrl) {
          URL.revokeObjectURL(preview.previewUrl);
        }
      });
    }
  }, [files, previews, productId, uploading, onUploadComplete]);
  
  // Set primary image
  const setPrimaryImage = useCallback((index) => {
    setPreviews(prev => prev.map((preview, i) => ({
      ...preview,
      metadata: { ...preview.metadata, isPrimary: i === index }
    })));
  }, []);
  
  return (
    <div className="image-upload-container">
      <div className="upload-area">
        {/* Drag and Drop Zone */}
        <div
          className={`drop-zone ${files.length > 0 ? 'has-files' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={() => fileInputRef.current?.click()}
        >
          {files.length === 0 ? (
            <>
              <div className="drop-zone-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                  <path d="M19 13H13V19H11V13H5V11H11V5H13V11H19V13Z" fill="currentColor"/>
                </svg>
              </div>
              <div className="drop-zone-text">
                <p>Drag & drop images here, or click to browse</p>
                <p className="hint">Supports JPEG, PNG, WebP • Max 5MB per file</p>
              </div>
            </>
          ) : (
            <div className="files-selected">
              <p>{files.length} image{files.length !== 1 ? 's' : ''} selected</p>
              <button 
                type="button"
                className="btn-add-more"
                onClick={(e) => {
                  e.stopPropagation();
                  fileInputRef.current?.click();
                }}
              >
                Add More
              </button>
            </div>
          )}
          
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/*"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
        </div>
        
        {/* Error Display */}
        {errors.length > 0 && (
          <div className="upload-errors">
            <h4>Upload Errors</h4>
            <ul>
              {errors.map((error, index) => (
                <li key={index}>
                  <strong>{error.file}:</strong> {error.message}
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Image Previews */}
        {previews.length > 0 && (
          <div className="image-previews">
            <h3>Selected Images ({previews.length})</h3>
            
            <div className="preview-grid">
              {previews.map((preview, index) => (
                <ImagePreview
                  key={index}
                  preview={preview}
                  index={index}
                  onUpdateMetadata={(updates) => updateFileMetadata(index, updates)}
                  onRemove={() => removeFile(index)}
                  onSetPrimary={() => setPrimaryImage(index)}
                  progress={progress[index]}
                  isUploading={uploading}
                />
              ))}
            </div>
            
            {/* Upload Progress */}
            {uploading && (
              <UploadProgress
                total={files.length}
                completed={Object.keys(progress).filter(i => progress[i] === 100).length}
                progress={progress}
              />
            )}
            
            {/* Upload Button */}
            <div className="upload-actions">
              <button
                type="button"
                onClick={handleUpload}
                disabled={uploading || files.length === 0}
                className="btn-upload"
              >
                {uploading ? 'Uploading...' : `Upload ${files.length} Image${files.length !== 1 ? 's' : ''}`}
              </button>
              
              {files.length > 0 && !uploading && (
                <button
                  type="button"
                  onClick={() => {
                    setFiles([]);
                    setPreviews([]);
                    setErrors([]);
                  }}
                  className="btn-clear"
                >
                  Clear All
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ProductImageUpload;
```

### Python with Advanced Image Processing
```python
import requests
import json
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple, BinaryIO
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import asyncio
from PIL import Image
import io

class ImageFormat(Enum):
    """Supported image formats."""
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"

class ImageSize(Enum):
    """Standard image sizes."""
    ORIGINAL = "original"
    LARGE = "large"      # 1200px width
    MEDIUM = "medium"    # 800px width
    THUMBNAIL = "thumb"  # 300px width
    TINY = "tiny"        # 100px width

@dataclass
class ImageMetadata:
    """Metadata for an uploaded image."""
    filename: str
    original_name: str
    mime_type: str
    size: int
    width: int
    height: int
    aspect_ratio: str
    color_profile: str = "sRGB"
    has_alpha: bool = False
    
    @classmethod
    def from_file(cls, file_path: Path) -> 'ImageMetadata':
        """Create metadata from image file."""
        with Image.open(file_path) as img:
            width, height = img.size
            has_alpha = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)
            
            return cls(
                filename=file_path.name,
                original_name=file_path.name,
                mime_type=mimetypes.guess_type(file_path)[0] or 'image/jpeg',
                size=file_path.stat().st_size,
                width=width,
                height=height,
                aspect_ratio=f"{width}:{height}",
                has_alpha=has_alpha
            )

class ProductImageUploader:
    """Advanced product image uploader with processing capabilities."""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        })
        
        # Configuration
        self.max_file_size = 5 * 1024 * 1024  # 5MB
        self.allowed_types = {
            'image/jpeg': ImageFormat.JPEG,
            'image/png': ImageFormat.PNG,
            'image/webp': ImageFormat.WEBP
        }
        self.min_dimensions = (300, 300)
        self.max_dimensions = (5000, 5000)
        
        # Processing queue
        self.upload_queue = []
        self.processing_tasks = {}
    
    def upload_image(
        self,
        image_path: Path,
        product_id: str,
        options: Optional[Dict] = None
    ) -> Dict:
        """
        Upload a single image with optional processing.
        
        Args:
            image_path: Path to image file
            product_id: Product identifier
            options: Upload options
            
        Returns:
            Upload result
        """
        options = options or {}
        
        # Validate image
        self._validate_image_file(image_path)
        
        # Process image if requested
        processed_image = None
        if options.get('process', True):
            processed_image = self._process_image(image_path, options.get('processing_options', {}))
        
        # Prepare upload data
        upload_data = self._prepare_upload_data(
            image_path,
            processed_image,
            product_id,
            options
        )
        
        # Upload to API
        result = self._upload_to_api(upload_data)
        
        # Clean up temporary files
        if processed_image and processed_image != image_path:
            processed_image.unlink(missing_ok=True)
        
        return result
    
    def upload_multiple_images(
        self,
        image_paths: List[Path],
        product_id: str,
        options: Optional[Dict] = None
    ) -> Dict:
        """
        Upload multiple images with parallel processing.
        
        Args:
            image_paths: List of image file paths
            product_id: Product identifier
            options: Upload options
            
        Returns:
            Bulk upload results
        """
        options = options or {}
        
        results = {
            'total': len(image_paths),
            'successful': [],
            'failed': [],
            'started_at': datetime.utcnow()
        }
        
        # Process in parallel if enabled
        if options.get('parallel', True):
            import concurrent.futures
            
            max_workers = options.get('max_workers', 3)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all upload tasks
                future_to_path = {
                    executor.submit(self._safe_upload, path, product_id, options): path
                    for path in image_paths
                }
                
                # Process results as they complete
                for future in concurrent.futures.as_completed(future_to_path):
                    path = future_to_path[future]
                    try:
                        result = future.result()
                        results['successful'].append({
                            'path': str(path),
                            'result': result
                        })
                    except Exception as e:
                        results['failed'].append({
                            'path': str(path),
                            'error': str(e)
                        })
        else:
            # Process sequentially
            for path in image_paths:
                try:
                    result = self._safe_upload(path, product_id, options)
                    results['successful'].append({
                        'path': str(path),
                        'result': result
                    })
                except Exception as e:
                    results['failed'].append({
                        'path': str(path),
                        'error': str(e)
                    })
        
        results['completed_at'] = datetime.utcnow()
        results['duration'] = (results['completed_at'] - results['started_at']).total_seconds()
        
        return results
    
    def upload_from_directory(
        self,
        directory: Path,
        product_id: str,
        file_pattern: str = "*.{jpg,jpeg,png,webp}",
        options: Optional[Dict] = None
    ) -> Dict:
        """
        Upload all images from a directory.
        
        Args:
            directory: Directory containing images
            product_id: Product identifier
            file_pattern: Glob pattern for image files
            options: Upload options
            
        Returns:
            Directory upload results
        """
        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")
        
        # Find image files
        image_paths = []
        for ext in file_pattern.strip('{}').split(','):
            image_paths.extend(directory.glob(f"*.{ext}"))
        
        if not image_paths:
            return {
                'total': 0,
                'successful': [],
                'failed': [],
                'message': 'No image files found'
            }
        
        # Upload all images
        return self.upload_multiple_images(image_paths, product_id, options)
    
    def upload_with_processing_pipeline(
        self,
        image_path: Path,
        product_id: str,
        pipeline: List[Dict]
    ) -> Dict:
        """
        Upload image with custom processing pipeline.
        
        Args:
            image_path: Path to image file
            product_id: Product identifier
            pipeline: List of processing steps
            
        Returns:
            Upload result with processing metadata
        """
        # Validate pipeline
        if not pipeline:
            raise ValueError("Processing pipeline cannot be empty")
        
        # Process image through pipeline
        processed_images = []
        current_image = image_path
        
        for step in pipeline:
            step_type = step.get('type')
            step_options = step.get('options', {})
            
            if step_type == 'resize':
                current_image = self._resize_image(current_image, **step_options)
            elif step_type == 'crop':
                current_image = self._crop_image(current_image, **step_options)
            elif step_type == 'compress':
                current_image = self._compress_image(current_image, **step_options)
            elif step_type == 'convert':
                current_image = self._convert_format(current_image, **step_options)
            elif step_type == 'watermark':
                current_image = self._add_watermark(current_image, **step_options)
            else:
                raise ValueError(f"Unknown processing step: {step_type}")
            
            processed_images.append({
                'step': step_type,
                'image': current_image,
                'metadata': ImageMetadata.from_file(current_image)
            })
        
        # Upload final processed image
        upload_result = self.upload_image(current_image, product_id, {'process': False})
        
        # Add processing metadata to result
        upload_result['processing_pipeline'] = [
            {
                'step': img['step'],
                'metadata': img['metadata'].__dict__
            }
            for img in processed_images
        ]
        
        # Clean up temporary files
        for img in processed_images:
            if img['image'] != image_path:
                img['image'].unlink(missing_ok=True)
        
        return upload_result
    
    def generate_image_variants(
        self,
        image_path: Path,
        variants: List[Dict]
    ) -> Dict[str, Path]:
        """
        Generate multiple variants of an image.
        
        Args:
            image_path: Source image path
            variants: List of variant specifications
            
        Returns:
            Dictionary of variant names to file paths
        """
        results = {}
        
        for variant in variants:
            variant_name = variant.get('name', 'variant')
            width = variant.get('width')
            height = variant.get('height')
            quality = variant.get('quality', 85)
            format_name = variant.get('format', 'jpeg')
            
            # Create variant
            variant_path = self._create_variant(
                image_path,
                variant_name,
                width,
                height,
                quality,
                format_name
            )
            
            results[variant_name] = variant_path
        
        return results
    
    def upload_with_variants(
        self,
        image_path: Path,
        product_id: str,
        variants: List[Dict]
    ) -> Dict:
        """
        Upload image with multiple variants.
        
        Args:
            image_path: Source image path
            product_id: Product identifier
            variants: List of variant specifications
            
        Returns:
            Upload result with variant information
        """
        # Generate variants
        variant_files = self.generate_image_variants(image_path, variants)
        
        # Upload original image
        main_result = self.upload_image(image_path, product_id, {'process': False})
        
        # Upload variants
        variant_results = {}
        for variant_name, variant_path in variant_files.items():
            try:
                # Upload variant as separate image (linked to main)
                variant_result = self.upload_image(
                    variant_path,
                    product_id,
                    {
                        'process': False,
                        'metadata': {
                            'is_variant': True,
                            'variant_of': main_result['id'],
                            'variant_name': variant_name
                        }
                    }
                )
                variant_results[variant_name] = variant_result
            except Exception as e:
                variant_results[variant_name] = {'error': str(e)}
            finally:
                # Clean up variant file
                variant_path.unlink(missing_ok=True)
        
        main_result['variants'] = variant_results
        return main_result
    
    # Private helper methods
    def _safe_upload(
        self,
        image_path: Path,
        product_id: str,
        options: Dict
    ) -> Dict:
        """Safe wrapper for upload with error handling."""
        try:
            return self.upload_image(image_path, product_id, options)
        except ImageValidationError:
            # Try without processing
            return self.upload_image(image_path, product_id, {**options, 'process': False})
        except Exception as e:
            raise UploadError(f"Failed to upload {image_path}: {e}")
    
    def _validate_image_file(self, image_path: Path):
        """Validate image file before upload."""
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        if not image_path.is_file():
            raise ValueError(f"Not a file: {image_path}")
        
        # Check file size
        file_size = image_path.stat().st_size
        if file_size > self.max_file_size:
            raise ImageValidationError(
                f"File too large: {file_size} bytes. Maximum: {self.max_file_size} bytes",
                {'max_size': self.max_file_size, 'actual_size': file_size}
            )
        
        # Check file type
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type or mime_type not in self.allowed_types:
            raise ImageValidationError(
                f"Unsupported file type: {mime_type}. Allowed: {list(self.allowed_types.keys())}",
                {'allowed_types': list(self.allowed_types.keys()), 'actual_type': mime_type}
            )
        
        # Check image dimensions
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                if width < self.min_dimensions[0] or height < self.min_dimensions[1]:
                    raise ImageValidationError(
                        f"Image too small: {width}x{height}. Minimum: {self.min_dimensions[0]}x{self.min_dimensions[1]}",
                        {'min_dimensions': self.min_dimensions, 'actual_dimensions': (width, height)}
                    )
                
                if width > self.max_dimensions[0] or height > self.max_dimensions[1]:
                    raise ImageValidationError(
                        f"Image too large: {width}x{height}. Maximum: {self.max_dimensions[0]}x{self.max_dimensions[1]}",
                        {'max_dimensions': self.max_dimensions, 'actual_dimensions': (width, height)}
                    )
        except Exception as e:
            raise ImageValidationError(f"Failed to read image: {e}")
    
    def _process_image(self, image_path: Path, options: Dict) -> Path:
        """
        Process image (resize, compress, etc.).
        
        Args:
            image_path: Source image path
            options: Processing options
            
        Returns:
            Path to processed image (may be same as input)
        """
        # Default processing options
        default_options = {
            'max_width': 1200,
            'max_height': 1200,
            'quality': 85,
            'format': 'jpeg',
            'preserve_metadata': True
        }
        
        processing_options = {**default_options, **options}
        
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparent images
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if needed
                if img.width > processing_options['max_width'] or img.height > processing_options['max_height']:
                    img.thumbnail(
                        (processing_options['max_width'], processing_options['max_height']),
                        Image.Resampling.LANCZOS
                    )
                
                # Determine output format
                output_format = processing_options['format'].upper()
                if output_format not in ['JPEG', 'PNG', 'WEBP']:
                    output_format = 'JPEG'
                
                # Prepare save options
                save_options = {}
                if output_format == 'JPEG':
                    save_options['quality'] = processing_options['quality']
                    save_options['optimize'] = True
                elif output_format == 'WEBP':
                    save_options['quality'] = processing_options['quality']
                
                # Create output path
                output_path = image_path.parent / f"processed_{image_path.stem}.{output_format.lower()}"
                
                # Save processed image
                img.save(output_path, output_format, **save_options)
                
                return output_path
                
        except Exception as e:
            raise ImageProcessingError(f"Failed to process image: {e}")
    
    def _prepare_upload_data(
        self,
        image_path: Path,
        processed_image: Optional[Path],
        product_id: str,
        options: Dict
    ) -> Dict:
        """Prepare data for upload request."""
        # Use processed image if available, otherwise original
        upload_path = processed_image or image_path
        metadata = ImageMetadata.from_file(upload_path)
        
        # Get additional metadata from options
        alt_text = options.get('alt_text', '')
        caption = options.get('caption', '')
        is_primary = options.get('is_primary', False)
        order = options.get('order', 0)
        tags = options.get('tags', [])
        custom_metadata = options.get('metadata', {})
        
        # Prepare FormData
        form_data = {
            'productId': (None, product_id),
            'is_primary': (None, str(is_primary).lower() if is_primary else None),
            'alt_text': (None, alt_text if alt_text else None),
            'caption': (None, caption if caption else None),
            'order': (None, str(order) if order > 0 else None)
        }
        
        # Add tags
        for tag in tags:
            form_data[f'tags[]'] = (None, tag)
        
        # Add custom metadata
        if custom_metadata:
            form_data['metadata'] = (None, json.dumps(custom_metadata))
        
        # Add file
        with open(upload_path, 'rb') as f:
            form_data['file'] = (
                metadata.original_name,
                f,
                metadata.mime_type
            )
        
        return form_data
    
    def _upload_to_api(self, upload_data: Dict) -> Dict:
        """Upload image to API."""
        # Filter out None values
        filtered_data = {k: v for k, v in upload_data.items() if v[1] is not None}
        
        # Prepare files for upload
        files = {}
        for key, value in filtered_data.items():
            if key == 'file':
                files['file'] = value
            else:
                if key not in files:
                    files[key] = []
                files[key].append(value[1])
        
        # Make request
        try:
            response = self.session.post(
                f"{self.base_url}/files",
                files=filtered_data,
                timeout=60  # Longer timeout for large files
            )
            
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_data = e.response.json() if e.response.content else {}
            raise UploadAPIError(
                f"Upload failed: {error_data.get('detail', str(e))}",
                status_code=e.response.status_code,
                error_data=error_data
            )
    
    def _resize_image(
        self,
        image_path: Path,
        width: Optional[int] = None,
        height: Optional[int] = None,
        **kwargs
    ) -> Path:
        """Resize image to specified dimensions."""
        with Image.open(image_path) as img:
            # Calculate new dimensions
            if width and height:
                new_size = (width, height)
            elif width:
                ratio = width / img.width
                new_size = (width, int(img.height * ratio))
            elif height:
                ratio = height / img.height
                new_size = (int(img.width * ratio), height)
            else:
                return image_path  # No resizing needed
            
            # Resize
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Save to temporary file
            output_path = image_path.parent / f"resized_{image_path.stem}{image_path.suffix}"
            img.save(output_path, quality=kwargs.get('quality', 85))
            
            return output_path
    
    def _crop_image(
        self,
        image_path: Path,
        left: int,
        top: int,
        right: int,
        bottom: int,
        **kwargs
    ) -> Path:
        """Crop image to specified rectangle."""
        with Image.open(image_path) as img:
            # Validate crop coordinates
            width, height = img.size
            if left < 0 or top < 0 or right > width or bottom > height or left >= right or top >= bottom:
                raise ValueError(f"Invalid crop coordinates: ({left}, {top}, {right}, {bottom})")
            
            # Crop
            img = img.crop((left, top, right, bottom))
            
            # Save to temporary file
            output_path = image_path.parent / f"cropped_{image_path.stem}{image_path.suffix}"
            img.save(output_path, quality=kwargs.get('quality', 85))
            
            return output_path
    
    def _compress_image(
        self,
        image_path: Path,
        quality: int = 85,
        **kwargs
    ) -> Path:
        """Compress image with specified quality."""
        with Image.open(image_path) as img:
            # Determine format
            format_name = img.format or 'JPEG'
            
            # Save with compression
            output_path = image_path.parent / f"compressed_{image_path.stem}{image_path.suffix}"
            
            save_options = {'quality': quality}
            if format_name == 'JPEG':
                save_options['optimize'] = True
            elif format_name == 'WEBP':
                save_options['method'] = 6  # Best compression
            
            img.save(output_path, **save_options)
            
            return output_path
    
    def _convert_format(
        self,
        image_path: Path,
        format_name: str = 'jpeg',
        **kwargs
    ) -> Path:
        """Convert image to specified format."""
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if format_name.lower() in ['jpeg', 'jpg'] and img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB' and format_name.lower() == 'jpeg':
                img = img.convert('RGB')
            
            # Determine extension
            ext_map = {
                'jpeg': '.jpg',
                'jpg': '.jpg',
                'png': '.png',
                'webp': '.webp'
            }
            ext = ext_map.get(format_name.lower(), '.jpg')
            
            # Save in new format
            output_path = image_path.parent / f"converted_{image_path.stem}{ext}"
            
            save_options = {'quality': kwargs.get('quality', 85)}
            if format_name.lower() == 'jpeg':
                save_options['optimize'] = True
            
            img.save(output_path, format_name.upper(), **save_options)
            
            return output_path
    
    def _add_watermark(
        self,
        image_path: Path,
        watermark_path: Path,
        position: str = 'bottom-right',
        opacity: float = 0.5,
        **kwargs
    ) -> Path:
        """Add watermark to image."""
        with Image.open(image_path) as img:
            with Image.open(watermark_path) as watermark:
                # Resize watermark if needed
                max_watermark_size = (img.width // 4, img.height // 4)
                watermark.thumbnail(max_watermark_size, Image.Resampling.LANCZOS)
                
                # Convert watermark to RGBA if needed
                if watermark.mode != 'RGBA':
                    watermark = watermark.convert('RGBA')
                
                # Adjust opacity
                if opacity < 1.0:
                    alpha = watermark.split()[3]
                    alpha = alpha.point(lambda p: p * opacity)
                    watermark.putalpha(alpha)
                
                # Calculate position
                if position == 'bottom-right':
                    position_coords = (
                        img.width - watermark.width - 20,
                        img.height - watermark.height - 20
                    )
                elif position == 'bottom-left':
                    position_coords = (20, img.height - watermark.height - 20)
                elif position == 'top-right':
                    position_coords = (img.width - watermark.width - 20, 20)
                elif position == 'top-left':
                    position_coords = (20, 20)
                elif position == 'center':
                    position_coords = (
                        (img.width - watermark.width) // 2,
                        (img.height - watermark.height) // 2
                    )
                else:
                    position_coords = (20, 20)
                
                # Create watermark layer
                watermark_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
                watermark_layer.paste(watermark, position_coords)
                
                # Composite images
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                result = Image.alpha_composite(img, watermark_layer)
                
                # Convert back to original mode if needed
                if image_path.suffix.lower() in ['.jpg', '.jpeg']:
                    result = result.convert('RGB')
                
                # Save result
                output_path = image_path.parent / f"watermarked_{image_path.stem}{image_path.suffix}"
                result.save(output_path, quality=kwargs.get('quality', 85))
                
                return output_path
    
    def _create_variant(
        self,
        image_path: Path,
        variant_name: str,
        width: Optional[int],
        height: Optional[int],
        quality: int,
        format_name: str
    ) -> Path:
        """Create a single image variant."""
        # Open and process image
        with Image.open(image_path) as img:
            # Resize if dimensions specified
            if width or height:
                if width and height:
                    new_size = (width, height)
                elif width:
                    ratio = width / img.width
                    new_size = (width, int(img.height * ratio))
                else:  # height
                    ratio = height / img.height
                    new_size = (int(img.width * ratio), height)
                
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Determine output format
            output_format = format_name.upper()
            if output_format not in ['JPEG', 'PNG', 'WEBP']:
                output_format = 'JPEG'
            
            # Prepare output path
            ext_map = {
                'JPEG': '.jpg',
                'JPG': '.jpg',
                'PNG': '.png',
                'WEBP': '.webp'
            }
            ext = ext_map.get(output_format, '.jpg')
            output_path = image_path.parent / f"{variant_name}_{image_path.stem}{ext}"
            
            # Save options
            save_options = {'quality': quality}
            if output_format == 'JPEG':
                save_options['optimize'] = True
            
            # Save variant
            img.save(output_path, output_format, **save_options)
            
            return output_path

# Custom Exceptions
class ImageValidationError(Exception):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details

class ImageProcessingError(Exception):
    pass

class UploadError(Exception):
    pass

class UploadAPIError(Exception):
    def __init__(self, message, status_code=None, error_data=None):
        super().__init__(message)
        self.status_code = status_code
        self.error_data = error_data

# Usage Examples
def demonstrate_image_upload_workflows():
    """Demonstrate various image upload workflows."""
    
    uploader = ProductImageUploader(
        base_url="http://localhost:8000/api",
        token="your_admin_token_here"
    )
    
    product_id = "prod_789"
    image_dir = Path("/path/to/product/images")
    
    try:
        # Example 1: Single image upload
        print("Example 1: Uploading single image...")
        image_path = image_dir / "keyboard-main.jpg"
        
        if image_path.exists():
            result1 = uploader.upload_image(
                image_path,
                product_id,
                {
                    'is_primary': True,
                    'alt_text': 'Premium wireless keyboard',
                    'caption': 'Main product image',
                    'tags': ['lifestyle', 'keyboard'],
                    'metadata': {
                        'photographer': 'John Doe',
                        'shot_on': '2024-01-15'
                    }
                }
            )
            print(f"Uploaded: {result1['id']}")
        
        # Example 2: Multiple image upload
        print("\nExample 2: Uploading multiple images...")
        image_files = list(image_dir.glob("*.jpg"))[:3]  # First 3 JPG files
        
        if image_files:
            result2 = uploader.upload_multiple_images(
                image_files,
                product_id,
                {
                    'parallel': True,
                    'max_workers': 2
                }
            )
            print(f"Batch upload: {len(result2['successful'])} successful, {len(result2['failed'])} failed")
        
        # Example 3: Upload with processing pipeline
        print("\nExample 3: Upload with processing pipeline...")
        if image_path.exists():
            pipeline = [
                {
                    'type': 'resize',
                    'options': {'max_width': 1200, 'max_height': 1200}
                },
                {
                    'type': 'compress',
                    'options': {'quality': 80}
                },
                {
                    'type': 'convert',
                    'options': {'format': 'webp'}
                }
            ]
            
            result3 = uploader.upload_with_processing_pipeline(
                image_path,
                product_id,
                pipeline
            )
            print(f"Processed upload: {result3['id']}")
            print(f"Processing steps: {len(result3['processing_pipeline'])}")
        
        # Example 4: Upload with variants
        print("\nExample 4: Upload with variants...")
        if image_path.exists():
            variants = [
                {
                    'name': 'large',
                    'width': 1200,
                    'quality': 85,
                    'format': 'jpeg'
                },
                {
                    'name': 'medium',
                    'width': 800,
                    'quality': 85,
                    'format': 'jpeg'
                },
                {
                    'name': 'thumbnail',
                    'width': 300,
                    'quality': 75,
                    'format': 'jpeg'
                },
                {
                    'name': 'webp',
                    'width': 1200,
                    'quality': 85,
                    'format': 'webp'
                }
            ]
            
            result4 = uploader.upload_with_variants(
                image_path,
                product_id,
                variants
            )
            print(f"Main image: {result4['id']}")
            print(f"Variants created: {len(result4.get('variants', {}))}")
        
        # Example 5: Upload from directory
        print("\nExample 5: Upload from directory...")
        if image_dir.exists():
            result5 = uploader.upload_from_directory(
                image_dir,
                product_id,
                file_pattern="*.{jpg,jpeg,png,webp}",
                options={'parallel': True, 'max_workers': 3}
            )
            print(f"Directory upload: {result5['total']} total, {len(result5['successful'])} successful")
        
    except ImageValidationError as e:
        print(f"Image validation error: {e}")
        if e.details:
            print(f"Details: {e.details}")
    except UploadAPIError as e:
        print(f"Upload API error: {e}")
        print(f"Status: {e.status_code}")
        if e.error_data:
            print(f"Error details: {e.error_data}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    demonstrate_image_upload_workflows()
```

### Best Practices for Image Upload

#### 1. **Client-Side Validation**
```javascript
// Comprehensive client-side validation
function validateImageBeforeUpload(file) {
  const errors = [];
  
  // File type validation
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
  if (!allowedTypes.includes(file.type)) {
    errors.push(`File type ${file.type} not supported`);
  }
  
  // File size validation
  const maxSize = 5 * 1024 * 1024; // 5MB
  if (file.size > maxSize) {
    errors.push(`File size ${formatBytes(file.size)} exceeds maximum ${formatBytes(maxSize)}`);
  }
  
  // Dimension validation using HTMLImageElement
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      if (img.width < 300 || img.height < 300) {
        errors.push(`Image dimensions ${img.width}x${img.height} too small. Minimum: 300x300`);
      }
      if (img.width > 5000 || img.height > 5000) {
        errors.push(`Image dimensions ${img.width}x${img.height} too large. Maximum: 5000x5000`);
      }
      resolve({ valid: errors.length === 0, errors });
    };
    img.onerror = () => {
      errors.push('Failed to load image for validation');
      resolve({ valid: false, errors });
    };
    img.src = URL.createObjectURL(file);
  });
}
```

#### 2. **Progressive Enhancement**
```javascript
// Fallback for older browsers
function uploadWithFallback(file, productId, token) {
  // Try Fetch API first
  if (window.fetch && window.FormData) {
    return uploadWithFetch(file, productId, token);
  }
  
  // Fallback to XHR
  return uploadWithXHR(file, productId, token);
}

// Even older fallback
function uploadWithIframe(file, productId, token) {
  // Create hidden iframe for form submission
  const iframe = document.createElement('iframe');
  iframe.name = 'upload-iframe';
  iframe.style.display = 'none';
  document.body.appendChild(iframe);
  
  // Create form
  const form = document.createElement('form');
  form.target = 'upload-iframe';
  form.method = 'POST';
  form.action = '/api/files';
  form.enctype = 'multipart/form-data';
  
  // Add fields
  addFormField(form, 'productId', productId);
  addFormField(form, 'file', file);
  
  // Submit form
  form.submit();
  
  // Clean up
  setTimeout(() => document.body.removeChild(iframe), 5000);
}
```

#### 3. **Retry Logic**
```javascript
// Automatic retry with exponential backoff
async function uploadWithRetry(file, productId, token, maxRetries = 3) {
  let lastError;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await uploadImage(file, productId, token);
    } catch (error) {
      lastError = error;
      
      // Don't retry on validation errors
      if ([400, 413, 415, 422].includes(error.status)) {
        throw error;
      }
      
      if (attempt < maxRetries) {
        // Exponential backoff
        const delay = Math.pow(2, attempt - 1) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  throw lastError;
}
```

#### 4. **Offline Support**
```javascript
// Queue uploads when offline
class OfflineImageUploader {
  constructor() {
    this.queue = [];
    this.isOnline = navigator.onLine;
    
    // Listen for connectivity changes
    window.addEventListener('online', () => this.processQueue());
    window.addEventListener('offline', () => this.isOnline = false);
  }
  
  async upload(file, productId, token) {
    if (this.isOnline) {
      // Upload immediately
      return uploadImage(file, productId, token);
    } else {
      // Queue for later
      const queuedItem = {
        id: generateId(),
        file,
        productId,
        token,
        queuedAt: new Date()
      };
      
      this.queue.push(queuedItem);
      
      // Store in IndexedDB for persistence
      await this.storeInIndexedDB(queuedItem);
      
      return {
        queued: true,
        id: queuedItem.id,
        message: 'Image queued for upload when online'
      };
    }
  }
  
  async processQueue() {
    this.isOnline = true;
    
    while (this.queue.length > 0) {
      const item = this.queue.shift();
      
      try {
        await uploadImage(item.file, item.productId, item.token);
        await this.removeFromIndexedDB(item.id);
      } catch (error) {
        // Re-queue on failure
        this.queue.unshift(item);
        break;
      }
    }
  }
}
```

### Security Considerations

#### 1. **File Validation**
```javascript
// Server-side validation is crucial
async function validateUploadedImage(fileBuffer) {
  // Check magic numbers (file signatures)
  const signatures = {
    'jpeg': Buffer.from([0xFF, 0xD8, 0xFF]),
    'png': Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]),
    'webp': Buffer.from([0x52, 0x49, 0x46, 0x46])
  };
  
  // Check against known signatures
  let isValid = false;
  for (const [format, signature] of Object.entries(signatures)) {
    if (fileBuffer.slice(0, signature.length).equals(signature)) {
      isValid = true;
      break;
    }
  }
  
  if (!isValid) {
    throw new Error('Invalid image file signature');
  }
  
  // Additional checks
  // - File size limits
  // - Image dimensions
  // - No embedded scripts
  // - No EXIF data leakage
}
```

#### 2. **Secure File Storage**
```javascript
// Store files securely
const storageConfig = {
  // Use random filenames to prevent path traversal
  generateFilename: (originalName) => {
    const extension = originalName.split('.').pop();
    const random = crypto.randomBytes(16).toString('hex');
    return `${random}.${extension}`;
  },
  
  // Store in separate directories by product
  getStoragePath: (productId, filename) => {
    return `products/${productId}/${filename}`;
  },
  
  // Set proper permissions
  permissions: {
    read: 'public',
    write: 'authenticated'
  }
};
```

#### 3. **Content Security**
```javascript
// Prevent malicious content
async function sanitizeImage(imageBuffer) {
  // Remove EXIF data to prevent privacy leakage
  const sharp = require('sharp');
  
  return sharp(imageBuffer)
    .rotate() // Auto-rotate based on EXIF
    .withMetadata({}) // Strip all metadata
    .toBuffer();
}
```

#### 4. **Rate Limiting**
```javascript
// Prevent abuse with rate limiting
const uploadRateLimits = {
  perUser: {
    window: 3600000, // 1 hour
    max: 50          // 50 uploads per hour
  },
  perIP: {
    window: 3600000,
    max: 100         // 100 uploads per hour per IP
  },
  perProduct: {
    window: 86400000, // 24 hours
    max: 1000         // 1000 images per product per day
  }
};
```

### Performance Optimization

#### 1. **Client-Side Compression**
```javascript
// Compress images before upload
async function compressImageBeforeUpload(file, quality = 0.8) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0);
      
      canvas.toBlob(
        (blob) => resolve(new File([blob], file.name, { type: 'image/jpeg' })),
        'image/jpeg',
        quality
      );
    };
    img.src = URL.createObjectURL(file);
  });
}
```

#### 2. **Parallel Uploads**
```javascript
// Upload multiple files in parallel with concurrency control
async function uploadParallel(files, productId, token, concurrency = 3) {
  const results = [];
  const queue = [...files];
  
  // Worker function
  const worker = async () => {
    while (queue.length > 0) {
      const file = queue.shift();
      try {
        const result = await uploadImage(file, productId, token);
        results.push({ file: file.name, success: true, result });
      } catch (error) {
        results.push({ file: file.name, success: false, error });
      }
    }
  };
  
  // Start workers
  const workers = Array(concurrency).fill().map(() => worker());
  await Promise.all(workers);
  
  return results;
}
```

#### 3. **Lazy Loading**
```javascript
// Implement lazy loading for image galleries
class LazyImageLoader {
  constructor(container) {
    this.container = container;
    this.observer = new IntersectionObserver(
      (entries) => this.handleIntersection(entries),
      { rootMargin: '50px' }
    );
  }
  
  observeImages() {
    const images = this.container.querySelectorAll('img[data-src]');
    images.forEach(img => this.observer.observe(img));
  }
  
  handleIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
        this.observer.unobserve(img);
      }
    });
  }
}
```

---

## Related Endpoints
- [GET /files](../../images/list-images.md) - List product images
- [GET /files/{fileId}](../../images/get-image.md) - Get image metadata
- [DELETE /files/{fileId}](../../images/delete-image.md) - Delete product image
- [PATCH /files/{fileId}/primary](../../images/set-primary.md) - Set as primary image
- [Error Responses](../../errors.md) - Error handling details

## Notes
- Always validate files on both client and server side
- Implement proper error handling for failed uploads
- Consider implementing image CDN for better performance
- Use WebP format for better compression when supported
- Implement image moderation for user-generated content
- Consider adding image search capabilities

## SEO Considerations
- Use descriptive filenames (e.g., `premium-wireless-keyboard.jpg`)
- Include alt text for accessibility and SEO
- Implement structured data for product images
- Generate sitemap with image URLs
- Use lazy loading for better page performance

## Compliance and Regulations
- GDPR: Handle personal data in images (faces, license plates)
- ADA: Provide proper alt text for accessibility
- Copyright: Ensure proper licensing for product images
- Privacy: Strip EXIF data to prevent location leakage
- Industry-specific regulations may apply

## Performance Optimization
- Implement image CDN with edge caching
- Use responsive images with srcset
- Implement lazy loading for image galleries
- Optimize images during upload (resize, compress)
- Use modern formats (WebP, AVIF) when supported
- Implement image prefetching for critical images