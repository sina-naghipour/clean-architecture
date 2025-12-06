# cURL Examples

Complete command-line examples using cURL for the Ecommerce API.

## Table of Contents
- [Setup & Configuration](#setup-configuration)
- [Authentication](#authentication)
- [Products](#products)
- [Product Images](#product-images)
- [Shopping Cart](#shopping-cart)
- [Orders](#orders)
- [Error Handling](#error-handling)

## Setup & Configuration

### Environment Variables Setup

Set your API base URL and tokens as environment variables:

```bash
export API_BASE="http://localhost:8000/api"
export ACCESS_TOKEN="your_access_token_here"
export REFRESH_TOKEN="your_refresh_token_here"
```

### Base cURL Options

Create reusable cURL functions in your shell profile:

```bash
curl_json() {
    curl -s -H "Content-Type: application/json" "$@"
}

curl_auth() {
    curl -s -H "Content-Type: application/json" \
         -H "Authorization: Bearer $ACCESS_TOKEN" "$@"
}

curl_form() {
    curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
         -F "$@"
}
```

## Authentication

### 1. User Registration

Register a new user account:

```bash
curl -X POST "$API_BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "S3cureP@ss123",
    "name": "Alice Johnson"
  }'
```

**Response (201 Created):**
```json
{
  "id": "user_123",
  "email": "alice@example.com",
  "name": "Alice Johnson"
}
```

### 2. User Login

Authenticate and obtain tokens:

```bash
response=$(curl -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "S3cureP@ss123"
  }')

# Extract tokens (requires jq)
ACCESS_TOKEN=$(echo $response | jq -r '.accessToken')
REFRESH_TOKEN=$(echo $response | jq -r '.refreshToken')
```

**Response (200 OK):**
```json
{
  "accessToken": "eyJhbGciOi...",
  "refreshToken": "rft_abcdef"
}
```

### 3. Refresh Access Token

Get a new access token using refresh token:

```bash
curl -X POST "$API_BASE/auth/refresh-token" \
  -H "Content-Type: application/json" \
  -d '{
    "refreshToken": "'"$REFRESH_TOKEN"'"
  }'
```

### 4. Logout

Revoke refresh token:

```bash
curl -X POST "$API_BASE/auth/logout" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## Products

### 1. List All Products (No Auth Required)

Basic product listing:

```bash
curl "$API_BASE/products"
```

With pagination:

```bash
curl "$API_BASE/products?page=2&pageSize=10"
```

With search and filters:

```bash
curl "$API_BASE/products?q=wireless&tags=electronics&min_price=20&max_price=100"
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "prod_1",
      "name": "Wireless Mouse",
      "price": 29.99,
      "stock": 100,
      "description": "Ergonomic wireless mouse",
      "tags": ["electronics", "peripheral"],
      "images": ["/static/img/products/prod_1/image1.jpg"],
      "primaryImageId": "img_123",
      "created_at": "2023-10-01T12:00:00Z",
      "updated_at": "2023-10-01T12:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "pageSize": 20
}
```

### 2. Create Product (Admin Only)

Add a new product to the catalog:

```bash
curl -X POST "$API_BASE/products" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wireless Mechanical Keyboard",
    "price": 129.99,
    "stock": 50,
    "description": "RGB mechanical keyboard with wireless connectivity",
    "tags": ["electronics", "keyboard", "peripheral"],
    "images": []
  }'
```

### 3. Get Specific Product

Retrieve details for a single product:

```bash
curl "$API_BASE/products/prod_42"
```

### 4. Update Product (Partial Update)

Modify specific product fields:

```bash
curl -X PATCH "$API_BASE/products/prod_42" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 119.99,
    "description": "Updated description with new features"
  }'
```

### 5. Update Product Stock

Adjust inventory levels:

```bash
curl -X PATCH "$API_BASE/products/prod_42/inventory" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock": 75
  }'
```

**Response (200 OK):**
```json
{
  "id": "prod_42",
  "stock": 75
}
```

### 6. Delete Product

Remove product from catalog:

```bash
curl -X DELETE "$API_BASE/products/prod_42" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## Product Images

### 1. Upload Product Image

Upload an image file for a product:

```bash
curl -X POST "$API_BASE/files" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@/path/to/image.jpg" \
  -F "is_primary=true"
```

**Response (201 Created):**
```json
{
  "id": "img_12345678-1234-5678-1234-567812345678",
  "productId": "prod_42",
  "filename": "prod_42_abc123.jpg",
  "originalName": "mouse.jpg",
  "mimeType": "image/jpeg",
  "size": 2048576,
  "width": 800,
  "height": 600,
  "isPrimary": true,
  "url": "/static/img/products/prod_42/prod_42_abc123.jpg",
  "uploadedAt": "2023-10-01T12:00:00Z"
}
```

### 2. List All Images

Retrieve metadata for all uploaded images:

```bash
curl "$API_BASE/files"
```

### 3. Get Image Metadata

Get details for a specific image:

```bash
curl "$API_BASE/files/img_12345678-1234-5678-1234-567812345678"
```

### 4. Set Image as Primary

Designate an image as the primary product image:

```bash
curl -X PATCH "$API_BASE/files/img_12345678-1234-5678-1234-567812345678/primary" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 5. Delete Image

Remove an uploaded image:

```bash
curl -X DELETE "$API_BASE/files/img_12345678-1234-5678-1234-567812345678" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## Shopping Cart

### 1. Get Current Cart

Retrieve the authenticated user's shopping cart:

```bash
curl "$API_BASE/cart" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Response (200 OK):**
```json
{
  "id": "cart_123",
  "items": [
    {
      "id": "item_1",
      "product_id": "prod_42",
      "name": "Wireless Mouse",
      "quantity": 2,
      "unit_price": 29.99
    }
  ],
  "total": 59.98
}
```

### 2. Add Item to Cart

Add a product to the shopping cart:

```bash
curl -X POST "$API_BASE/cart/items" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "prod_42",
    "quantity": 2
  }'
```

### 3. Update Cart Item Quantity

Modify the quantity of a cart item:

```bash
curl -X PATCH "$API_BASE/cart/items/item_123" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 3
  }'
```

### 4. Remove Item from Cart

Remove an item from the cart:

```bash
curl -X DELETE "$API_BASE/cart/items/item_123" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 5. Clear Entire Cart

Remove all items from the cart:

```bash
curl -X DELETE "$API_BASE/cart" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## Orders

### 1. Create Order (Checkout)

Convert cart to an order:

```bash
curl -X POST "$API_BASE/orders" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "billingAddressId": "addr_1",
    "shippingAddressId": "addr_2",
    "paymentMethodToken": "pm_tok_abc123"
  }'
```

**Response (201 Created):**
```json
{
  "id": "order_1001",
  "status": "created",
  "total": 59.98,
  "billing_address_id": "addr_1",
  "shipping_address_id": "addr_2",
  "items": [
    {
      "product_id": "prod_42",
      "name": "Wireless Mouse",
      "quantity": 2,
      "unit_price": 29.99
    }
  ],
  "created_at": "2023-10-01T12:00:00Z"
}
```

### 2. List User's Orders

Retrieve order history with pagination:

```bash
curl "$API_BASE/orders" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

With specific pagination:

```bash
curl "$API_BASE/orders?page=1&page_size=10" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 3. Get Order Details

Get detailed information about a specific order:

```bash
curl "$API_BASE/orders/order_1001" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## Health & Service Info

### 1. Health Check

Check service health status:

```bash
curl "$API_BASE/health"
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "ecommerce-api",
  "timestamp": "2023-10-01T12:00:00Z",
  "environment": "development"
}
```

### 2. Readiness Check

Verify service readiness:

```bash
curl "$API_BASE/ready"
```

### 3. Service Information

Get service metadata:

```bash
curl "$API_BASE/info"
```

## Error Handling Examples

### 1. Handle 400 Bad Request

Malformed JSON payload:

```bash
curl -X POST "$API_BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{malformed json}'
```

**Response:**
```json
{
  "type": "https://example.com/errors/bad-request",
  "title": "Bad Request",
  "status": 400,
  "detail": "Malformed JSON body.",
  "instance": "/auth/register"
}
```

### 2. Handle 401 Unauthorized

Missing or invalid authentication:

```bash
curl -X GET "$API_BASE/cart"
```

### 3. Handle 404 Not Found

Non-existent resource:

```bash
curl "$API_BASE/products/nonexistent_id"
```

### 4. Handle 422 Unprocessable Entity

Validation errors:

```bash
curl -X POST "$API_BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "not-an-email",
    "password": "short",
    "name": "A"
  }'
```

## Advanced Examples

### Complete Shopping Flow

A complete shopping workflow from adding items to checkout:

```bash
# 1. Login
response=$(curl -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"S3cureP@ss123"}')
ACCESS_TOKEN=$(echo $response | jq -r '.accessToken')

# 2. Add items to cart
curl -X POST "$API_BASE/cart/items" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id":"prod_42","quantity":2}'

curl -X POST "$API_BASE/cart/items" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id":"prod_43","quantity":1}'

# 3. View cart
curl "$API_BASE/cart" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# 4. Checkout
curl -X POST "$API_BASE/orders" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "billingAddressId": "addr_1",
    "shippingAddressId": "addr_1",
    "paymentMethodToken": "pm_tok_abc123"
  }'

# 5. Clear cart
curl -X DELETE "$API_BASE/cart" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### File Upload with Progress

Upload large files with progress indication:

```bash
# Upload with progress bar
curl -X POST "$API_BASE/files" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@/path/to/large-image.jpg" \
  --progress-bar

# Resume failed upload
curl -X POST "$API_BASE/files" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@/path/to/large-image.jpg" \
  -C -  # Resume from previous position
```

### Testing with HTTP Status Codes

Test different scenarios and check status codes:

```bash
# Check only the HTTP status code
curl -o /dev/null -s -w "%{http_code}\n" "$API_BASE/health"

# Verbose output for debugging
curl -v "$API_BASE/products" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Follow redirects (if any)
curl -L "$API_BASE/info"

# Set timeout
curl --max-time 5 "$API_BASE/health"

# Retry on failure
curl --retry 3 "$API_BASE/health"
```

## Troubleshooting

### Common Issues

1. **"jq: command not found"**
   Install jq: `sudo apt-get install jq` (Ubuntu) or `brew install jq` (macOS)

2. **"curl: (7) Failed to connect"**
   Ensure your API server is running: `curl http://localhost:8000/api/health`

3. **"curl: (22) The requested URL returned error: 401"**
   Check your access token is valid: `echo $ACCESS_TOKEN`

4. **"curl: (60) SSL certificate problem"**
   For development with self-signed certificates, use `-k` flag to skip verification

### Debugging Commands

```bash
# Check network connectivity
ping -c 3 localhost

# Check if port is open
nc -z localhost 8000

# Test DNS resolution
dig localhost

# Monitor requests in real-time
curl -w "@curl-format.txt" "$API_BASE/products"
```

Create a `curl-format.txt` file for detailed timing:
```
time_namelookup:  %{time_namelookup}\n
time_connect:  %{time_connect}\n
time_appconnect:  %{time_appconnect}\n
time_pretransfer:  %{time_pretransfer}\n
time_redirect:  %{time_redirect}\n
time_starttransfer:  %{time_starttransfer}\n
----------\n
time_total:  %{time_total}\n
```

## Tips & Best Practices

1. **Store tokens securely**: Never commit tokens to version control
2. **Use environment variables**: For different environments (dev, staging, prod)
3. **Implement retry logic**: For transient failures
4. **Add timeouts**: Prevent hanging requests
5. **Validate responses**: Check status codes and response structure
6. **Log requests**: For debugging and monitoring
7. **Rate limiting**: Respect API rate limits
8. **Error handling**: Implement proper error handling in scripts

### Sample Shell Script

Create a reusable script for API operations:

```bash
#!/bin/bash
# api-client.sh - Ecommerce API Client

API_BASE="${API_BASE:-http://localhost:8000/api}"
ACCESS_TOKEN_FILE="${HOME}/.ecommerce_token"

load_token() {
    if [ -f "$ACCESS_TOKEN_FILE" ]; then
        ACCESS_TOKEN=$(cat "$ACCESS_TOKEN_FILE")
    fi
}

save_token() {
    echo "$1" > "$ACCESS_TOKEN_FILE"
    chmod 600 "$ACCESS_TOKEN_FILE"
}

api_request() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    curl -s -X "$method" \
         -H "Content-Type: application/json" \
         -H "Authorization: Bearer $ACCESS_TOKEN" \
         -d "$data" \
         "${API_BASE}${endpoint}"
}

# Example usage
load_token
api_request "GET" "/cart"
```