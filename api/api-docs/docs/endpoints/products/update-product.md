# PATCH /products/{productId}

**Update Product** - Partially update product details (Admin Only)

**Tags:** Products

**Authentication:** Required (Bearer Token with Admin privileges)

---

## Description
Update specific fields of an existing product without replacing the entire resource. This partial update is ideal for making incremental changes to product information. Only the fields provided in the request will be modified; all other fields remain unchanged.

## Authentication
**Required:** Bearer Token with Admin role

### Headers
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

## Request

### URL Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `productId` | string | ✓ | Unique product identifier | `prod_1` |

### Body
**Schema:** ProductPatch (Partial update schema)

```json
{
  "name": "Premium Wireless Keyboard Pro",
  "price": 94.99,
  "stock": 200,
  "description": "Updated description: Mechanical wireless keyboard with RGB backlighting, customizable macros, and 5000mAh battery.",
  "tags": ["electronics", "keyboard", "gaming", "wireless", "premium"],
  "is_featured": true,
  "original_price": 119.99,
  "meta_title": "Premium Wireless Mechanical Keyboard Pro | TechGear 2024"
}
```

**Partial Update Fields:**

| Field | Type | Constraints | Description | Notes |
|-------|------|-------------|-------------|-------|
| `name` | string | 3-200 chars | Product name | Optional |
| `price` | number | ≥ 0 | Product price | Optional |
| `stock` | integer | ≥ 0 | Available quantity | Optional |
| `description` | string | ≤ 5000 chars | Product description | Optional |
| `tags` | string[] | ≤ 20 tags | Product categories/tags | Optional |
| `images` | string[] | ≤ 10 images | Image URLs | Optional |
| `sku` | string | Unique | Stock Keeping Unit | Optional, must be unique |
| `category` | string | - | Product category | Optional |
| `brand` | string | - | Manufacturer brand | Optional |
| `specifications` | object | - | Technical specifications | Optional |
| `features` | string[] | ≤ 50 items | Key features | Optional |
| `weight` | number | ≥ 0 | Weight in kg | Optional |
| `dimensions` | object | - | {length, width, height} cm | Optional |
| `is_active` | boolean | - | Product visibility | Optional |
| `is_featured` | boolean | - | Featured product status | Optional |
| `original_price` | number | ≥ price | Original price for discounts | Optional |
| `tax_rate` | number | 0-1 | Tax rate | Optional |
| `meta_title` | string | ≤ 60 chars | SEO meta title | Optional |
| `meta_description` | string | ≤ 160 chars | SEO meta description | Optional |
| `slug` | string | Unique, URL-safe | URL slug | Optional |
| `variant_of` | string | - | Parent product ID | Optional |
| `options` | object | - | Variant options | Optional |
| `reorder_level` | integer | ≥ 0 | Stock reorder threshold | Optional |
| `lead_time` | integer | ≥ 0 | Days to restock | Optional |

## Responses

### 200 OK - Product updated successfully
**Body:**
```json
{
  "id": "prod_789",
  "name": "Premium Wireless Keyboard Pro",
  "price": 94.99,
  "stock": 200,
  "description": "Updated description: Mechanical wireless keyboard with RGB backlighting, customizable macros, and 5000mAh battery.",
  "tags": ["electronics", "keyboard", "gaming", "wireless", "premium"],
  "images": [
    "/static/img/products/prod_789/keyboard-main.jpg",
    "/static/img/products/prod_789/keyboard-angle.jpg"
  ],
  "primaryImageId": "img_123456",
  "sku": "KB-PRO-2023",
  "category": "Computer Accessories",
  "brand": "TechGear",
  "specifications": {
    "connection": "Wireless 2.4GHz + Bluetooth 5.0",
    "switch_type": "Mechanical (Blue)",
    "keycaps": "Double-shot PBT",
    "battery": "5000mAh",
    "backlight": "RGB per-key"
  },
  "features": [
    "Hot-swappable switches",
    "On-board memory for profiles",
    "N-key rollover",
    "Detachable USB-C cable",
    "Adjustable feet"
  ],
  "is_active": true,
  "is_featured": true,
  "original_price": 119.99,
  "meta_title": "Premium Wireless Mechanical Keyboard Pro | TechGear 2024",
  "updated_at": "2024-01-15T14:30:00Z",
  "previous_values": {
    "price": 89.99,
    "stock": 150,
    "original_price": 109.99,
    "is_featured": false
  }
}
```

**Special Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `updated_at` | string | New update timestamp |
| `previous_values` | object | Previous values of changed fields (optional) |

### 400 Bad Request - Invalid input
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/bad-request",
  "title": "Bad Request",
  "status": 400,
  "detail": "Invalid price: must be greater than or equal to 0.",
  "instance": "/products/prod_789",
  "errors": [
    {
      "field": "price",
      "message": "must be greater than or equal to 0"
    }
  ]
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
  "instance": "/products/prod_789"
}
```

### 403 Forbidden - Insufficient permissions
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "Insufficient permissions to update products.",
  "instance": "/products/prod_789"
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
  "instance": "/products/prod_999"
}
```

### 409 Conflict - Duplicate SKU or slug
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/conflict",
  "title": "Conflict",
  "status": 409,
  "detail": "SKU 'KB-PRO-2023' already exists for another product.",
  "instance": "/products/prod_789"
}
```

### 422 Unprocessable Entity - Validation error
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/validation",
  "title": "Validation failed",
  "status": 422,
  "detail": "The request contains invalid data.",
  "instance": "/products/prod_789",
  "errors": [
    {
      "field": "original_price",
      "message": "cannot be less than current price"
    },
    {
      "field": "tags",
      "message": "maximum 20 tags allowed"
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
  "detail": "Failed to update product due to database error.",
  "instance": "/products/prod_789"
}
```

## Examples

### Basic cURL Request
```bash
# Update product price and stock
curl -X PATCH "http://localhost:8000/api/products/prod_789" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "price": 94.99,
    "stock": 200
  }'
```

### Complete cURL Request
```bash
curl -X PATCH "http://localhost:8000/api/products/prod_789" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Wireless Keyboard Pro",
    "price": 94.99,
    "description": "Updated with 5000mAh battery and improved switches.",
    "tags": ["electronics", "keyboard", "gaming", "wireless", "premium"],
    "is_featured": true,
    "original_price": 119.99,
    "specifications": {
      "battery": "5000mAh",
      "switch_type": "Mechanical (Red)"
    }
  }'
```

### JavaScript (Fetch) with Advanced Features
```javascript
/**
 * Advanced product update service with change tracking and validation
 */
class ProductUpdater {
  constructor(apiUrl = 'http://localhost:8000/api') {
    this.apiUrl = apiUrl;
    this.changeHistory = new Map();
  }
  
  /**
   * Update product with partial data
   */
  async updateProduct(productId, updateData, accessToken, options = {}) {
    const {
      validate = true,
      trackChanges = true,
      returnChanges = false,
      force = false
    } = options;
    
    // Get current product if tracking changes
    let previousData = null;
    if (trackChanges) {
      try {
        previousData = await this.getProduct(productId, accessToken);
      } catch (error) {
        console.warn('Could not fetch previous data for change tracking:', error);
      }
    }
    
    // Validate update data
    if (validate) {
      const validation = this.validateUpdateData(updateData, previousData);
      if (!validation.valid) {
        throw new ValidationError('Update validation failed', validation.errors);
      }
    }
    
    // Prepare request
    const headers = {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      'X-Update-Reason': options.reason || 'Admin update',
      'X-Request-ID': this.generateRequestId()
    };
    
    if (force) {
      headers['X-Force-Update'] = 'true';
    }
    
    try {
      const response = await fetch(`${this.apiUrl}/products/${productId}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(updateData)
      });
      
      const responseData = response.headers.get('content-type')?.includes('application/json')
        ? await response.json()
        : null;
      
      // Handle response
      if (response.ok) {
        const updatedProduct = responseData;
        
        // Track changes
        if (trackChanges && previousData) {
          const changes = this.calculateChanges(previousData, updatedProduct, updateData);
          this.recordChange(productId, changes, options.reason);
        }
        
        // Fire webhook or event
        this.triggerProductUpdated(productId, updatedProduct, updateData);
        
        const result = {
          success: true,
          product: updatedProduct,
          status: response.status
        };
        
        if (returnChanges && previousData) {
          result.changes = this.calculateChanges(previousData, updatedProduct, updateData);
        }
        
        return result;
        
      } else {
        // Handle specific error cases
        if (response.status === 404) {
          throw new ProductNotFoundError(`Product ${productId} not found`);
        } else if (response.status === 409) {
          throw new ConflictError(
            responseData?.detail || 'Update conflict',
            responseData
          );
        } else if (response.status === 422) {
          throw new ValidationError(
            'Update validation failed',
            responseData?.errors || []
          );
        } else {
          throw new ProductUpdateError(
            `Update failed: ${response.status}`,
            responseData,
            response.status
          );
        }
      }
      
    } catch (error) {
      if (error instanceof ValidationError || 
          error instanceof ConflictError || 
          error instanceof ProductNotFoundError) {
        throw error;
      }
      
      // Network or unknown error
      throw new ProductUpdateError(
        `Network error: ${error.message}`,
        null,
        null,
        error
      );
    }
  }
  
  /**
   * Bulk update multiple products
   */
  async bulkUpdate(updates, accessToken, options = {}) {
    const {
      concurrency = 3,
      onProgress = null
    } = options;
    
    const results = {
      successful: [],
      failed: [],
      total: updates.length
    };
    
    // Process in batches for concurrency control
    for (let i = 0; i < updates.length; i += concurrency) {
      const batch = updates.slice(i, i + concurrency);
      const batchPromises = batch.map(update =>
        this.updateProduct(update.productId, update.data, accessToken, update.options)
          .then(result => ({ success: true, result, update }))
          .catch(error => ({ success: false, error, update }))
      );
      
      const batchResults = await Promise.all(batchPromises);
      
      batchResults.forEach((result, index) => {
        const update = batch[index];
        
        if (result.success) {
          results.successful.push({
            productId: update.productId,
            result: result.result,
            update: update.data
          });
        } else {
          results.failed.push({
            productId: update.productId,
            error: result.error,
            update: update.data
          });
        }
        
        // Progress callback
        if (onProgress) {
          const processed = results.successful.length + results.failed.length;
          onProgress(processed, updates.length);
        }
      });
    }
    
    return results;
  }
  
  /**
   * Update product with optimistic UI updates
   */
  async updateProductOptimistic(productId, updateData, accessToken, uiUpdateCallback) {
    // Store current state for rollback
    const currentState = await this.getProduct(productId, accessToken);
    
    // Apply optimistic update to UI
    const optimisticData = { ...currentState, ...updateData };
    uiUpdateCallback(optimisticData);
    
    try {
      // Perform actual update
      const result = await this.updateProduct(productId, updateData, accessToken);
      return result;
    } catch (error) {
      // Rollback UI to original state
      uiUpdateCallback(currentState);
      throw error;
    }
  }
  
  /**
   * Calculate what changed between versions
   */
  calculateChanges(previous, current, updateData) {
    const changes = {};
    
    // Check each field in update data
    Object.keys(updateData).forEach(key => {
      const prevValue = previous[key];
      const newValue = current[key];
      
      // Handle arrays and objects
      if (Array.isArray(prevValue) && Array.isArray(newValue)) {
        if (JSON.stringify(prevValue) !== JSON.stringify(newValue)) {
          changes[key] = {
            from: prevValue,
            to: newValue,
            type: 'array'
          };
        }
      } else if (typeof prevValue === 'object' && typeof newValue === 'object') {
        if (JSON.stringify(prevValue) !== JSON.stringify(newValue)) {
          changes[key] = {
            from: prevValue,
            to: newValue,
            type: 'object'
          };
        }
      } else if (prevValue !== newValue) {
        changes[key] = {
          from: prevValue,
          to: newValue,
          type: typeof prevValue
        };
      }
    });
    
    return changes;
  }
  
  /**
   * Record change history
   */
  recordChange(productId, changes, reason = '') {
    const historyKey = `product:${productId}`;
    const timestamp = new Date().toISOString();
    
    const changeRecord = {
      timestamp,
      changes,
      reason,
      user: this.getCurrentUser() // Implement user tracking
    };
    
    if (!this.changeHistory.has(historyKey)) {
      this.changeHistory.set(historyKey, []);
    }
    
    this.changeHistory.get(historyKey).push(changeRecord);
    
    // Keep only last 100 changes per product
    const history = this.changeHistory.get(historyKey);
    if (history.length > 100) {
      history.shift();
    }
  }
  
  /**
   * Validate update data
   */
  validateUpdateData(updateData, previousData = null) {
    const errors = [];
    
    // Field-specific validations
    if ('price' in updateData) {
      if (typeof updateData.price !== 'number') {
        errors.push({
          field: 'price',
          message: 'Price must be a number'
        });
      } else if (updateData.price < 0) {
        errors.push({
          field: 'price',
          message: 'Price must be non-negative'
        });
      }
    }
    
    if ('original_price' in updateData && 'price' in updateData) {
      if (updateData.original_price < updateData.price) {
        errors.push({
          field: 'original_price',
          message: 'Original price cannot be less than current price'
        });
      }
    }
    
    if ('original_price' in updateData && !('price' in updateData) && previousData) {
      if (updateData.original_price < previousData.price) {
        errors.push({
          field: 'original_price',
          message: 'Original price cannot be less than current price'
        });
      }
    }
    
    if ('stock' in updateData) {
      if (!Number.isInteger(updateData.stock)) {
        errors.push({
          field: 'stock',
          message: 'Stock must be an integer'
        });
      } else if (updateData.stock < 0) {
        errors.push({
          field: 'stock',
          message: 'Stock must be non-negative'
        });
      }
    }
    
    if ('tags' in updateData) {
      if (!Array.isArray(updateData.tags)) {
        errors.push({
          field: 'tags',
          message: 'Tags must be an array'
        });
      } else if (updateData.tags.length > 20) {
        errors.push({
          field: 'tags',
          message: 'Maximum 20 tags allowed'
        });
      }
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
  
  /**
   * Get product details
   */
  async getProduct(productId, accessToken) {
    const response = await fetch(`${this.apiUrl}/products/${productId}`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get product: ${response.status}`);
    }
    
    return response.json();
  }
  
  /**
   * Trigger product updated event
   */
  triggerProductUpdated(productId, productData, updateData) {
    // Dispatch custom event
    const event = new CustomEvent('productUpdated', {
      detail: {
        productId,
        product: productData,
        update: updateData,
        timestamp: new Date().toISOString()
      }
    });
    
    window.dispatchEvent(event);
    
    // Send analytics
    if (window.gtag) {
      window.gtag('event', 'update_product', {
        product_id: productId,
        updated_fields: Object.keys(updateData)
      });
    }
  }
  
  generateRequestId() {
    return `update_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  getCurrentUser() {
    // Implement user retrieval
    return localStorage.getItem('userId') || 'unknown';
  }
}

// Custom Error Classes
class ProductNotFoundError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ProductNotFoundError';
  }
}

class ProductUpdateError extends Error {
  constructor(message, responseData = null, statusCode = null, originalError = null) {
    super(message);
    this.name = 'ProductUpdateError';
    this.responseData = responseData;
    this.statusCode = statusCode;
    this.originalError = originalError;
  }
}

// Usage Example
async function updateProductExample() {
  const updater = new ProductUpdater();
  const accessToken = localStorage.getItem('accessToken');
  const productId = 'prod_789';
  
  const updateData = {
    name: 'Premium Wireless Keyboard Pro',
    price: 94.99,
    stock: 200,
    is_featured: true,
    tags: ['electronics', 'keyboard', 'gaming', 'wireless', 'premium']
  };
  
  try {
    const result = await updater.updateProduct(
      productId,
      updateData,
      accessToken,
      {
        reason: 'Price increase and stock update',
        trackChanges: true,
        returnChanges: true
      }
    );
    
    console.log('Update successful:', {
      productId: result.product.id,
      name: result.product.name,
      price: result.product.price,
      changes: result.changes
    });
    
    // Show success message
    showNotification('Product updated successfully!', 'success');
    
  } catch (error) {
    console.error('Update failed:', error);
    
    if (error instanceof ValidationError) {
      error.errors.forEach(err => {
        showFieldError(err.field, err.message);
      });
      showNotification('Please fix validation errors', 'error');
    } else if (error instanceof ConflictError) {
      showNotification('Update conflict: ' + error.message, 'error');
    } else if (error instanceof ProductNotFoundError) {
      showNotification('Product not found', 'error');
    } else {
      showNotification('Failed to update product', 'error');
    }
  }
}
```

### React Admin Component with Real-time Updates
```jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ProductForm from './ProductForm';
import ChangeHistory from './ChangeHistory';
import LivePreview from './LivePreview';

function UpdateProductPage() {
  const { productId } = useParams();
  const navigate = useNavigate();
  
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState(null);
  const [changeHistory, setChangeHistory] = useState([]);
  const [livePreview, setLivePreview] = useState(null);
  
  // Fetch product data
  useEffect(() => {
    fetchProduct();
  }, [productId]);
  
  const fetchProduct = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const accessToken = localStorage.getItem('accessToken');
      
      const response = await fetch(`http://localhost:8000/api/products/${productId}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });
      
      if (!response.ok) {
        if (response.status === 404) {
          navigate('/admin/products', { state: { error: 'Product not found' } });
          return;
        }
        throw new Error(`Failed to fetch product: ${response.status}`);
      }
      
      const data = await response.json();
      setProduct(data);
      setLivePreview(data);
      
      // Fetch change history
      fetchChangeHistory(data.id);
      
    } catch (err) {
      setError(err.message);
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const fetchChangeHistory = async (productId) => {
    try {
      // This would be a separate endpoint in production
      const response = await fetch(`/api/products/${productId}/changes`);
      if (response.ok) {
        const history = await response.json();
        setChangeHistory(history);
      }
    } catch (err) {
      console.error('Failed to fetch change history:', err);
    }
  };
  
  const handleSubmit = async (updateData) => {
    setUpdating(true);
    setError(null);
    
    try {
      const accessToken = localStorage.getItem('accessToken');
      
      const response = await fetch(`http://localhost:8000/api/products/${productId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
          'X-Update-Reason': 'Admin update via UI'
        },
        body: JSON.stringify(updateData)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Update failed');
      }
      
      const updatedProduct = await response.json();
      
      // Update local state
      setProduct(updatedProduct);
      setLivePreview(updatedProduct);
      
      // Add to change history
      const change = {
        timestamp: new Date().toISOString(),
        changes: calculateChanges(product, updatedProduct),
        user: 'Current User'
      };
      
      setChangeHistory(prev => [change, ...prev.slice(0, 9)]);
      
      // Show success
      showSuccess('Product updated successfully!');
      
      // Navigate or stay on page
      if (updateData.redirect) {
        navigate('/admin/products');
      }
      
    } catch (err) {
      setError(err.message);
      console.error('Update error:', err);
      showError('Failed to update product: ' + err.message);
    } finally {
      setUpdating(false);
    }
  };
  
  const handleFieldChange = (field, value) => {
    // Update live preview in real-time
    setLivePreview(prev => ({
      ...prev,
      [field]: value
    }));
  };
  
  const calculateChanges = (oldData, newData) => {
    const changes = {};
    
    Object.keys(newData).forEach(key => {
      if (JSON.stringify(oldData[key]) !== JSON.stringify(newData[key])) {
        changes[key] = {
          from: oldData[key],
          to: newData[key]
        };
      }
    });
    
    return changes;
  };
  
  const handleBulkUpdate = async (updates) => {
    // Implement bulk update for multiple fields
    const updateData = {};
    updates.forEach(update => {
      updateData[update.field] = update.value;
    });
    
    await handleSubmit(updateData);
  };
  
  const handleRevert = async (changeIndex) => {
    const change = changeHistory[changeIndex];
    
    // Build revert data
    const revertData = {};
    Object.keys(change.changes).forEach(field => {
      revertData[field] = change.changes[field].from;
    });
    
    revertData.revert_reason = `Reverted to state from ${new Date(change.timestamp).toLocaleString()}`;
    
    await handleSubmit(revertData);
  };
  
  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading product details...</p>
      </div>
    );
  }
  
  if (error && !product) {
    return (
      <div className="error-container">
        <h2>Error Loading Product</h2>
        <p>{error}</p>
        <button onClick={fetchProduct}>Retry</button>
      </div>
    );
  }
  
  return (
    <div className="update-product-page">
      <div className="page-header">
        <h1>Update Product: {product.name}</h1>
        <div className="header-actions">
          <button 
            className="btn-back"
            onClick={() => navigate('/admin/products')}
          >
            Back to Products
          </button>
          <button 
            className="btn-view"
            onClick={() => navigate(`/products/${productId}`)}
            target="_blank"
          >
            View Live Product
          </button>
        </div>
      </div>
      
      <div className="product-update-layout">
        {/* Left: Update Form */}
        <div className="update-form-section">
          <h2>Update Product Details</h2>
          
          {error && (
            <div className="alert alert-error">
              <strong>Error:</strong> {error}
            </div>
          )}
          
          <ProductForm
            product={product}
            onSubmit={handleSubmit}
            loading={updating}
            onFieldChange={handleFieldChange}
            mode="update"
          />
          
          {/* Quick Actions */}
          <div className="quick-actions">
            <h3>Quick Actions</h3>
            <div className="action-buttons">
              <button 
                onClick={() => handleSubmit({ is_featured: !product.is_featured })}
                className={`btn-featured ${product.is_featured ? 'active' : ''}`}
              >
                {product.is_featured ? 'Remove Featured' : 'Mark as Featured'}
              </button>
              
              <button 
                onClick={() => handleSubmit({ is_active: !product.is_active })}
                className={`btn-active ${product.is_active ? 'active' : ''}`}
              >
                {product.is_active ? 'Deactivate' : 'Activate'}
              </button>
              
              <button 
                onClick={() => handleSubmit({ stock: product.stock + 10 })}
                className="btn-stock"
              >
                Add 10 to Stock
              </button>
            </div>
          </div>
        </div>
        
        {/* Middle: Live Preview */}
        <div className="preview-section">
          <h2>Live Preview</h2>
          <LivePreview
            product={livePreview}
            originalProduct={product}
          />
        </div>
        
        {/* Right: Change History */}
        <div className="history-section">
          <h2>Change History</h2>
          <ChangeHistory
            history={changeHistory}
            onRevert={handleRevert}
          />
        </div>
      </div>
      
      {/* Batch Update Panel (Collapsible) */}
      <div className="batch-update-panel">
        <h3>Batch Update</h3>
        <BatchUpdateForm
          onUpdate={handleBulkUpdate}
          product={product}
        />
      </div>
    </div>
  );
}

export default UpdateProductPage;
```

### Python with Advanced Update Logic
```python
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum

class UpdateStrategy(Enum):
    """Strategies for handling product updates."""
    PARTIAL = "partial"  # Only update provided fields
    MERGE = "merge"      # Merge objects/arrays
    REPLACE = "replace"  # Replace entire field
    INCREMENT = "increment"  # Increment numeric values

class ProductUpdateManager:
    """Advanced product update management with conflict resolution."""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.update_history = {}
    
    def update_product(
        self,
        product_id: str,
        update_data: Dict,
        strategy: UpdateStrategy = UpdateStrategy.PARTIAL,
        options: Optional[Dict] = None
    ) -> Dict:
        """
        Update product with specified strategy.
        
        Args:
            product_id: Product identifier
            update_data: Data to update
            strategy: Update strategy to use
            options: Additional options
            
        Returns:
            Updated product data
        """
        options = options or {}
        
        # Get current product state
        current_product = self._get_product(product_id)
        
        # Apply update strategy
        if strategy == UpdateStrategy.MERGE:
            update_data = self._apply_merge_strategy(current_product, update_data)
        elif strategy == UpdateStrategy.INCREMENT:
            update_data = self._apply_increment_strategy(current_product, update_data)
        
        # Check for conflicts
        if not options.get('force', False):
            conflicts = self._check_conflicts(current_product, update_data)
            if conflicts:
                raise UpdateConflictError("Update conflicts detected", conflicts)
        
        # Prepare request
        headers = {
            'X-Update-Strategy': strategy.value,
            'X-Update-ID': self._generate_update_id(),
            'X-Update-Reason': options.get('reason', '')
        }
        
        try:
            response = self.session.patch(
                f"{self.base_url}/products/{product_id}",
                json=update_data,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            
            updated_product = response.json()
            
            # Record update
            self._record_update(
                product_id,
                current_product,
                updated_product,
                update_data,
                strategy.value,
                options.get('reason')
            )
            
            # Trigger post-update actions
            self._post_update_actions(product_id, current_product, updated_product)
            
            return updated_product
            
        except requests.exceptions.HTTPError as e:
            error_data = e.response.json() if e.response.content else {}
            self._handle_update_error(e, error_data)
    
    def bulk_update_products(
        self,
        updates: List[Dict],
        batch_size: int = 10,
        on_progress=None
    ) -> Dict:
        """
        Update multiple products with progress tracking.
        
        Args:
            updates: List of update dicts with product_id and data
            batch_size: Number of concurrent updates
            on_progress: Progress callback function
            
        Returns:
            Bulk update results
        """
        results = {
            'successful': [],
            'failed': [],
            'total': len(updates)
        }
        
        # Process in batches
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            batch_results = []
            
            for update in batch:
                try:
                    result = self.update_product(
                        update['product_id'],
                        update['data'],
                        update.get('strategy', UpdateStrategy.PARTIAL),
                        update.get('options', {})
                    )
                    batch_results.append({
                        'success': True,
                        'product_id': update['product_id'],
                        'result': result
                    })
                except Exception as e:
                    batch_results.append({
                        'success': False,
                        'product_id': update['product_id'],
                        'error': str(e)
                    })
            
            # Process batch results
            for result in batch_results:
                if result['success']:
                    results['successful'].append(result)
                else:
                    results['failed'].append(result)
            
            # Progress callback
            if on_progress:
                processed = len(results['successful']) + len(results['failed'])
                on_progress(processed, len(updates))
        
        return results
    
    def update_with_rollback(
        self,
        product_id: str,
        update_data: Dict,
        rollback_strategy: UpdateStrategy = UpdateStrategy.PARTIAL
    ) -> Dict:
        """
        Update product with automatic rollback on failure.
        
        Args:
            product_id: Product identifier
            update_data: Data to update
            rollback_strategy: Strategy to use for rollback
            
        Returns:
            Updated product data
        """
        # Get current state for potential rollback
        original_state = self._get_product(product_id)
        
        try:
            # Attempt update
            result = self.update_product(product_id, update_data)
            return result
            
        except Exception as e:
            # Rollback to original state
            print(f"Update failed, rolling back: {e}")
            
            try:
                rollback_data = self._create_rollback_data(original_state, update_data, rollback_strategy)
                self.update_product(product_id, rollback_data, UpdateStrategy.REPLACE, {'force': True})
                print("Rollback successful")
            except Exception as rollback_error:
                print(f"Rollback failed: {rollback_error}")
            
            raise UpdateError(f"Update failed and rolled back: {e}")
    
    def update_product_field(
        self,
        product_id: str,
        field_path: str,
        value,
        strategy: UpdateStrategy = UpdateStrategy.REPLACE
    ) -> Dict:
        """
        Update specific field using dot notation path.
        
        Args:
            product_id: Product identifier
            field_path: Dot notation path (e.g., 'specifications.battery')
            value: New value
            strategy: Update strategy
            
        Returns:
            Updated product data
        """
        # Create nested update structure
        update_data = self._create_nested_update(field_path, value)
        
        return self.update_product(
            product_id,
            update_data,
            strategy
        )
    
    def _apply_merge_strategy(self, current: Dict, update: Dict) -> Dict:
        """Merge objects and arrays instead of replacing."""
        result = current.copy()
        
        for key, value in update.items():
            if key in current:
                # Merge arrays
                if isinstance(current[key], list) and isinstance(value, list):
                    # Combine unique items
                    current_list = current[key]
                    update_list = value
                    merged = current_list + [item for item in update_list if item not in current_list]
                    result[key] = merged
                
                # Merge objects
                elif isinstance(current[key], dict) and isinstance(value, dict):
                    result[key] = {**current[key], **value}
                
                else:
                    result[key] = value
            else:
                result[key] = value
        
        return result
    
    def _apply_increment_strategy(self, current: Dict, update: Dict) -> Dict:
        """Increment numeric values."""
        result = {}
        
        for key, value in update.items():
            if key in current and isinstance(current[key], (int, float)) and isinstance(value, (int, float)):
                result[key] = current[key] + value
            else:
                result[key] = value
        
        return result
    
    def _check_conflicts(self, current: Dict, update: Dict) -> List[Dict]:
        """Check for update conflicts."""
        conflicts = []
        
        # Check for concurrent modifications
        # This would typically compare timestamps or versions
        if 'updated_at' in current and 'updated_at' in update:
            current_time = datetime.fromisoformat(current['updated_at'].replace('Z', '+00:00'))
            update_time = datetime.fromisoformat(update['updated_at'].replace('Z', '+00:00'))
            
            if update_time < current_time:
                conflicts.append({
                    'field': 'updated_at',
                    'message': 'Product has been modified since you loaded it',
                    'current': current['updated_at'],
                    'attempted': update['updated_at']
                })
        
        # Check for business logic conflicts
        if 'stock' in update and 'stock' in current:
            if update['stock'] < 0:
                conflicts.append({
                    'field': 'stock',
                    'message': 'Stock cannot be negative',
                    'current': current['stock'],
                    'attempted': update['stock']
                })
        
        if 'price' in update and 'original_price' in update:
            if update['original_price'] < update['price']:
                conflicts.append({
                    'field': 'original_price',
                    'message': 'Original price cannot be less than current price',
                    'price': update['price'],
                    'original_price': update['original_price']
                })
        
        return conflicts
    
    def _create_nested_update(self, field_path: str, value) -> Dict:
        """Create nested update structure from dot notation path."""
        result = {}
        current = result
        
        parts = field_path.split('.')
        
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                current[part] = value
            else:
                current[part] = {}
                current = current[part]
        
        return result
    
    def _create_rollback_data(self, original: Dict, update: Dict, strategy: UpdateStrategy) -> Dict:
        """Create data to rollback an update."""
        if strategy == UpdateStrategy.REPLACE:
            return original
        
        rollback_data = {}
        
        # Only rollback fields that were updated
        for key in update.keys():
            if key in original:
                rollback_data[key] = original[key]
        
        return rollback_data
    
    def _record_update(
        self,
        product_id: str,
        before: Dict,
        after: Dict,
        update_data: Dict,
        strategy: str,
        reason: str = ''
    ):
        """Record update for audit trail."""
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        record = {
            'timestamp': timestamp,
            'product_id': product_id,
            'before': before,
            'after': after,
            'update_data': update_data,
            'strategy': strategy,
            'reason': reason,
            'user': self._get_current_user()
        }
        
        if product_id not in self.update_history:
            self.update_history[product_id] = []
        
        self.update_history[product_id].append(record)
        
        # Keep only last 100 records per product
        if len(self.update_history[product_id]) > 100:
            self.update_history[product_id].pop(0)
    
    def _post_update_actions(self, product_id: str, before: Dict, after: Dict):
        """Execute actions after successful update."""
        
        # Reindex search if name or description changed
        if before.get('name') != after.get('name') or before.get('description') != after.get('description'):
            self._reindex_product(product_id)
        
        # Clear cache
        self._clear_product_cache(product_id)
        
        # Notify subscribers
        self._notify_product_update(product_id, before, after)
        
        # Log update
        self._log_update_event(product_id, before, after)
    
    def _reindex_product(self, product_id: str):
        """Reindex product in search engine."""
        # Implementation depends on search solution
        pass
    
    def _clear_product_cache(self, product_id: str):
        """Clear product from cache."""
        # Implementation depends on caching solution
        pass
    
    def _notify_product_update(self, product_id: str, before: Dict, after: Dict):
        """Notify other systems about product update."""
        # Send webhook or message queue notification
        pass
    
    def _log_update_event(self, product_id: str, before: Dict, after: Dict):
        """Log update event for analytics."""
        # Log to analytics service
        pass
    
    def _get_product(self, product_id: str) -> Dict:
        """Get product details."""
        response = self.session.get(f"{self.base_url}/products/{product_id}")
        response.raise_for_status()
        return response.json()
    
    def _generate_update_id(self) -> str:
        """Generate unique update ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _get_current_user(self) -> str:
        """Get current user identifier."""
        # Implementation depends on authentication system
        return "admin_user"
    
    def _handle_update_error(self, error: requests.exceptions.HTTPError, error_data: Dict):
        """Handle update errors appropriately."""
        status_code = error.response.status_code
        
        if status_code == 409:
            raise UpdateConflictError(
                error_data.get('detail', 'Conflict occurred'),
                error_data.get('conflicts', [])
            )
        elif status_code == 422:
            raise ValidationError(
                error_data.get('detail', 'Validation failed'),
                error_data.get('errors', [])
            )
        elif status_code == 404:
            raise ProductNotFoundError(f"Product not found: {error_data.get('detail', '')}")
        else:
            raise UpdateError(
                f"Update failed with status {status_code}: {error_data.get('detail', 'Unknown error')}"
            )

class UpdateError(Exception):
    pass

class UpdateConflictError(UpdateError):
    def __init__(self, message, conflicts=None):
        super().__init__(message)
        self.conflicts = conflicts or []

# Usage Example
def demonstrate_update_strategies():
    """Demonstrate different update strategies."""
    
    manager = ProductUpdateManager(
        base_url="http://localhost:8000/api",
        token="your_admin_token_here"
    )
    
    product_id = "prod_789"
    
    try:
        # Example 1: Simple partial update
        print("Example 1: Partial update")
        result1 = manager.update_product(
            product_id,
            {"price": 94.99, "stock": 200},
            UpdateStrategy.PARTIAL,
            {"reason": "Price increase and stock replenishment"}
        )
        print(f"Updated price to: {result1['price']}")
        print(f"Updated stock to: {result1['stock']}")
        
        # Example 2: Merge strategy for arrays
        print("\nExample 2: Merge tags")
        result2 = manager.update_product(
            product_id,
            {"tags": ["new_tag", "updated"]},
            UpdateStrategy.MERGE
        )
        print(f"Tags after merge: {result2['tags']}")
        
        # Example 3: Increment strategy
        print("\nExample 3: Increment stock")
        result3 = manager.update_product(
            product_id,
            {"stock": 50},  # Add 50 to current stock
            UpdateStrategy.INCREMENT
        )
        print(f"Stock after increment: {result3['stock']}")
        
        # Example 4: Update nested field
        print("\nExample 4: Update nested specifications")
        result4 = manager.update_product_field(
            product_id,
            "specifications.battery",
            "6000mAh"
        )
        print(f"Battery updated: {result4['specifications']['battery']}")
        
        # Example 5: Bulk update
        print("\nExample 5: Bulk update")
        bulk_updates = [
            {
                "product_id": "prod_789",
                "data": {"price": 99.99, "is_featured": True},
                "strategy": UpdateStrategy.PARTIAL
            },
            {
                "product_id": "prod_790",
                "data": {"stock": 100},
                "strategy": UpdateStrategy.PARTIAL
            }
        ]
        
        def progress_callback(processed, total):
            print(f"Progress: {processed}/{total}")
        
        bulk_result = manager.bulk_update_products(
            bulk_updates,
            batch_size=2,
            on_progress=progress_callback
        )
        
        print(f"Bulk update complete. Successful: {len(bulk_result['successful'])}, Failed: {len(bulk_result['failed'])}")
        
        # Example 6: Update with rollback safety
        print("\nExample 6: Safe update with rollback")
        try:
            result6 = manager.update_with_rollback(
                product_id,
                {"price": -10},  # Invalid price
                UpdateStrategy.PARTIAL
            )
        except UpdateError as e:
            print(f"Update failed as expected: {e}")
        
    except UpdateConflictError as e:
        print(f"Conflict error: {e}")
        for conflict in e.conflicts:
            print(f"  - {conflict['field']}: {conflict['message']}")
    except ValidationError as e:
        print(f"Validation error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    demonstrate_update_strategies()
```

### Best Practices for Product Updates

#### 1. **Atomic Updates**
```javascript
// Ensure related updates happen together
async function updateProductWithInventory(productId, priceUpdate, stockUpdate) {
  const updateData = {
    ...priceUpdate,
    ...stockUpdate,
    updated_at: new Date().toISOString()
  };
  
  // Single atomic update
  return updateProduct(productId, updateData);
}
```

#### 2. **Version Control**
```javascript
// Implement optimistic concurrency control
async function updateWithVersion(productId, updateData, currentVersion) {
  const response = await fetch(`/api/products/${productId}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'If-Match': currentVersion // ETag or version number
    },
    body: JSON.stringify(updateData)
  });
  
  if (response.status === 412) {
    throw new VersionConflictError('Product was modified by another user');
  }
  
  return response.json();
}
```

#### 3. **Change Notifications**
```javascript
// Notify relevant systems about updates
async function updateProductWithNotifications(productId, updateData) {
  const result = await updateProduct(productId, updateData);
  
  // Notify search index
  await reindexProduct(productId);
  
  // Invalidate cache
  await invalidateCache(`product:${productId}`);
  
  // Send webhook notifications
  await sendWebhook('product.updated', {
    productId,
    changes: updateData,
    timestamp: new Date().toISOString()
  });
  
  return result;
}
```

#### 4. **Audit Trail**
```javascript
// Maintain detailed audit log
function createAuditLog(productId, changes, userId) {
  return {
    id: generateId(),
    product_id: productId,
    user_id: userId,
    action: 'update',
    changes: changes,
    timestamp: new Date().toISOString(),
    ip_address: getClientIP(),
    user_agent: getUserAgent()
  };
}
```

### Error Recovery Patterns

```javascript
// Retry with exponential backoff for transient failures
async function updateWithRetry(productId, updateData, maxRetries = 3) {
  let lastError;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await updateProduct(productId, updateData);
    } catch (error) {
      lastError = error;
      
      // Don't retry on validation or conflict errors
      if ([400, 422, 409].includes(error.statusCode)) {
        throw error;
      }
      
      if (attempt < maxRetries) {
        const delay = Math.pow(2, attempt - 1) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  throw lastError;
}

// Fallback to queue for unreliable updates
async function updateWithFallback(productId, updateData) {
  try {
    return await updateProduct(productId, updateData);
  } catch (error) {
    if (isTransientError(error)) {
      // Queue for later retry
      await queueProductUpdate(productId, updateData);
      return { queued: true, message: 'Update queued for retry' };
    }
    throw error;
  }
}
```

---

## Related Endpoints
- [PUT /products/{productId}](../products/update-product.md#put-method) - Full product replacement
- [PATCH /products/{productId}/inventory](../products/inventory.md) - Update inventory only
- [GET /products/{productId}/changes](../../endpoints/product-changes.md) - Get change history
- [POST /products](../products/create-product.md) - Create new product
- [Error Responses](../../errors.md) - Error handling details

## Notes
- PATCH is idempotent but not necessarily safe
- Use ETags or Last-Modified headers for optimistic concurrency
- Consider implementing field-level permissions for updates
- Track update reasons for audit purposes
- Implement rate limiting for frequent updates
- Consider batch operations for mass updates

## Security Considerations
- Validate all input fields to prevent injection
- Implement proper authorization checks
- Sanitize HTML in descriptions
- Validate image URLs to prevent SSRF
- Implement CSRF protection for web interfaces
- Log all update attempts for security monitoring

## Performance Optimization
- Use selective field updates to minimize data transfer
- Implement caching strategies for frequently updated products
- Use batch updates for multiple product changes
- Consider asynchronous updates for non-critical changes
- Implement change data capture for synchronization