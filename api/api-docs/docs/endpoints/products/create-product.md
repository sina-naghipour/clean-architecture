# POST /products

**Create Product** - Create a new product in the catalog (Admin Only)

**Tags:** Products

**Authentication:** Required (Bearer Token with Admin privileges)

---

## Description
Create a new product in the ecommerce catalog. This endpoint is restricted to administrators only. Products can include images, tags, pricing, and inventory information.

## Authentication
**Required:** Bearer Token with Admin role

### Headers
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

## Request

### Body
**Schema:** ProductRequest

```json
{
  "name": "Premium Wireless Keyboard",
  "price": 89.99,
  "stock": 150,
  "description": "Mechanical wireless keyboard with RGB backlighting, customizable macros, and 4000mAh battery.",
  "tags": ["electronics", "keyboard", "gaming", "wireless"],
  "images": [
    "/static/img/products/temp/keyboard-main.jpg",
    "/static/img/products/temp/keyboard-angle.jpg"
  ],
  "sku": "KB-PRO-2023",
  "category": "Computer Accessories",
  "brand": "TechGear",
  "specifications": {
    "connection": "Wireless 2.4GHz + Bluetooth 5.0",
    "switch_type": "Mechanical (Blue)",
    "keycaps": "Double-shot PBT",
    "battery": "4000mAh",
    "backlight": "RGB per-key",
    "weight": "1.2kg"
  },
  "features": [
    "Hot-swappable switches",
    "On-board memory for profiles",
    "N-key rollover",
    "Detachable USB-C cable",
    "Adjustable feet"
  ],
  "weight": 1.2,
  "dimensions": {
    "length": 44.5,
    "width": 15.2,
    "height": 3.8
  },
  "is_active": true,
  "is_featured": false,
  "original_price": 109.99,
  "tax_rate": 0.08,
  "meta_title": "Premium Wireless Mechanical Keyboard | TechGear",
  "meta_description": "High-performance wireless mechanical keyboard with RGB lighting and customizable macros for gaming and productivity."
}
```

**Required Fields:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `name` | string | ✓ | 3-200 characters | Product name |
| `price` | number | ✓ | ≥ 0 | Product price |

**Optional Fields:**

| Field | Type | Constraints | Description | Default |
|-------|------|-------------|-------------|---------|
| `stock` | integer | ≥ 0 | Available quantity | `0` |
| `description` | string | ≤ 5000 chars | Detailed description | `""` |
| `tags` | string[] | ≤ 20 tags | Product categories/tags | `[]` |
| `images` | string[] | ≤ 10 images | Image URLs | `[]` |
| `sku` | string | Unique | Stock Keeping Unit | Auto-generated |
| `category` | string | - | Product category | `"Uncategorized"` |
| `brand` | string | - | Manufacturer brand | `null` |
| `specifications` | object | - | Technical specs | `{}` |
| `features` | string[] | ≤ 50 items | Key features | `[]` |
| `weight` | number | ≥ 0 | Weight in kg | `null` |
| `dimensions` | object | - | {length, width, height} cm | `null` |
| `is_active` | boolean | - | Product visibility | `true` |
| `is_featured` | boolean | - | Featured product | `false` |
| `original_price` | number | ≥ price | Original price for discounts | `null` |
| `tax_rate` | number | 0-1 | Tax rate (0.08 = 8%) | `0.08` |
| `meta_title` | string | ≤ 60 chars | SEO meta title | Based on name |
| `meta_description` | string | ≤ 160 chars | SEO meta description | Based on description |
| `variant_of` | string | - | Parent product ID for variants | `null` |
| `options` | object | - | Variant options \{color, size, etc.\} | `{}` |
| `supplier` | string | - | Supplier information | `null` |
| `reorder_level` | integer | ≥ 0 | Stock reorder threshold | `10` |
| `lead_time` | integer | ≥ 0 | Days to restock | `7` |

## Responses

### 201 Created - Product successfully created
**Headers:**
- `Location`: `/products/prod_new_id` (URI to created product)
- `X-Product-ID`: `prod_new_id` (Product identifier)

**Body:**
```json
{
  "id": "prod_789",
  "name": "Premium Wireless Keyboard",
  "price": 89.99,
  "stock": 150,
  "description": "Mechanical wireless keyboard with RGB backlighting, customizable macros, and 4000mAh battery.",
  "tags": ["electronics", "keyboard", "gaming", "wireless"],
  "images": [
    "/static/img/products/prod_789/keyboard-main.jpg",
    "/static/img/products/prod_789/keyboard-angle.jpg"
  ],
  "primaryImageId": null,
  "sku": "KB-PRO-2023",
  "category": "Computer Accessories",
  "brand": "TechGear",
  "specifications": {
    "connection": "Wireless 2.4GHz + Bluetooth 5.0",
    "switch_type": "Mechanical (Blue)",
    "keycaps": "Double-shot PBT",
    "battery": "4000mAh",
    "backlight": "RGB per-key"
  },
  "features": [
    "Hot-swappable switches",
    "On-board memory for profiles",
    "N-key rollover",
    "Detachable USB-C cable",
    "Adjustable feet"
  ],
  "weight": 1.2,
  "dimensions": {
    "length": 44.5,
    "width": 15.2,
    "height": 3.8
  },
  "is_active": true,
  "is_featured": false,
  "original_price": 109.99,
  "tax_rate": 0.08,
  "meta_title": "Premium Wireless Mechanical Keyboard | TechGear",
  "meta_description": "High-performance wireless mechanical keyboard with RGB lighting and customizable macros for gaming and productivity.",
  "created_at": "2023-12-15T10:30:00Z",
  "updated_at": "2023-12-15T10:30:00Z",
  "variant_of": null,
  "options": {},
  "supplier": "TechGear Inc.",
  "reorder_level": 10,
  "lead_time": 7,
  "slug": "premium-wireless-keyboard-prod-789"
}
```

### 400 Bad Request - Invalid input
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/bad-request",
  "title": "Bad Request",
  "status": 400,
  "detail": "Invalid price: must be greater than or equal to 0.",
  "instance": "/products",
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
  "instance": "/products"
}
```

### 403 Forbidden - Insufficient permissions
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "Insufficient permissions to create products.",
  "instance": "/products"
}
```

### 409 Conflict - Duplicate SKU or slug
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/conflict",
  "title": "Conflict",
  "status": 409,
  "detail": "SKU 'KB-PRO-2023' already exists.",
  "instance": "/products"
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
  "instance": "/products",
  "errors": [
    {
      "field": "name",
      "message": "must be between 3 and 200 characters"
    },
    {
      "field": "images",
      "message": "maximum 10 images allowed"
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
  "detail": "Failed to create product due to database error.",
  "instance": "/products"
}
```

## Examples

### Basic cURL Request
```bash
# Create a simple product
curl -X POST "http://localhost:8000/api/products" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Basic Mouse",
    "price": 19.99,
    "description": "A simple wired mouse"
  }'
```

### Complete cURL Request
```bash
curl -X POST "http://localhost:8000/api/products" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Wireless Keyboard",
    "price": 89.99,
    "stock": 150,
    "description": "Mechanical wireless keyboard with RGB backlighting.",
    "tags": ["electronics", "keyboard", "gaming"],
    "sku": "KB-PRO-2023",
    "category": "Computer Accessories",
    "brand": "TechGear",
    "specifications": {
      "connection": "Wireless 2.4GHz + Bluetooth 5.0",
      "switch_type": "Mechanical"
    },
    "features": [
      "Hot-swappable switches",
      "RGB backlighting"
    ],
    "weight": 1.2,
    "original_price": 109.99,
    "is_featured": true
  }'
```

### JavaScript (Fetch) with Validation
```javascript
/**
 * Product creation service with comprehensive validation
 */
class ProductCreator {
  constructor(apiUrl = 'http://localhost:8000/api') {
    this.apiUrl = apiUrl;
  }
  
  /**
   * Create a new product
   */
  async createProduct(productData, accessToken) {
    // Validate required fields
    const validation = this.validateProductData(productData);
    if (!validation.valid) {
      throw new ValidationError('Product validation failed', validation.errors);
    }
    
    // Prepare request
    const headers = {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      'X-Request-ID': this.generateRequestId()
    };
    
    try {
      const response = await fetch(`${this.apiUrl}/products`, {
        method: 'POST',
        headers,
        body: JSON.stringify(productData)
      });
      
      // Parse response
      const contentType = response.headers.get('content-type');
      let data;
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      }
      
      // Handle different status codes
      if (response.status === 201) {
        const productId = response.headers.get('X-Product-ID') || data.id;
        const location = response.headers.get('Location');
        
        // Track analytics
        this.trackProductCreation(productId, productData);
        
        return {
          success: true,
          product: data,
          productId,
          location,
          headers: Object.fromEntries(response.headers.entries())
        };
      } else if (response.status === 409) {
        throw new ConflictError(data?.detail || 'Product conflict error', data);
      } else if (response.status === 422) {
        throw new ValidationError('Validation failed', data?.errors || []);
      } else if (!response.ok) {
        throw new ProductCreationError(
          `Failed to create product: ${response.status}`,
          data,
          response.status
        );
      }
    } catch (error) {
      if (error instanceof ValidationError || error instanceof ConflictError) {
        throw error;
      }
      
      // Network or unknown error
      throw new ProductCreationError(
        `Network error: ${error.message}`,
        null,
        null,
        error
      );
    }
  }
  
  /**
   * Validate product data before sending
   */
  validateProductData(data) {
    const errors = [];
    
    // Required fields
    if (!data.name || data.name.trim().length < 3) {
      errors.push({
        field: 'name',
        message: 'Product name must be at least 3 characters'
      });
    }
    
    if (!data.name || data.name.trim().length > 200) {
      errors.push({
        field: 'name',
        message: 'Product name cannot exceed 200 characters'
      });
    }
    
    if (typeof data.price !== 'number' || data.price < 0) {
      errors.push({
        field: 'price',
        message: 'Price must be a non-negative number'
      });
    }
    
    // Optional field validations
    if (data.stock !== undefined) {
      if (!Number.isInteger(data.stock) || data.stock < 0) {
        errors.push({
          field: 'stock',
          message: 'Stock must be a non-negative integer'
        });
      }
    }
    
    if (data.tags && Array.isArray(data.tags)) {
      if (data.tags.length > 20) {
        errors.push({
          field: 'tags',
          message: 'Maximum 20 tags allowed'
        });
      }
      
      // Validate each tag
      data.tags.forEach((tag, index) => {
        if (typeof tag !== 'string' || tag.trim().length === 0) {
          errors.push({
            field: `tags[${index}]`,
            message: 'Tag must be a non-empty string'
          });
        }
      });
    }
    
    if (data.original_price !== undefined && data.price !== undefined) {
      if (data.original_price < data.price) {
        errors.push({
          field: 'original_price',
          message: 'Original price cannot be less than current price'
        });
      }
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
  
  /**
   * Generate unique request ID for tracking
   */
  generateRequestId() {
    return `prod_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  /**
   * Track product creation for analytics
   */
  trackProductCreation(productId, productData) {
    // Send to analytics service
    if (window.gtag) {
      window.gtag('event', 'create_product', {
        product_id: productId,
        product_name: productData.name,
        product_price: productData.price,
        product_category: productData.category || 'Uncategorized'
      });
    }
    
    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`Product created: ${productId}`, productData);
    }
  }
  
  /**
   * Create product with image uploads
   */
  async createProductWithImages(productData, imageFiles, accessToken) {
    // First, create the product
    const result = await this.createProduct(productData, accessToken);
    
    // Then upload images if provided
    if (imageFiles && imageFiles.length > 0) {
      const uploadPromises = imageFiles.map(file => 
        this.uploadProductImage(result.productId, file, accessToken)
      );
      
      await Promise.all(uploadPromises);
      
      // Refresh product to get updated images
      return this.getProduct(result.productId, accessToken);
    }
    
    return result;
  }
  
  /**
   * Helper method to upload product images
   */
  async uploadProductImage(productId, imageFile, accessToken) {
    const formData = new FormData();
    formData.append('file', imageFile);
    formData.append('productId', productId);
    
    const response = await fetch(`${this.apiUrl}/files`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`
      },
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`Failed to upload image: ${response.status}`);
    }
    
    return response.json();
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
}

// Custom Error Classes
class ValidationError extends Error {
  constructor(message, errors = []) {
    super(message);
    this.name = 'ValidationError';
    this.errors = errors;
  }
}

class ConflictError extends Error {
  constructor(message, details = null) {
    super(message);
    this.name = 'ConflictError';
    this.details = details;
  }
}

class ProductCreationError extends Error {
  constructor(message, responseData = null, statusCode = null, originalError = null) {
    super(message);
    this.name = 'ProductCreationError';
    this.responseData = responseData;
    this.statusCode = statusCode;
    this.originalError = originalError;
  }
}

// Usage Example
async function handleProductCreation() {
  const productCreator = new ProductCreator();
  const accessToken = localStorage.getItem('accessToken');
  
  const productData = {
    name: "Premium Wireless Keyboard",
    price: 89.99,
    stock: 150,
    description: "Mechanical wireless keyboard with RGB backlighting.",
    tags: ["electronics", "keyboard", "gaming"],
    category: "Computer Accessories",
    brand: "TechGear",
    is_featured: true
  };
  
  try {
    const result = await productCreator.createProduct(productData, accessToken);
    
    console.log('Product created successfully:', {
      id: result.productId,
      name: result.product.name,
      location: result.location
    });
    
    // Navigate to product page or show success message
    alert(`Product "${result.product.name}" created successfully!`);
    window.location.href = `/admin/products/${result.productId}`;
    
  } catch (error) {
    console.error('Product creation failed:', error);
    
    if (error instanceof ValidationError) {
      // Show validation errors to user
      error.errors.forEach(err => {
        console.error(`Field ${err.field}: ${err.message}`);
      });
      alert('Please fix the validation errors and try again.');
    } else if (error instanceof ConflictError) {
      alert(`Conflict: ${error.message}. Please use a different SKU or name.`);
    } else {
      alert('Failed to create product. Please try again later.');
    }
  }
}
```

### React Admin Component Example
```jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ProductForm from './ProductForm';
import ImageUploader from './ImageUploader';

function CreateProductPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [images, setImages] = useState([]);
  
  const handleSubmit = async (productData) => {
    setLoading(true);
    setError(null);
    
    try {
      const accessToken = localStorage.getItem('accessToken');
      
      // Create product
      const productResponse = await fetch('http://localhost:8000/api/products', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(productData)
      });
      
      if (!productResponse.ok) {
        const errorData = await productResponse.json();
        throw new Error(errorData.detail || 'Failed to create product');
      }
      
      const product = await productResponse.json();
      const productId = product.id;
      
      // Upload images if any
      if (images.length > 0) {
        await uploadImages(productId, images, accessToken);
      }
      
      // Success - redirect to product page
      navigate(`/admin/products/${productId}`, {
        state: { message: 'Product created successfully!' }
      });
      
    } catch (err) {
      setError(err.message);
      console.error('Create product error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const uploadImages = async (productId, imageFiles, accessToken) => {
    const uploadPromises = imageFiles.map(file => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('productId', productId);
      formData.append('is_primary', false); // Will set first as primary
      
      return fetch('http://localhost:8000/api/files', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`
        },
        body: formData
      });
    });
    
    await Promise.all(uploadPromises);
  };
  
  const handleImageUpload = (files) => {
    setImages(prev => [...prev, ...files]);
  };
  
  const handleImageRemove = (index) => {
    setImages(prev => prev.filter((_, i) => i !== index));
  };
  
  return (
    <div className="create-product-page">
      <div className="page-header">
        <h1>Create New Product</h1>
        <button 
          className="btn-back"
          onClick={() => navigate('/admin/products')}
        >
          Back to Products
        </button>
      </div>
      
      {error && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
        </div>
      )}
      
      <div className="product-form-container">
        <div className="form-section">
          <h2>Product Images</h2>
          <ImageUploader
            images={images}
            onUpload={handleImageUpload}
            onRemove={handleImageRemove}
            maxImages={10}
            accept="image/*"
          />
        </div>
        
        <div className="form-section">
          <h2>Product Details</h2>
          <ProductForm
            onSubmit={handleSubmit}
            loading={loading}
            initialValues={{
              name: '',
              price: '',
              stock: 0,
              description: '',
              tags: [],
              category: '',
              brand: '',
              is_active: true,
              is_featured: false
            }}
          />
        </div>
        
        <div className="form-section">
          <h2>SEO & Metadata</h2>
          <div className="seo-preview">
            {/* SEO preview component */}
          </div>
        </div>
      </div>
    </div>
  );
}

export default CreateProductPage;
```

### Python with Product Variants Example
```python
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime

class ProductManager:
    """Product management API client for admin operations."""
    
    def __init__(self, base_url: str, api_key: str = None, token: str = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        if token:
            self.session.headers.update({
                'Authorization': f'Bearer {token}'
            })
        elif api_key:
            self.session.headers.update({
                'X-API-Key': api_key
            })
        
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def create_product(self, product_data: Dict) -> Dict:
        """
        Create a new product.
        
        Args:
            product_data: Product information
            
        Returns:
            Created product data
            
        Raises:
            ProductCreationError: If creation fails
            ValidationError: If data validation fails
        """
        # Validate required fields
        self._validate_product_data(product_data)
        
        # Generate SKU if not provided
        if 'sku' not in product_data or not product_data['sku']:
            product_data['sku'] = self._generate_sku(product_data['name'])
        
        # Generate slug if not provided
        if 'slug' not in product_data:
            product_data['slug'] = self._generate_slug(product_data['name'])
        
        # Set timestamps
        product_data['created_at'] = datetime.utcnow().isoformat() + 'Z'
        product_data['updated_at'] = product_data['created_at']
        
        try:
            response = self.session.post(
                f"{self.base_url}/products",
                json=product_data,
                timeout=30
            )
            
            response.raise_for_status()
            
            created_product = response.json()
            
            # Log creation
            self._log_product_creation(created_product['id'], product_data)
            
            return created_product
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 422:
                error_data = e.response.json()
                raise ValidationError(
                    "Product validation failed",
                    errors=error_data.get('errors', [])
                )
            elif e.response.status_code == 409:
                error_data = e.response.json()
                raise ConflictError(
                    error_data.get('detail', 'Conflict occurred'),
                    error_data
                )
            else:
                raise ProductCreationError(
                    f"Failed to create product: {e.response.status_code}",
                    status_code=e.response.status_code,
                    response_data=e.response.json() if e.response.content else None
                )
    
    def create_product_with_variants(
        self,
        base_product: Dict,
        variants: List[Dict]
    ) -> Dict:
        """
        Create a product with multiple variants.
        
        Args:
            base_product: Base product data
            variants: List of variant data
            
        Returns:
            Dictionary with base product and variants
        """
        # Create base product
        base_product['has_variants'] = True
        base_result = self.create_product(base_product)
        base_product_id = base_result['id']
        
        created_variants = []
        
        # Create each variant
        for variant_data in variants:
            # Link variant to base product
            variant_data['variant_of'] = base_product_id
            
            # Inherit common properties from base product
            variant_data.setdefault('category', base_product.get('category'))
            variant_data.setdefault('brand', base_product.get('brand'))
            variant_data.setdefault('description', base_product.get('description'))
            
            # Create variant
            try:
                variant_result = self.create_product(variant_data)
                created_variants.append(variant_result)
            except Exception as e:
                # Log error but continue with other variants
                print(f"Failed to create variant: {str(e)}")
        
        return {
            'base_product': base_result,
            'variants': created_variants,
            'total_variants_created': len(created_variants)
        }
    
    def create_product_batch(self, products: List[Dict]) -> Dict:
        """
        Create multiple products in batch.
        
        Args:
            products: List of product data dictionaries
            
        Returns:
            Batch creation results
        """
        results = {
            'successful': [],
            'failed': [],
            'total': len(products)
        }
        
        for i, product_data in enumerate(products):
            try:
                result = self.create_product(product_data)
                results['successful'].append({
                    'index': i,
                    'product': result,
                    'product_id': result['id']
                })
                print(f"Created product {i+1}/{len(products)}: {result['name']}")
            except Exception as e:
                results['failed'].append({
                    'index': i,
                    'error': str(e),
                    'product_data': product_data
                })
                print(f"Failed to create product {i+1}: {str(e)}")
        
        return results
    
    def _validate_product_data(self, data: Dict) -> None:
        """Validate product data before submission."""
        errors = []
        
        # Required fields
        if 'name' not in data or not data['name'].strip():
            errors.append({'field': 'name', 'message': 'Product name is required'})
        elif len(data['name'].strip()) < 3:
            errors.append({'field': 'name', 'message': 'Product name must be at least 3 characters'})
        elif len(data['name'].strip()) > 200:
            errors.append({'field': 'name', 'message': 'Product name cannot exceed 200 characters'})
        
        if 'price' not in data:
            errors.append({'field': 'price', 'message': 'Price is required'})
        elif not isinstance(data['price'], (int, float)):
            errors.append({'field': 'price', 'message': 'Price must be a number'})
        elif data['price'] < 0:
            errors.append({'field': 'price', 'message': 'Price must be non-negative'})
        
        # Optional field validations
        if 'stock' in data and data['stock'] is not None:
            if not isinstance(data['stock'], int):
                errors.append({'field': 'stock', 'message': 'Stock must be an integer'})
            elif data['stock'] < 0:
                errors.append({'field': 'stock', 'message': 'Stock must be non-negative'})
        
        if 'tags' in data and data['tags']:
            if not isinstance(data['tags'], list):
                errors.append({'field': 'tags', 'message': 'Tags must be a list'})
            elif len(data['tags']) > 20:
                errors.append({'field': 'tags', 'message': 'Maximum 20 tags allowed'})
        
        if 'images' in data and data['images']:
            if not isinstance(data['images'], list):
                errors.append({'field': 'images', 'message': 'Images must be a list'})
            elif len(data['images']) > 10:
                errors.append({'field': 'images', 'message': 'Maximum 10 images allowed'})
        
        if errors:
            raise ValidationError("Product validation failed", errors=errors)
    
    def _generate_sku(self, product_name: str) -> str:
        """Generate a SKU from product name."""
        import hashlib
        
        # Simple SKU generation - in production use a more robust method
        name_part = ''.join([c for c in product_name[:3].upper() if c.isalnum()])
        hash_part = hashlib.md5(product_name.encode()).hexdigest()[:6].upper()
        timestamp = datetime.utcnow().strftime('%y%m%d')
        
        return f"{name_part}-{hash_part}-{timestamp}"
    
    def _generate_slug(self, product_name: str) -> str:
        """Generate URL-friendly slug from product name."""
        import re
        import unicodedata
        
        # Normalize unicode
        name = unicodedata.normalize('NFKD', product_name)
        
        # Replace non-ASCII characters
        name = name.encode('ASCII', 'ignore').decode('ASCII')
        
        # Convert to lowercase and replace spaces/special chars
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')
        
        # Add timestamp for uniqueness
        timestamp = datetime.utcnow().strftime('%y%m%d')
        
        return f"{slug}-{timestamp}"
    
    def _log_product_creation(self, product_id: str, product_data: Dict) -> None:
        """Log product creation for auditing."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'product_id': product_id,
            'product_name': product_data.get('name'),
            'price': product_data.get('price'),
            'category': product_data.get('category'),
            'action': 'create'
        }
        
        # In production, save to database or logging service
        print(f"Product created: {json.dumps(log_entry, indent=2)}")

class ValidationError(Exception):
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors or []

class ConflictError(Exception):
    pass

class ProductCreationError(Exception):
    def __init__(self, message, status_code=None, response_data=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

# Usage Example
def create_sample_products():
    """Example of creating different types of products."""
    
    # Initialize product manager
    manager = ProductManager(
        base_url="http://localhost:8000/api",
        token="your_admin_token_here"
    )
    
    # Example 1: Simple product
    simple_product = {
        "name": "Basic Wireless Mouse",
        "price": 24.99,
        "description": "Simple wireless mouse for everyday use.",
        "category": "Computer Accessories",
        "stock": 100,
        "tags": ["electronics", "mouse"]
    }
    
    # Example 2: Product with variants (T-shirt in different sizes/colors)
    base_tshirt = {
        "name": "Premium Cotton T-Shirt",
        "price": 29.99,
        "description": "100% cotton premium t-shirt.",
        "category": "Clothing",
        "brand": "FashionCo"
    }
    
    tshirt_variants = [
        {
            "name": "Premium Cotton T-Shirt - Small / Black",
            "price": 29.99,
            "options": {
                "size": "S",
                "color": "Black"
            },
            "sku": "TSHIRT-S-BLK",
            "stock": 50
        },
        {
            "name": "Premium Cotton T-Shirt - Medium / White",
            "price": 29.99,
            "options": {
                "size": "M",
                "color": "White"
            },
            "sku": "TSHIRT-M-WHT",
            "stock": 75
        }
    ]
    
    # Example 3: Product bundle
    product_bundle = {
        "name": "Gaming Starter Bundle",
        "price": 199.99,
        "description": "Complete gaming setup including keyboard, mouse, and headset.",
        "category": "Gaming",
        "is_bundle": True,
        "bundle_items": [
            {"product_id": "prod_keyboard", "quantity": 1},
            {"product_id": "prod_mouse", "quantity": 1},
            {"product_id": "prod_headset", "quantity": 1}
        ],
        "original_price": 249.99,
        "is_featured": True
    }
    
    try:
        # Create simple product
        print("Creating simple product...")
        result1 = manager.create_product(simple_product)
        print(f"Created product: {result1['id']} - {result1['name']}")
        
        # Create product with variants
        print("\nCreating product with variants...")
        result2 = manager.create_product_with_variants(base_tshirt, tshirt_variants)
        print(f"Created base product: {result2['base_product']['id']}")
        print(f"Created {result2['total_variants_created']} variants")
        
        # Create product bundle
        print("\nCreating product bundle...")
        result3 = manager.create_product(product_bundle)
        print(f"Created bundle: {result3['id']} - {result3['name']}")
        
        return {
            'simple_product': result1,
            'variants_product': result2,
            'bundle_product': result3
        }
        
    except ValidationError as e:
        print(f"Validation error: {e}")
        for error in e.errors:
            print(f"  - {error['field']}: {error['message']}")
    except ProductCreationError as e:
        print(f"Product creation error: {e}")
        if e.response_data:
            print(f"Response: {json.dumps(e.response_data, indent=2)}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    # Run example
    create_sample_products()
```

### Best Practices for Product Creation

#### 1. **Image Handling Strategy**
```javascript
// Pre-upload images to CDN/temporary storage
async function createProductWithImages(productData, images) {
  // 1. Upload images first
  const imageUrls = await Promise.all(
    images.map(image => uploadToCDN(image))
  );
  
  // 2. Add image URLs to product data
  productData.images = imageUrls;
  
  // 3. Create product
  return createProduct(productData);
}
```

#### 2. **Inventory Management**
```javascript
// Set up inventory tracking
const productData = {
  ...productData,
  reorder_level: 10, // Alert when stock ≤ 10
  lead_time: 7, // Days to restock
  supplier: "TechGear Inc.",
  supplier_code: "TG-2023-001"
};
```

#### 3. **SEO Optimization**
```javascript
// Auto-generate SEO fields if not provided
function enhanceProductData(productData) {
  return {
    ...productData,
    meta_title: productData.meta_title || 
      `${productData.name} | ${productData.brand || 'Our Store'}`,
    meta_description: productData.meta_description ||
      truncate(productData.description, 150),
    slug: productData.slug || 
      generateSlug(productData.name)
  };
}
```

#### 4. **Validation Rules**
```javascript
const productValidationRules = {
  name: {
    required: true,
    min: 3,
    max: 200
  },
  price: {
    required: true,
    min: 0,
    max: 1000000
  },
  sku: {
    pattern: /^[A-Z0-9-]+$/,
    unique: true
  },
  tags: {
    max: 20,
    each: {
      min: 2,
      max: 50
    }
  }
};
```

### Error Recovery and Retry Logic

```javascript
// Retry product creation with exponential backoff
async function createProductWithRetry(productData, maxRetries = 3) {
  let lastError;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await createProduct(productData);
    } catch (error) {
      lastError = error;
      
      if (attempt === maxRetries) break;
      
      // Exponential backoff
      const delay = Math.pow(2, attempt - 1) * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
      
      // For conflict errors, modify SKU and retry
      if (error.statusCode === 409) {
        productData.sku = `${productData.sku}-${Date.now()}`;
      }
    }
  }
  
  throw lastError;
}
```

---

## Related Endpoints
- [GET /products](../products/list-products.md) - List all products
- [GET /products/{productId}](../products/get-product.md) - Get product details
- [PATCH /products/{productId}](../products/update-product.md) - Update product
- [DELETE /products/{productId}](../products/delete-product.md) - Delete product
- [POST /files](../images/upload-image.md) - Upload product images
- [Error Responses](../../errors.md) - Error handling details

## Notes
- Always validate data before sending to API
- Consider implementing draft/save functionality for complex products
- Set up webhooks to notify other systems when products are created
- Implement audit logging for all product creation actions
- Consider rate limiting for bulk product creation
- Use transaction IDs for tracking product creation across systems

## Security Considerations
- Validate all input fields to prevent injection attacks
- Implement proper authorization checks (admin-only)
- Sanitize HTML in descriptions to prevent XSS
- Validate image URLs to prevent SSRF attacks
- Implement rate limiting to prevent abuse
- Log all creation attempts for security monitoring