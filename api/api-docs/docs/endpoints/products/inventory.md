# PATCH /products/{productId}/inventory

**Update Product Stock** - Update inventory quantity for a specific product (Admin Only)

**Tags:** Products

**Authentication:** Required (Bearer Token with Admin privileges)

---

## Description
Update the stock quantity for a specific product. This endpoint is idempotent and designed specifically for inventory management operations. It provides atomic stock updates with optional reason tracking and supports both absolute and relative quantity adjustments.

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
**Schema:** InventoryUpdate

```json
{
  "stock": 150,
  "operation": "set",
  "reason": "restock",
  "notes": "Received shipment from warehouse",
  "adjustment_id": "adj_202401151030",
  "location": "warehouse-a",
  "cost_per_unit": 19.99,
  "expires_at": "2024-06-30T00:00:00Z"
}
```

**Fields:**

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `stock` | integer | ✓ | - | ≥ 0 | Target stock quantity or adjustment amount |
| `operation` | string | No | `set` | `set`, `increment`, `decrement` | Operation type |
| `reason` | string | No | - | ≤ 100 chars | Reason for inventory change |
| `notes` | string | No | - | ≤ 500 chars | Additional notes |
| `adjustment_id` | string | No | - | Unique | External adjustment ID for idempotency |
| `location` | string | No | - | ≤ 50 chars | Inventory location |
| `cost_per_unit` | number | No | - | ≥ 0 | Cost per unit for this batch |
| `expires_at` | string | No | - | ISO 8601 date | Expiration date for this batch |
| `reserved` | integer | No | 0 | ≥ 0 | Quantity to reserve (not available for sale) |
| `available` | integer | No | - | ≥ 0 | Available quantity (calculated if not provided) |
| `backorder_allowed` | boolean | No | false | - | Allow backorders if stock is insufficient |
| `reorder_threshold` | integer | No | - | ≥ 0 | Trigger reorder alert at this level |
| `batch_number` | string | No | - | ≤ 50 chars | Manufacturing batch/lot number |

## Responses

### 200 OK - Inventory updated successfully
**Body:**
```json
{
  "id": "prod_789",
  "stock": 150,
  "available": 145,
  "reserved": 5,
  "previous_stock": 100,
  "adjustment": 50,
  "operation": "increment",
  "updated_at": "2024-01-15T10:30:00Z",
  "inventory_history_id": "inv_123456",
  "metadata": {
    "reason": "restock",
    "notes": "Received shipment from warehouse",
    "location": "warehouse-a",
    "adjusted_by": "admin_user"
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Product identifier |
| `stock` | integer | New total stock quantity |
| `available` | integer | Available quantity for sale |
| `reserved` | integer | Reserved quantity |
| `previous_stock` | integer | Previous stock quantity |
| `adjustment` | integer | Net change in stock |
| `operation` | string | Operation performed |
| `updated_at` | string | Update timestamp |
| `inventory_history_id` | string | ID of inventory history record |
| `metadata` | object | Additional metadata about the update |

### 400 Bad Request - Invalid input
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/bad-request",
  "title": "Bad Request",
  "status": 400,
  "detail": "Stock cannot be negative.",
  "instance": "/products/prod_789/inventory",
  "errors": [
    {
      "field": "stock",
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
  "instance": "/products/prod_789/inventory"
}
```

### 403 Forbidden - Insufficient permissions
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "Insufficient permissions to update inventory.",
  "instance": "/products/prod_789/inventory"
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
  "instance": "/products/prod_999/inventory"
}
```

### 409 Conflict - Adjustment ID already used
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/conflict",
  "title": "Conflict",
  "status": 409,
  "detail": "Adjustment ID 'adj_202401151030' has already been processed.",
  "instance": "/products/prod_789/inventory"
}
```

### 422 Unprocessable Entity - Business rule violation
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/validation",
  "title": "Validation failed",
  "status": 422,
  "detail": "Cannot decrement stock below reserved quantity.",
  "instance": "/products/prod_789/inventory",
  "errors": [
    {
      "field": "stock",
      "message": "Stock cannot be less than reserved quantity (5 units)"
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
  "detail": "Failed to update inventory due to database error.",
  "instance": "/products/prod_789/inventory"
}
```

## Examples

### Basic cURL Request
```bash
# Set absolute stock quantity
curl -X PATCH "http://localhost:8000/api/products/prod_789/inventory" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "stock": 150
  }'
```

### Increment/Decrement Operations
```bash
# Increment stock by 50 units
curl -X PATCH "http://localhost:8000/api/products/prod_789/inventory" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "stock": 50,
    "operation": "increment",
    "reason": "restock",
    "notes": "Weekly restock from supplier"
  }'

# Decrement stock by 10 units
curl -X PATCH "http://localhost:8000/api/products/prod_789/inventory" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "stock": 10,
    "operation": "decrement",
    "reason": "damaged",
    "notes": "Damaged during handling"
  }'
```

### Idempotent Request with Adjustment ID
```bash
# Idempotent inventory update
curl -X PATCH "http://localhost:8000/api/products/prod_789/inventory" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "stock": 200,
    "operation": "set",
    "adjustment_id": "shipment_12345_20240115",
    "reason": "warehouse_receipt",
    "location": "warehouse-b",
    "batch_number": "BATCH-2024-001"
  }'
```

### Complete Inventory Update
```bash
curl -X PATCH "http://localhost:8000/api/products/prod_789/inventory" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "stock": 250,
    "operation": "set",
    "reason": "bulk_restock",
    "notes": "Quarterly bulk order from manufacturer",
    "adjustment_id": "bulk_2024_q1",
    "location": "main_warehouse",
    "cost_per_unit": 24.99,
    "expires_at": "2025-12-31T00:00:00Z",
    "reserved": 25,
    "backorder_allowed": true,
    "reorder_threshold": 50,
    "batch_number": "MFG-2024-001"
  }'
```

### JavaScript (Fetch) with Advanced Inventory Management
```javascript
/**
 * Advanced inventory management service with transaction support
 */
class InventoryManager {
  constructor(apiUrl = 'http://localhost:8000/api') {
    this.apiUrl = apiUrl;
    this.pendingAdjustments = new Map();
    this.inventoryCache = new Map();
  }
  
  /**
   * Update product inventory with comprehensive features
   */
  async updateInventory(productId, inventoryData, accessToken, options = {}) {
    const {
      validate = true,
      requireConfirmation = false,
      trackHistory = true,
      idempotencyKey = null,
      timeout = 30000
    } = options;
    
    // Validate input
    if (validate) {
      const validation = this.validateInventoryData(inventoryData);
      if (!validation.valid) {
        throw new InventoryValidationError('Invalid inventory data', validation.errors);
      }
    }
    
    // Check for duplicate idempotency key
    if (idempotencyKey) {
      const existing = this.pendingAdjustments.get(idempotencyKey);
      if (existing && existing.status === 'completed') {
        // Return cached result for idempotent retry
        return existing.result;
      }
      
      if (existing && existing.status === 'processing') {
        throw new InventoryConflictError(
          'Inventory update already in progress',
          { idempotencyKey }
        );
      }
    }
    
    // Add to pending adjustments if idempotency key provided
    if (idempotencyKey) {
      this.pendingAdjustments.set(idempotencyKey, {
        productId,
        data: inventoryData,
        status: 'processing',
        startedAt: new Date()
      });
    }
    
    try {
      // Prepare request headers
      const headers = {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      };
      
      if (idempotencyKey) {
        headers['Idempotency-Key'] = idempotencyKey;
        headers['X-Adjustment-ID'] = inventoryData.adjustment_id || idempotencyKey;
      }
      
      if (requireConfirmation) {
        headers['X-Require-Confirmation'] = 'true';
      }
      
      // Make request
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);
      
      const response = await fetch(`${this.apiUrl}/products/${productId}/inventory`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(inventoryData),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      // Parse response
      const result = await this.parseInventoryResponse(response, inventoryData);
      
      // Update cache
      this.updateInventoryCache(productId, result);
      
      // Track history if enabled
      if (trackHistory) {
        await this.recordInventoryHistory(productId, inventoryData, result);
      }
      
      // Trigger inventory events
      this.triggerInventoryEvents(productId, inventoryData, result);
      
      // Update pending adjustments
      if (idempotencyKey) {
        this.pendingAdjustments.set(idempotencyKey, {
          ...this.pendingAdjustments.get(idempotencyKey),
          status: 'completed',
          result,
          completedAt: new Date()
        });
      }
      
      return result;
      
    } catch (error) {
      // Update pending adjustments on error
      if (idempotencyKey) {
        this.pendingAdjustments.set(idempotencyKey, {
          ...this.pendingAdjustments.get(idempotencyKey),
          status: 'failed',
          error: error.message,
          failedAt: new Date()
        });
      }
      
      throw this.handleInventoryError(error, productId, inventoryData);
    }
  }
  
  /**
   * Bulk inventory update for multiple products
   */
  async bulkUpdateInventory(updates, accessToken, options = {}) {
    const {
      batchSize = 10,
      parallel = true,
      stopOnError = false,
      onProgress = null
    } = options;
    
    const results = {
      successful: [],
      failed: [],
      total: updates.length
    };
    
    if (parallel) {
      // Process in parallel batches
      for (let i = 0; i < updates.length; i += batchSize) {
        const batch = updates.slice(i, i + batchSize);
        const batchPromises = batch.map(update =>
          this.updateInventory(
            update.productId,
            update.data,
            accessToken,
            update.options || {}
          )
            .then(result => ({ success: true, update, result }))
            .catch(error => ({ success: false, update, error }))
        );
        
        const batchResults = await Promise.all(batchPromises);
        
        batchResults.forEach(result => {
          if (result.success) {
            results.successful.push({
              productId: result.update.productId,
              result: result.result
            });
          } else {
            results.failed.push({
              productId: result.update.productId,
              error: result.error
            });
            
            if (stopOnError) {
              throw new BulkInventoryError('Bulk update stopped due to error', results);
            }
          }
        });
        
        // Progress callback
        if (onProgress) {
          const processed = results.successful.length + results.failed.length;
          onProgress(processed, updates.length);
        }
      }
    } else {
      // Process sequentially
      for (const update of updates) {
        try {
          const result = await this.updateInventory(
            update.productId,
            update.data,
            accessToken,
            update.options || {}
          );
          
          results.successful.push({
            productId: update.productId,
            result
          });
        } catch (error) {
          results.failed.push({
            productId: update.productId,
            error
          });
          
          if (stopOnError) {
            throw new BulkInventoryError('Bulk update stopped due to error', results);
          }
        }
        
        // Progress callback
        if (onProgress) {
          const processed = results.successful.length + results.failed.length;
          onProgress(processed, updates.length);
        }
      }
    }
    
    // Generate summary
    results.summary = {
      totalAdjustment: this.calculateTotalAdjustment(results.successful),
      averageAdjustment: this.calculateAverageAdjustment(results.successful),
      affectedProducts: results.successful.length
    };
    
    return results;
  }
  
  /**
   * Reserve inventory for an order
   */
  async reserveInventory(productId, quantity, accessToken, options = {}) {
    const {
      orderId,
      expirationMinutes = 30,
      allowPartial = false,
      skipAvailableCheck = false
    } = options;
    
    // Get current inventory
    const currentInventory = await this.getInventory(productId, accessToken);
    
    // Check availability
    if (!skipAvailableCheck) {
      const available = currentInventory.available || currentInventory.stock;
      
      if (quantity > available) {
        if (!allowPartial) {
          throw new InventoryInsufficientError(
            `Insufficient inventory. Available: ${available}, Requested: ${quantity}`,
            { available, requested: quantity }
          );
        }
        
        // Reserve only available quantity
        quantity = available;
      }
    }
    
    // Create reservation data
    const reservationData = {
      stock: currentInventory.stock, // Keep total stock same
      reserved: (currentInventory.reserved || 0) + quantity,
      operation: 'set',
      reason: 'order_reservation',
      notes: `Reservation for order ${orderId}`,
      adjustment_id: `reserve_${orderId}_${Date.now()}`,
      metadata: {
        orderId,
        reservationExpiresAt: new Date(Date.now() + expirationMinutes * 60000).toISOString(),
        reservedQuantity: quantity
      }
    };
    
    return this.updateInventory(productId, reservationData, accessToken, {
      idempotencyKey: `reserve_${orderId}_${productId}`
    });
  }
  
  /**
   * Release reserved inventory
   */
  async releaseInventory(productId, quantity, accessToken, options = {}) {
    const { orderId, reason = 'order_cancelled' } = options;
    
    // Get current inventory
    const currentInventory = await this.getInventory(productId, accessToken);
    
    // Calculate new reserved quantity
    const currentReserved = currentInventory.reserved || 0;
    const newReserved = Math.max(0, currentReserved - quantity);
    
    const releaseData = {
      stock: currentInventory.stock,
      reserved: newReserved,
      operation: 'set',
      reason,
      notes: `Release from order ${orderId}`,
      adjustment_id: `release_${orderId}_${Date.now()}`,
      metadata: {
        orderId,
        releasedQuantity: quantity,
        previousReserved: currentReserved
      }
    };
    
    return this.updateInventory(productId, releaseData, accessToken, {
      idempotencyKey: `release_${orderId}_${productId}`
    });
  }
  
  /**
   * Process inventory adjustment from sales
   */
  async processSale(productId, quantity, accessToken, options = {}) {
    const {
      orderId,
      reduceReserved = true,
      allowBackorder = false
    } = options;
    
    // Get current inventory
    const currentInventory = await this.getInventory(productId, accessToken);
    
    // Calculate adjustments
    let stockAdjustment = -quantity;
    let reservedAdjustment = reduceReserved ? -Math.min(quantity, currentInventory.reserved || 0) : 0;
    
    // Check for backorder
    const available = currentInventory.available || currentInventory.stock;
    const backorderQuantity = allowBackorder ? Math.max(0, quantity - available) : 0;
    
    const saleData = {
      stock: currentInventory.stock + stockAdjustment,
      reserved: (currentInventory.reserved || 0) + reservedAdjustment,
      operation: 'set',
      reason: 'sale_fulfillment',
      notes: `Sale fulfillment for order ${orderId}`,
      adjustment_id: `sale_${orderId}_${Date.now()}`,
      metadata: {
        orderId,
        saleQuantity: quantity,
        backorderQuantity,
        reservedReduced: Math.abs(reservedAdjustment)
      }
    };
    
    const result = await this.updateInventory(productId, saleData, accessToken, {
      idempotencyKey: `sale_${orderId}_${productId}`
    });
    
    // Handle backorder if needed
    if (backorderQuantity > 0) {
      await this.createBackorder(productId, backorderQuantity, orderId, accessToken);
      result.backorder_created = true;
      result.backorder_quantity = backorderQuantity;
    }
    
    return result;
  }
  
  /**
   * Get current inventory status
   */
  async getInventory(productId, accessToken, forceRefresh = false) {
    // Check cache first
    const cached = this.inventoryCache.get(productId);
    if (!forceRefresh && cached && Date.now() - cached.timestamp < 30000) { // 30 second cache
      return cached.data;
    }
    
    try {
      const response = await fetch(`${this.apiUrl}/products/${productId}`, {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch inventory: ${response.status}`);
      }
      
      const product = await response.json();
      const inventory = {
        stock: product.stock,
        available: product.available || product.stock,
        reserved: product.reserved || 0,
        updated_at: product.updated_at,
        reorder_threshold: product.reorder_threshold,
        backorder_allowed: product.backorder_allowed || false
      };
      
      // Update cache
      this.inventoryCache.set(productId, {
        data: inventory,
        timestamp: Date.now()
      });
      
      return inventory;
      
    } catch (error) {
      // Return cached data if available
      if (cached) {
        console.warn(`Using cached inventory for ${productId}:`, error.message);
        return cached.data;
      }
      throw error;
    }
  }
  
  /**
   * Get inventory history for a product
   */
  async getInventoryHistory(productId, accessToken, options = {}) {
    const {
      startDate,
      endDate,
      limit = 100,
      offset = 0
    } = options;
    
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString()
    });
    
    if (startDate) params.append('start_date', startDate.toISOString());
    if (endDate) params.append('end_date', endDate.toISOString());
    
    const response = await fetch(
      `${this.apiUrl}/products/${productId}/inventory/history?${params}`,
      {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      }
    );
    
    if (!response.ok) {
      throw new Error(`Failed to fetch inventory history: ${response.status}`);
    }
    
    return response.json();
  }
  
  /**
   * Check low stock alerts
   */
  async checkLowStock(products, accessToken, threshold = null) {
    const lowStockProducts = [];
    
    for (const productId of products) {
      try {
        const inventory = await this.getInventory(productId, accessToken);
        const reorderLevel = threshold || inventory.reorder_threshold;
        
        if (reorderLevel !== undefined && inventory.available <= reorderLevel) {
          lowStockProducts.push({
            productId,
            currentStock: inventory.available,
            reorderLevel,
            needsReorder: inventory.available <= reorderLevel * 0.5 // Critical threshold
          });
        }
      } catch (error) {
        console.warn(`Failed to check stock for ${productId}:`, error.message);
      }
    }
    
    return {
      lowStockProducts,
      totalChecked: products.length,
      criticalCount: lowStockProducts.filter(p => p.needsReorder).length
    };
  }
  
  /**
   * Validate inventory data
   */
  validateInventoryData(data) {
    const errors = [];
    
    // Required fields
    if (typeof data.stock !== 'number' || !Number.isInteger(data.stock)) {
      errors.push({
        field: 'stock',
        message: 'Stock must be an integer'
      });
    }
    
    if (data.stock < 0) {
      errors.push({
        field: 'stock',
        message: 'Stock cannot be negative'
      });
    }
    
    // Operation validation
    if (data.operation && !['set', 'increment', 'decrement'].includes(data.operation)) {
      errors.push({
        field: 'operation',
        message: 'Operation must be one of: set, increment, decrement'
      });
    }
    
    // Reserved validation
    if (data.reserved !== undefined) {
      if (!Number.isInteger(data.reserved) || data.reserved < 0) {
        errors.push({
          field: 'reserved',
          message: 'Reserved must be a non-negative integer'
        });
      }
      
      if (data.reserved > data.stock) {
        errors.push({
          field: 'reserved',
          message: 'Reserved cannot exceed total stock'
        });
      }
    }
    
    // Cost validation
    if (data.cost_per_unit !== undefined && data.cost_per_unit < 0) {
      errors.push({
        field: 'cost_per_unit',
        message: 'Cost per unit cannot be negative'
      });
    }
    
    // Reason length
    if (data.reason && data.reason.length > 100) {
      errors.push({
        field: 'reason',
        message: 'Reason cannot exceed 100 characters'
      });
    }
    
    // Notes length
    if (data.notes && data.notes.length > 500) {
      errors.push({
        field: 'notes',
        message: 'Notes cannot exceed 500 characters'
      });
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
  
  /**
   * Parse inventory response
   */
  async parseInventoryResponse(response, requestData) {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new InventoryError(
        errorData.detail || `Inventory update failed: ${response.status}`,
        response.status,
        errorData
      );
    }
    
    const result = await response.json();
    
    // Add request metadata to result
    result.request = {
      operation: requestData.operation || 'set',
      reason: requestData.reason,
      timestamp: new Date().toISOString()
    };
    
    return result;
  }
  
  /**
   * Handle inventory errors
   */
  handleInventoryError(error, productId, inventoryData) {
    if (error.name === 'AbortError') {
      return new InventoryTimeoutError(
        `Inventory update timeout for product ${productId}`,
        { productId, timeout: 30000 }
      );
    }
    
    if (error instanceof InventoryError) {
      return error;
    }
    
    return new InventoryError(
      `Inventory update failed: ${error.message}`,
      null,
      { productId, inventoryData, originalError: error }
    );
  }
  
  /**
   * Update inventory cache
   */
  updateInventoryCache(productId, result) {
    this.inventoryCache.set(productId, {
      data: {
        stock: result.stock,
        available: result.available,
        reserved: result.reserved,
        updated_at: result.updated_at
      },
      timestamp: Date.now()
    });
  }
  
  /**
   * Record inventory history
   */
  async recordInventoryHistory(productId, requestData, result) {
    const historyEntry = {
      productId,
      timestamp: new Date().toISOString(),
      previousStock: result.previous_stock,
      newStock: result.stock,
      adjustment: result.adjustment,
      operation: result.operation || requestData.operation,
      reason: requestData.reason,
      notes: requestData.notes,
      adjustedBy: this.getCurrentUser(),
      metadata: {
        adjustment_id: requestData.adjustment_id,
        location: requestData.location,
        batchNumber: requestData.batch_number
      }
    };
    
    // Store locally (in production, send to history service)
    const historyKey = `inventory_history_${productId}`;
    const history = JSON.parse(localStorage.getItem(historyKey) || '[]');
    history.unshift(historyEntry);
    
    // Keep only last 100 entries
    if (history.length > 100) {
      history.pop();
    }
    
    localStorage.setItem(historyKey, JSON.stringify(history));
  }
  
  /**
   * Trigger inventory events
   */
  triggerInventoryEvents(productId, requestData, result) {
    // Custom event for UI updates
    const event = new CustomEvent('inventoryUpdated', {
      detail: {
        productId,
        request: requestData,
        result,
        timestamp: new Date().toISOString()
      }
    });
    
    window.dispatchEvent(event);
    
    // Analytics
    if (window.gtag) {
      window.gtag('event', 'inventory_update', {
        product_id: productId,
        operation: requestData.operation,
        adjustment: result.adjustment,
        new_stock: result.stock
      });
    }
    
    // Check for low stock alerts
    if (result.stock <= (result.reorder_threshold || 10)) {
      this.triggerLowStockAlert(productId, result);
    }
  }
  
  /**
   * Trigger low stock alert
   */
  triggerLowStockAlert(productId, inventory) {
    const alertEvent = new CustomEvent('lowStockAlert', {
      detail: {
        productId,
        currentStock: inventory.stock,
        available: inventory.available,
        threshold: inventory.reorder_threshold,
        timestamp: new Date().toISOString()
      }
    });
    
    window.dispatchEvent(alertEvent);
    
    // Send notification
    if (Notification.permission === 'granted') {
      new Notification('Low Stock Alert', {
        body: `Product ${productId} has low stock: ${inventory.stock} units`,
        icon: '/icon.png'
      });
    }
  }
  
  /**
   * Create backorder record
   */
  async createBackorder(productId, quantity, orderId, accessToken) {
    // Implementation depends on backorder system
    console.log(`Creating backorder for ${quantity} units of ${productId} for order ${orderId}`);
    
    // In production, this would create a backorder record in your database
    return {
      productId,
      quantity,
      orderId,
      created_at: new Date().toISOString(),
      status: 'pending'
    };
  }
  
  /**
   * Calculate total adjustment from results
   */
  calculateTotalAdjustment(successfulResults) {
    return successfulResults.reduce((total, result) => {
      return total + (result.result.adjustment || 0);
    }, 0);
  }
  
  /**
   * Calculate average adjustment
   */
  calculateAverageAdjustment(successfulResults) {
    if (successfulResults.length === 0) return 0;
    return this.calculateTotalAdjustment(successfulResults) / successfulResults.length;
  }
  
  getCurrentUser() {
    return localStorage.getItem('userId') || 'system';
  }
}

// Custom Error Classes
class InventoryError extends Error {
  constructor(message, statusCode = null, details = null) {
    super(message);
    this.name = 'InventoryError';
    this.status = statusCode;
    this.details = details;
  }
}

class InventoryValidationError extends InventoryError {
  constructor(message, errors = []) {
    super(message);
    this.name = 'InventoryValidationError';
    this.errors = errors;
  }
}

class InventoryConflictError extends InventoryError {
  constructor(message, conflictDetails = null) {
    super(message);
    this.name = 'InventoryConflictError';
    this.conflictDetails = conflictDetails;
  }
}

class InventoryInsufficientError extends InventoryError {
  constructor(message, stockDetails = null) {
    super(message);
    this.name = 'InventoryInsufficientError';
    this.stockDetails = stockDetails;
  }
}

class InventoryTimeoutError extends InventoryError {
  constructor(message, timeoutDetails = null) {
    super(message);
    this.name = 'InventoryTimeoutError';
    this.timeoutDetails = timeoutDetails;
  }
}

class BulkInventoryError extends InventoryError {
  constructor(message, results = null) {
    super(message);
    this.name = 'BulkInventoryError';
    this.results = results;
  }
}

// Usage Examples
async function demonstrateInventoryOperations() {
  const inventoryManager = new InventoryManager();
  const accessToken = localStorage.getItem('accessToken');
  const productId = 'prod_789';
  
  try {
    // Example 1: Basic stock update
    console.log('Example 1: Basic stock update...');
    const result1 = await inventoryManager.updateInventory(
      productId,
      { stock: 150, reason: 'restock' },
      accessToken
    );
    console.log('Stock updated:', result1);
    
    // Example 2: Increment with idempotency
    console.log('\nExample 2: Idempotent increment...');
    const result2 = await inventoryManager.updateInventory(
      productId,
      {
        stock: 50,
        operation: 'increment',
        reason: 'warehouse_receipt',
        adjustment_id: 'receipt_12345'
      },
      accessToken,
      { idempotencyKey: 'receipt_12345' }
    );
    console.log('Incremented:', result2);
    
    // Example 3: Reserve inventory for order
    console.log('\nExample 3: Reserve inventory...');
    const result3 = await inventoryManager.reserveInventory(
      productId,
      5,
      accessToken,
      { orderId: 'order_123', expirationMinutes: 60 }
    );
    console.log('Reserved:', result3);
    
    // Example 4: Process sale
    console.log('\nExample 4: Process sale...');
    const result4 = await inventoryManager.processSale(
      productId,
      3,
      accessToken,
      { orderId: 'order_123', reduceReserved: true }
    );
    console.log('Sale processed:', result4);
    
    // Example 5: Bulk update
    console.log('\nExample 5: Bulk inventory update...');
    const bulkResult = await inventoryManager.bulkUpdateInventory(
      [
        {
          productId: 'prod_789',
          data: { stock: 200, operation: 'set', reason: 'bulk_update' }
        },
        {
          productId: 'prod_790',
          data: { stock: 100, operation: 'set', reason: 'bulk_update' }
        }
      ],
      accessToken,
      {
        parallel: true,
        onProgress: (processed, total) => {
          console.log(`Progress: ${processed}/${total}`);
        }
      }
    );
    console.log('Bulk update complete:', bulkResult.summary);
    
    // Example 6: Check low stock
    console.log('\nExample 6: Check low stock...');
    const lowStock = await inventoryManager.checkLowStock(
      ['prod_789', 'prod_790'],
      accessToken,
      20
    );
    console.log('Low stock check:', lowStock);
    
  } catch (error) {
    console.error('Inventory operation error:', error);
    
    if (error instanceof InventoryValidationError) {
      console.error('Validation errors:');
      error.errors.forEach(err => console.error(`  - ${err.field}: ${err.message}`));
    } else if (error instanceof InventoryInsufficientError) {
      console.error('Insufficient stock:', error.stockDetails);
    }
  }
}
```

### React Component for Inventory Management
```jsx
import React, { useState, useEffect } from 'react';
import InventoryHistory from './InventoryHistory';
import LowStockAlert from './LowStockAlert';

function InventoryManagementPage({ productId }) {
  const [inventory, setInventory] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [adjustmentType, setAdjustmentType] = useState('set');
  const [quantity, setQuantity] = useState('');
  const [reason, setReason] = useState('');
  const [notes, setNotes] = useState('');
  const [showHistory, setShowHistory] = useState(false);
  
  // Load current inventory
  useEffect(() => {
    loadInventory();
  }, [productId]);
  
  const loadInventory = async () => {
    try {
      setLoading(true);
      const accessToken = localStorage.getItem('accessToken');
      
      const response = await fetch(`http://localhost:8000/api/products/${productId}`, {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      });
      
      if (!response.ok) throw new Error('Failed to load inventory');
      
      const product = await response.json();
      setInventory({
        stock: product.stock,
        available: product.available || product.stock,
        reserved: product.reserved || 0,
        reorderLevel: product.reorder_threshold,
        lastUpdated: product.updated_at
      });
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  const handleAdjustment = async (e) => {
    e.preventDefault();
    
    if (!quantity || isNaN(quantity) || parseInt(quantity) < 0) {
      setError('Please enter a valid quantity');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const accessToken = localStorage.getItem('accessToken');
      const quantityNum = parseInt(quantity);
      
      // Prepare inventory data
      const inventoryData = {
        stock: quantityNum,
        operation: adjustmentType,
        reason: reason || 'manual_adjustment',
        notes: notes || undefined
      };
      
      // Calculate new stock based on operation
      if (adjustmentType === 'increment') {
        inventoryData.stock = (inventory?.stock || 0) + quantityNum;
      } else if (adjustmentType === 'decrement') {
        inventoryData.stock = Math.max(0, (inventory?.stock || 0) - quantityNum);
      }
      
      // Make API call
      const response = await fetch(
        `http://localhost:8000/api/products/${productId}/inventory`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(inventoryData)
        }
      );
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Inventory update failed');
      }
      
      const result = await response.json();
      
      // Update local state
      setInventory({
        stock: result.stock,
        available: result.available,
        reserved: result.reserved,
        lastUpdated: result.updated_at
      });
      
      // Reset form
      setQuantity('');
      setReason('');
      setNotes('');
      
      // Show success message
      showNotification('Inventory updated successfully', 'success');
      
      // Refresh inventory
      loadInventory();
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  const handleQuickAction = async (action, amount) => {
    setLoading(true);
    
    try {
      const accessToken = localStorage.getItem('accessToken');
      let inventoryData;
      
      switch (action) {
        case 'restock':
          inventoryData = {
            stock: (inventory?.stock || 0) + amount,
            operation: 'increment',
            reason: 'quick_restock',
            notes: `Quick restock of ${amount} units`
          };
          break;
          
        case 'damage':
          inventoryData = {
            stock: Math.max(0, (inventory?.stock || 0) - amount),
            operation: 'decrement',
            reason: 'damaged_goods',
            notes: `Recorded ${amount} damaged units`
          };
          break;
          
        case 'set_minimum':
          inventoryData = {
            stock: amount,
            operation: 'set',
            reason: 'set_minimum_stock',
            notes: 'Set to minimum stock level'
          };
          break;
      }
      
      const response = await fetch(
        `http://localhost:8000/api/products/${productId}/inventory`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(inventoryData)
        }
      );
      
      if (!response.ok) throw new Error('Quick action failed');
      
      const result = await response.json();
      setInventory({
        stock: result.stock,
        available: result.available,
        reserved: result.reserved,
        lastUpdated: result.updated_at
      });
      
      showNotification(`${action.replace('_', ' ')} completed`, 'success');
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  if (loading && !inventory) {
    return <div className="loading">Loading inventory...</div>;
  }
  
  return (
    <div className="inventory-management-page">
      <div className="page-header">
        <h1>Inventory Management</h1>
        <div className="header-actions">
          <button 
            className="btn-refresh"
            onClick={loadInventory}
            disabled={loading}
          >
            Refresh
          </button>
          <button 
            className="btn-history"
            onClick={() => setShowHistory(!showHistory)}
          >
            {showHistory ? 'Hide History' : 'Show History'}
          </button>
        </div>
      </div>
      
      {/* Current Inventory Status */}
      <div className="inventory-status">
        <div className="status-card">
          <h3>Current Stock</h3>
          <div className="stock-value">{inventory?.stock || 0}</div>
          <div className="status-details">
            <div className="detail-item">
              <span className="label">Available:</span>
              <span className="value">{inventory?.available || 0}</span>
            </div>
            <div className="detail-item">
              <span className="label">Reserved:</span>
              <span className="value">{inventory?.reserved || 0}</span>
            </div>
            <div className="detail-item">
              <span className="label">Last Updated:</span>
              <span className="value">
                {inventory?.lastUpdated 
                  ? new Date(inventory.lastUpdated).toLocaleString() 
                  : 'N/A'}
              </span>
            </div>
          </div>
        </div>
        
        {/* Low Stock Alert */}
        {inventory && inventory.reorderLevel && inventory.available <= inventory.reorderLevel && (
          <LowStockAlert
            currentStock={inventory.available}
            reorderLevel={inventory.reorderLevel}
          />
        )}
      </div>
      
      {/* Quick Actions */}
      <div className="quick-actions">
        <h3>Quick Actions</h3>
        <div className="action-buttons">
          <button
            onClick={() => handleQuickAction('restock', 10)}
            disabled={loading}
            className="btn-action btn-restock"
          >
            Restock +10
          </button>
          <button
            onClick={() => handleQuickAction('restock', 50)}
            disabled={loading}
            className="btn-action btn-restock"
          >
            Restock +50
          </button>
          <button
            onClick={() => handleQuickAction('damage', 1)}
            disabled={loading}
            className="btn-action btn-damage"
          >
            Record Damage -1
          </button>
          <button
            onClick={() => handleQuickAction('set_minimum', 25)}
            disabled={loading}
            className="btn-action btn-set-min"
          >
            Set to 25
          </button>
        </div>
      </div>
      
      {/* Manual Adjustment Form */}
      <div className="adjustment-form">
        <h3>Manual Adjustment</h3>
        
        {error && (
          <div className="alert alert-error">{error}</div>
        )}
        
        <form onSubmit={handleAdjustment}>
          <div className="form-group">
            <label htmlFor="adjustmentType">Operation Type</label>
            <select
              id="adjustmentType"
              value={adjustmentType}
              onChange={(e) => setAdjustmentType(e.target.value)}
              disabled={loading}
            >
              <option value="set">Set Absolute Quantity</option>
              <option value="increment">Increase Stock</option>
              <option value="decrement">Decrease Stock</option>
            </select>
          </div>
          
          <div className="form-group">
            <label htmlFor="quantity">
              {adjustmentType === 'set' ? 'New Stock Quantity' :
               adjustmentType === 'increment' ? 'Quantity to Add' :
               'Quantity to Remove'}
            </label>
            <input
              type="number"
              id="quantity"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              min="0"
              required
              disabled={loading}
              placeholder={
                adjustmentType === 'set' ? 'Enter new total stock' :
                adjustmentType === 'increment' ? 'Enter quantity to add' :
                'Enter quantity to remove'
              }
            />
            {inventory && adjustmentType !== 'set' && (
              <div className="hint">
                Current: {inventory.stock} → New:{' '}
                {adjustmentType === 'increment' 
                  ? inventory.stock + (parseInt(quantity) || 0)
                  : Math.max(0, inventory.stock - (parseInt(quantity) || 0))}
              </div>
            )}
          </div>
          
          <div className="form-group">
            <label htmlFor="reason">Reason for Adjustment</label>
            <select
              id="reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              disabled={loading}
            >
              <option value="">Select a reason</option>
              <option value="restock">Restock from Supplier</option>
              <option value="warehouse_transfer">Warehouse Transfer</option>
              <option value="damaged">Damaged Goods</option>
              <option value="return">Customer Return</option>
              <option value="audit">Inventory Audit</option>
              <option value="other">Other</option>
            </select>
          </div>
          
          <div className="form-group">
            <label htmlFor="notes">Notes (Optional)</label>
            <textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              disabled={loading}
              rows={3}
              placeholder="Additional details about this adjustment..."
            />
          </div>
          
          <button 
            type="submit" 
            disabled={loading || !quantity}
            className="btn-submit"
          >
            {loading ? 'Processing...' : 'Update Inventory'}
          </button>
        </form>
      </div>
      
      {/* Inventory History */}
      {showHistory && (
        <InventoryHistory productId={productId} />
      )}
    </div>
  );
}

export default InventoryManagementPage;
```

### Python with Advanced Inventory Logic
```python
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from decimal import Decimal
import hashlib

class InventoryOperation(Enum):
    """Inventory operation types."""
    SET = "set"
    INCREMENT = "increment"
    DECREMENT = "decrement"

class InventoryAdjustment:
    """Represents an inventory adjustment with full metadata."""
    
    def __init__(
        self,
        product_id: str,
        quantity: int,
        operation: InventoryOperation = InventoryOperation.SET,
        reason: str = "",
        **kwargs
    ):
        self.product_id = product_id
        self.quantity = quantity
        self.operation = operation
        self.reason = reason
        self.notes = kwargs.get('notes', '')
        self.adjustment_id = kwargs.get('adjustment_id')
        self.location = kwargs.get('location')
        self.cost_per_unit = kwargs.get('cost_per_unit')
        self.expires_at = kwargs.get('expires_at')
        self.batch_number = kwargs.get('batch_number')
        self.reserved = kwargs.get('reserved')
        self.metadata = kwargs.get('metadata', {})
        
        # Generate adjustment ID if not provided
        if not self.adjustment_id:
            self.adjustment_id = self._generate_adjustment_id()
        
        # Timestamps
        self.created_at = datetime.utcnow()
        self.created_by = kwargs.get('created_by', 'system')
    
    def _generate_adjustment_id(self) -> str:
        """Generate unique adjustment ID."""
        timestamp = int(self.created_at.timestamp())
        unique_str = f"{self.product_id}_{timestamp}_{self.quantity}_{self.operation.value}"
        return f"adj_{hashlib.md5(unique_str.encode()).hexdigest()[:16]}"
    
    def to_api_payload(self) -> Dict:
        """Convert to API request payload."""
        payload = {
            "stock": self.quantity,
            "operation": self.operation.value,
            "reason": self.reason
        }
        
        # Add optional fields if present
        if self.notes:
            payload["notes"] = self.notes
        if self.adjustment_id:
            payload["adjustment_id"] = self.adjustment_id
        if self.location:
            payload["location"] = self.location
        if self.cost_per_unit is not None:
            payload["cost_per_unit"] = float(self.cost_per_unit)
        if self.expires_at:
            payload["expires_at"] = self.expires_at.isoformat() + 'Z'
        if self.batch_number:
            payload["batch_number"] = self.batch_number
        if self.reserved is not None:
            payload["reserved"] = self.reserved
        
        # Add metadata
        if self.metadata:
            payload["metadata"] = self.metadata
        
        return payload
    
    def calculate_new_stock(self, current_stock: int) -> int:
        """Calculate new stock based on operation."""
        if self.operation == InventoryOperation.SET:
            return self.quantity
        elif self.operation == InventoryOperation.INCREMENT:
            return current_stock + self.quantity
        elif self.operation == InventoryOperation.DECREMENT:
            return max(0, current_stock - self.quantity)
        else:
            raise ValueError(f"Unknown operation: {self.operation}")

class InventoryManager:
    """Comprehensive inventory management system."""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Cache and state
        self.inventory_cache = {}
        self.adjustment_history = []
        self.pending_reservations = {}
    
    def update_inventory(
        self,
        adjustment: InventoryAdjustment,
        options: Optional[Dict] = None
    ) -> Dict:
        """
        Update inventory with the given adjustment.
        
        Args:
            adjustment: InventoryAdjustment object
            options: Additional options
            
        Returns:
            API response
        """
        options = options or {}
        
        # Validate adjustment
        self._validate_adjustment(adjustment)
        
        # Get current inventory
        current_inventory = self.get_inventory(adjustment.product_id)
        
        # Check business rules
        if not options.get('force', False):
            self._check_business_rules(adjustment, current_inventory)
        
        # Prepare request
        headers = {}
        if options.get('idempotency_key'):
            headers['Idempotency-Key'] = options['idempotency_key']
        
        if options.get('require_confirmation'):
            headers['X-Require-Confirmation'] = 'true'
        
        # Make API call
        try:
            response = self.session.patch(
                f"{self.base_url}/products/{adjustment.product_id}/inventory",
                json=adjustment.to_api_payload(),
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            
            result = response.json()
            
            # Update cache
            self._update_inventory_cache(adjustment.product_id, result)
            
            # Record history
            self._record_adjustment(adjustment, current_inventory, result)
            
            # Trigger events
            self._trigger_inventory_events(adjustment, result)
            
            return result
            
        except requests.exceptions.HTTPError as e:
            error_data = e.response.json() if e.response.content else {}
            raise InventoryAPIError(
                f"Inventory update failed: {error_data.get('detail', str(e))}",
                status_code=e.response.status_code,
                error_data=error_data
            )
    
    def bulk_update_inventory(
        self,
        adjustments: List[InventoryAdjustment],
        batch_size: int = 10,
        parallel: bool = True
    ) -> Dict:
        """
        Process multiple inventory adjustments.
        
        Args:
            adjustments: List of InventoryAdjustment objects
            batch_size: Size of processing batches
            parallel: Whether to process in parallel
            
        Returns:
            Bulk update results
        """
        results = {
            'total': len(adjustments),
            'successful': [],
            'failed': [],
            'started_at': datetime.utcnow()
        }
        
        if parallel:
            # Process in parallel batches
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
                # Submit all adjustments
                future_to_adj = {
                    executor.submit(self._safe_update, adj): adj 
                    for adj in adjustments
                }
                
                # Process results as they complete
                for future in concurrent.futures.as_completed(future_to_adj):
                    adj = future_to_adj[future]
                    try:
                        result = future.result()
                        results['successful'].append({
                            'product_id': adj.product_id,
                            'adjustment_id': adj.adjustment_id,
                            'result': result
                        })
                    except Exception as e:
                        results['failed'].append({
                            'product_id': adj.product_id,
                            'adjustment_id': adj.adjustment_id,
                            'error': str(e)
                        })
        else:
            # Process sequentially
            for adj in adjustments:
                try:
                    result = self._safe_update(adj)
                    results['successful'].append({
                        'product_id': adj.product_id,
                        'adjustment_id': adj.adjustment_id,
                        'result': result
                    })
                except Exception as e:
                    results['failed'].append({
                        'product_id': adj.product_id,
                        'adjustment_id': adj.adjustment_id,
                        'error': str(e)
                    })
        
        results['completed_at'] = datetime.utcnow()
        results['duration'] = (results['completed_at'] - results['started_at']).total_seconds()
        
        # Generate summary statistics
        results['summary'] = self._generate_bulk_summary(results['successful'])
        
        return results
    
    def reserve_inventory(
        self,
        product_id: str,
        quantity: int,
        reservation_data: Dict
    ) -> Dict:
        """
        Reserve inventory for an order.
        
        Args:
            product_id: Product identifier
            quantity: Quantity to reserve
            reservation_data: Reservation metadata
            
        Returns:
            Reservation result
        """
        # Get current inventory
        inventory = self.get_inventory(product_id)
        
        # Check availability
        available = inventory.get('available', inventory['stock'])
        if quantity > available:
            raise InventoryInsufficientError(
                f"Insufficient inventory. Available: {available}, Requested: {quantity}",
                available=available,
                requested=quantity
            )
        
        # Create reservation adjustment
        reservation = InventoryAdjustment(
            product_id=product_id,
            quantity=inventory['stock'],  # Keep total stock same
            operation=InventoryOperation.SET,
            reason='order_reservation',
            notes=f"Reservation for {reservation_data.get('order_id', 'unknown')}",
            reserved=(inventory.get('reserved', 0) + quantity),
            metadata={
                'reservation_id': reservation_data.get('reservation_id'),
                'order_id': reservation_data.get('order_id'),
                'customer_id': reservation_data.get('customer_id'),
                'expires_at': reservation_data.get('expires_at'),
                'reserved_quantity': quantity
            }
        )
        
        # Store reservation
        reservation_key = f"{product_id}_{reservation_data.get('reservation_id', 'temp')}"
        self.pending_reservations[reservation_key] = {
            'adjustment': reservation,
            'created_at': datetime.utcnow(),
            'data': reservation_data
        }
        
        # Update inventory
        return self.update_inventory(reservation, {
            'idempotency_key': reservation_key
        })
    
    def release_reservation(
        self,
        product_id: str,
        reservation_id: str,
        reason: str = 'order_cancelled'
    ) -> Dict:
        """
        Release previously reserved inventory.
        
        Args:
            product_id: Product identifier
            reservation_id: Reservation identifier
            reason: Reason for release
            
        Returns:
            Release result
        """
        reservation_key = f"{product_id}_{reservation_id}"
        
        if reservation_key not in self.pending_reservations:
            raise ReservationNotFoundError(
                f"Reservation {reservation_id} not found for product {product_id}"
            )
        
        reservation = self.pending_reservations[reservation_key]
        
        # Get current inventory
        inventory = self.get_inventory(product_id)
        
        # Calculate released quantity
        reserved_quantity = reservation['adjustment'].metadata.get('reserved_quantity', 0)
        new_reserved = max(0, inventory.get('reserved', 0) - reserved_quantity)
        
        # Create release adjustment
        release = InventoryAdjustment(
            product_id=product_id,
            quantity=inventory['stock'],  # Keep total stock same
            operation=InventoryOperation.SET,
            reason=reason,
            notes=f"Release reservation {reservation_id}",
            reserved=new_reserved,
            metadata={
                'released_reservation': reservation_id,
                'released_quantity': reserved_quantity
            }
        )
        
        # Remove from pending reservations
        del self.pending_reservations[reservation_key]
        
        return self.update_inventory(release, {
            'idempotency_key': f"release_{reservation_key}"
        })
    
    def process_sale(
        self,
        product_id: str,
        quantity: int,
        sale_data: Dict
    ) -> Dict:
        """
        Process inventory for a sale.
        
        Args:
            product_id: Product identifier
            quantity: Quantity sold
            sale_data: Sale metadata
            
        Returns:
            Sale processing result
        """
        # Get current inventory
        inventory = self.get_inventory(product_id)
        
        # Calculate adjustments
        new_stock = max(0, inventory['stock'] - quantity)
        
        # Reduce reserved if applicable
        new_reserved = inventory.get('reserved', 0)
        if sale_data.get('reduce_reserved', True):
            reserved_reduction = min(quantity, new_reserved)
            new_reserved = max(0, new_reserved - reserved_reduction)
        
        # Check for backorder
        available = inventory.get('available', inventory['stock'])
        backorder_quantity = 0
        if quantity > available and sale_data.get('allow_backorder', False):
            backorder_quantity = quantity - available
        
        # Create sale adjustment
        sale_adjustment = InventoryAdjustment(
            product_id=product_id,
            quantity=new_stock,
            operation=InventoryOperation.SET,
            reason='sale_fulfillment',
            notes=f"Sale for order {sale_data.get('order_id', 'unknown')}",
            reserved=new_reserved,
            metadata={
                'order_id': sale_data.get('order_id'),
                'sale_quantity': quantity,
                'backorder_quantity': backorder_quantity,
                'reserved_reduced': min(quantity, inventory.get('reserved', 0))
            }
        )
        
        result = self.update_inventory(sale_adjustment, {
            'idempotency_key': f"sale_{sale_data.get('order_id', 'temp')}_{product_id}"
        })
        
        # Handle backorder if needed
        if backorder_quantity > 0:
            self._create_backorder(product_id, backorder_quantity, sale_data)
            result['backorder_created'] = True
            result['backorder_quantity'] = backorder_quantity
        
        return result
    
    def get_inventory(self, product_id: str, force_refresh: bool = False) -> Dict:
        """
        Get current inventory for a product.
        
        Args:
            product_id: Product identifier
            force_refresh: Whether to bypass cache
            
        Returns:
            Inventory data
        """
        # Check cache
        if not force_refresh and product_id in self.inventory_cache:
            cached = self.inventory_cache[product_id]
            cache_age = (datetime.utcnow() - cached['timestamp']).total_seconds()
            if cache_age < 30:  # 30 second cache
                return cached['data']
        
        try:
            response = self.session.get(
                f"{self.base_url}/products/{product_id}",
                timeout=10
            )
            response.raise_for_status()
            
            product = response.json()
            inventory = {
                'stock': product['stock'],
                'available': product.get('available', product['stock']),
                'reserved': product.get('reserved', 0),
                'reorder_threshold': product.get('reorder_threshold'),
                'backorder_allowed': product.get('backorder_allowed', False),
                'updated_at': product['updated_at']
            }
            
            # Update cache
            self.inventory_cache[product_id] = {
                'data': inventory,
                'timestamp': datetime.utcnow()
            }
            
            return inventory
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ProductNotFoundError(f"Product {product_id} not found")
            raise
    
    def get_inventory_history(
        self,
        product_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get inventory history for a product.
        
        Args:
            product_id: Product identifier
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum number of records
            
        Returns:
            Inventory history
        """
        params = {'limit': limit}
        
        if start_date:
            params['start_date'] = start_date.isoformat() + 'Z'
        if end_date:
            params['end_date'] = end_date.isoformat() + 'Z'
        
        try:
            response = self.session.get(
                f"{self.base_url}/products/{product_id}/inventory/history",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return []
            raise
    
    def check_low_stock(
        self,
        product_ids: List[str],
        threshold: Optional[int] = None
    ) -> Dict:
        """
        Check for low stock across multiple products.
        
        Args:
            product_ids: List of product IDs to check
            threshold: Custom threshold (overrides product reorder_threshold)
            
        Returns:
            Low stock report
        """
        low_stock = []
        
        for product_id in product_ids:
            try:
                inventory = self.get_inventory(product_id)
                
                # Determine threshold
                check_threshold = threshold or inventory.get('reorder_threshold')
                if check_threshold is None:
                    continue
                
                available = inventory.get('available', inventory['stock'])
                
                if available <= check_threshold:
                    low_stock.append({
                        'product_id': product_id,
                        'current_stock': available,
                        'total_stock': inventory['stock'],
                        'reserved': inventory.get('reserved', 0),
                        'threshold': check_threshold,
                        'status': 'critical' if available <= check_threshold * 0.5 else 'warning',
                        'last_updated': inventory['updated_at']
                    })
                    
            except Exception as e:
                print(f"Warning: Failed to check stock for {product_id}: {e}")
        
        # Sort by status and stock level
        low_stock.sort(key=lambda x: (x['status'] == 'critical', x['current_stock']))
        
        return {
            'low_stock_products': low_stock,
            'total_checked': len(product_ids),
            'critical_count': len([p for p in low_stock if p['status'] == 'critical']),
            'warning_count': len([p for p in low_stock if p['status'] == 'warning'])
        }
    
    def expire_old_reservations(self, max_age_minutes: int = 30):
        """
        Expire old reservations.
        
        Args:
            max_age_minutes: Maximum age in minutes
        """
        expired = []
        now = datetime.utcnow()
        
        for key, reservation in list(self.pending_reservations.items()):
            age = (now - reservation['created_at']).total_seconds() / 60
            
            if age > max_age_minutes:
                # Auto-release expired reservation
                try:
                    product_id, reservation_id = key.split('_', 1)
                    self.release_reservation(
                        product_id,
                        reservation_id,
                        reason='reservation_expired'
                    )
                    expired.append(key)
                except Exception as e:
                    print(f"Failed to expire reservation {key}: {e}")
        
        return expired
    
    # Private helper methods
    def _safe_update(self, adjustment: InventoryAdjustment) -> Dict:
        """Safe wrapper for inventory updates with error handling."""
        try:
            return self.update_inventory(adjustment)
        except InventoryAPIError as e:
            if e.status_code == 409:  # Conflict
                # Check if it's an idempotency conflict
                if 'already been processed' in str(e.error_data):
                    # Return cached result
                    return self._get_cached_adjustment_result(adjustment.adjustment_id)
            raise
    
    def _validate_adjustment(self, adjustment: InventoryAdjustment):
        """Validate inventory adjustment."""
        if adjustment.quantity < 0:
            raise ValidationError("Stock quantity cannot be negative")
        
        if adjustment.reserved is not None and adjustment.reserved < 0:
            raise ValidationError("Reserved quantity cannot be negative")
        
        if adjustment.reserved is not None and adjustment.quantity < adjustment.reserved:
            raise ValidationError("Total stock cannot be less than reserved quantity")
        
        if adjustment.reason and len(adjustment.reason) > 100:
            raise ValidationError("Reason cannot exceed 100 characters")
    
    def _check_business_rules(self, adjustment: InventoryAdjustment, current_inventory: Dict):
        """Check business rules before applying adjustment."""
        new_stock = adjustment.calculate_new_stock(current_inventory['stock'])
        
        # Check minimum stock
        if new_stock < 0:
            raise BusinessRuleError("Stock cannot be negative")
        
        # Check reserved constraints
        current_reserved = current_inventory.get('reserved', 0)
        if new_stock < current_reserved:
            raise BusinessRuleError(
                f"Stock cannot be less than reserved quantity ({current_reserved})"
            )
        
        # Check for massive adjustments (possible error)
        if abs(new_stock - current_inventory['stock']) > 10000:
            # This would typically trigger a confirmation requirement
            pass
    
    def _update_inventory_cache(self, product_id: str, result: Dict):
        """Update inventory cache with new data."""
        self.inventory_cache[product_id] = {
            'data': {
                'stock': result['stock'],
                'available': result.get('available', result['stock']),
                'reserved': result.get('reserved', 0),
                'updated_at': result['updated_at']
            },
            'timestamp': datetime.utcnow()
        }
    
    def _record_adjustment(
        self,
        adjustment: InventoryAdjustment,
        previous_inventory: Dict,
        result: Dict
    ):
        """Record adjustment in history."""
        history_entry = {
            'adjustment_id': adjustment.adjustment_id,
            'product_id': adjustment.product_id,
            'timestamp': datetime.utcnow().isoformat(),
            'operation': adjustment.operation.value,
            'quantity': adjustment.quantity,
            'reason': adjustment.reason,
            'notes': adjustment.notes,
            'previous_stock': previous_inventory['stock'],
            'new_stock': result['stock'],
            'adjustment': result.get('adjustment', 0),
            'adjusted_by': adjustment.created_by,
            'metadata': adjustment.metadata
        }
        
        self.adjustment_history.append(history_entry)
        
        # Keep only last 1000 entries
        if len(self.adjustment_history) > 1000:
            self.adjustment_history.pop(0)
    
    def _trigger_inventory_events(self, adjustment: InventoryAdjustment, result: Dict):
        """Trigger inventory-related events."""
        # Check for low stock
        if result['stock'] <= (result.get('reorder_threshold') or 10):
            self._trigger_low_stock_alert(adjustment.product_id, result)
        
        # Check for stockout
        if result['stock'] == 0:
            self._trigger_stockout_alert(adjustment.product_id, result)
        
        # Log to audit trail
        self._log_to_audit_trail(adjustment, result)
    
    def _trigger_low_stock_alert(self, product_id: str, inventory: Dict):
        """Trigger low stock alert."""
        print(f"Low stock alert: Product {product_id} has {inventory['stock']} units")
        # In production, send notification or trigger workflow
    
    def _trigger_stockout_alert(self, product_id: str, inventory: Dict):
        """Trigger stockout alert."""
        print(f"Stockout alert: Product {product_id} is out of stock")
        # In production, send notification or trigger reorder
    
    def _log_to_audit_trail(self, adjustment: InventoryAdjustment, result: Dict):
        """Log to audit trail."""
        # Implementation depends on audit system
        pass
    
    def _create_backorder(self, product_id: str, quantity: int, sale_data: Dict):
        """Create backorder record."""
        print(f"Creating backorder for {quantity} units of {product_id}")
        # Implementation depends on backorder system
    
    def _generate_bulk_summary(self, successful_results: List[Dict]) -> Dict:
        """Generate summary for bulk operations."""
        if not successful_results:
            return {}
        
        total_adjustment = sum(
            result['result'].get('adjustment', 0) 
            for result in successful_results
        )
        
        return {
            'total_adjustment': total_adjustment,
            'average_adjustment': total_adjustment / len(successful_results),
            'affected_products': len(successful_results),
            'total_stock_after': sum(
                result['result']['stock'] 
                for result in successful_results
            )
        }
    
    def _get_cached_adjustment_result(self, adjustment_id: str) -> Optional[Dict]:
        """Get cached result for an adjustment."""
        for entry in self.adjustment_history:
            if entry['adjustment_id'] == adjustment_id:
                return {
                    'stock': entry['new_stock'],
                    'adjustment': entry['adjustment'],
                    'adjustment_id': adjustment_id,
                    'from_cache': True
                }
        return None

# Custom Exceptions
class InventoryAPIError(Exception):
    def __init__(self, message, status_code=None, error_data=None):
        super().__init__(message)
        self.status_code = status_code
        self.error_data = error_data

class ValidationError(Exception):
    pass

class BusinessRuleError(Exception):
    pass

class InventoryInsufficientError(Exception):
    def __init__(self, message, available=None, requested=None):
        super().__init__(message)
        self.available = available
        self.requested = requested

class ReservationNotFoundError(Exception):
    pass

class ProductNotFoundError(Exception):
    pass

# Usage Examples
def demonstrate_inventory_operations():
    """Demonstrate various inventory operations."""
    
    manager = InventoryManager(
        base_url="http://localhost:8000/api",
        token="your_admin_token_here"
    )
    
    product_id = "prod_789"
    
    try:
        # Example 1: Get current inventory
        print("Example 1: Getting current inventory...")
        inventory = manager.get_inventory(product_id)
        print(f"Current inventory: {inventory}")
        
        # Example 2: Simple restock
        print("\nExample 2: Restocking product...")
        restock = InventoryAdjustment(
            product_id=product_id,
            quantity=50,
            operation=InventoryOperation.INCREMENT,
            reason="weekly_restock",
            notes="Restock from main supplier"
        )
        
        result1 = manager.update_inventory(restock)
        print(f"Restock result: {result1}")
        
        # Example 3: Reserve inventory for order
        print("\nExample 3: Reserving inventory...")
        result2 = manager.reserve_inventory(
            product_id=product_id,
            quantity=5,
            reservation_data={
                'order_id': 'order_12345',
                'customer_id': 'cust_67890',
                'reservation_id': 'res_20240115'
            }
        )
        print(f"Reservation result: {result2}")
        
        # Example 4: Process sale
        print("\nExample 4: Processing sale...")
        result3 = manager.process_sale(
            product_id=product_id,
            quantity=3,
            sale_data={
                'order_id': 'order_12345',
                'reduce_reserved': True,
                'allow_backorder': False
            }
        )
        print(f"Sale result: {result3}")
        
        # Example 5: Bulk update
        print("\nExample 5: Bulk inventory update...")
        adjustments = [
            InventoryAdjustment(
                product_id='prod_789',
                quantity=100,
                operation=InventoryOperation.SET,
                reason='inventory_correction'
            ),
            InventoryAdjustment(
                product_id='prod_790',
                quantity=200,
                operation=InventoryOperation.SET,
                reason='inventory_correction'
            )
        ]
        
        bulk_result = manager.bulk_update_inventory(adjustments, parallel=True)
        print(f"Bulk update: {bulk_result['summary']}")
        
        # Example 6: Check low stock
        print("\nExample 6: Checking low stock...")
        low_stock = manager.check_low_stock(['prod_789', 'prod_790'], threshold=20)
        print(f"Low stock products: {len(low_stock['low_stock_products'])}")
        
        # Example 7: Get inventory history
        print("\nExample 7: Getting inventory history...")
        history = manager.get_inventory_history(
            product_id,
            start_date=datetime.utcnow() - timedelta(days=7),
            limit=10
        )
        print(f"Recent history entries: {len(history)}")
        
    except InventoryAPIError as e:
        print(f"Inventory API error: {e}")
        if e.error_data:
            print(f"Error details: {e.error_data}")
    except InventoryInsufficientError as e:
        print(f"Insufficient inventory: {e}")
        print(f"Available: {e.available}, Requested: {e.requested}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    demonstrate_inventory_operations()
```

### Best Practices for Inventory Management

#### 1. **Atomic Operations**
```javascript
// Ensure inventory updates are atomic
async function updateInventoryAtomic(productId, adjustment) {
  // Use database transactions or optimistic concurrency control
  const result = await fetch(`/api/products/${productId}/inventory`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'If-Match': currentVersion // Optimistic concurrency
    },
    body: JSON.stringify(adjustment)
  });
  
  if (result.status === 412) {
    // Version conflict - retry with fresh data
    return updateInventoryAtomic(productId, adjustment);
  }
  
  return result.json();
}
```

#### 2. **Real-time Updates**
```javascript
// Use WebSockets for real-time inventory updates
class RealtimeInventory {
  constructor(productId) {
    this.productId = productId;
    this.ws = new WebSocket(`wss://api.example.com/inventory/${productId}`);
    this.listeners = new Set();
    
    this.ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      this.notifyListeners(update);
    };
  }
  
  subscribe(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }
  
  notifyListeners(update) {
    this.listeners.forEach(callback => callback(update));
  }
}
```

#### 3. **Batch Processing**
```javascript
// Process inventory updates in batches for performance
async function processInventoryBatch(updates) {
  const batchResult = await fetch('/api/inventory/batch', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ updates })
  });
  
  return batchResult.json();
}
```

#### 4. **Audit Trail**
```javascript
// Maintain complete audit trail
class InventoryAudit {
  constructor() {
    this.auditLog = [];
  }
  
  logAdjustment(productId, adjustment, userId, ip) {
    const entry = {
      id: generateId(),
      productId,
      timestamp: new Date().toISOString(),
      userId,
      ipAddress: ip,
      adjustment,
      metadata: {
        userAgent: navigator.userAgent,
        sessionId: getSessionId()
      }
    };
    
    this.auditLog.push(entry);
    
    // Send to audit service
    this.sendToAuditService(entry);
    
    // Store locally for redundancy
    this.storeLocalCopy(entry);
  }
}
```

### Security Considerations

#### 1. **Authorization Levels**
```javascript
// Implement granular inventory permissions
const inventoryPermissions = {
  view: ['admin', 'manager', 'staff'],
  adjust: ['admin', 'manager'],
  reserve: ['admin', 'manager', 'sales'],
  bulk_update: ['admin'],
  history_view: ['admin', 'manager', 'auditor']
};

function checkInventoryPermission(userRole, action) {
  return inventoryPermissions[action]?.includes(userRole) || false;
}
```

#### 2. **Rate Limiting**
```javascript
// Prevent inventory abuse
class InventoryRateLimiter {
  constructor() {
    this.userLimits = new Map();
    this.ipLimits = new Map();
  }
  
  canAdjust(userId, ip) {
    const userKey = `user:${userId}`;
    const ipKey = `ip:${ip}`;
    
    const userLimit = this.checkLimit(userKey, 100); // 100 per hour per user
    const ipLimit = this.checkLimit(ipKey, 1000); // 1000 per hour per IP
    
    return userLimit.allowed && ipLimit.allowed;
  }
}
```

#### 3. **Validation Rules**
```javascript
// Comprehensive validation
const inventoryValidationRules = {
  stock: {
    min: 0,
    max: 1000000,
    increment: 1 // Must be integer
  },
  reserved: {
    maxPercentage: 0.8 // Cannot reserve more than 80% of stock
  },
  adjustments: {
    maxDaily: 50, // Max 50 adjustments per product per day
    maxSingle: 10000 // Cannot adjust more than 10k units at once
  }
};
```

---

## Related Endpoints
- [GET /products/{productId}](../products/get-product.md) - Get product including stock
- [GET /products/{productId}/inventory/history](../../endpoints/inventory-history.md) - Get inventory history
- [POST /inventory/batch-update](../../endpoints/bulk-inventory.md) - Bulk inventory operations
- [GET /inventory/low-stock](../../endpoints/low-stock.md) - Get low stock alerts
- [Error Responses](../../errors.md) - Error handling details

## Notes
- Inventory updates are idempotent when using adjustment_id
- Consider implementing inventory snapshots for reporting
- Use WebSockets for real-time inventory updates in multi-user environments
- Implement dead stock detection and alerts
- Consider seasonality and trends in inventory planning
- Integrate with warehouse management systems for accurate counts

## Compliance and Reporting
- Maintain inventory audit trail for financial reporting
- Implement cycle counting procedures
- Track inventory aging and expiration
- Generate inventory valuation reports
- Comply with industry-specific inventory regulations

## Performance Optimization
- Cache frequently accessed inventory data
- Use batch operations for mass updates
- Implement read replicas for inventory queries
- Use materialized views for inventory reports
- Consider eventual consistency for non-critical updates