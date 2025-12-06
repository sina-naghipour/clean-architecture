# GET /products/{productId}

**Get Product Details** - Retrieve detailed information about a specific product

**Tags:** Products

---

## Description
Retrieve comprehensive information about a single product by its unique identifier. Returns all product details including images, stock status, pricing, and metadata.

## Authentication
Optional - Public endpoint accessible to all users

## Request

### URL Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `productId` | string | ✓ | Unique product identifier | `prod_1` |

### Path
```
GET /products/{productId}
```

## Responses

### 200 OK - Product details retrieved successfully
**Body:**
```json
{
  "id": "prod_1",
  "name": "Premium Wireless Mouse",
  "price": 49.99,
  "stock": 42,
  "description": "Ergonomic wireless mouse with 12,000 DPI optical sensor, programmable buttons, and 50-hour battery life. Perfect for gaming and productivity.",
  "tags": ["electronics", "gaming", "peripheral", "wireless"],
  "images": [
    "/static/img/products/prod_1/main.jpg",
    "/static/img/products/prod_1/side.jpg",
    "/static/img/products/prod_1/angle.jpg"
  ],
  "primaryImageId": "img_123456",
  "specifications": {
    "connection": "Wireless 2.4GHz + Bluetooth",
    "dpi": "12000",
    "buttons": 6,
    "battery": "50 hours",
    "weight": "95g",
    "dimensions": "125 x 68 x 40 mm"
  },
  "features": [
    "Programmable buttons",
    "RGB lighting",
    "On-board memory",
    "Adjustable weight system"
  ],
  "created_at": "2023-10-01T12:00:00Z",
  "updated_at": "2023-11-15T09:30:00Z",
  "category": "Computer Accessories",
  "sku": "WM-PRO-2023",
  "brand": "TechGear",
  "rating": 4.5,
  "review_count": 127,
  "related_products": ["prod_2", "prod_3", "prod_4"]
}
```

**Response Fields:**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | string | Unique product identifier | `"prod_1"` |
| `name` | string | Product name | `"Premium Wireless Mouse"` |
| `price` | number | Product price in USD | `49.99` |
| `stock` | integer | Available quantity | `42` |
| `description` | string | Detailed product description | `"Ergonomic wireless mouse..."` |
| `tags` | string[] | Product categories/tags | `["electronics", "gaming"]` |
| `images` | string[] | Array of image URLs | `["/static/img/..."]` |
| `primaryImageId` | string | ID of primary product image | `"img_123456"` |
| `specifications` | object | Technical specifications | `{"connection": "Wireless"}` |
| `features` | string[] | Key features | `["Programmable buttons"]` |
| `created_at` | string | Creation timestamp (ISO 8601) | `"2023-10-01T12:00:00Z"` |
| `updated_at` | string | Last update timestamp | `"2023-11-15T09:30:00Z"` |
| `category` | string | Product category | `"Computer Accessories"` |
| `sku` | string | Stock Keeping Unit | `"WM-PRO-2023"` |
| `brand` | string | Manufacturer brand | `"TechGear"` |
| `rating` | number | Average customer rating (0-5) | `4.5` |
| `review_count` | integer | Number of customer reviews | `127` |
| `related_products` | string[] | IDs of related products | `["prod_2", "prod_3"]` |

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

**Causes:**
- Product ID doesn't exist
- Product has been deleted
- Invalid product ID format

### 400 Bad Request - Invalid product ID
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/bad-request",
  "title": "Bad Request",
  "status": 400,
  "detail": "Invalid product ID format.",
  "instance": "/products/invalid-id"
}
```

### 500 Internal Server Error
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/internal",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "Unexpected server error.",
  "instance": "/products/prod_1"
}
```

## Examples

### Basic Request
```bash
# Get product details
curl -X GET "http://localhost:8000/api/products/prod_1"
```

### With Headers
```bash
# Get product with specific headers
curl -X GET "http://localhost:8000/api/products/prod_1" \
  -H "Accept: application/json" \
  -H "Accept-Language: en-US"
```

### JavaScript (Fetch)
```javascript
/**
 * Fetch product details by ID
 * @param {string} productId - Product identifier
 * @returns {Promise<Object>} Product data
 */
async function getProduct(productId) {
  if (!productId || typeof productId !== 'string') {
    throw new Error('Valid product ID is required');
  }
  
  try {
    const response = await fetch(`http://localhost:8000/api/products/${encodeURIComponent(productId)}`);
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Product '${productId}' not found`);
      }
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const product = await response.json();
    return product;
  } catch (error) {
    console.error(`Error fetching product ${productId}:`, error);
    throw error;
  }
}

/**
 * Get product with enhanced error handling and caching
 */
class ProductService {
  constructor() {
    this.cache = new Map();
    this.cacheDuration = 5 * 60 * 1000; // 5 minutes
  }
  
  async getProduct(productId, forceRefresh = false) {
    // Check cache first
    const cached = this.cache.get(productId);
    if (!forceRefresh && cached && Date.now() - cached.timestamp < this.cacheDuration) {
      return cached.data;
    }
    
    try {
      const product = await getProduct(productId);
      
      // Cache the result
      this.cache.set(productId, {
        data: product,
        timestamp: Date.now()
      });
      
      return product;
    } catch (error) {
      // Return cached data if available (even if stale)
      if (cached) {
        console.warn(`Using cached data for ${productId}:`, error.message);
        return cached.data;
      }
      throw error;
    }
  }
  
  clearCache(productId = null) {
    if (productId) {
      this.cache.delete(productId);
    } else {
      this.cache.clear();
    }
  }
}

// Usage
const productService = new ProductService();

// Get product with caching
productService.getProduct('prod_1')
  .then(product => {
    console.log('Product:', product.name);
    console.log('Price:', product.price);
    console.log('In stock:', product.stock > 0);
  })
  .catch(error => console.error('Error:', error.message));

// Force refresh
productService.getProduct('prod_1', true)
  .then(product => console.log('Fresh data:', product));
```

### React Component Example
```jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ProductGallery from './ProductGallery';
import ProductSpecs from './ProductSpecs';
import ProductReviews from './ProductReviews';
import AddToCartButton from './AddToCartButton';

function ProductDetailPage() {
  const { productId } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [quantity, setQuantity] = useState(1);

  useEffect(() => {
    fetchProduct();
  }, [productId]);

  const fetchProduct = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://localhost:8000/api/products/${productId}`);
      
      if (response.status === 404) {
        navigate('/products', { state: { error: 'Product not found' } });
        return;
      }
      
      if (!response.ok) {
        throw new Error(`Failed to load product: ${response.status}`);
      }
      
      const data = await response.json();
      setProduct(data);
      
      // Update page title
      document.title = `${data.name} | Ecommerce Store`;
      
      // Track product view (analytics)
      trackProductView(productId);
    } catch (err) {
      setError(err.message);
      console.error('Product fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const trackProductView = (id) => {
    // Analytics tracking
    if (window.gtag) {
      window.gtag('event', 'view_item', {
        items: [{
          item_id: id,
          item_name: product?.name,
          price: product?.price,
          item_category: product?.category
        }]
      });
    }
  };

  const handleAddToCart = async () => {
    if (!product || product.stock === 0) return;
    
    try {
      const response = await fetch('http://localhost:8000/api/cart/items', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          product_id: productId,
          quantity: quantity
        })
      });
      
      if (response.ok) {
        alert('Product added to cart!');
        // Update UI or trigger cart refresh
      }
    } catch (err) {
      console.error('Add to cart error:', err);
    }
  };

  const handleQuantityChange = (newQuantity) => {
    if (newQuantity < 1 || newQuantity > product.stock) return;
    setQuantity(newQuantity);
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading product details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error Loading Product</h2>
        <p>{error}</p>
        <button onClick={fetchProduct}>Retry</button>
      </div>
    );
  }

  if (!product) {
    return null;
  }

  return (
    <div className="product-detail">
      {/* Breadcrumb Navigation */}
      <nav className="breadcrumb">
        <a href="/">Home</a> &gt;
        <a href="/products">Products</a> &gt;
        <a href={`/products/${product.category?.toLowerCase()}`}>{product.category}</a> &gt;
        <span>{product.name}</span>
      </nav>

      <div className="product-layout">
        {/* Left Column: Images */}
        <div className="product-images">
          <ProductGallery 
            images={product.images}
            primaryImageId={product.primaryImageId}
            productName={product.name}
          />
        </div>

        {/* Middle Column: Product Info */}
        <div className="product-info">
          <h1 className="product-title">{product.name}</h1>
          
          <div className="product-meta">
            <span className="product-sku">SKU: {product.sku}</span>
            <span className="product-brand">Brand: {product.brand}</span>
            {product.rating && (
              <div className="product-rating">
                <span className="stars">{'★'.repeat(Math.floor(product.rating))}</span>
                <span>({product.review_count} reviews)</span>
              </div>
            )}
          </div>

          <div className="product-price">
            <span className="current-price">${product.price.toFixed(2)}</span>
            {product.originalPrice && (
              <span className="original-price">${product.originalPrice.toFixed(2)}</span>
            )}
          </div>

          <div className="product-stock">
            {product.stock > 0 ? (
              <span className="in-stock">
                {product.stock > 10 ? 'In Stock' : `Only ${product.stock} left`}
              </span>
            ) : (
              <span className="out-of-stock">Out of Stock</span>
            )}
          </div>

          <div className="product-description">
            <h3>Description</h3>
            <p>{product.description}</p>
          </div>

          <div className="product-features">
            <h3>Key Features</h3>
            <ul>
              {product.features?.map((feature, index) => (
                <li key={index}>{feature}</li>
              ))}
            </ul>
          </div>

          {/* Add to Cart Section */}
          {product.stock > 0 && (
            <div className="add-to-cart-section">
              <div className="quantity-selector">
                <button 
                  onClick={() => handleQuantityChange(quantity - 1)}
                  disabled={quantity <= 1}
                >
                  −
                </button>
                <input 
                  type="number" 
                  value={quantity}
                  min="1"
                  max={product.stock}
                  onChange={(e) => handleQuantityChange(parseInt(e.target.value))}
                />
                <button 
                  onClick={() => handleQuantityChange(quantity + 1)}
                  disabled={quantity >= product.stock}
                >
                  +
                </button>
              </div>
              
              <AddToCartButton 
                product={product}
                quantity={quantity}
                onAddToCart={handleAddToCart}
              />
              
              <button className="buy-now-btn">
                Buy Now
              </button>
            </div>
          )}
        </div>

        {/* Right Column: Specifications/Sidebar */}
        <div className="product-sidebar">
          <ProductSpecs specifications={product.specifications} />
          
          <div className="shipping-info">
            <h4>Shipping & Returns</h4>
            <p>Free shipping on orders over $50</p>
            <p>30-day return policy</p>
          </div>
          
          <div className="social-share">
            <h4>Share this product</h4>
            {/* Social media buttons */}
          </div>
        </div>
      </div>

      {/* Tabs for additional info */}
      <div className="product-tabs">
        <div className="tab-content">
          <ProductSpecs specifications={product.specifications} detailed={true} />
        </div>
        
        <div className="tab-content">
          <ProductReviews 
            productId={productId}
            rating={product.rating}
            reviewCount={product.review_count}
          />
        </div>
        
        {product.related_products && product.related_products.length > 0 && (
          <div className="tab-content">
            <h3>Related Products</h3>
            {/* Related products component */}
          </div>
        )}
      </div>
    </div>
  );
}

export default ProductDetailPage;
```

### Python with Flask/Django Example
```python
import requests
from flask import jsonify, request
from functools import lru_cache
import time

class ProductAPI:
    def __init__(self, base_url="http://localhost:8000/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'ProductAPI/1.0'
        })
    
    def get_product(self, product_id, timeout=10):
        """
        Fetch product details with timeout and retry logic.
        
        Args:
            product_id (str): Product identifier
            timeout (int): Request timeout in seconds
            
        Returns:
            dict: Product data
            
        Raises:
            requests.exceptions.RequestException: On request failure
            ValueError: On invalid response
        """
        if not product_id or not isinstance(product_id, str):
            raise ValueError("product_id must be a non-empty string")
        
        url = f"{self.base_url}/products/{product_id}"
        
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            product_data = response.json()
            
            # Validate response structure
            required_fields = ['id', 'name', 'price', 'stock']
            for field in required_fields:
                if field not in product_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add calculated fields
            product_data['in_stock'] = product_data.get('stock', 0) > 0
            product_data['formatted_price'] = f"${product_data['price']:.2f}"
            
            # Calculate discount if original price exists
            if 'original_price' in product_data and product_data['original_price']:
                discount = ((product_data['original_price'] - product_data['price']) / 
                          product_data['original_price'] * 100)
                product_data['discount_percentage'] = round(discount, 1)
            
            return product_data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ProductNotFoundError(f"Product '{product_id}' not found")
            raise
        except requests.exceptions.Timeout:
            raise ProductAPITimeoutError(f"Request timeout for product '{product_id}'")
    
    @lru_cache(maxsize=100)
    def get_product_cached(self, product_id, cache_ttl=300):
        """
        Get product with in-memory caching.
        
        Args:
            product_id (str): Product identifier
            cache_ttl (int): Cache time-to-live in seconds
            
        Returns:
            dict: Cached product data
        """
        # Create cache key
        cache_key = f"product:{product_id}"
        
        # In production, use Redis or similar
        # For now, using simple in-memory with lru_cache
        return self.get_product(product_id)
    
    def get_multiple_products(self, product_ids, parallel=False):
        """
        Fetch multiple products efficiently.
        
        Args:
            product_ids (list): List of product IDs
            parallel (bool): Whether to fetch in parallel
            
        Returns:
            dict: {product_id: product_data} mapping
        """
        results = {}
        
        if parallel:
            # Use concurrent.futures for parallel requests
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_id = {
                    executor.submit(self.get_product, pid): pid 
                    for pid in product_ids
                }
                
                for future in concurrent.futures.as_completed(future_to_id):
                    pid = future_to_id[future]
                    try:
                        results[pid] = future.result()
                    except Exception as e:
                        results[pid] = {'error': str(e)}
        else:
            # Sequential requests
            for pid in product_ids:
                try:
                    results[pid] = self.get_product(pid)
                except Exception as e:
                    results[pid] = {'error': str(e)}
        
        return results

class ProductNotFoundError(Exception):
    pass

class ProductAPITimeoutError(Exception):
    pass

# Flask endpoint example
from flask import Flask, abort

app = Flask(__name__)
product_api = ProductAPI()

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product_endpoint(product_id):
    """
    Flask endpoint to serve product data.
    """
    try:
        # Get product with caching
        product = product_api.get_product_cached(product_id)
        
        # Add CORS headers if needed
        response = jsonify(product)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Cache-Control', 'public, max-age=300')  # 5 minutes
        
        return response
        
    except ProductNotFoundError as e:
        abort(404, description=str(e))
    except ProductAPITimeoutError as e:
        abort(504, description=str(e))
    except Exception as e:
        app.logger.error(f"Error fetching product {product_id}: {str(e)}")
        abort(500, description="Internal server error")

# Usage example
if __name__ == "__main__":
    api = ProductAPI()
    
    try:
        # Get single product
        product = api.get_product("prod_1")
        print(f"Product: {product['name']}")
        print(f"Price: {product['formatted_price']}")
        print(f"In stock: {product['in_stock']}")
        
        # Get multiple products
        products = api.get_multiple_products(["prod_1", "prod_2", "prod_3"])
        for pid, data in products.items():
            if 'error' not in data:
                print(f"{pid}: {data['name']}")
        
    except ProductNotFoundError as e:
        print(f"Product error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
```

### Error Handling and Edge Cases

```javascript
// Comprehensive error handling for product fetching
async function getProductWithFallback(productId) {
  try {
    const product = await getProduct(productId);
    return product;
  } catch (error) {
    console.error(`Failed to fetch product ${productId}:`, error);
    
    // Check if it's a network error
    if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
      // Try offline cache
      const offlineProduct = await getFromOfflineCache(productId);
      if (offlineProduct) {
        return { ...offlineProduct, offline: true };
      }
    }
    
    // For 404 errors, check if we have a similar product
    if (error.message.includes('404') || error.message.includes('not found')) {
      // Try to find alternative product
      const alternatives = await findAlternativeProducts(productId);
      if (alternatives.length > 0) {
        throw new ProductNotFoundError(
          `Product not found. Try one of these: ${alternatives.map(p => p.name).join(', ')}`,
          alternatives
        );
      }
    }
    
    // Generic fallback
    return {
      id: productId,
      name: "Product Unavailable",
      description: "This product is currently unavailable. Please try again later.",
      price: 0,
      stock: 0,
      unavailable: true
    };
  }
}

class ProductNotFoundError extends Error {
  constructor(message, alternatives = []) {
    super(message);
    this.name = 'ProductNotFoundError';
    this.alternatives = alternatives;
  }
}
```

### Performance Optimization

```javascript
// Prefetch related products
function prefetchRelatedProducts(productId) {
  // Get product first
  getProduct(productId).then(product => {
    if (product.related_products && product.related_products.length > 0) {
      // Prefetch related products in background
      product.related_products.forEach(relatedId => {
        fetch(`/api/products/${relatedId}`, { priority: 'low' })
          .then(res => res.json())
          .then(data => {
            // Store in cache
            cacheProduct(data);
          });
      });
    }
  });
}

// Image optimization
function optimizeProductImages(product) {
  return {
    ...product,
    images: product.images.map(img => ({
      original: img,
      thumbnail: img.replace('.jpg', '-thumb.jpg'),
      medium: img.replace('.jpg', '-medium.jpg'),
      large: img.replace('.jpg', '-large.jpg')
    }))
  };
}
```

---

## Related Endpoints
- [GET /products](../products/list-products.md) - List all products with filtering
- [POST /cart/items](../cart/add-to-cart.md) - Add this product to cart
- [GET /files/{fileId}](../images/get-image.md) - Get product image details
- [Error Responses](../../errors.md) - Error handling details

## Notes
- Product IDs are case-sensitive
- Consider implementing product variants if needed (colors, sizes)
- For out-of-stock products, consider showing estimated restock dates
- Implement product view tracking for analytics
- Consider adding "frequently bought together" recommendations
- Add social sharing meta tags for SEO

## SEO Considerations
- Include structured data (JSON-LD) for product pages
- Implement proper meta tags (title, description, Open Graph)
- Generate SEO-friendly URLs: `/products/premium-wireless-mouse-prod_1`
- Implement canonical URLs to avoid duplicate content