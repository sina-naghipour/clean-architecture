# GET /products

**List Products** - Retrieve paginated and filtered product catalog

**Tags:** Products

---

## Description
Retrieve a paginated list of products with optional filtering, sorting, and search capabilities. This endpoint supports full-text search across product names and descriptions, price range filtering, and tag-based filtering.

## Authentication
Optional - Some features may require authentication for premium results

## Request

### Query Parameters

| Parameter | Type | Required | Default | Description | Example |
|-----------|------|----------|---------|-------------|---------|
| `page` | integer | No | 1 | Page number (1-indexed) | `?page=2` |
| `pageSize` | integer | No | 20 | Items per page (1-100) | `?pageSize=50` |
| `q` | string | No | - | Full-text search query | `?q=laptop` |
| `tags` | string[] | No | - | Filter by tags (comma-separated) | `?tags=electronics,computer` |
| `min_price` | number | No | - | Minimum price filter | `?min_price=100` |
| `max_price` | number | No | - | Maximum price filter | `?max_price=1000` |
| `sort` | string | No | `created_at` | Sort field (`price`, `name`, `created_at`) | `?sort=price` |
| `order` | string | No | `desc` | Sort order (`asc`, `desc`) | `?order=asc` |
| `in_stock` | boolean | No | - | Only products with stock > 0 | `?in_stock=true` |

## Responses

### 200 OK - Products retrieved successfully
**Body:**
```json
{
  "items": [
    {
      "id": "prod_1",
      "name": "Wireless Mouse",
      "price": 29.99,
      "stock": 100,
      "description": "Ergonomic wireless mouse with precision tracking",
      "tags": ["electronics", "peripheral"],
      "images": [
        "/static/img/products/prod_1/image1.jpg",
        "/static/img/products/prod_1/image2.jpg"
      ],
      "primaryImageId": "img_123",
      "created_at": "2023-10-01T12:00:00Z",
      "updated_at": "2023-10-01T12:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "pageSize": 20
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `items` | ProductResponse[] | Array of products |
| `total` | integer | Total number of products matching filters |
| `page` | integer | Current page number |
| `pageSize` | integer | Number of items per page |

**Product Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique product identifier |
| `name` | string | Product name |
| `price` | number | Product price |
| `stock` | integer | Available stock quantity |
| `description` | string | Product description |
| `tags` | string[] | Product categories/tags |
| `images` | string[] | URLs to product images |
| `primaryImageId` | string | ID of primary image (null if none) |
| `created_at` | string | Creation timestamp |
| `updated_at` | string | Last update timestamp |

### 400 Bad Request - Invalid parameters
**Content-Type:** `application/problem+json`

```json
{
  "type": "https://example.com/errors/bad-request",
  "title": "Bad Request",
  "status": 400,
  "detail": "Invalid page size. Must be between 1 and 100.",
  "instance": "/products"
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
  "instance": "/products"
}
```

## Examples

### Basic Request
```bash
# Get first page of products
curl -X GET "http://localhost:8000/api/products"
```

### With Pagination
```bash
# Get second page, 10 items per page
curl -X GET "http://localhost:8000/api/products?page=2&pageSize=10"
```

### With Search
```bash
# Search for "laptop"
curl -X GET "http://localhost:8000/api/products?q=laptop"

# Search with multiple filters
curl -X GET "http://localhost:8000/api/products?q=gaming&min_price=500&max_price=2000&in_stock=true"
```

### With Tags Filter
```bash
# Filter by electronics and computer tags
curl -X GET "http://localhost:8000/api/products?tags=electronics,computer"

# URL encoded version
curl -X GET "http://localhost:8000/api/products?tags=electronics%2Ccomputer"
```

### Complete Example
```bash
curl -X GET "http://localhost:8000/api/products?q=wireless&tags=electronics&min_price=10&max_price=100&page=1&pageSize=25&sort=price&order=asc&in_stock=true"
```

### JavaScript (Fetch)
```javascript
async function getProducts(filters = {}) {
  const {
    page = 1,
    pageSize = 20,
    query = '',
    tags = [],
    minPrice,
    maxPrice,
    inStock,
    sort = 'created_at',
    order = 'desc'
  } = filters;
  
  // Build query parameters
  const params = new URLSearchParams({
    page: page.toString(),
    pageSize: pageSize.toString(),
    sort,
    order
  });
  
  if (query) params.append('q', query);
  if (tags.length > 0) params.append('tags', tags.join(','));
  if (minPrice !== undefined) params.append('min_price', minPrice);
  if (maxPrice !== undefined) params.append('max_price', maxPrice);
  if (inStock !== undefined) params.append('in_stock', inStock);
  
  try {
    const response = await fetch(`http://localhost:8000/api/products?${params.toString()}`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    // Calculate pagination metadata
    const totalPages = Math.ceil(data.total / data.pageSize);
    const hasNextPage = data.page < totalPages;
    const hasPrevPage = data.page > 1;
    
    return {
      products: data.items,
      pagination: {
        currentPage: data.page,
        pageSize: data.pageSize,
        totalItems: data.total,
        totalPages,
        hasNextPage,
        hasPrevPage
      }
    };
  } catch (error) {
    console.error('Error fetching products:', error);
    throw error;
  }
}

// Usage examples
getProducts({ page: 1, pageSize: 12 })
  .then(result => console.log('Products:', result.products));

getProducts({ 
  query: 'gaming',
  tags: ['electronics', 'gaming'],
  minPrice: 500,
  maxPrice: 2000,
  inStock: true,
  sort: 'price',
  order: 'asc'
})
  .then(result => console.log('Filtered products:', result));
```

### React Component Example
```jsx
import React, { useState, useEffect } from 'react';
import ProductCard from './ProductCard';

function ProductList() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    page: 1,
    pageSize: 12,
    query: '',
    minPrice: '',
    maxPrice: '',
    tags: [],
    inStock: false
  });
  const [pagination, setPagination] = useState({
    totalItems: 0,
    totalPages: 0,
    currentPage: 1
  });

  const fetchProducts = async (filterParams) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await getProducts(filterParams);
      setProducts(result.products);
      setPagination(result.pagination);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts(filters);
  }, [filters.page, filters.query, filters.minPrice, filters.maxPrice, filters.tags, filters.inStock]);

  const handleSearch = (query) => {
    setFilters(prev => ({ ...prev, query, page: 1 }));
  };

  const handlePageChange = (page) => {
    setFilters(prev => ({ ...prev, page }));
  };

  const handleFilterChange = (newFilters) => {
    setFilters(prev => ({ ...prev, ...newFilters, page: 1 }));
  };

  if (loading) return <div className="loading">Loading products...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="product-list">
      {/* Search and Filters Component */}
      <ProductFilters 
        filters={filters}
        onSearch={handleSearch}
        onFilterChange={handleFilterChange}
      />
      
      {/* Product Grid */}
      <div className="product-grid">
        {products.length === 0 ? (
          <div className="no-results">
            <p>No products found. Try different search terms.</p>
          </div>
        ) : (
          products.map(product => (
            <ProductCard 
              key={product.id}
              product={product}
            />
          ))
        )}
      </div>
      
      {/* Pagination */}
      {pagination.totalPages > 1 && (
        <Pagination 
          currentPage={pagination.currentPage}
          totalPages={pagination.totalPages}
          onPageChange={handlePageChange}
        />
      )}
    </div>
  );
}

// Product Filters Component
function ProductFilters({ filters, onSearch, onFilterChange }) {
  const [searchTerm, setSearchTerm] = useState(filters.query);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(searchTerm);
  };
  
  return (
    <form onSubmit={handleSubmit} className="product-filters">
      <input
        type="text"
        placeholder="Search products..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
      <button type="submit">Search</button>
      
      <div className="price-filters">
        <input
          type="number"
          placeholder="Min price"
          value={filters.minPrice}
          onChange={(e) => onFilterChange({ minPrice: e.target.value })}
        />
        <span>to</span>
        <input
          type="number"
          placeholder="Max price"
          value={filters.maxPrice}
          onChange={(e) => onFilterChange({ maxPrice: e.target.value })}
        />
      </div>
      
      <label>
        <input
          type="checkbox"
          checked={filters.inStock}
          onChange={(e) => onFilterChange({ inStock: e.target.checked })}
        />
        In Stock Only
      </label>
    </form>
  );
}
```

### Python
```python
import requests
from typing import Dict, List, Optional

class ProductAPI:
    BASE_URL = "http://localhost:8000/api"
    
    def list_products(
        self,
        page: int = 1,
        page_size: int = 20,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock: Optional[bool] = None,
        sort: str = "created_at",
        order: str = "desc"
    ) -> Dict:
        """Fetch paginated list of products with optional filters."""
        params = {
            "page": page,
            "pageSize": page_size,
            "sort": sort,
            "order": order
        }
        
        if query:
            params["q"] = query
        if tags:
            params["tags"] = ",".join(tags)
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        if in_stock is not None:
            params["in_stock"] = "true" if in_stock else "false"
        
        try:
            response = requests.get(f"{self.BASE_URL}/products", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Error: {str(e)}")
            raise
    
    def search_products(self, query: str, **kwargs) -> List[Dict]:
        """Search products by query."""
        result = self.list_products(query=query, **kwargs)
        return result["items"]
    
    def get_products_by_price_range(
        self,
        min_price: float,
        max_price: float,
        **kwargs
    ) -> List[Dict]:
        """Get products within price range."""
        result = self.list_products(
            min_price=min_price,
            max_price=max_price,
            **kwargs
        )
        return result["items"]

# Usage
api = ProductAPI()

# Get first page
products = api.list_products(page=1, page_size=12)
print(f"Total products: {products['total']}")
for product in products["items"]:
    print(f"{product['name']}: ${product['price']}")

# Search with filters
gaming_products = api.search_products(
    query="gaming",
    tags=["electronics"],
    min_price=100,
    max_price=2000,
    in_stock=True
)
```

### Advanced Features

#### Real-time Search with Debouncing
```javascript
function createProductSearch() {
  let timeoutId;
  
  return {
    search: function(query, delay = 300) {
      clearTimeout(timeoutId);
      
      return new Promise((resolve) => {
        timeoutId = setTimeout(async () => {
          if (query.trim().length === 0) {
            resolve([]);
            return;
          }
          
          try {
            const result = await getProducts({ query, pageSize: 10 });
            resolve(result.products);
          } catch (error) {
            console.error('Search error:', error);
            resolve([]);
          }
        }, delay);
      });
    }
  };
}

// Usage in React
const searchService = createProductSearch();

const handleSearchInput = async (value) => {
  const results = await searchService.search(value);
  setSearchResults(results);
};
```

#### Infinite Scroll Implementation
```javascript
class InfiniteProductLoader {
  constructor(container, loadCallback) {
    this.container = container;
    this.loadCallback = loadCallback;
    this.page = 1;
    this.loading = false;
    this.hasMore = true;
    
    this.init();
  }
  
  init() {
    this.container.addEventListener('scroll', this.handleScroll.bind(this));
    this.loadMore();
  }
  
  async handleScroll() {
    const { scrollTop, scrollHeight, clientHeight } = this.container;
    const isBottom = scrollTop + clientHeight >= scrollHeight - 100;
    
    if (isBottom && !this.loading && this.hasMore) {
      await this.loadMore();
    }
  }
  
  async loadMore() {
    this.loading = true;
    
    try {
      const result = await this.loadCallback(this.page);
      
      if (result.products.length === 0) {
        this.hasMore = false;
      } else {
        this.page++;
      }
    } catch (error) {
      console.error('Load error:', error);
    } finally {
      this.loading = false;
    }
  }
  
  reset() {
    this.page = 1;
    this.hasMore = true;
    this.loading = false;
  }
}
```

## Performance Considerations

### Caching Strategy
```javascript
// Simple client-side caching
const productCache = new Map();

async function getProductsWithCache(filters) {
  const cacheKey = JSON.stringify(filters);
  
  if (productCache.has(cacheKey)) {
    return productCache.get(cacheKey);
  }
  
  const result = await getProducts(filters);
  productCache.set(cacheKey, result);
  
  // Clear cache after 5 minutes
  setTimeout(() => productCache.delete(cacheKey), 5 * 60 * 1000);
  
  return result;
}
```

### API Rate Limiting
```javascript
// Implement request throttling
const rateLimiter = {
  lastRequest: 0,
  minInterval: 1000, // 1 second between requests
  
  async makeRequest(fetchFn) {
    const now = Date.now();
    const timeSinceLastRequest = now - this.lastRequest;
    
    if (timeSinceLastRequest < this.minInterval) {
      await new Promise(resolve => 
        setTimeout(resolve, this.minInterval - timeSinceLastRequest)
      );
    }
    
    this.lastRequest = Date.now();
    return fetchFn();
  }
};

// Usage
const result = await rateLimiter.makeRequest(() => getProducts(filters));
```

## Error Handling

### Retry Logic
```javascript
async function getProductsWithRetry(filters, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await getProducts(filters);
    } catch (error) {
      if (attempt === maxRetries) throw error;
      
      // Exponential backoff
      const delay = 1000 * Math.pow(2, attempt - 1);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}
```

### Fallback Data
```javascript
const fallbackProducts = [
  {
    id: "fallback_1",
    name: "Sample Product",
    price: 99.99,
    description: "Product information currently unavailable",
    images: ["/static/img/fallback.jpg"]
  }
];

async function getProductsSafe(filters) {
  try {
    return await getProducts(filters);
  } catch (error) {
    console.error('Failed to load products, using fallback:', error);
    return {
      items: fallbackProducts,
      total: fallbackProducts.length,
      page: 1,
      pageSize: fallbackProducts.length
    };
  }
}
```

---

## Related Endpoints
- [GET /products/{productId}](../products/get-product.md) - Get single product details
- [POST /products](../products/create-product.md) - Create new product (admin)
- [GET /files](../images/list-images.md) - List product images
- [Error Responses](../../errors.md) - Error handling details

## Notes
- Default page size is 20, maximum is 100
- Search is case-insensitive and supports partial matching
- Multiple tags are treated as AND filters
- Price filters use inclusive ranges (≥ min_price, ≤ max_price)
- Consider implementing category-based filtering if needed
- For large catalogs, implement server-side sorting and indexing