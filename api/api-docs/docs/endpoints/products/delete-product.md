# DELETE /products/{productId}

**Delete Product** - Remove a product from the catalog (Admin Only)

**Tags:** Products

**Authentication:** Required (Bearer Token with Admin privileges)

---

## Description
Permanently delete a product from the catalog. This operation is irreversible and will remove all product data, including images, inventory information, and metadata. Consider using soft deletion (deactivation) instead if you need to preserve data for reporting or recovery purposes.

## Authentication
**Required:** Bearer Token with Admin role

### Headers
```
Authorization: Bearer <access_token>
```

## Request

### URL Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `productId` | string | ✓ | Unique product identifier | `prod_1` |

## Responses

### 204 No Content - Product successfully deleted
**Response Body:** None

**Description:** Product has been permanently deleted. No content is returned.

### 400 Bad Request - Invalid request
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/bad-request",
  "title": "Bad Request",
  "status": 400,
  "detail": "Product cannot be deleted because it has active orders.",
  "instance": "/products/prod_789"
}
```

**Common Business Logic Errors:**
- Product has active orders
- Product is part of a bundle
- Product has dependent variants
- Product is referenced by other resources

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
  "detail": "Insufficient permissions to delete products.",
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
  "detail": "Product with ID 'prod_999' not found or already deleted.",
  "instance": "/products/prod_999"
}
```

### 409 Conflict - Cannot delete due to constraints
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/conflict",
  "title": "Conflict",
  "status": 409,
  "detail": "Product is currently featured and cannot be deleted. Please unfeature first.",
  "instance": "/products/prod_789",
  "constraints": [
    {
      "type": "featured_product",
      "message": "Product is featured on homepage",
      "action_required": "Unfeature product before deletion"
    }
  ]
}
```

### 423 Locked - Resource locked
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/locked",
  "title": "Locked",
  "status": 423,
  "detail": "Product is currently being processed by another operation.",
  "instance": "/products/prod_789",
  "retry_after": 30
}
```

### 500 Internal Server Error
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/internal",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "Failed to delete product due to database constraint.",
  "instance": "/products/prod_789"
}
```

## Examples

### Basic cURL Request
```bash
# Delete a product
curl -X DELETE "http://localhost:8000/api/products/prod_789" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### With Confirmation Header
```bash
# Delete with explicit confirmation
curl -X DELETE "http://localhost:8000/api/products/prod_789" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Confirm-Deletion: true"
```

### JavaScript (Fetch) with Comprehensive Error Handling
```javascript
/**
 * Advanced product deletion service with safety checks and recovery options
 */
class ProductDeleter {
  constructor(apiUrl = 'http://localhost:8000/api') {
    this.apiUrl = apiUrl;
    this.deletionQueue = new Map();
    this.recycleBin = new Map();
  }
  
  /**
   * Delete a product with comprehensive safety checks
   */
  async deleteProduct(productId, accessToken, options = {}) {
    const {
      force = false,
      softDelete = false,
      archive = true,
      reason = '',
      confirm = true
    } = options;
    
    // Safety checks
    if (!confirm && !force) {
      throw new SafetyError('Deletion requires confirmation');
    }
    
    // Validate product ID
    if (!this.isValidProductId(productId)) {
      throw new ValidationError('Invalid product ID format');
    }
    
    // Check if already queued for deletion
    if (this.deletionQueue.has(productId)) {
      throw new DeletionError('Product is already queued for deletion');
    }
    
    // Add to deletion queue
    const deletionId = this.addToDeletionQueue(productId, options);
    
    try {
      // Pre-deletion checks (optional)
      if (!force) {
        await this.performPreDeletionChecks(productId, accessToken);
      }
      
      // Archive product data if requested
      let archivedData = null;
      if (archive) {
        archivedData = await this.archiveProduct(productId, accessToken);
      }
      
      // Perform deletion
      let result;
      if (softDelete) {
        result = await this.softDeleteProduct(productId, accessToken, reason);
      } else {
        result = await this.hardDeleteProduct(productId, accessToken, force);
      }
      
      // Record deletion
      this.recordDeletion(productId, {
        method: softDelete ? 'soft' : 'hard',
        archived: !!archivedData,
        reason,
        timestamp: new Date().toISOString(),
        user: this.getCurrentUser()
      });
      
      // Clean up related resources
      if (!softDelete) {
        await this.cleanupRelatedResources(productId, accessToken);
      }
      
      // Fire deletion events
      this.triggerDeletionEvents(productId, softDelete, reason);
      
      return {
        success: true,
        productId,
        method: softDelete ? 'soft' : 'hard',
        archived: !!archivedData,
        timestamp: new Date().toISOString()
      };
      
    } catch (error) {
      // Handle specific error cases
      if (error.status === 409) {
        throw new ConstraintError(
          error.message || 'Deletion constraint violation',
          error.constraints || []
        );
      } else if (error.status === 423) {
        const retryAfter = error.retry_after || 30;
        throw new ResourceLockedError(
          `Resource locked, retry after ${retryAfter} seconds`,
          retryAfter
        );
      } else if (error.status === 404 && force) {
        // Product might already be deleted - treat as success
        return {
          success: true,
          productId,
          alreadyDeleted: true,
          timestamp: new Date().toISOString()
        };
      } else {
        throw new DeletionError(
          `Failed to delete product: ${error.message}`,
          error.status,
          error
        );
      }
    } finally {
      // Remove from deletion queue
      this.deletionQueue.delete(productId);
    }
  }
  
  /**
   * Soft delete (deactivate) product
   */
  async softDeleteProduct(productId, accessToken, reason = '') {
    try {
      const response = await fetch(`${this.apiUrl}/products/${productId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
          'X-Deletion-Reason': reason
        },
        body: JSON.stringify({
          is_active: false,
          deleted_at: new Date().toISOString(),
          deletion_reason: reason
        })
      });
      
      if (!response.ok) {
        const errorData = await this.parseError(response);
        throw errorData;
      }
      
      const product = await response.json();
      
      // Add to recycle bin
      this.recycleBin.set(productId, {
        data: product,
        deletedAt: new Date(),
        reason,
        softDelete: true
      });
      
      return product;
      
    } catch (error) {
      throw new DeletionError(`Soft delete failed: ${error.message}`, error.status, error);
    }
  }
  
  /**
   * Hard delete (permanent) product
   */
  async hardDeleteProduct(productId, accessToken, force = false) {
    const headers = {
      'Authorization': `Bearer ${accessToken}`
    };
    
    if (force) {
      headers['X-Force-Delete'] = 'true';
    }
    
    // Add confirmation header for destructive operations
    headers['X-Confirm-Deletion'] = 'true';
    
    try {
      const response = await fetch(`${this.apiUrl}/products/${productId}`, {
        method: 'DELETE',
        headers
      });
      
      if (!response.ok) {
        const errorData = await this.parseError(response);
        throw errorData;
      }
      
      // Success - product is permanently deleted
      return null;
      
    } catch (error) {
      throw new DeletionError(`Hard delete failed: ${error.message}`, error.status, error);
    }
  }
  
  /**
   * Batch delete multiple products
   */
  async batchDelete(productIds, accessToken, options = {}) {
    const {
      parallel = false,
      onProgress = null,
      stopOnError = false
    } = options;
    
    const results = {
      successful: [],
      failed: [],
      total: productIds.length
    };
    
    if (parallel) {
      // Parallel deletion with concurrency control
      const batchSize = options.batchSize || 3;
      
      for (let i = 0; i < productIds.length; i += batchSize) {
        const batch = productIds.slice(i, i + batchSize);
        const batchPromises = batch.map(productId =>
          this.deleteProduct(productId, accessToken, options)
            .then(result => ({ success: true, productId, result }))
            .catch(error => ({ success: false, productId, error }))
        );
        
        const batchResults = await Promise.all(batchPromises);
        
        batchResults.forEach(result => {
          if (result.success) {
            results.successful.push({
              productId: result.productId,
              result: result.result
            });
          } else {
            results.failed.push({
              productId: result.productId,
              error: result.error
            });
            
            if (stopOnError) {
              throw new BatchDeletionError('Batch deletion stopped due to error', results);
            }
          }
          
          // Progress callback
          if (onProgress) {
            const processed = results.successful.length + results.failed.length;
            onProgress(processed, productIds.length);
          }
        });
      }
    } else {
      // Sequential deletion
      for (let i = 0; i < productIds.length; i++) {
        const productId = productIds[i];
        
        try {
          const result = await this.deleteProduct(productId, accessToken, options);
          results.successful.push({ productId, result });
        } catch (error) {
          results.failed.push({ productId, error });
          
          if (stopOnError) {
            throw new BatchDeletionError('Batch deletion stopped due to error', results);
          }
        }
        
        // Progress callback
        if (onProgress) {
          onProgress(i + 1, productIds.length);
        }
      }
    }
    
    return results;
  }
  
  /**
   * Restore soft-deleted product
   */
  async restoreProduct(productId, accessToken) {
    if (!this.recycleBin.has(productId)) {
      throw new NotFoundError('Product not found in recycle bin');
    }
    
    const deletedProduct = this.recycleBin.get(productId);
    
    if (!deletedProduct.softDelete) {
      throw new DeletionError('Cannot restore hard-deleted product');
    }
    
    try {
      const response = await fetch(`${this.apiUrl}/products/${productId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          is_active: true,
          deleted_at: null,
          deletion_reason: null
        })
      });
      
      if (!response.ok) {
        throw new Error(`Restore failed: ${response.status}`);
      }
      
      const restoredProduct = await response.json();
      
      // Remove from recycle bin
      this.recycleBin.delete(productId);
      
      // Fire restoration event
      this.triggerRestorationEvent(productId);
      
      return {
        success: true,
        product: restoredProduct,
        restoredFrom: deletedProduct.deletedAt
      };
      
    } catch (error) {
      throw new RestorationError(`Failed to restore product: ${error.message}`);
    }
  }
  
  /**
   * Check if product can be deleted
   */
  async checkDeletionConstraints(productId, accessToken) {
    const constraints = [];
    
    try {
      // Check for active orders
      const hasActiveOrders = await this.hasActiveOrders(productId, accessToken);
      if (hasActiveOrders) {
        constraints.push({
          type: 'active_orders',
          message: 'Product has active orders',
          severity: 'high',
          action: 'Cancel or fulfill orders first'
        });
      }
      
      // Check if featured
      const isFeatured = await this.isProductFeatured(productId, accessToken);
      if (isFeatured) {
        constraints.push({
          type: 'featured',
          message: 'Product is currently featured',
          severity: 'medium',
          action: 'Unfeature product before deletion'
        });
      }
      
      // Check for dependent variants
      const hasVariants = await this.hasDependentVariants(productId, accessToken);
      if (hasVariants) {
        constraints.push({
          type: 'variants',
          message: 'Product has dependent variants',
          severity: 'high',
          action: 'Delete variants first or use cascade delete'
        });
      }
      
      // Check for cart references
      const inActiveCarts = await this.isInActiveCarts(productId, accessToken);
      if (inActiveCarts) {
        constraints.push({
          type: 'active_carts',
          message: 'Product is in active shopping carts',
          severity: 'low',
          action: 'Consider soft delete or notify customers'
        });
      }
      
      return {
        canDelete: constraints.length === 0,
        constraints,
        productId
      };
      
    } catch (error) {
      throw new ConstraintCheckError(`Failed to check constraints: ${error.message}`);
    }
  }
  
  /**
   * Archive product data before deletion
   */
  async archiveProduct(productId, accessToken) {
    try {
      // Fetch full product data
      const product = await this.fetchProduct(productId, accessToken);
      
      // Fetch related data
      const images = await this.fetchProductImages(productId, accessToken);
      const inventoryHistory = await this.fetchInventoryHistory(productId, accessToken);
      const salesData = await this.fetchSalesData(productId, accessToken);
      
      const archive = {
        product,
        images,
        inventoryHistory,
        salesData,
        archivedAt: new Date().toISOString(),
        archivedBy: this.getCurrentUser()
      };
      
      // Store archive (in production, save to database or cold storage)
      const archiveId = `archive_${productId}_${Date.now()}`;
      localStorage.setItem(archiveId, JSON.stringify(archive));
      
      // Set expiration (e.g., 30 days)
      setTimeout(() => {
        localStorage.removeItem(archiveId);
      }, 30 * 24 * 60 * 60 * 1000);
      
      return {
        archiveId,
        size: JSON.stringify(archive).length,
        timestamp: new Date().toISOString()
      };
      
    } catch (error) {
      console.warn(`Failed to archive product ${productId}:`, error);
      return null;
    }
  }
  
  /**
   * Clean up related resources after deletion
   */
  async cleanupRelatedResources(productId, accessToken) {
    const cleanupTasks = [
      // Delete product images
      this.deleteProductImages(productId, accessToken),
      
      // Remove from search index
      this.removeFromSearchIndex(productId),
      
      // Invalidate cache
      this.invalidateProductCache(productId),
      
      // Remove from recommendation engine
      this.removeFromRecommendations(productId),
      
      // Clean up temporary files
      this.cleanupTempFiles(productId)
    ];
    
    // Execute cleanup in parallel, ignoring failures
    await Promise.allSettled(cleanupTasks);
  }
  
  /**
   * Helper methods
   */
  async fetchProduct(productId, accessToken) {
    const response = await fetch(`${this.apiUrl}/products/${productId}`, {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    });
    
    if (!response.ok) throw new Error(`Failed to fetch product: ${response.status}`);
    return response.json();
  }
  
  async fetchProductImages(productId, accessToken) {
    // Implementation depends on your image API
    return [];
  }
  
  async fetchInventoryHistory(productId, accessToken) {
    // Implementation depends on your inventory API
    return [];
  }
  
  async fetchSalesData(productId, accessToken) {
    // Implementation depends on your sales API
    return [];
  }
  
  async hasActiveOrders(productId, accessToken) {
    // Check if product has active/unfulfilled orders
    return false;
  }
  
  async isProductFeatured(productId, accessToken) {
    const product = await this.fetchProduct(productId, accessToken);
    return product.is_featured || false;
  }
  
  async hasDependentVariants(productId, accessToken) {
    // Check if product has variants
    return false;
  }
  
  async isInActiveCarts(productId, accessToken) {
    // Check if product is in active shopping carts
    return false;
  }
  
  async deleteProductImages(productId, accessToken) {
    // Delete all images associated with product
    try {
      const response = await fetch(`${this.apiUrl}/files?productId=${productId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${accessToken}` }
      });
      return response.ok;
    } catch (error) {
      console.warn(`Failed to delete images for ${productId}:`, error);
      return false;
    }
  }
  
  removeFromSearchIndex(productId) {
    // Remove from search index
    console.log(`Removed ${productId} from search index`);
    return Promise.resolve();
  }
  
  invalidateProductCache(productId) {
    // Invalidate cache entries
    console.log(`Invalidated cache for ${productId}`);
    return Promise.resolve();
  }
  
  removeFromRecommendations(productId) {
    // Remove from recommendation engine
    console.log(`Removed ${productId} from recommendations`);
    return Promise.resolve();
  }
  
  cleanupTempFiles(productId) {
    // Clean up temporary files
    console.log(`Cleaned up temp files for ${productId}`);
    return Promise.resolve();
  }
  
  addToDeletionQueue(productId, options) {
    const queueId = `del_${productId}_${Date.now()}`;
    this.deletionQueue.set(productId, {
      id: queueId,
      productId,
      options,
      queuedAt: new Date(),
      status: 'pending'
    });
    return queueId;
  }
  
  recordDeletion(productId, metadata) {
    const deletions = JSON.parse(localStorage.getItem('product_deletions') || '[]');
    deletions.push({
      productId,
      ...metadata,
      recordedAt: new Date().toISOString()
    });
    
    // Keep only last 100 deletions
    if (deletions.length > 100) {
      deletions.shift();
    }
    
    localStorage.setItem('product_deletions', JSON.stringify(deletions));
  }
  
  triggerDeletionEvents(productId, softDelete, reason) {
    // Dispatch custom event
    const event = new CustomEvent('productDeleted', {
      detail: {
        productId,
        softDelete,
        reason,
        timestamp: new Date().toISOString(),
        user: this.getCurrentUser()
      }
    });
    
    window.dispatchEvent(event);
    
    // Send analytics
    if (window.gtag) {
      window.gtag('event', softDelete ? 'soft_delete_product' : 'delete_product', {
        product_id: productId,
        deletion_reason: reason
      });
    }
  }
  
  triggerRestorationEvent(productId) {
    const event = new CustomEvent('productRestored', {
      detail: {
        productId,
        timestamp: new Date().toISOString()
      }
    });
    
    window.dispatchEvent(event);
  }
  
  isValidProductId(productId) {
    return productId && typeof productId === 'string' && productId.startsWith('prod_');
  }
  
  getCurrentUser() {
    // Get current user from your auth system
    return localStorage.getItem('userId') || 'admin';
  }
  
  async parseError(response) {
    const contentType = response.headers.get('content-type');
    
    if (contentType && contentType.includes('application/problem+json')) {
      const errorData = await response.json();
      return {
        message: errorData.detail || errorData.title,
        status: response.status,
        ...errorData
      };
    } else {
      return {
        message: response.statusText,
        status: response.status
      };
    }
  }
  
  async performPreDeletionChecks(productId, accessToken) {
    // Optional pre-deletion checks
    const constraints = await this.checkDeletionConstraints(productId, accessToken);
    
    if (!constraints.canDelete) {
      throw new ConstraintError(
        'Product deletion constraints violated',
        constraints.constraints
      );
    }
    
    return constraints;
  }
}

// Custom Error Classes
class SafetyError extends Error {
  constructor(message) {
    super(message);
    this.name = 'SafetyError';
  }
}

class ValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ValidationError';
  }
}

class DeletionError extends Error {
  constructor(message, statusCode = null, originalError = null) {
    super(message);
    this.name = 'DeletionError';
    this.status = statusCode;
    this.originalError = originalError;
  }
}

class ConstraintError extends Error {
  constructor(message, constraints = []) {
    super(message);
    this.name = 'ConstraintError';
    this.constraints = constraints;
  }
}

class ResourceLockedError extends Error {
  constructor(message, retryAfter = 30) {
    super(message);
    this.name = 'ResourceLockedError';
    this.retry_after = retryAfter;
  }
}

class ConstraintCheckError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ConstraintCheckError';
  }
}

class BatchDeletionError extends Error {
  constructor(message, results = null) {
    super(message);
    this.name = 'BatchDeletionError';
    this.results = results;
  }
}

class NotFoundError extends Error {
  constructor(message) {
    super(message);
    this.name = 'NotFoundError';
  }
}

class RestorationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'RestorationError';
  }
}

// Usage Examples
async function demonstrateDeletionScenarios() {
  const deleter = new ProductDeleter();
  const accessToken = localStorage.getItem('accessToken');
  const productId = 'prod_789';
  
  try {
    // Example 1: Check constraints before deletion
    console.log('Example 1: Checking deletion constraints...');
    const constraints = await deleter.checkDeletionConstraints(productId, accessToken);
    
    if (!constraints.canDelete) {
      console.warn('Cannot delete product due to constraints:');
      constraints.constraints.forEach(c => {
        console.log(`  - ${c.message} (${c.severity}): ${c.action}`);
      });
      return;
    }
    
    // Example 2: Soft delete (deactivate)
    console.log('\nExample 2: Soft deleting product...');
    const softResult = await deleter.deleteProduct(productId, accessToken, {
      softDelete: true,
      reason: 'Seasonal product removal',
      confirm: true,
      archive: true
    });
    
    console.log('Soft delete result:', softResult);
    
    // Example 3: Restore soft-deleted product
    console.log('\nExample 3: Restoring product...');
    const restoreResult = await deleter.restoreProduct(productId, accessToken);
    console.log('Restore result:', restoreResult);
    
    // Example 4: Hard delete (permanent)
    console.log('\nExample 4: Hard deleting product...');
    const hardResult = await deleter.deleteProduct(productId, accessToken, {
      softDelete: false,
      reason: 'Discontinued product',
      confirm: true,
      archive: true,
      force: false
    });
    
    console.log('Hard delete result:', hardResult);
    
    // Example 5: Batch delete
    console.log('\nExample 5: Batch deleting products...');
    const batchResult = await deleter.batchDelete(
      ['prod_790', 'prod_791', 'prod_792'],
      accessToken,
      {
        softDelete: true,
        parallel: true,
        batchSize: 2,
        onProgress: (processed, total) => {
          console.log(`Progress: ${processed}/${total}`);
        }
      }
    );
    
    console.log('Batch delete complete:', {
      successful: batchResult.successful.length,
      failed: batchResult.failed.length
    });
    
  } catch (error) {
    console.error('Deletion error:', error);
    
    if (error instanceof ConstraintError) {
      console.error('Constraints violated:');
      error.constraints.forEach(c => console.error(`  - ${c.message}`));
    } else if (error instanceof ResourceLockedError) {
      console.error(`Resource locked, retry after ${error.retry_after} seconds`);
    }
  }
}
```

### React Admin Component with Confirmation Dialog
```jsx
import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import ConfirmationDialog from './ConfirmationDialog';
import ConstraintChecker from './ConstraintChecker';

function DeleteProductPage() {
  const { productId } = useParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [constraints, setConstraints] = useState(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [deletionType, setDeletionType] = useState('soft'); // 'soft' or 'hard'
  const [deletionReason, setDeletionReason] = useState('');
  const [archiveData, setArchiveData] = useState(true);
  
  // Load deletion constraints
  const loadConstraints = async () => {
    try {
      const accessToken = localStorage.getItem('accessToken');
      const response = await fetch(
        `${apiUrl}/products/${productId}/deletion-constraints`,
        {
          headers: { 'Authorization': `Bearer ${accessToken}` }
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setConstraints(data);
      }
    } catch (err) {
      console.error('Failed to load constraints:', err);
    }
  };
  
  // Handle deletion
  const handleDelete = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const accessToken = localStorage.getItem('accessToken');
      
      const options = {
        method: deletionType === 'soft' ? 'PATCH' : 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
          'X-Delete-Reason': deletionReason,
          'X-Archive-Data': archiveData.toString()
        }
      };
      
      if (deletionType === 'soft') {
        options.body = JSON.stringify({
          is_active: false,
          deleted_at: new Date().toISOString(),
          deletion_reason: deletionReason
        });
      }
      
      const response = await fetch(
        `${apiUrl}/products/${productId}`,
        options
      );
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Deletion failed');
      }
      
      // Success - navigate away
      navigate('/admin/products', {
        state: {
          message: `Product ${deletionType === 'soft' ? 'deactivated' : 'deleted'} successfully`,
          severity: 'success'
        }
      });
      
    } catch (err) {
      setError(err.message);
      console.error('Deletion error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleBulkDelete = async (productIds) => {
    setLoading(true);
    
    try {
      const accessToken = localStorage.getItem('accessToken');
      
      const response = await fetch(`${apiUrl}/products/bulk-delete`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          product_ids: productIds,
          deletion_type: deletionType,
          reason: deletionReason,
          archive: archiveData
        })
      });
      
      if (!response.ok) {
        throw new Error('Bulk deletion failed');
      }
      
      const result = await response.json();
      
      navigate('/admin/products', {
        state: {
          message: `Deleted ${result.successful} products successfully`,
          failed: result.failed,
          severity: 'success'
        }
      });
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="delete-product-page">
      <div className="page-header">
        <h1>Delete Product</h1>
        <button 
          className="btn-back"
          onClick={() => navigate(`/admin/products/${productId}`)}
        >
          Cancel
        </button>
      </div>
      
      {/* Constraint Checker */}
      <ConstraintChecker
        productId={productId}
        onConstraintsLoaded={setConstraints}
      />
      
      {constraints && !constraints.canDelete && (
        <div className="constraint-warning">
          <h3>⚠️ Cannot Delete Product</h3>
          <ul>
            {constraints.constraints.map((c, idx) => (
              <li key={idx}>
                <strong>{c.message}</strong> - {c.action}
              </li>
            ))}
          </ul>
          <button
            className="btn-resolve"
            onClick={() => navigate(`/admin/products/${productId}/resolve-constraints`)}
          >
            Resolve Constraints
          </button>
        </div>
      )}
      
      {/* Deletion Options */}
      <div className="deletion-options">
        <h2>Deletion Options</h2>
        
        <div className="option-group">
          <label>
            <input
              type="radio"
              value="soft"
              checked={deletionType === 'soft'}
              onChange={(e) => setDeletionType(e.target.value)}
            />
            <div className="option-content">
              <h3>Soft Delete (Deactivate)</h3>
              <p>Product will be hidden but data preserved. Can be restored later.</p>
              <ul>
                <li>✅ Preserves historical data</li>
                <li>✅ Can be restored</li>
                <li>✅ Maintains order history</li>
                <li>❌ Still uses storage</li>
              </ul>
            </div>
          </label>
          
          <label>
            <input
              type="radio"
              value="hard"
              checked={deletionType === 'hard'}
              onChange={(e) => setDeletionType(e.target.value)}
            />
            <div className="option-content">
              <h3>Hard Delete (Permanent)</h3>
              <p>Product and all associated data will be permanently removed.</p>
              <ul>
                <li>✅ Frees up storage</li>
                <li>✅ Complete removal</li>
                <li>❌ Cannot be undone</li>
                <li>❌ Loss of historical data</li>
              </ul>
            </div>
          </label>
        </div>
        
        <div className="deletion-reason">
          <label htmlFor="reason">Reason for deletion:</label>
          <textarea
            id="reason"
            value={deletionReason}
            onChange={(e) => setDeletionReason(e.target.value)}
            placeholder="Enter reason for deletion (required for audit trail)..."
            rows={3}
            required
          />
        </div>
        
        <div className="archive-option">
          <label>
            <input
              type="checkbox"
              checked={archiveData}
              onChange={(e) => setArchiveData(e.target.checked)}
            />
            Archive product data before deletion
            <span className="hint">(Recommended for compliance and recovery)</span>
          </label>
        </div>
        
        <div className="action-buttons">
          <button
            className="btn-delete"
            onClick={() => setShowConfirm(true)}
            disabled={loading || (constraints && !constraints.canDelete)}
          >
            {loading ? 'Processing...' : `Confirm ${deletionType} Delete`}
          </button>
          
          <button
            className="btn-cancel"
            onClick={() => navigate(`/admin/products/${productId}`)}
          >
            Cancel
          </button>
        </div>
      </div>
      
      {/* Confirmation Dialog */}
      {showConfirm && (
        <ConfirmationDialog
          title={`Confirm ${deletionType === 'soft' ? 'Deactivation' : 'Permanent Deletion'}`}
          message={
            deletionType === 'soft' 
              ? `Are you sure you want to deactivate this product? It will be hidden from customers but can be restored later.`
              : `⚠️ WARNING: This will permanently delete the product and all associated data. This action cannot be undone.`
          }
          severity={deletionType === 'hard' ? 'danger' : 'warning'}
          onConfirm={handleDelete}
          onCancel={() => setShowConfirm(false)}
          confirmText={deletionType === 'soft' ? 'Deactivate' : 'Delete Permanently'}
          cancelText="Cancel"
          requireTypeConfirm={deletionType === 'hard'}
          typeConfirmText="DELETE"
        />
      )}
      
      {/* Error Display */}
      {error && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
        </div>
      )}
    </div>
  );
}

export default DeleteProductPage;
```

### Python with Advanced Deletion Patterns
```python
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import asyncio
from contextlib import asynccontextmanager

class DeletionStrategy(Enum):
    """Strategies for product deletion."""
    SOFT = "soft"      # Deactivate only
    HARD = "hard"      # Permanent deletion
    ARCHIVE = "archive" # Archive then delete
    CASCADE = "cascade" # Delete with dependencies

class ProductDeletionManager:
    """Advanced product deletion management with multiple strategies."""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        })
        self.deletion_log = []
        self.recycle_bin = {}
    
    def delete_product(
        self,
        product_id: str,
        strategy: DeletionStrategy = DeletionStrategy.SOFT,
        reason: str = "",
        options: Optional[Dict] = None
    ) -> Dict:
        """
        Delete product using specified strategy.
        
        Args:
            product_id: Product identifier
            strategy: Deletion strategy
            reason: Reason for deletion
            options: Additional options
            
        Returns:
            Deletion result
        """
        options = options or {}
        
        # Validate input
        self._validate_deletion_request(product_id, strategy, reason)
        
        # Check constraints if not forced
        if not options.get('force', False):
            constraints = self.check_deletion_constraints(product_id)
            if not constraints['can_delete']:
                raise DeletionConstraintError(
                    "Product deletion constraints violated",
                    constraints['constraints']
                )
        
        # Archive before deletion if requested
        archive_result = None
        if options.get('archive', True) and strategy != DeletionStrategy.SOFT:
            archive_result = self._archive_product(product_id)
        
        # Execute deletion based on strategy
        result = None
        
        if strategy == DeletionStrategy.SOFT:
            result = self._soft_delete(product_id, reason)
        elif strategy == DeletionStrategy.HARD:
            result = self._hard_delete(product_id, reason, options.get('force', False))
        elif strategy == DeletionStrategy.ARCHIVE:
            result = self._archive_and_delete(product_id, reason)
        elif strategy == DeletionStrategy.CASCADE:
            result = self._cascade_delete(product_id, reason)
        
        # Log deletion
        self._log_deletion(
            product_id=product_id,
            strategy=strategy.value,
            reason=reason,
            archived=archive_result is not None,
            user=options.get('user', 'system')
        )
        
        # Clean up resources
        if strategy != DeletionStrategy.SOFT:
            self._cleanup_resources(product_id)
        
        return {
            'success': True,
            'product_id': product_id,
            'strategy': strategy.value,
            'archived': archive_result is not None,
            'archive_id': archive_result.get('id') if archive_result else None,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    def batch_delete(
        self,
        product_ids: List[str],
        strategy: DeletionStrategy = DeletionStrategy.SOFT,
        reason: str = "",
        batch_size: int = 10,
        parallel: bool = True
    ) -> Dict:
        """
        Delete multiple products.
        
        Args:
            product_ids: List of product IDs
            strategy: Deletion strategy
            reason: Reason for deletion
            batch_size: Size of processing batches
            parallel: Whether to process in parallel
            
        Returns:
            Batch deletion results
        """
        results = {
            'total': len(product_ids),
            'successful': [],
            'failed': [],
            'started_at': datetime.utcnow().isoformat()
        }
        
        if parallel:
            # Process in parallel batches
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
                future_to_id = {
                    executor.submit(
                        self._safe_delete,
                        pid,
                        strategy,
                        reason
                    ): pid for pid in product_ids
                }
                
                for future in concurrent.futures.as_completed(future_to_id):
                    pid = future_to_id[future]
                    try:
                        result = future.result()
                        results['successful'].append({
                            'product_id': pid,
                            'result': result
                        })
                    except Exception as e:
                        results['failed'].append({
                            'product_id': pid,
                            'error': str(e)
                        })
        else:
            # Process sequentially
            for pid in product_ids:
                try:
                    result = self._safe_delete(pid, strategy, reason)
                    results['successful'].append({
                        'product_id': pid,
                        'result': result
                    })
                except Exception as e:
                    results['failed'].append({
                        'product_id': pid,
                        'error': str(e)
                    })
        
        results['completed_at'] = datetime.utcnow().isoformat()
        results['duration_seconds'] = (
            datetime.fromisoformat(results['completed_at'].replace('Z', '+00:00')) -
            datetime.fromisoformat(results['started_at'].replace('Z', '+00:00'))
        ).total_seconds()
        
        return results
    
    def check_deletion_constraints(self, product_id: str) -> Dict:
        """
        Check if product can be deleted.
        
        Args:
            product_id: Product identifier
            
        Returns:
            Constraint check results
        """
        constraints = []
        
        try:
            # Get product details
            product = self._get_product(product_id)
            
            # Check for active orders
            if self._has_active_orders(product_id):
                constraints.append({
                    'type': 'active_orders',
                    'message': 'Product has active orders',
                    'severity': 'high'
                })
            
            # Check if featured
            if product.get('is_featured', False):
                constraints.append({
                    'type': 'featured',
                    'message': 'Product is currently featured',
                    'severity': 'medium'
                })
            
            # Check inventory
            if product.get('stock', 0) > 0:
                constraints.append({
                    'type': 'inventory',
                    'message': f'Product has {product["stock"]} units in stock',
                    'severity': 'medium'
                })
            
            # Check variants
            if product.get('has_variants', False):
                constraints.append({
                    'type': 'variants',
                    'message': 'Product has dependent variants',
                    'severity': 'high'
                })
            
            # Check bundles
            if self._is_in_bundles(product_id):
                constraints.append({
                    'type': 'bundles',
                    'message': 'Product is part of product bundles',
                    'severity': 'high'
                })
            
            return {
                'can_delete': len(constraints) == 0,
                'constraints': constraints,
                'product_id': product_id,
                'checked_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'can_delete': False,
                'constraints': [{
                    'type': 'check_failed',
                    'message': f'Failed to check constraints: {str(e)}',
                    'severity': 'high'
                }],
                'product_id': product_id
            }
    
    def restore_product(self, product_id: str) -> Dict:
        """
        Restore a soft-deleted product.
        
        Args:
            product_id: Product identifier
            
        Returns:
            Restoration result
        """
        # Check if in recycle bin
        if product_id not in self.recycle_bin:
            raise NotFoundError(f"Product {product_id} not found in recycle bin")
        
        deletion_record = self.recycle_bin[product_id]
        
        if deletion_record['strategy'] != 'soft':
            raise RestorationError(
                f"Cannot restore product deleted with strategy: {deletion_record['strategy']}"
            )
        
        try:
            # Restore product
            response = self.session.patch(
                f"{self.base_url}/products/{product_id}",
                json={
                    'is_active': True,
                    'deleted_at': None,
                    'deletion_reason': None
                }
            )
            response.raise_for_status()
            
            restored_product = response.json()
            
            # Remove from recycle bin
            del self.recycle_bin[product_id]
            
            # Log restoration
            self._log_restoration(product_id, deletion_record)
            
            return {
                'success': True,
                'product': restored_product,
                'restored_from': deletion_record['deleted_at'],
                'restored_at': datetime.utcnow().isoformat()
            }
            
        except requests.exceptions.HTTPError as e:
            raise RestorationError(f"Failed to restore product: {e}")
    
    def get_deletion_history(
        self,
        product_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get deletion history with filtering.
        
        Args:
            product_id: Filter by product ID
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of records
            
        Returns:
            Deletion history
        """
        filtered = self.deletion_log
        
        if product_id:
            filtered = [log for log in filtered if log['product_id'] == product_id]
        
        if start_date:
            filtered = [
                log for log in filtered 
                if datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) >= start_date
            ]
        
        if end_date:
            filtered = [
                log for log in filtered 
                if datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) <= end_date
            ]
        
        # Sort by timestamp descending
        filtered.sort(
            key=lambda x: datetime.fromisoformat(x['timestamp'].replace('Z', '+00:00')),
            reverse=True
        )
        
        return filtered[:limit]
    
    def cleanup_expired_archives(self, expiration_days: int = 30):
        """
        Clean up archives older than specified days.
        
        Args:
            expiration_days: Days before archive expiration
        """
        cutoff = datetime.utcnow() - timedelta(days=expiration_days)
        
        expired = [
            log for log in self.deletion_log
            if log.get('archived', False) and
            datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) < cutoff
        ]
        
        for log in expired:
            if log.get('archive_id'):
                self._delete_archive(log['archive_id'])
                log['archive_cleaned'] = True
                log['archive_cleaned_at'] = datetime.utcnow().isoformat()
    
    # Private implementation methods
    def _safe_delete(
        self,
        product_id: str,
        strategy: DeletionStrategy,
        reason: str
    ) -> Dict:
        """Safe wrapper for deletion with error handling."""
        try:
            return self.delete_product(
                product_id,
                strategy,
                reason,
                {'force': False, 'archive': True}
            )
        except DeletionConstraintError:
            # Try with force if constraints prevent deletion
            return self.delete_product(
                product_id,
                strategy,
                reason,
                {'force': True, 'archive': True}
            )
    
    def _soft_delete(self, product_id: str, reason: str) -> Dict:
        """Soft delete (deactivate) product."""
        response = self.session.patch(
            f"{self.base_url}/products/{product_id}",
            json={
                'is_active': False,
                'deleted_at': datetime.utcnow().isoformat() + 'Z',
                'deletion_reason': reason
            }
        )
        response.raise_for_status()
        
        product = response.json()
        
        # Store in recycle bin
        self.recycle_bin[product_id] = {
            'data': product,
            'strategy': 'soft',
            'deleted_at': datetime.utcnow().isoformat(),
            'reason': reason
        }
        
        return product
    
    def _hard_delete(
        self,
        product_id: str,
        reason: str,
        force: bool = False
    ) -> None:
        """Hard delete (permanent) product."""
        headers = {'X-Confirm-Deletion': 'true'}
        
        if force:
            headers['X-Force-Delete'] = 'true'
        
        response = self.session.delete(
            f"{self.base_url}/products/{product_id}",
            headers=headers
        )
        
        if response.status_code == 404 and force:
            # Product might already be deleted
            return
        
        response.raise_for_status()
    
    def _archive_and_delete(self, product_id: str, reason: str) -> None:
        """Archive then hard delete product."""
        # Archive first
        archive_result = self._archive_product(product_id)
        
        # Then delete
        self._hard_delete(product_id, reason, False)
        
        return archive_result
    
    def _cascade_delete(self, product_id: str, reason: str) -> Dict:
        """Delete product and all dependencies."""
        # Get dependencies
        dependencies = self._get_product_dependencies(product_id)
        
        # Delete dependencies first
        dependency_results = []
        for dep in dependencies:
            try:
                result = self.delete_product(
                    dep['id'],
                    DeletionStrategy.HARD,
                    f"Cascade delete from {product_id}: {reason}",
                    {'force': True, 'archive': False}
                )
                dependency_results.append({
                    'dependency_id': dep['id'],
                    'type': dep['type'],
                    'success': True,
                    'result': result
                })
            except Exception as e:
                dependency_results.append({
                    'dependency_id': dep['id'],
                    'type': dep['type'],
                    'success': False,
                    'error': str(e)
                })
        
        # Delete main product
        self._hard_delete(product_id, reason, True)
        
        return {
            'dependencies_deleted': dependency_results,
            'main_product_deleted': True
        }
    
    def _archive_product(self, product_id: str) -> Dict:
        """Archive product data before deletion."""
        try:
            # Get product data
            product = self._get_product(product_id)
            
            # Get related data
            images = self._get_product_images(product_id)
            inventory_history = self._get_inventory_history(product_id)
            sales_data = self._get_sales_data(product_id)
            
            archive = {
                'product': product,
                'images': images,
                'inventory_history': inventory_history,
                'sales_data': sales_data,
                'archived_at': datetime.utcnow().isoformat(),
                'archived_by': self._get_current_user()
            }
            
            # Generate archive ID
            archive_id = f"archive_{product_id}_{int(datetime.utcnow().timestamp())}"
            
            # In production, save to database or object storage
            # For demo, we'll store in memory
            self._store_archive(archive_id, archive)
            
            return {
                'id': archive_id,
                'size': len(json.dumps(archive)),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Warning: Failed to archive product {product_id}: {e}")
            return None
    
    def _cleanup_resources(self, product_id: str):
        """Clean up resources after deletion."""
        cleanup_tasks = [
            self._delete_product_images(product_id),
            self._remove_from_search_index(product_id),
            self._invalidate_cache(product_id),
            self._remove_from_recommendations(product_id)
        ]
        
        # Execute cleanup tasks (simplified)
        for task in cleanup_tasks:
            try:
                task()
            except Exception as e:
                print(f"Cleanup warning for {product_id}: {e}")
    
    def _validate_deletion_request(
        self,
        product_id: str,
        strategy: DeletionStrategy,
        reason: str
    ):
        """Validate deletion request parameters."""
        if not product_id or not isinstance(product_id, str):
            raise ValidationError("Valid product ID is required")
        
        if not reason and strategy != DeletionStrategy.SOFT:
            raise ValidationError("Deletion reason is required for destructive operations")
        
        if len(reason) > 500:
            raise ValidationError("Deletion reason cannot exceed 500 characters")
    
    def _log_deletion(
        self,
        product_id: str,
        strategy: str,
        reason: str,
        archived: bool,
        user: str
    ):
        """Log deletion for audit trail."""
        log_entry = {
            'product_id': product_id,
            'strategy': strategy,
            'reason': reason,
            'archived': archived,
            'user': user,
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': self._get_client_ip()
        }
        
        self.deletion_log.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.deletion_log) > 1000:
            self.deletion_log.pop(0)
    
    def _log_restoration(self, product_id: str, deletion_record: Dict):
        """Log product restoration."""
        log_entry = {
            'product_id': product_id,
            'restored_from': deletion_record['deleted_at'],
            'restored_at': datetime.utcnow().isoformat(),
            'user': self._get_current_user(),
            'previous_deletion_reason': deletion_record['reason']
        }
        
        # Add to deletion log for completeness
        self.deletion_log.append({
            **log_entry,
            'action': 'restore',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    # Helper methods (simplified for example)
    def _get_product(self, product_id: str) -> Dict:
        response = self.session.get(f"{self.base_url}/products/{product_id}")
        response.raise_for_status()
        return response.json()
    
    def _has_active_orders(self, product_id: str) -> bool:
        # Implementation depends on order system
        return False
    
    def _is_in_bundles(self, product_id: str) -> bool:
        # Implementation depends on product bundle system
        return False
    
    def _get_product_dependencies(self, product_id: str) -> List[Dict]:
        # Implementation depends on product relationships
        return []
    
    def _get_product_images(self, product_id: str) -> List[Dict]:
        # Implementation depends on image system
        return []
    
    def _get_inventory_history(self, product_id: str) -> List[Dict]:
        # Implementation depends on inventory system
        return []
    
    def _get_sales_data(self, product_id: str) -> Dict:
        # Implementation depends on sales system
        return {}
    
    def _delete_product_images(self, product_id: str):
        # Delete product images
        pass
    
    def _remove_from_search_index(self, product_id: str):
        # Remove from search index
        pass
    
    def _invalidate_cache(self, product_id: str):
        # Invalidate cache
        pass
    
    def _remove_from_recommendations(self, product_id: str):
        # Remove from recommendations
        pass
    
    def _store_archive(self, archive_id: str, archive: Dict):
        # Store archive data
        pass
    
    def _delete_archive(self, archive_id: str):
        # Delete archive data
        pass
    
    def _get_current_user(self) -> str:
        # Get current user from authentication context
        return "admin"
    
    def _get_client_ip(self) -> str:
        # Get client IP address
        return "127.0.0.1"

# Custom Exceptions
class DeletionConstraintError(Exception):
    def __init__(self, message, constraints=None):
        super().__init__(message)
        self.constraints = constraints or []

class ValidationError(Exception):
    pass

class NotFoundError(Exception):
    pass

class RestorationError(Exception):
    pass

# Usage Examples
def demonstrate_deletion_workflows():
    """Demonstrate different deletion workflows."""
    
    manager = ProductDeletionManager(
        base_url="http://localhost:8000/api",
        token="your_admin_token_here"
    )
    
    product_id = "prod_789"
    
    try:
        # Example 1: Check constraints
        print("Example 1: Checking deletion constraints...")
        constraints = manager.check_deletion_constraints(product_id)
        
        if not constraints['can_delete']:
            print("Cannot delete due to constraints:")
            for c in constraints['constraints']:
                print(f"  - {c['message']} ({c['severity']})")
        
        # Example 2: Soft delete
        print("\nExample 2: Soft deleting product...")
        result1 = manager.delete_product(
            product_id,
            DeletionStrategy.SOFT,
            "Seasonal product rotation"
        )
        print(f"Soft delete result: {result1}")
        
        # Example 3: Restore soft-deleted
        print("\nExample 3: Restoring product...")
        restore_result = manager.restore_product(product_id)
        print(f"Restore result: {restore_result['success']}")
        
        # Example 4: Archive and delete
        print("\nExample 4: Archiving and deleting...")
        result2 = manager.delete_product(
            product_id,
            DeletionStrategy.ARCHIVE,
            "Product discontinued",
            {'archive': True}
        )
        print(f"Archive and delete result: {result2}")
        
        # Example 5: Batch delete
        print("\nExample 5: Batch deleting products...")
        batch_result = manager.batch_delete(
            ["prod_790", "prod_791", "prod_792"],
            DeletionStrategy.SOFT,
            "End of season clearance",
            batch_size=2,
            parallel=True
        )
        
        print(f"Batch delete complete. Successful: {len(batch_result['successful'])}, Failed: {len(batch_result['failed'])}")
        
        # Example 6: Get deletion history
        print("\nExample 6: Viewing deletion history...")
        history = manager.get_deletion_history(limit=5)
        for log in history:
            print(f"{log['timestamp']}: {log['product_id']} - {log['strategy']} - {log['reason']}")
        
        # Example 7: Clean up expired archives
        print("\nExample 7: Cleaning expired archives...")
        manager.cleanup_expired_archives(expiration_days=30)
        print("Cleanup complete")
        
    except DeletionConstraintError as e:
        print(f"Deletion constraint error: {e}")
        for constraint in e.constraints:
            print(f"  - {constraint['message']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    demonstrate_deletion_workflows()
```

### Best Practices for Product Deletion

#### 1. **Soft Delete First Strategy**
```javascript
// Default to soft delete, with option to hard delete later
async function safeDeleteProduct(productId, reason) {
  // First, soft delete
  await softDeleteProduct(productId, reason);
  
  // Schedule hard delete after retention period
  setTimeout(async () => {
    await hardDeleteProduct(productId, `${reason} - Automated cleanup`);
  }, 30 * 24 * 60 * 60 * 1000); // 30 days
}
```

#### 2. **Cascade Delete Considerations**
```javascript
// Handle dependent resources
async function deleteProductCascade(productId) {
  // 1. Get all dependent resources
  const dependencies = await getProductDependencies(productId);
  
  // 2. Delete dependencies first
  for (const dependency of dependencies) {
    await deleteDependency(dependency);
  }
  
  // 3. Delete main product
  await deleteProduct(productId);
  
  // 4. Clean up orphaned data
  await cleanupOrphanedData();
}
```

#### 3. **Audit Trail Implementation**
```javascript
// Comprehensive audit logging
function logDeletion(productId, userId, reason, metadata) {
  const auditLog = {
    event: 'product_deletion',
    product_id: productId,
    user_id: userId,
    timestamp: new Date().toISOString(),
    reason: reason,
    metadata: metadata,
    ip_address: getClientIP(),
    user_agent: getUserAgent(),
    session_id: getSessionId()
  };
  
  // Send to audit service
  sendToAuditService(auditLog);
  
  // Store locally for redundancy
  storeLocalAuditLog(auditLog);
}
```

#### 4. **Recovery Options**
```javascript
// Implement recovery mechanisms
class ProductRecoveryService {
  constructor() {
    this.backupStore = new Map();
  }
  
  async backupBeforeDelete(productId) {
    const product = await getProduct(productId);
    const backupId = `backup_${productId}_${Date.now()}`;
    
    this.backupStore.set(backupId, {
      product,
      backedUpAt: new Date(),
      ttl: 90 * 24 * 60 * 60 * 1000 // 90 days
    });
    
    return backupId;
  }
  
  async recoverProduct(backupId) {
    const backup = this.backupStore.get(backupId);
    if (!backup) throw new Error('Backup not found');
    
    // Restore product
    const restoredProduct = await createProduct(backup.product);
    
    // Clean up backup
    this.backupStore.delete(backupId);
    
    return restoredProduct;
  }
}
```

### Security Considerations

#### 1. **Authorization and Authentication**
```javascript
// Multi-level authorization check
async function authorizeDeletion(productId, userId) {
  // Check user role
  const userRole = await getUserRole(userId);
  if (!['admin', 'product_manager'].includes(userRole)) {
    throw new AuthorizationError('Insufficient permissions');
  }
  
  // Check product ownership (if applicable)
  const productOwner = await getProductOwner(productId);
  if (productOwner !== userId && userRole !== 'admin') {
    throw new AuthorizationError('Not product owner');
  }
  
  // Check recent activity (prevent mass deletion)
  const recentDeletions = await getUserRecentDeletions(userId);
  if (recentDeletions > 10) {
    throw new RateLimitError('Too many deletions recently');
  }
}
```

#### 2. **Confirmation Mechanisms**
```javascript
// Multi-step confirmation
async function deleteWithConfirmation(productId, userId) {
  // Step 1: Initial confirmation
  const confirmed = await showConfirmationDialog();
  if (!confirmed) return;
  
  // Step 2: Type confirmation for destructive operations
  const typeConfirmed = await typeConfirmation('DELETE');
  if (!typeConfirmed) return;
  
  // Step 3: Two-factor for sensitive products
  if (await isSensitiveProduct(productId)) {
    const twoFactorValid = await validateTwoFactor(userId);
    if (!twoFactorValid) return;
  }
  
  // Execute deletion
  return deleteProduct(productId);
}
```

#### 3. **Rate Limiting**
```javascript
// Implement rate limiting for deletions
class DeletionRateLimiter {
  constructor() {
    this.userDeletions = new Map();
    this.ipDeletions = new Map();
  }
  
  canDelete(userId, ipAddress) {
    const userLimit = this.getUserLimit(userId);
    const ipLimit = this.getIPLimit(ipAddress);
    
    return userLimit.canProceed && ipLimit.canProceed;
  }
  
  getUserLimit(userId) {
    const now = Date.now();
    const userDeletions = this.userDeletions.get(userId) || [];
    
    // Clean old entries
    const recentDeletions = userDeletions.filter(time => now - time < 3600000); // 1 hour
    
    // Update
    this.userDeletions.set(userId, [...recentDeletions, now]);
    
    return {
      canProceed: recentDeletions.length < 10, // Max 10 per hour
      remaining: 10 - recentDeletions.length,
      resetIn: 3600000 - (now - (recentDeletions[0] || now))
    };
  }
}
```

---

## Related Endpoints
- [PATCH /products/{productId}](../products/update-product.md) - Soft delete via deactivation
- [GET /products/deleted](../../endpoints/deleted-products.md) - List deleted products
- [POST /products/restore/{productId}](../../endpoints/restore-product.md) - Restore soft-deleted product
- [POST /products/bulk-delete](../../endpoints/bulk-delete.md) - Bulk delete endpoint
- [Error Responses](../../errors.md) - Error handling details

## Notes
- Consider implementing a quarantine period before permanent deletion
- Always archive important data before deletion for compliance
- Implement proper cleanup of related resources (images, cache, search index)
- Use asynchronous deletion for large products to avoid timeouts
- Consider implementing deletion approval workflows for sensitive products

## Compliance and Regulations
- GDPR: Implement right to erasure with proper data removal
- SOX: Maintain audit trails for financial products
- HIPAA: Special handling for healthcare-related products
- PCI DSS: Secure deletion of payment-related product data
- Industry-specific regulations may apply

## Performance Considerations
- Use batch operations for mass deletions
- Implement asynchronous cleanup tasks
- Consider database indexing for deletion performance
- Monitor deletion performance and optimize as needed
- Implement queue-based deletion for large catalogs