# GET /files

**List Product Images** - Retrieve a list of product images with optional filtering

**Tags:** Product Images

**Authentication:** Optional (Public endpoint, admin features may require authentication)

---

## Description
Retrieve a paginated list of product images with optional filtering by product, tags, or other criteria. This endpoint returns image metadata including URLs, dimensions, and associated product information.

## Authentication
**Optional:** Bearer Token for administrative features or when accessing restricted images

## Request

### Query Parameters

| Parameter | Type | Required | Default | Description | Example |
|-----------|------|----------|---------|-------------|---------|
| `productId` | string | No | - | Filter by specific product | `?productId=prod_789` |
| `is_primary` | boolean | No | - | Filter by primary image status | `?is_primary=true` |
| `tags` | string[] | No | - | Filter by image tags (comma-separated) | `?tags=lifestyle,desk` |
| `mime_type` | string | No | - | Filter by MIME type | `?mime_type=image/jpeg` |
| `min_width` | integer | No | - | Minimum image width filter | `?min_width=800` |
| `min_height` | integer | No | - | Minimum image height filter | `?min_height=600` |
| `uploaded_after` | string | No | - | Filter images uploaded after date (ISO 8601) | `?uploaded_after=2024-01-01` |
| `uploaded_before` | string | No | - | Filter images uploaded before date (ISO 8601) | `?uploaded_before=2024-12-31` |
| `page` | integer | No | 1 | Page number (1-indexed) | `?page=2` |
| `page_size` | integer | No | 20 | Items per page (1-100) | `?page_size=50` |
| `sort_by` | string | No | `uploaded_at` | Sort field (`uploaded_at`, `filename`, `size`, `width`) | `?sort_by=filename` |
| `sort_order` | string | No | `desc` | Sort order (`asc`, `desc`) | `?sort_order=asc` |
| `search` | string | No | - | Search across filename, alt_text, caption | `?search=keyboard` |
| `include_variants` | boolean | No | `false` | Include image variants in response | `?include_variants=true` |

## Responses

### 200 OK - Images retrieved successfully
**Body:**
```json
{
  "items": [
    {
      "id": "img_12345678-1234-5678-1234-567812345678",
      "productId": "prod_789",
      "productName": "Premium Wireless Keyboard",
      "filename": "prod_789_abc123def456.jpg",
      "originalName": "keyboard-main.jpg",
      "mimeType": "image/jpeg",
      "size": 2457600,
      "dimensions": {
        "width": 1200,
        "height": 800,
        "aspectRatio": "3:2"
      },
      "variants": {
        "original": "https://cdn.example.com/products/prod_789/prod_789_abc123def456.jpg",
        "large": "https://cdn.example.com/products/prod_789/large/prod_789_abc123def456.jpg",
        "medium": "https://cdn.example.com/products/prod_789/medium/prod_789_abc123def456.jpg",
        "thumbnail": "https://cdn.example.com/products/prod_789/thumb/prod_789_abc123def456.jpg",
        "webp": "https://cdn.example.com/products/prod_789/webp/prod_789_abc123def456.webp"
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
      },
      "analytics": {
        "views": 1245,
        "downloads": 89,
        "lastAccessed": "2024-01-20T14:30:00Z"
      }
    }
  ],
  "total": 1,
  "page": 1,
  "pageSize": 20,
  "totalPages": 1,
  "hasNext": false,
  "hasPrev": false,
  "filters": {
    "applied": {
      "productId": "prod_789"
    },
    "available": {
      "tags": ["lifestyle", "desk", "keyboard", "product", "shot"],
      "mimeTypes": ["image/jpeg", "image/png", "image/webp"]
    }
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `items` | ProductImage[] | Array of product images |
| `total` | integer | Total number of images matching filters |
| `page` | integer | Current page number |
| `pageSize` | integer | Number of items per page |
| `totalPages` | integer | Total number of pages |
| `hasNext` | boolean | Whether there's a next page |
| `hasPrev` | boolean | Whether there's a previous page |
| `filters` | object | Information about applied and available filters |

**Product Image Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique image identifier (UUID) |
| `productId` | string | Associated product ID |
| `productName` | string | Name of associated product |
| `filename` | string | Server-generated filename |
| `originalName` | string | Original client filename |
| `mimeType` | string | MIME type of image |
| `size` | integer | File size in bytes |
| `dimensions` | object | Image width, height, and aspect ratio |
| `variants` | object | URLs to different image sizes/formats |
| `isPrimary` | boolean | Whether this is primary product image |
| `altText` | string | Alternative text for accessibility |
| `caption` | string | Image caption/description |
| `order` | integer | Display order |
| `tags` | string[] | Image tags for categorization |
| `metadata` | object | Additional metadata |
| `uploadedAt` | string | Upload timestamp |
| `uploadedBy` | string | User who uploaded the image |
| `processingStatus` | string | Status of image processing |
| `storage` | object | Storage location information |
| `analytics` | object | Usage analytics (views, downloads) |

### 400 Bad Request - Invalid parameters
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/bad-request",
  "title": "Bad Request",
  "status": 400,
  "detail": "Invalid page size. Must be between 1 and 100.",
  "instance": "/files",
  "errors": [
    {
      "field": "page_size",
      "message": "must be between 1 and 100"
    }
  ]
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

**Note:** Only returned when filtering by a specific productId that doesn't exist.

### 500 Internal Server Error
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/internal",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "Failed to retrieve images due to database error.",
  "instance": "/files"
}
```

## Examples

### Basic Request
```bash
# Get all images (first page)
curl -X GET "http://localhost:8000/api/files"
```

### Filter by Product
```bash
# Get all images for a specific product
curl -X GET "http://localhost:8000/api/files?productId=prod_789"

# Get primary image for a product
curl -X GET "http://localhost:8000/api/files?productId=prod_789&is_primary=true"
```

### Filter with Multiple Criteria
```bash
# Get JPEG images for a product uploaded after specific date
curl -X GET "http://localhost:8000/api/files?productId=prod_789&mime_type=image/jpeg&uploaded_after=2024-01-01&min_width=800"

# Get images with specific tags
curl -X GET "http://localhost:8000/api/files?tags=lifestyle,desk&min_width=1200&min_height=800"
```

### Pagination and Sorting
```bash
# Get second page, 50 items per page, sorted by upload date
curl -X GET "http://localhost:8000/api/files?page=2&page_size=50&sort_by=uploaded_at&sort_order=desc"

# Search for images with "keyboard" in filename or alt text
curl -X GET "http://localhost:8000/api/files?search=keyboard&page=1&page_size=20"
```

### Complete Example
```bash
curl -X GET "http://localhost:8000/api/files?productId=prod_789&is_primary=false&tags=lifestyle,desk&mime_type=image/jpeg&min_width=800&min_height=600&uploaded_after=2024-01-01&uploaded_before=2024-12-31&page=1&page_size=25&sort_by=filename&sort_order=asc&search=keyboard&include_variants=true"
```

### JavaScript (Fetch) with Advanced Filtering
```javascript
/**
 * Advanced product image listing service with caching and filtering
 */
class ProductImageLister {
  constructor(apiUrl = 'http://localhost:8000/api') {
    this.apiUrl = apiUrl;
    this.cache = new Map();
    this.defaultCacheTTL = 300000; // 5 minutes
  }
  
  /**
   * List product images with comprehensive filtering
   */
  async listImages(filters = {}, options = {}) {
    const {
      useCache = true,
      forceRefresh = false,
      timeout = 30000
    } = options;
    
    // Generate cache key from filters
    const cacheKey = this.generateCacheKey(filters);
    
    // Check cache first
    if (useCache && !forceRefresh) {
      const cached = this.cache.get(cacheKey);
      if (cached && Date.now() - cached.timestamp < cached.ttl) {
        console.log('Returning cached image list');
        return cached.data;
      }
    }
    
    try {
      // Build query parameters
      const params = this.buildQueryParams(filters);
      
      // Set up abort controller for timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);
      
      // Make request
      const response = await fetch(`${this.apiUrl}/files?${params}`, {
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
          ...(options.accessToken && {
            'Authorization': `Bearer ${options.accessToken}`
          })
        }
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Enhance data with additional calculations
      const enhancedData = this.enhanceImageList(data, filters);
      
      // Cache the result
      if (useCache) {
        this.cache.set(cacheKey, {
          data: enhancedData,
          timestamp: Date.now(),
          ttl: options.cacheTTL || this.defaultCacheTTL
        });
      }
      
      return enhancedData;
      
    } catch (error) {
      // Return cached data if available (even if stale)
      if (useCache) {
        const cached = this.cache.get(cacheKey);
        if (cached) {
          console.warn('Using stale cache due to error:', error.message);
          return cached.data;
        }
      }
      
      throw this.handleListError(error, filters);
    }
  }
  
  /**
   * Get images for a specific product with intelligent loading
   */
  async getProductImages(productId, options = {}) {
    const {
      includeVariants = false,
      onlyPrimary = false,
      sortBy = 'order',
      sortOrder = 'asc'
    } = options;
    
    const filters = {
      productId,
      include_variants: includeVariants,
      ...(onlyPrimary && { is_primary: true }),
      sort_by: sortBy,
      sort_order: sortOrder
    };
    
    return this.listImages(filters, options);
  }
  
  /**
   * Get primary image for a product
   */
  async getPrimaryImage(productId, options = {}) {
    const result = await this.getProductImages(productId, {
      ...options,
      onlyPrimary: true,
      page_size: 1
    });
    
    return result.items[0] || null;
  }
  
  /**
   * Search images across all products
   */
  async searchImages(query, options = {}) {
    const {
      searchIn = 'all', // 'all', 'filename', 'altText', 'caption'
      ...otherOptions
    } = options;
    
    const filters = {
      search: query,
      ...otherOptions
    };
    
    return this.listImages(filters, options);
  }
  
  /**
   * Get images by tag
   */
  async getImagesByTag(tag, options = {}) {
    const filters = {
      tags: Array.isArray(tag) ? tag : [tag],
      ...options
    };
    
    return this.listImages(filters, options);
  }
  
  /**
   * Get recently uploaded images
   */
  async getRecentImages(days = 7, limit = 20, options = {}) {
    const uploadedAfter = new Date();
    uploadedAfter.setDate(uploadedAfter.getDate() - days);
    
    const filters = {
      uploaded_after: uploadedAfter.toISOString().split('T')[0],
      page_size: limit,
      sort_by: 'uploaded_at',
      sort_order: 'desc',
      ...options
    };
    
    return this.listImages(filters, options);
  }
  
  /**
   * Get image statistics
   */
  async getImageStats(filters = {}, options = {}) {
    // First, get images with minimal fields
    const imageList = await this.listImages({
      ...filters,
      page_size: 1 // We only need total count
    }, options);
    
    // If we have access to more data, we could compute additional stats
    const stats = {
      total: imageList.total,
      totalPages: imageList.totalPages,
      filtersApplied: Object.keys(filters).length
    };
    
    // Add filter-specific stats if available
    if (filters.productId) {
      // Could fetch product details here
      stats.productId = filters.productId;
    }
    
    return stats;
  }
  
  /**
   * Preload images for better UX
   */
  async preloadImages(imageUrls, options = {}) {
    const {
      priority = 'low',
      onProgress = null,
      concurrency = 3
    } = options;
    
    const results = {
      loaded: 0,
      failed: 0,
      total: imageUrls.length
    };
    
    // Process in batches for concurrency control
    for (let i = 0; i < imageUrls.length; i += concurrency) {
      const batch = imageUrls.slice(i, i + concurrency);
      const batchPromises = batch.map(url =>
        this.preloadSingleImage(url, priority)
          .then(() => ({ success: true, url }))
          .catch(error => ({ success: false, url, error }))
      );
      
      const batchResults = await Promise.all(batchPromises);
      
      batchResults.forEach(result => {
        if (result.success) {
          results.loaded++;
        } else {
          results.failed++;
        }
      });
      
      // Progress callback
      if (onProgress) {
        const processed = results.loaded + results.failed;
        onProgress(processed, imageUrls.length);
      }
    }
    
    return results;
  }
  
  /**
   * Generate responsive image srcset
   */
  generateSrcset(imageData) {
    if (!imageData.variants) {
      return imageData.variants?.original || '';
    }
    
    const srcset = [];
    
    if (imageData.variants.large) {
      srcset.push(`${imageData.variants.large} 1200w`);
    }
    
    if (imageData.variants.medium) {
      srcset.push(`${imageData.variants.medium} 800w`);
    }
    
    if (imageData.variants.thumbnail) {
      srcset.push(`${imageData.variants.thumbnail} 300w`);
    }
    
    return srcset.join(', ');
  }
  
  /**
   * Get image suitable for specific use case
   */
  getImageForUseCase(imageData, useCase) {
    const variants = imageData.variants || {};
    
    switch (useCase) {
      case 'hero':
        return variants.large || variants.original;
      case 'gallery':
        return variants.medium || variants.original;
      case 'thumbnail':
        return variants.thumbnail || variants.original;
      case 'product-card':
        return variants.thumbnail || variants.original;
      case 'zoom':
        return variants.original;
      default:
        return variants.original;
    }
  }
  
  /**
   * Build query parameters from filters
   */
  buildQueryParams(filters) {
    const params = new URLSearchParams();
    
    // Pagination
    if (filters.page) params.set('page', filters.page.toString());
    if (filters.page_size) params.set('page_size', filters.page_size.toString());
    if (filters.pageSize) params.set('page_size', filters.pageSize.toString());
    
    // Sorting
    if (filters.sort_by) params.set('sort_by', filters.sort_by);
    if (filters.sort_order) params.set('sort_order', filters.sort_order);
    
    // Filters
    if (filters.productId) params.set('productId', filters.productId);
    if (filters.is_primary !== undefined) params.set('is_primary', filters.is_primary.toString());
    
    if (filters.tags) {
      const tags = Array.isArray(filters.tags) ? filters.tags : [filters.tags];
      tags.forEach(tag => params.append('tags', tag));
    }
    
    if (filters.mime_type) params.set('mime_type', filters.mime_type);
    if (filters.min_width) params.set('min_width', filters.min_width.toString());
    if (filters.min_height) params.set('min_height', filters.min_height.toString());
    
    if (filters.uploaded_after) {
      const date = new Date(filters.uploaded_after);
      params.set('uploaded_after', date.toISOString().split('T')[0]);
    }
    
    if (filters.uploaded_before) {
      const date = new Date(filters.uploaded_before);
      params.set('uploaded_before', date.toISOString().split('T')[0]);
    }
    
    if (filters.search) params.set('search', filters.search);
    if (filters.include_variants) params.set('include_variants', filters.include_variants.toString());
    
    return params.toString();
  }
  
  /**
   * Generate cache key from filters
   */
  generateCacheKey(filters) {
    // Create a stable string representation of filters
    const normalizedFilters = { ...filters };
    
    // Sort tags array for consistent keys
    if (normalizedFilters.tags && Array.isArray(normalizedFilters.tags)) {
      normalizedFilters.tags = [...normalizedFilters.tags].sort();
    }
    
    // Convert to string
    const filterString = JSON.stringify(normalizedFilters);
    
    // Create hash
    return `images:${this.hashString(filterString)}`;
  }
  
  /**
   * Enhance image list with additional data
   */
  enhanceImageList(data, filters) {
    const enhanced = { ...data };
    
    // Calculate image statistics
    if (enhanced.items && enhanced.items.length > 0) {
      enhanced.stats = this.calculateImageStats(enhanced.items);
      
      // Add srcset for each image
      enhanced.items = enhanced.items.map(image => ({
        ...image,
        srcset: this.generateSrcset(image),
        optimizedUrl: this.getImageForUseCase(image, 'gallery')
      }));
    }
    
    // Add filter information
    enhanced.request = {
      filters,
      timestamp: new Date().toISOString()
    };
    
    return enhanced;
  }
  
  /**
   * Calculate statistics for image list
   */
  calculateImageStats(images) {
    if (!images || images.length === 0) {
      return null;
    }
    
    let totalSize = 0;
    let maxWidth = 0;
    let maxHeight = 0;
    const mimeTypes = new Set();
    const tags = new Set();
    
    images.forEach(image => {
      totalSize += image.size || 0;
      
      if (image.dimensions) {
        maxWidth = Math.max(maxWidth, image.dimensions.width || 0);
        maxHeight = Math.max(maxHeight, image.dimensions.height || 0);
      }
      
      if (image.mimeType) {
        mimeTypes.add(image.mimeType);
      }
      
      if (image.tags && Array.isArray(image.tags)) {
        image.tags.forEach(tag => tags.add(tag));
      }
    });
    
    return {
      count: images.length,
      totalSize,
      formattedTotalSize: this.formatBytes(totalSize),
      averageSize: Math.round(totalSize / images.length),
      maxDimensions: { width: maxWidth, height: maxHeight },
      mimeTypes: Array.from(mimeTypes),
      uniqueTags: Array.from(tags).slice(0, 10), // Top 10 tags
      primaryImages: images.filter(img => img.isPrimary).length
    };
  }
  
  /**
   * Preload single image
   */
  preloadSingleImage(url, priority = 'low') {
    return new Promise((resolve, reject) => {
      const img = new Image();
      
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error(`Failed to load image: ${url}`));
      
      // Set loading priority
      if (priority === 'high' && 'fetchPriority' in img) {
        img.fetchPriority = 'high';
      }
      
      img.src = url;
    });
  }
  
  /**
   * Handle list errors
   */
  handleListError(error, filters) {
    if (error.name === 'AbortError') {
      return new ImageListError(
        `Image list request timed out after 30 seconds`,
        'TIMEOUT',
        { filters }
      );
    }
    
    if (error.message.includes('404')) {
      return new ImageListError(
        `Product not found: ${filters.productId}`,
        'PRODUCT_NOT_FOUND',
        { filters }
      );
    }
    
    return new ImageListError(
      `Failed to list images: ${error.message}`,
      'NETWORK_ERROR',
      { filters, originalError: error }
    );
  }
  
  /**
   * Helper methods
   */
  hashString(str) {
    // Simple hash function for cache keys
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return hash.toString(36);
  }
  
  formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }
  
  clearCache(pattern = null) {
    if (!pattern) {
      this.cache.clear();
      return;
    }
    
    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    }
  }
}

// Custom Error Classes
class ImageListError extends Error {
  constructor(message, code = 'UNKNOWN', details = null) {
    super(message);
    this.name = 'ImageListError';
    this.code = code;
    this.details = details;
  }
}

// Usage Examples
async function demonstrateImageListing() {
  const lister = new ProductImageLister();
  
  try {
    // Example 1: Get all images for a product
    console.log('Example 1: Getting product images...');
    const productImages = await lister.getProductImages('prod_789', {
      includeVariants: true,
      sortBy: 'order',
      sortOrder: 'asc'
    });
    
    console.log(`Found ${productImages.total} images for product`);
    
    if (productImages.items.length > 0) {
      const primaryImage = productImages.items.find(img => img.isPrimary);
      if (primaryImage) {
        console.log(`Primary image: ${primaryImage.filename}`);
      }
    }
    
    // Example 2: Search images
    console.log('\nExample 2: Searching images...');
    const searchResults = await lister.searchImages('keyboard', {
      page_size: 10,
      mime_type: 'image/jpeg'
    });
    
    console.log(`Search found ${searchResults.total} images`);
    
    // Example 3: Get recent images
    console.log('\nExample 3: Getting recent images...');
    const recentImages = await lister.getRecentImages(7, 5);
    
    console.log(`Recent images (last 7 days):`);
    recentImages.items.forEach((img, index) => {
      console.log(`${index + 1}. ${img.filename} (${new Date(img.uploadedAt).toLocaleDateString()})`);
    });
    
    // Example 4: Get image statistics
    console.log('\nExample 4: Getting image statistics...');
    const stats = await lister.getImageStats({ productId: 'prod_789' });
    
    console.log('Image statistics:', stats);
    
    // Example 5: Preload images for better UX
    console.log('\nExample 5: Preloading images...');
    const imageUrls = productImages.items
      .slice(0, 3)
      .map(img => lister.getImageForUseCase(img, 'thumbnail'));
    
    const preloadResults = await lister.preloadImages(imageUrls, {
      priority: 'low',
      onProgress: (loaded, total) => {
        console.log(`Preload progress: ${loaded}/${total}`);
      }
    });
    
    console.log(`Preloaded ${preloadResults.loaded}/${preloadResults.total} images`);
    
  } catch (error) {
    console.error('Image listing error:', error);
    
    if (error instanceof ImageListError) {
      console.error(`Error code: ${error.code}`);
      if (error.details) {
        console.error('Details:', error.details);
      }
    }
  }
}
```

### React Component for Image Gallery
```jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import ImageGallery from './ImageGallery';
import ImageFilters from './ImageFilters';
import Pagination from './Pagination';

function ProductImageBrowser({ productId, onImageSelect }) {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    productId: productId || '',
    page: 1,
    pageSize: 20,
    sortBy: 'order',
    sortOrder: 'asc'
  });
  const [pagination, setPagination] = useState({
    total: 0,
    totalPages: 0,
    hasNext: false,
    hasPrev: false
  });
  const [selectedImage, setSelectedImage] = useState(null);
  const [viewMode, setViewMode] = useState('grid'); // 'grid', 'list', 'detail'
  
  // Fetch images when filters change
  useEffect(() => {
    fetchImages();
  }, [filters.page, filters.pageSize, filters.sortBy, filters.sortOrder, filters.productId]);
  
  const fetchImages = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const lister = new ProductImageLister();
      const result = await lister.listImages(filters);
      
      setImages(result.items);
      setPagination({
        total: result.total,
        totalPages: result.totalPages,
        hasNext: result.hasNext,
        hasPrev: result.hasPrev
      });
      
    } catch (err) {
      setError(err.message);
      console.error('Failed to fetch images:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleFilterChange = useCallback((newFilters) => {
    setFilters(prev => ({
      ...prev,
      ...newFilters,
      page: 1 // Reset to first page when filters change
    }));
  }, []);
  
  const handlePageChange = useCallback((page) => {
    setFilters(prev => ({ ...prev, page }));
  }, []);
  
  const handleImageSelect = useCallback((image) => {
    setSelectedImage(image);
    if (onImageSelect) {
      onImageSelect(image);
    }
  }, [onImageSelect]);
  
  const handleRefresh = useCallback(() => {
    fetchImages();
  }, []);
  
  const handleClearFilters = useCallback(() => {
    setFilters({
      productId: productId || '',
      page: 1,
      pageSize: 20,
      sortBy: 'order',
      sortOrder: 'asc'
    });
  }, [productId]);
  
  // Get primary image
  const primaryImage = useMemo(() => {
    return images.find(img => img.isPrimary);
  }, [images]);
  
  // Group images by tag for filtering
  const availableTags = useMemo(() => {
    const tags = new Set();
    images.forEach(img => {
      if (img.tags && Array.isArray(img.tags)) {
        img.tags.forEach(tag => tags.add(tag));
      }
    });
    return Array.from(tags).sort();
  }, [images]);
  
  // Calculate statistics
  const stats = useMemo(() => {
    if (images.length === 0) return null;
    
    let totalSize = 0;
    const mimeTypes = new Set();
    
    images.forEach(img => {
      totalSize += img.size || 0;
      if (img.mimeType) mimeTypes.add(img.mimeType);
    });
    
    return {
      count: images.length,
      totalSize,
      formattedTotalSize: formatBytes(totalSize),
      mimeTypes: Array.from(mimeTypes),
      primaryCount: images.filter(img => img.isPrimary).length
    };
  }, [images]);
  
  if (loading && images.length === 0) {
    return (
      <div className="image-browser-loading">
        <div className="spinner"></div>
        <p>Loading images...</p>
      </div>
    );
  }
  
  return (
    <div className="product-image-browser">
      {/* Header */}
      <div className="browser-header">
        <div className="header-left">
          <h2>Product Images</h2>
          {stats && (
            <div className="stats-badge">
              <span>{stats.count} images</span>
              <span>{stats.formattedTotalSize}</span>
              {stats.primaryCount > 0 && (
                <span>{stats.primaryCount} primary</span>
              )}
            </div>
          )}
        </div>
        
        <div className="header-right">
          <div className="view-mode-selector">
            <button
              className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
              onClick={() => setViewMode('grid')}
              title="Grid View"
            >
              <svg width="20" height="20" viewBox="0 0 24 24">
                <path d="M3 3H10V10H3V3Z" fill="currentColor"/>
                <path d="M3 14H10V21H3V14Z" fill="currentColor"/>
                <path d="M14 3H21V10H14V3Z" fill="currentColor"/>
                <path d="M14 14H21V21H14V14Z" fill="currentColor"/>
              </svg>
            </button>
            <button
              className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
              onClick={() => setViewMode('list')}
              title="List View"
            >
              <svg width="20" height="20" viewBox="0 0 24 24">
                <path d="M3 4H21V6H3V4ZM3 11H21V13H3V11ZM3 18H21V20H3V18Z" fill="currentColor"/>
              </svg>
            </button>
          </div>
          
          <button
            className="btn-refresh"
            onClick={handleRefresh}
            disabled={loading}
            title="Refresh Images"
          >
            <svg width="16" height="16" viewBox="0 0 24 24">
              <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4C7.58 4 4 7.58 4 12C4 16.42 7.58 20 12 20C15.73 20 18.84 17.45 19.73 14H17.65C16.83 16.33 14.61 18 12 18C8.69 18 6 15.31 6 12C6 8.69 8.69 6 12 6C13.66 6 15.14 6.69 16.22 7.78L13 11H20V4L17.65 6.35Z" fill="currentColor"/>
            </svg>
          </button>
        </div>
      </div>
      
      {/* Error Display */}
      {error && (
        <div className="browser-error">
          <div className="alert alert-error">
            <strong>Error:</strong> {error}
            <button onClick={handleRefresh}>Retry</button>
          </div>
        </div>
      )}
      
      {/* Filters */}
      <ImageFilters
        filters={filters}
        availableTags={availableTags}
        onFilterChange={handleFilterChange}
        onClearFilters={handleClearFilters}
        loading={loading}
      />
      
      {/* Primary Image Highlight */}
      {primaryImage && (
        <div className="primary-image-highlight">
          <div className="highlight-header">
            <h3>Primary Image</h3>
            <span className="badge-primary">Primary</span>
          </div>
          <div className="highlight-content">
            <img
              src={primaryImage.variants?.thumbnail || primaryImage.variants?.original}
              alt={primaryImage.altText || 'Primary product image'}
              className="highlight-thumbnail"
              onClick={() => handleImageSelect(primaryImage)}
            />
            <div className="highlight-details">
              <h4>{primaryImage.filename}</h4>
              <p>{primaryImage.caption || 'No caption'}</p>
              <div className="image-meta">
                <span>{primaryImage.dimensions?.width}×{primaryImage.dimensions?.height}</span>
                <span>{formatBytes(primaryImage.size)}</span>
                <span>{new Date(primaryImage.uploadedAt).toLocaleDateString()}</span>
              </div>
              {primaryImage.tags && primaryImage.tags.length > 0 && (
                <div className="image-tags">
                  {primaryImage.tags.map(tag => (
                    <span key={tag} className="tag">{tag}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* Image Gallery */}
      <div className="image-gallery-container">
        {images.length === 0 ? (
          <div className="no-images">
            <div className="no-images-icon">
              <svg width="64" height="64" viewBox="0 0 24 24">
                <path d="M21 19V5C21 3.9 20.1 3 19 3H5C3.9 3 3 3.9 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19ZM8.5 13.5L11 16.51L14.5 12L19 18H5L8.5 13.5Z" fill="currentColor"/>
              </svg>
            </div>
            <h3>No Images Found</h3>
            <p>Try adjusting your filters or upload new images.</p>
            <button onClick={handleClearFilters}>Clear All Filters</button>
          </div>
        ) : (
          <>
            <ImageGallery
              images={images}
              viewMode={viewMode}
              onImageSelect={handleImageSelect}
              selectedImageId={selectedImage?.id}
            />
            
            {/* Pagination */}
            {pagination.totalPages > 1 && (
              <Pagination
                currentPage={filters.page}
                totalPages={pagination.totalPages}
                hasNext={pagination.hasNext}
                hasPrev={pagination.hasPrev}
                onPageChange={handlePageChange}
              />
            )}
          </>
        )}
      </div>
      
      {/* Selected Image Detail Modal */}
      {selectedImage && (
        <ImageDetailModal
          image={selectedImage}
          onClose={() => setSelectedImage(null)}
          onSelect={handleImageSelect}
        />
      )}
    </div>
  );
}

// Helper function
function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

export default ProductImageBrowser;
```

### Python with Advanced Image Querying
```python
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import cachetools

class SortField(Enum):
    """Fields available for sorting."""
    UPLOADED_AT = "uploaded_at"
    FILENAME = "filename"
    SIZE = "size"
    WIDTH = "width"
    HEIGHT = "height"
    ORDER = "order"

class SortOrder(Enum):
    """Sort order options."""
    ASC = "asc"
    DESC = "desc"

@dataclass
class ImageFilter:
    """Image filter configuration."""
    product_id: Optional[str] = None
    is_primary: Optional[bool] = None
    tags: Optional[List[str]] = None
    mime_type: Optional[str] = None
    min_width: Optional[int] = None
    min_height: Optional[int] = None
    uploaded_after: Optional[datetime] = None
    uploaded_before: Optional[datetime] = None
    search: Optional[str] = None
    include_variants: bool = False
    
    def to_query_params(self) -> Dict[str, str]:
        """Convert filter to query parameters."""
        params = {}
        
        if self.product_id:
            params['productId'] = self.product_id
        
        if self.is_primary is not None:
            params['is_primary'] = str(self.is_primary).lower()
        
        if self.tags:
            params['tags'] = ','.join(self.tags)
        
        if self.mime_type:
            params['mime_type'] = self.mime_type
        
        if self.min_width:
            params['min_width'] = str(self.min_width)
        
        if self.min_height:
            params['min_height'] = str(self.min_height)
        
        if self.uploaded_after:
            params['uploaded_after'] = self.uploaded_after.date().isoformat()
        
        if self.uploaded_before:
            params['uploaded_before'] = self.uploaded_before.date().isoformat()
        
        if self.search:
            params['search'] = self.search
        
        if self.include_variants:
            params['include_variants'] = 'true'
        
        return params

@dataclass
class Pagination:
    """Pagination configuration."""
    page: int = 1
    page_size: int = 20
    sort_by: SortField = SortField.UPLOADED_AT
    sort_order: SortOrder = SortOrder.DESC
    
    def to_query_params(self) -> Dict[str, str]:
        """Convert pagination to query parameters."""
        return {
            'page': str(self.page),
            'page_size': str(self.page_size),
            'sort_by': self.sort_by.value,
            'sort_order': self.sort_order.value
        }

@dataclass
class ImageListResult:
    """Result of image listing operation."""
    items: List[Dict]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    filters: Dict[str, Any]
    stats: Optional[Dict] = None
    
    @classmethod
    def from_api_response(cls, response_data: Dict, filters: Dict) -> 'ImageListResult':
        """Create result from API response."""
        return cls(
            items=response_data.get('items', []),
            total=response_data.get('total', 0),
            page=response_data.get('page', 1),
            page_size=response_data.get('pageSize', 20),
            total_pages=response_data.get('totalPages', 1),
            has_next=response_data.get('hasNext', False),
            has_prev=response_data.get('hasPrev', False),
            filters=filters
        )

class ProductImageQuery:
    """Advanced product image querying with caching and filtering."""
    
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        if token:
            self.session.headers.update({
                'Authorization': f'Bearer {token}'
            })
        
        self.session.headers.update({
            'Accept': 'application/json'
        })
        
        # Cache configuration
        self.cache = cachetools.TTLCache(maxsize=100, ttl=300)  # 5 minutes
        self.cache_enabled = True
    
    def list_images(
        self,
        filter_config: Optional[ImageFilter] = None,
        pagination: Optional[Pagination] = None,
        options: Optional[Dict] = None
    ) -> ImageListResult:
        """
        List images with filtering and pagination.
        
        Args:
            filter_config: Image filter configuration
            pagination: Pagination configuration
            options: Additional options
            
        Returns:
            ImageListResult object
        """
        options = options or {}
        filter_config = filter_config or ImageFilter()
        pagination = pagination or Pagination()
        
        # Generate cache key
        cache_key = self._generate_cache_key(filter_config, pagination)
        
        # Check cache
        if self.cache_enabled and not options.get('force_refresh', False):
            cached_result = self.cache.get(cache_key)
            if cached_result:
                print(f"Cache hit for key: {cache_key[:50]}...")
                return cached_result
        
        try:
            # Build query parameters
            params = {}
            params.update(filter_config.to_query_params())
            params.update(pagination.to_query_params())
            
            # Add timeout to options
            timeout = options.get('timeout', 30)
            
            # Make request
            response = self.session.get(
                f"{self.base_url}/files",
                params=params,
                timeout=timeout
            )
            
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            # Create result object
            result = ImageListResult.from_api_response(
                response_data,
                {
                    'filter': asdict(filter_config),
                    'pagination': asdict(pagination)
                }
            )
            
            # Calculate statistics
            result.stats = self._calculate_image_stats(result.items)
            
            # Cache the result
            if self.cache_enabled:
                self.cache[cache_key] = result
            
            return result
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # Product not found - return empty result
                return ImageListResult(
                    items=[],
                    total=0,
                    page=pagination.page,
                    page_size=pagination.page_size,
                    total_pages=0,
                    has_next=False,
                    has_prev=False,
                    filters={
                        'filter': asdict(filter_config),
                        'pagination': asdict(pagination)
                    }
                )
            raise ImageQueryError(f"Failed to list images: {e}")
    
    def get_product_images(
        self,
        product_id: str,
        include_primary: bool = True,
        include_variants: bool = False,
        options: Optional[Dict] = None
    ) -> ImageListResult:
        """
        Get all images for a specific product.
        
        Args:
            product_id: Product identifier
            include_primary: Whether to include primary images
            include_variants: Whether to include image variants
            options: Additional options
            
        Returns:
            ImageListResult object
        """
        filter_config = ImageFilter(
            product_id=product_id,
            include_variants=include_variants
        )
        
        if not include_primary:
            filter_config.is_primary = False
        
        return self.list_images(filter_config, Pagination(page_size=100), options)
    
    def get_primary_image(self, product_id: str, options: Optional[Dict] = None) -> Optional[Dict]:
        """
        Get primary image for a product.
        
        Args:
            product_id: Product identifier
            options: Additional options
            
        Returns:
            Primary image data or None
        """
        filter_config = ImageFilter(
            product_id=product_id,
            is_primary=True
        )
        
        pagination = Pagination(page_size=1, sort_by=SortField.UPLOADED_AT, sort_order=SortOrder.DESC)
        
        result = self.list_images(filter_config, pagination, options)
        
        return result.items[0] if result.items else None
    
    def search_images(
        self,
        search_term: str,
        search_fields: Optional[List[str]] = None,
        options: Optional[Dict] = None
    ) -> ImageListResult:
        """
        Search images by text.
        
        Args:
            search_term: Text to search for
            search_fields: Fields to search in (defaults to all)
            options: Additional options
            
        Returns:
            ImageListResult object
        """
        filter_config = ImageFilter(search=search_term)
        
        # Adjust pagination for search results
        pagination = Pagination(
            page_size=options.get('page_size', 20) if options else 20,
            sort_by=SortField.UPLOADED_AT,
            sort_order=SortOrder.DESC
        )
        
        return self.list_images(filter_config, pagination, options)
    
    def get_images_by_tag(
        self,
        tag: str,
        options: Optional[Dict] = None
    ) -> ImageListResult:
        """
        Get images by tag.
        
        Args:
            tag: Tag to filter by
            options: Additional options
            
        Returns:
            ImageListResult object
        """
        filter_config = ImageFilter(tags=[tag])
        
        pagination = Pagination(
            page_size=options.get('page_size', 50) if options else 50,
            sort_by=SortField.UPLOADED_AT,
            sort_order=SortOrder.DESC
        )
        
        return self.list_images(filter_config, pagination, options)
    
    def get_recent_images(
        self,
        days: int = 7,
        limit: int = 20,
        options: Optional[Dict] = None
    ) -> ImageListResult:
        """
        Get recently uploaded images.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of images
            options: Additional options
            
        Returns:
            ImageListResult object
        """
        uploaded_after = datetime.now() - timedelta(days=days)
        
        filter_config = ImageFilter(uploaded_after=uploaded_after)
        
        pagination = Pagination(
            page=1,
            page_size=limit,
            sort_by=SortField.UPLOADED_AT,
            sort_order=SortOrder.DESC
        )
        
        return self.list_images(filter_config, pagination, options)
    
    def get_image_statistics(
        self,
        filter_config: Optional[ImageFilter] = None
    ) -> Dict[str, Any]:
        """
        Get statistics for images matching filters.
        
        Args:
            filter_config: Image filter configuration
            
        Returns:
            Statistics dictionary
        """
        # Get all images (with large page size)
        pagination = Pagination(page_size=1000, sort_by=SortField.UPLOADED_AT)
        result = self.list_images(filter_config, pagination, {'force_refresh': True})
        
        return self._calculate_image_stats(result.items)
    
    def get_available_filters(
        self,
        filter_config: Optional[ImageFilter] = None
    ) -> Dict[str, List[str]]:
        """
        Get available filter values based on current data.
        
        Args:
            filter_config: Base filter configuration
            
        Returns:
            Dictionary of available filter values
        """
        # Get a sample of images to analyze
        pagination = Pagination(page_size=100, sort_by=SortField.UPLOADED_AT)
        result = self.list_images(filter_config, pagination)
        
        # Extract unique values for filtering
        available_filters = {
            'tags': set(),
            'mime_types': set(),
            'products': set()
        }
        
        for image in result.items:
            if image.get('tags'):
                for tag in image['tags']:
                    available_filters['tags'].add(tag)
            
            if image.get('mimeType'):
                available_filters['mime_types'].add(image['mimeType'])
            
            if image.get('productId'):
                available_filters['products'].add(image['productId'])
        
        # Convert sets to sorted lists
        return {
            'tags': sorted(available_filters['tags']),
            'mime_types': sorted(available_filters['mime_types']),
            'products': sorted(available_filters['products'])
        }
    
    def stream_images(
        self,
        filter_config: Optional[ImageFilter] = None,
        batch_size: int = 50,
        on_batch: Optional[callable] = None
    ) -> List[Dict]:
        """
        Stream all images matching filters in batches.
        
        Args:
            filter_config: Image filter configuration
            batch_size: Number of images per batch
            on_batch: Callback function for each batch
            
        Returns:
            List of all images
        """
        all_images = []
        page = 1
        
        while True:
            pagination = Pagination(page=page, page_size=batch_size)
            result = self.list_images(filter_config, pagination)
            
            if not result.items:
                break
            
            all_images.extend(result.items)
            
            # Call batch callback if provided
            if on_batch:
                on_batch(result.items, page, result.total_pages)
            
            # Check if we've retrieved all images
            if page >= result.total_pages:
                break
            
            page += 1
        
        return all_images
    
    def export_image_list(
        self,
        filter_config: Optional[ImageFilter] = None,
        format: str = 'json',
        include_fields: Optional[List[str]] = None
    ) -> str:
        """
        Export image list in specified format.
        
        Args:
            filter_config: Image filter configuration
            format: Export format ('json', 'csv')
            include_fields: Fields to include in export
            
        Returns:
            Exported data as string
        """
        # Get all images
        all_images = self.stream_images(filter_config)
        
        # Default fields to include
        if not include_fields:
            include_fields = [
                'id', 'filename', 'originalName', 'productId',
                'dimensions.width', 'dimensions.height', 'size',
                'mimeType', 'uploadedAt', 'isPrimary'
            ]
        
        # Export based on format
        if format.lower() == 'json':
            return json.dumps(all_images, indent=2, default=str)
        
        elif format.lower() == 'csv':
            import csv
            import io
            
            # Flatten nested fields
            flattened_images = []
            for image in all_images:
                flat_image = {}
                for field in include_fields:
                    # Handle nested fields
                    if '.' in field:
                        parts = field.split('.')
                        value = image
                        for part in parts:
                            if isinstance(value, dict):
                                value = value.get(part)
                            else:
                                value = None
                                break
                        flat_image[field] = value
                    else:
                        flat_image[field] = image.get(field)
                flattened_images.append(flat_image)
            
            # Generate CSV
            output = io.StringIO()
            if flattened_images:
                writer = csv.DictWriter(output, fieldnames=include_fields)
                writer.writeheader()
                writer.writerows(flattened_images)
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    # Private helper methods
    def _generate_cache_key(
        self,
        filter_config: ImageFilter,
        pagination: Pagination
    ) -> str:
        """Generate cache key from filter and pagination."""
        # Create dictionary representation
        cache_data = {
            'filter': asdict(filter_config),
            'pagination': asdict(pagination)
        }
        
        # Convert to stable string
        cache_str = json.dumps(cache_data, sort_keys=True, default=str)
        
        # Generate hash
        return f"images:{hashlib.md5(cache_str.encode()).hexdigest()}"
    
    def _calculate_image_stats(self, images: List[Dict]) -> Dict[str, Any]:
        """Calculate statistics for image list."""
        if not images:
            return {
                'count': 0,
                'total_size': 0,
                'average_size': 0,
                'formats': {},
                'dimensions': {},
                'primary_count': 0
            }
        
        total_size = 0
        formats = {}
        widths = []
        heights = []
        primary_count = 0
        
        for image in images:
            # Size
            size = image.get('size', 0)
            total_size += size
            
            # Format
            mime_type = image.get('mimeType', 'unknown')
            formats[mime_type] = formats.get(mime_type, 0) + 1
            
            # Dimensions
            dimensions = image.get('dimensions', {})
            if dimensions:
                widths.append(dimensions.get('width', 0))
                heights.append(dimensions.get('height', 0))
            
            # Primary count
            if image.get('isPrimary'):
                primary_count += 1
        
        # Calculate averages
        avg_width = sum(widths) / len(widths) if widths else 0
        avg_height = sum(heights) / len(heights) if heights else 0
        
        return {
            'count': len(images),
            'total_size': total_size,
            'formatted_total_size': self._format_bytes(total_size),
            'average_size': total_size // len(images) if images else 0,
            'formats': formats,
            'dimensions': {
                'avg_width': round(avg_width, 1),
                'avg_height': round(avg_height, 1),
                'max_width': max(widths) if widths else 0,
                'max_height': max(heights) if heights else 0
            },
            'primary_count': primary_count,
            'primary_percentage': round((primary_count / len(images)) * 100, 1) if images else 0
        }
    
    def _format_bytes(self, bytes: int, decimals: int = 2) -> str:
        """Format bytes to human-readable string."""
        if bytes == 0:
            return "0 Bytes"
        
        k = 1024
        sizes = ["Bytes", "KB", "MB", "GB"]
        
        i = max(0, min(len(sizes) - 1, int(math.floor(math.log(bytes) / math.log(k)))))
        
        return f"{bytes / (k ** i):.{decimals}f} {sizes[i]}"
    
    def clear_cache(self, pattern: Optional[str] = None):
        """Clear cache entries."""
        if not pattern:
            self.cache.clear()
        else:
            keys_to_remove = [
                key for key in self.cache.keys()
                if pattern in key
            ]
            for key in keys_to_remove:
                del self.cache[key]

class ImageQueryError(Exception):
    """Custom exception for image query errors."""
    pass

# Usage Examples
def demonstrate_image_querying():
    """Demonstrate various image querying scenarios."""
    
    query = ProductImageQuery(
        base_url="http://localhost:8000/api",
        token="your_token_here"  # Optional for public endpoints
    )
    
    try:
        # Example 1: Get all images for a product
        print("Example 1: Getting product images...")
        product_images = query.get_product_images(
            product_id="prod_789",
            include_variants=True
        )
        
        print(f"Found {product_images.total} images for product")
        print(f"Page {product_images.page} of {product_images.total_pages}")
        
        if product_images.stats:
            print(f"Total size: {product_images.stats['formatted_total_size']}")
            print(f"Average dimensions: {product_images.stats['dimensions']['avg_width']}x{product_images.stats['dimensions']['avg_height']}")
        
        # Example 2: Get primary image
        print("\nExample 2: Getting primary image...")
        primary_image = query.get_primary_image("prod_789")
        
        if primary_image:
            print(f"Primary image: {primary_image['filename']}")
            print(f"Dimensions: {primary_image['dimensions']['width']}x{primary_image['dimensions']['height']}")
        else:
            print("No primary image found")
        
        # Example 3: Search images
        print("\nExample 3: Searching images...")
        search_results = query.search_images(
            search_term="keyboard",
            options={'page_size': 10}
        )
        
        print(f"Search found {search_results.total} images")
        for i, image in enumerate(search_results.items[:3], 1):
            print(f"{i}. {image['filename']} - {image.get('productId', 'N/A')}")
        
        # Example 4: Get recent images
        print("\nExample 4: Getting recent images...")
        recent_images = query.get_recent_images(days=7, limit=5)
        
        print(f"Recent images (last 7 days):")
        for i, image in enumerate(recent_images.items, 1):
            uploaded_date = datetime.fromisoformat(image['uploadedAt'].replace('Z', '+00:00'))
            print(f"{i}. {image['filename']} ({uploaded_date.strftime('%Y-%m-%d')})")
        
        # Example 5: Get statistics
        print("\nExample 5: Getting image statistics...")
        stats = query.get_image_statistics(
            ImageFilter(product_id="prod_789")
        )
        
        print("Image statistics:")
        print(f"  Count: {stats['count']}")
        print(f"  Total size: {stats['formatted_total_size']}")
        print(f"  Formats: {stats['formats']}")
        print(f"  Primary images: {stats['primary_count']} ({stats['primary_percentage']}%)")
        
        # Example 6: Export images
        print("\nExample 6: Exporting image list...")
        export_data = query.export_image_list(
            filter_config=ImageFilter(product_id="prod_789"),
            format="json",
            include_fields=["id", "filename", "dimensions.width", "dimensions.height", "size"]
        )
        
        print(f"Exported {len(export_data)} bytes of JSON data")
        
        # Example 7: Stream images
        print("\nExample 7: Streaming images...")
        def batch_callback(batch, page, total_pages):
            print(f"Processed batch {page}/{total_pages}: {len(batch)} images")
        
        all_images = query.stream_images(
            filter_config=ImageFilter(product_id="prod_789"),
            batch_size=20,
            on_batch=batch_callback
        )
        
        print(f"Streamed total of {len(all_images)} images")
        
        # Example 8: Get available filters
        print("\nExample 8: Getting available filters...")
        available_filters = query.get_available_filters(
            ImageFilter(product_id="prod_789")
        )
        
        print(f"Available tags: {available_filters['tags'][:5]}...")
        print(f"Available MIME types: {available_filters['mime_types']}")
        
    except ImageQueryError as e:
        print(f"Image query error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    demonstrate_image_querying()
```

### Best Practices for Image Listing

#### 1. **Optimized Image Loading**
```javascript
// Implement progressive image loading
class ProgressiveImageLoader {
  constructor() {
    this.imageCache = new Map();
    this.priorityQueue = [];
  }
  
  async loadImage(imageUrl, priority = 'medium') {
    // Check cache first
    if (this.imageCache.has(imageUrl)) {
      return this.imageCache.get(imageUrl);
    }
    
    // Add to priority queue
    const loadPromise = this.loadImageWithPriority(imageUrl, priority);
    this.imageCache.set(imageUrl, loadPromise);
    
    return loadPromise;
  }
  
  async loadImageWithPriority(imageUrl, priority) {
    // Create image element with appropriate attributes
    const img = new Image();
    
    // Set loading attributes based on priority
    if (priority === 'high') {
      img.loading = 'eager';
      if ('fetchPriority' in img) {
        img.fetchPriority = 'high';
      }
    } else {
      img.loading = 'lazy';
    }
    
    return new Promise((resolve, reject) => {
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.src = imageUrl;
    });
  }
  
  preloadImages(imageUrls) {
    // Preload images in the background
    imageUrls.forEach(url => {
      this.loadImage(url, 'low').catch(() => {
        // Silently fail for preloads
      });
    });
  }
}
```

#### 2. **Virtual Scrolling for Large Lists**
```javascript
// Implement virtual scrolling for performance
class VirtualImageGrid {
  constructor(container, itemHeight, buffer = 5) {
    this.container = container;
    this.itemHeight = itemHeight;
    this.buffer = buffer;
    this.visibleItems = new Set();
    this.data = [];
    
    this.init();
  }
  
  init() {
    // Set up scroll listener
    this.container.addEventListener('scroll', () => this.handleScroll());
    
    // Set container height
    this.updateContainerHeight();
  }
  
  setData(images) {
    this.data = images;
    this.updateContainerHeight();
    this.renderVisibleItems();
  }
  
  updateContainerHeight() {
    const totalHeight = this.data.length * this.itemHeight;
    this.container.style.height = `${totalHeight}px`;
  }
  
  getVisibleRange() {
    const scrollTop = this.container.scrollTop;
    const visibleHeight = this.container.clientHeight;
    
    const startIndex = Math.max(0, Math.floor(scrollTop / this.itemHeight) - this.buffer);
    const endIndex = Math.min(
      this.data.length - 1,
      Math.ceil((scrollTop + visibleHeight) / this.itemHeight) + this.buffer
    );
    
    return { startIndex, endIndex };
  }
  
  renderVisibleItems() {
    const { startIndex, endIndex } = this.getVisibleRange();
    const newVisibleItems = new Set();
    
    // Render visible items
    for (let i = startIndex; i <= endIndex; i++) {
      newVisibleItems.add(i);
      
      if (!this.visibleItems.has(i)) {
        this.renderItem(i);
      }
    }
    
    // Remove items that are no longer visible
    this.visibleItems.forEach(index => {
      if (!newVisibleItems.has(index)) {
        this.removeItem(index);
      }
    });
    
    this.visibleItems = newVisibleItems;
  }
  
  renderItem(index) {
    const image = this.data[index];
    const top = index * this.itemHeight;
    
    // Create and position image element
    const imgElement = this.createImageElement(image, top);
    this.container.appendChild(imgElement);
  }
  
  createImageElement(image, top) {
    const div = document.createElement('div');
    div.className = 'virtual-image-item';
    div.style.position = 'absolute';
    div.style.top = `${top}px`;
    div.style.height = `${this.itemHeight}px`;
    
    const img = document.createElement('img');
    img.src = image.variants?.thumbnail || image.variants?.original;
    img.alt = image.altText || '';
    img.loading = 'lazy';
    
    div.appendChild(img);
    return div;
  }
}
```

#### 3. **Intelligent Caching Strategy**
```javascript
class IntelligentImageCache {
  constructor() {
    this.cache = new Map();
    this.accessTimes = new Map();
    this.maxSize = 100; // Maximum number of cached items
    this.ttl = 5 * 60 * 1000; // 5 minutes
  }
  
  async getImage(imageId, fetchFunction) {
    const cached = this.cache.get(imageId);
    
    // Check if cached and not expired
    if (cached && Date.now() - cached.timestamp < this.ttl) {
      this.accessTimes.set(imageId, Date.now());
      return cached.data;
    }
    
    // Fetch new data
    const data = await fetchFunction(imageId);
    
    // Cache the result
    this.set(imageId, data);
    
    // Clean up if cache is too large
    this.cleanup();
    
    return data;
  }
  
  set(imageId, data) {
    this.cache.set(imageId, {
      data,
      timestamp: Date.now()
    });
    
    this.accessTimes.set(imageId, Date.now());
  }
  
  cleanup() {
    if (this.cache.size > this.maxSize) {
      // Find least recently used items
      const entries = Array.from(this.accessTimes.entries());
      entries.sort((a, b) => a[1] - b[1]);
      
      // Remove oldest items
      const toRemove = entries.slice(0, Math.floor(this.maxSize * 0.2)); // Remove 20%
      
      toRemove.forEach(([imageId]) => {
        this.cache.delete(imageId);
        this.accessTimes.delete(imageId);
      });
    }
  }
  
  // Preload images likely to be viewed
  preloadRelatedImages(currentImageId, imageList) {
    const currentIndex = imageList.findIndex(img => img.id === currentImageId);
    
    if (currentIndex === -1) return;
    
    // Preload next few images
    const toPreload = imageList.slice(currentIndex + 1, currentIndex + 4);
    
    toPreload.forEach(image => {
      if (!this.cache.has(image.id)) {
        // Start loading but don't wait for it
        this.preloadImage(image);
      }
    });
  }
  
  async preloadImage(image) {
    const img = new Image();
    img.src = image.variants?.thumbnail || image.variants?.original;
    
    try {
      await img.decode();
      this.set(image.id, image);
    } catch {
      // Silently fail for preloads
    }
  }
}
```

#### 4. **Image Analysis and Processing**
```javascript
// Analyze images for better display
class ImageAnalyzer {
  static async getDominantColor(imageUrl) {
    return new Promise((resolve) => {
      const img = new Image();
      img.crossOrigin = 'Anonymous';
      
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = img.width;
        canvas.height = img.height;
        
        ctx.drawImage(img, 0, 0);
        
        // Get image data
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;
        
        // Calculate average color
        let r = 0, g = 0, b = 0;
        
        for (let i = 0; i < data.length; i += 4) {
          r += data[i];
          g += data[i + 1];
          b += data[i + 2];
        }
        
        const pixelCount = data.length / 4;
        r = Math.floor(r / pixelCount);
        g = Math.floor(g / pixelCount);
        b = Math.floor(b / pixelCount);
        
        resolve(`rgb(${r}, ${g}, ${b})`);
      };
      
      img.src = imageUrl;
    });
  }
  
  static async getImageAspectClass(width, height) {
    const aspectRatio = width / height;
    
    if (aspectRatio > 1.5) return 'landscape';
    if (aspectRatio < 0.67) return 'portrait';
    return 'square';
  }
  
  static async optimizeImageUrl(imageData, containerWidth) {
    const variants = imageData.variants || {};
    
    // Choose the best variant based on container size
    if (containerWidth >= 1200 && variants.large) {
      return variants.large;
    } else if (containerWidth >= 800 && variants.medium) {
      return variants.medium;
    } else if (containerWidth >= 300 && variants.thumbnail) {
      return variants.thumbnail;
    }
    
    return variants.original || '';
  }
}
```

### Security Considerations

#### 1. **Access Control**
```javascript
// Implement proper access control for images
class ImageAccessControl {
  constructor() {
    this.publicPaths = ['/products/', '/thumbnails/'];
    this.privatePaths = ['/admin/', '/raw/'];
  }
  
  canAccessImage(imageUrl, userRole) {
    // Check if image is in public path
    if (this.isPublicImage(imageUrl)) {
      return true;
    }
    
    // Check user permissions for private images
    if (this.isPrivateImage(imageUrl)) {
      return this.hasAdminAccess(userRole);
    }
    
    // Default to deny
    return false;
  }
  
  isPublicImage(imageUrl) {
    return this.publicPaths.some(path => imageUrl.includes(path));
  }
  
  isPrivateImage(imageUrl) {
    return this.privatePaths.some(path => imageUrl.includes(path));
  }
  
  hasAdminAccess(userRole) {
    return ['admin', 'editor'].includes(userRole);
  }
}
```

#### 2. **Rate Limiting**
```javascript
// Prevent abuse with rate limiting
class ImageListRateLimiter {
  constructor() {
    this.limits = new Map();
    this.window = 60 * 1000; // 1 minute
  }
  
  canRequest(userId, endpoint) {
    const key = `${userId}:${endpoint}`;
    const now = Date.now();
    
    // Get existing requests
    const requests = this.limits.get(key) || [];
    
    // Clean up old requests
    const recentRequests = requests.filter(time => now - time < this.window);
    
    // Check limit
    const limit = this.getLimitForEndpoint(endpoint);
    if (recentRequests.length >= limit) {
      return false;
    }
    
    // Add new request
    recentRequests.push(now);
    this.limits.set(key, recentRequests);
    
    return true;
  }
  
  getLimitForEndpoint(endpoint) {
    const limits = {
      '/files': 60, // 60 requests per minute
      '/files/search': 30,
      '/files/stats': 10
    };
    
    return limits[endpoint] || 30;
  }
}
```

#### 3. **Data Validation**
```javascript
// Validate and sanitize image list parameters
class ImageListValidator {
  static validateFilters(filters) {
    const errors = [];
    
    // Page size validation
    if (filters.page_size) {
      const pageSize = parseInt(filters.page_size);
      if (isNaN(pageSize) || pageSize < 1 || pageSize > 100) {
        errors.push('page_size must be between 1 and 100');
      }
    }
    
    // Date validation
    if (filters.uploaded_after) {
      const date = new Date(filters.uploaded_after);
      if (isNaN(date.getTime())) {
        errors.push('uploaded_after must be a valid date');
      }
    }
    
    // Tag validation
    if (filters.tags) {
      const tags = Array.isArray(filters.tags) ? filters.tags : [filters.tags];
      if (tags.length > 10) {
        errors.push('Maximum 10 tags allowed');
      }
      
      tags.forEach(tag => {
        if (tag.length > 50) {
          errors.push('Tags cannot exceed 50 characters');
        }
      });
    }
    
    return errors;
  }
  
  static sanitizeFilters(filters) {
    const sanitized = { ...filters };
    
    // Sanitize search term
    if (sanitized.search) {
      sanitized.search = sanitized.search.substring(0, 100); // Limit length
      sanitized.search = sanitized.search.replace(/[<>]/g, ''); // Remove HTML tags
    }
    
    // Sanitize product ID
    if (sanitized.productId) {
      sanitized.productId = sanitized.productId.replace(/[^a-zA-Z0-9_-]/g, '');
    }
    
    return sanitized;
  }
}
```

---

## Related Endpoints
- [GET /files/{fileId}](../images/get-image.md) - Get single image metadata
- [POST /files](../images/upload-image.md) - Upload new product image
- [PATCH /files/{fileId}/primary](../images/set-primary.md) - Set image as primary
- [DELETE /files/{fileId}](../images/delete-image.md) - Delete product image
- [Error Responses](../../errors.md) - Error handling details

## Notes
- Use `include_variants=true` to get URLs for different image sizes
- Consider implementing infinite scroll for better UX with large image sets
- Cache image lists aggressively when possible
- Implement proper error boundaries for image loading failures
- Consider adding image moderation for user-generated content

## Performance Optimization
- Implement CDN for image delivery
- Use WebP format for better compression
- Implement lazy loading for image galleries
- Use placeholder images while loading
- Implement image preloading for better UX
- Consider implementing image CDN with edge caching

## SEO Considerations
- Include alt text for all images
- Use descriptive filenames
- Implement structured data for product images
- Generate sitemap with image URLs
- Use lazy loading with native browser support

## Compliance and Regulations
- GDPR: Handle personal data in images appropriately
- ADA: Provide proper alt text for accessibility
- Copyright: Ensure proper image licensing
- Privacy: Be cautious with images containing personal information
- Industry-specific regulations may apply