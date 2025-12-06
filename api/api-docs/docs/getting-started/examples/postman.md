# Postman Examples

Complete Postman examples and workflows for the Ecommerce API.

## Table of Contents
- [Postman Collection Setup](#postman-collection-setup)
- [Environment Variables](#environment-variables)
- [Authentication Workflow](#authentication-workflow)
- [Product Management](#product-management)
- [Product Images](#product-images-1)
- [Shopping Cart](#shopping-cart-1)
- [Orders](#orders-1)
- [Testing & Automation](#testing--automation)
- [Monitoring & Documentation](#monitoring--documentation)
- [Best Practices](#best-practices)

## Postman Collection Structure

```
Ecommerce API/
├── 📁 Authentication
│   ├── Register User
│   ├── Login User
│   ├── Refresh Token
│   └── Logout
├── 📁 Products
│   ├── List Products
│   ├── Get Product
│   ├── Create Product (Admin)
│   ├── Update Product (Admin)
│   ├── Update Stock (Admin)
│   └── Delete Product (Admin)
├── 📁 Product Images
│   ├── Upload Image (Admin)
│   ├── List Images
│   ├── Get Image Metadata
│   ├── Set Primary Image (Admin)
│   └── Delete Image (Admin)
├── 📁 Shopping Cart
│   ├── Get Cart
│   ├── Add to Cart
│   ├── Update Cart Item
│   ├── Remove from Cart
│   └── Clear Cart
├── 📁 Orders
│   ├── Create Order
│   ├── List Orders
│   └── Get Order Details
├── 📁 Health & Info
│   ├── Health Check
│   ├── Readiness Check
│   └── Service Info
└── 📁 Tests & Examples
    ├── Complete Shopping Flow
    ├── Batch Operations
    └── Error Handling Tests
```

## Environment Variables

### Development Environment
```json
{
  "base_url": "http://localhost:8000/api",
  "admin_email": "admin@example.com",
  "admin_password": "AdminPass123!",
  "user_email": "user@example.com",
  "user_password": "UserPass123!",
  "access_token": "",
  "refresh_token": "",
  "product_id": "",
  "image_id": "",
  "cart_item_id": "",
  "order_id": "",
  "test_product_id": "test_prod_123"
}
```

### Production Environment
```json
{
  "base_url": "https://api.ecommerce.com/v1",
  "api_key": "{{your_api_key}}",
  "access_token": "",
  "refresh_token": ""
}
```

## Authentication Workflow

### 1. User Registration Request
**POST** `{{base_url}}/auth/register`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Body (raw JSON):**
```json
{
  "email": "{{$randomEmail}}",
  "password": "SecurePass123!",
  "name": "{{$randomFullName}}"
}
```

**Tests:**
```javascript
// Test 1: Verify successful registration
pm.test("Status code is 201", function () {
    pm.response.to.have.status(201);
});

pm.test("Response has user data", function () {
    const response = pm.response.json();
    pm.expect(response).to.have.property('id');
    pm.expect(response).to.have.property('email');
    pm.expect(response).to.have.property('name');
});

// Test 2: Store user data for later use
const response = pm.response.json();
pm.environment.set("user_id", response.id);
pm.environment.set("user_email", response.email);
```

### 2. User Login Request
**POST** `{{base_url}}/auth/login`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Body:**
```json
{
  "email": "{{user_email}}",
  "password": "SecurePass123!"
}
```

**Pre-request Script:**
```javascript
// Set credentials from environment
const email = pm.environment.get("user_email") || "user@example.com";
const password = pm.environment.get("user_password") || "UserPass123!";

pm.request.body.raw = JSON.stringify({
    email: email,
    password: password
});
```

**Tests:**
```javascript
// Test 1: Verify successful login
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Test 2: Verify token structure
const response = pm.response.json();
pm.test("Response has access token", function () {
    pm.expect(response).to.have.property('accessToken');
    pm.expect(response.accessToken).to.be.a('string');
});

pm.test("Response has refresh token", function () {
    pm.expect(response).to.have.property('refreshToken');
    pm.expect(response.refreshToken).to.be.a('string');
});

// Test 3: Store tokens in environment
pm.environment.set("access_token", response.accessToken);
pm.environment.set("refresh_token", response.refreshToken);

console.log("Access token stored:", response.accessToken.substring(0, 20) + "...");
```

### 3. Refresh Token Request
**POST** `{{base_url}}/auth/refresh-token`

**Headers:**
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer {{access_token}}"
}
```

**Body:**
```json
{
  "refreshToken": "{{refresh_token}}"
}
```

**Tests:**
```javascript
// Test 1: Verify successful refresh
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Test 2: Verify new access token
const response = pm.response.json();
pm.test("Response has new access token", function () {
    pm.expect(response).to.have.property('accessToken');
    pm.expect(response.accessToken).to.be.a('string');
});

// Test 3: Update access token
pm.environment.set("access_token", response.accessToken);
console.log("Access token refreshed:", response.accessToken.substring(0, 20) + "...");
```

### 4. Logout Request
**POST** `{{base_url}}/auth/logout`

**Headers:**
```json
{
  "Authorization": "Bearer {{access_token}}"
}
```

**Tests:**
```javascript
// Test 1: Verify successful logout
pm.test("Status code is 204", function () {
    pm.response.to.have.status(204);
});

// Test 2: Clear tokens from environment (optional)
pm.environment.unset("access_token");
pm.environment.unset("refresh_token");
console.log("Logged out successfully");
```

## Product Management

### 1. List Products Request
**GET** `{{base_url}}/products`

**Query Parameters:**
| Parameter | Value | Description |
|-----------|-------|-------------|
| page | 1 | Page number |
| pageSize | 20 | Items per page |
| q | wireless | Search query (optional) |
| tags | electronics | Filter by tags (optional) |
| min_price | 20 | Minimum price (optional) |
| max_price | 100 | Maximum price (optional) |

**Tests:**
```javascript
// Test 1: Verify successful response
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Test 2: Verify response structure
const response = pm.response.json();
pm.test("Response has pagination data", function () {
    pm.expect(response).to.have.property('items');
    pm.expect(response).to.have.property('total');
    pm.expect(response).to.have.property('page');
    pm.expect(response).to.have.property('pageSize');
    
    pm.expect(response.items).to.be.an('array');
});

// Test 3: Verify product structure
if (response.items.length > 0) {
    const product = response.items[0];
    pm.test("Product has required fields", function () {
        pm.expect(product).to.have.property('id');
        pm.expect(product).to.have.property('name');
        pm.expect(product).to.have.property('price');
        pm.expect(product).to.have.property('stock');
    });
    
    // Store first product ID for later use
    pm.environment.set("sample_product_id", product.id);
}

// Test 4: Verify pagination
pm.test("Pagination values are valid", function () {
    pm.expect(response.page).to.be.at.least(1);
    pm.expect(response.pageSize).to.be.at.least(1);
    pm.expect(response.total).to.be.at.least(0);
});
```

### 2. Get Product Request
**GET** `{{base_url}}/products/{{product_id}}`

**Tests:**
```javascript
// Test 1: Verify successful response
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Test 2: Verify product structure
const response = pm.response.json();
pm.test("Product has complete data", function () {
    pm.expect(response).to.have.property('id');
    pm.expect(response).to.have.property('name');
    pm.expect(response).to.have.property('price');
    pm.expect(response).to.have.property('stock');
    pm.expect(response).to.have.property('description');
    pm.expect(response).to.have.property('tags');
    pm.expect(response).to.have.property('images');
    pm.expect(response).to.have.property('created_at');
    pm.expect(response).to.have.property('updated_at');
});

// Test 3: Verify data types
pm.test("Product data types are correct", function () {
    pm.expect(response.id).to.be.a('string');
    pm.expect(response.name).to.be.a('string');
    pm.expect(response.price).to.be.a('number');
    pm.expect(response.stock).to.be.a('number');
    pm.expect(response.tags).to.be.an('array');
    pm.expect(response.images).to.be.an('array');
});

// Test 4: Store product data for later
pm.environment.set("current_product_id", response.id);
pm.environment.set("current_product_price", response.price);
pm.environment.set("current_product_stock", response.stock);
```

### 3. Create Product Request (Admin)
**POST** `{{base_url}}/products`

**Headers:**
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer {{admin_access_token}}"
}
```

**Body:**
```json
{
  "name": "Wireless Mechanical Keyboard",
  "price": 129.99,
  "stock": 50,
  "description": "RGB mechanical keyboard with wireless connectivity",
  "tags": ["electronics", "keyboard", "peripheral"],
  "images": []
}
```

**Pre-request Script:**
```javascript
// Generate unique product name
const timestamp = new Date().getTime();
const productName = `Test Product ${timestamp}`;

pm.request.body.raw = JSON.stringify({
    name: productName,
    price: 99.99,
    stock: 100,
    description: "Test product created via Postman",
    tags: ["test", "electronics"],
    images: []
});

console.log("Creating product:", productName);
```

**Tests:**
```javascript
// Test 1: Verify successful creation
pm.test("Status code is 201", function () {
    pm.response.to.have.status(201);
});

// Test 2: Verify response structure
const response = pm.response.json();
pm.test("Product created with correct data", function () {
    pm.expect(response).to.have.property('id');
    pm.expect(response).to.have.property('name');
    pm.expect(response).to.have.property('price', 99.99);
    pm.expect(response).to.have.property('stock', 100);
    pm.expect(response.tags).to.include('test');
});

// Test 3: Store product ID for later use
pm.environment.set("created_product_id", response.id);
pm.environment.set("created_product_name", response.name);

// Test 4: Verify Location header
pm.test("Location header present", function () {
    pm.expect(pm.response.headers.get('Location')).to.include(response.id);
});

console.log("Product created with ID:", response.id);
```

### 4. Update Product Request (Admin)
**PATCH** `{{base_url}}/products/{{created_product_id}}`

**Headers:**
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer {{admin_access_token}}"
}
```

**Body:**
```json
{
  "price": 89.99,
  "description": "Updated description with new features",
  "stock": 75
}
```

**Tests:**
```javascript
// Test 1: Verify successful update
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Test 2: Verify updated fields
const response = pm.response.json();
pm.test("Price was updated", function () {
    pm.expect(response.price).to.equal(89.99);
});

pm.test("Stock was updated", function () {
    pm.expect(response.stock).to.equal(75);
});

pm.test("Description was updated", function () {
    pm.expect(response.description).to.equal("Updated description with new features");
});

// Test 3: Verify other fields unchanged
pm.test("Name unchanged", function () {
    const originalName = pm.environment.get("created_product_name");
    pm.expect(response.name).to.equal(originalName);
});

console.log("Product updated successfully");
```

### 5. Update Stock Request (Admin)
**PATCH** `{{base_url}}/products/{{created_product_id}}/inventory`

**Headers:**
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer {{admin_access_token}}"
}
```

**Body:**
```json
{
  "stock": 120
}
```

**Tests:**
```javascript
// Test 1: Verify successful update
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Test 2: Verify response structure
const response = pm.response.json();
pm.test("Response has product ID", function () {
    pm.expect(response).to.have.property('id');
    pm.expect(response.id).to.equal(pm.environment.get("created_product_id"));
});

pm.test("Stock was updated", function () {
    pm.expect(response).to.have.property('stock', 120);
});

// Test 3: Update environment variable
pm.environment.set("current_product_stock", response.stock);

console.log("Stock updated to:", response.stock);
```

### 6. Delete Product Request (Admin)
**DELETE** `{{base_url}}/products/{{created_product_id}}`

**Headers:**
```json
{
  "Authorization": "Bearer {{admin_access_token}}"
}
```

**Tests:**
```javascript
// Test 1: Verify successful deletion
pm.test("Status code is 204", function () {
    pm.response.to.have.status(204);
});

// Test 2: Verify product no longer exists
setTimeout(function() {
    pm.sendRequest({
        url: pm.environment.get("base_url") + "/products/" + pm.environment.get("created_product_id"),
        method: 'GET',
        header: {
            'Authorization': 'Bearer ' + pm.environment.get("admin_access_token")
        }
    }, function (err, res) {
        pm.test("Product should return 404 after deletion", function() {
            pm.expect(res.code).to.equal(404);
        });
    });
}, 1000);

// Test 3: Clean up environment
pm.environment.unset("created_product_id");
pm.environment.unset("created_product_name");

console.log("Product deleted successfully");
```

## Product Images

### 1. Upload Image Request (Admin)
**POST** `{{base_url}}/files`

**Headers:**
```json
{
  "Authorization": "Bearer {{admin_access_token}}"
}
```

**Body (form-data):**
| Key | Value | Type |
|-----|-------|------|
| file | Select file | File |
| is_primary | true | Text |

**Pre-request Script:**
```javascript
// Create a test image if no file is selected
if (!pm.request.body && pm.request.body.mode !== 'formdata') {
    // This is just for demonstration
    console.log("Please select an image file for upload");
}
```

**Tests:**
```javascript
// Test 1: Verify successful upload
pm.test("Status code is 201", function () {
    pm.response.to.have.status(201);
});

// Test 2: Verify response structure
const response = pm.response.json();
pm.test("Image has complete metadata", function () {
    pm.expect(response).to.have.property('id');
    pm.expect(response).to.have.property('productId');
    pm.expect(response).to.have.property('filename');
    pm.expect(response).to.have.property('originalName');
    pm.expect(response).to.have.property('mimeType');
    pm.expect(response).to.have.property('size');
    pm.expect(response).to.have.property('width');
    pm.expect(response).to.have.property('height');
    pm.expect(response).to.have.property('isPrimary');
    pm.expect(response).to.have.property('url');
    pm.expect(response).to.have.property('uploadedAt');
});

// Test 3: Store image ID for later use
pm.environment.set("uploaded_image_id", response.id);
pm.environment.set("uploaded_image_product_id", response.productId);

// Test 4: Verify file properties
pm.test("Image has valid properties", function () {
    pm.expect(response.size).to.be.at.least(1);
    pm.expect(response.width).to.be.at.least(1);
    pm.expect(response.height).to.be.at.least(1);
    pm.expect(['image/jpeg', 'image/png', 'image/webp']).to.include(response.mimeType);
});

// Test 5: Verify Location header
pm.test("Location header present", function () {
    pm.expect(pm.response.headers.get('Location')).to.include(response.id);
});

console.log("Image uploaded with ID:", response.id);
```

### 2. List Images Request
**GET** `{{base_url}}/files`

**Tests:**
```javascript
// Test 1: Verify successful response
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Test 2: Verify response is array
const response = pm.response.json();
pm.test("Response is an array", function () {
    pm.expect(response).to.be.an('array');
});

// Test 3: Verify image structure (if images exist)
if (response.length > 0) {
    const image = response[0];
    pm.test("First image has required fields", function () {
        pm.expect(image).to.have.property('id');
        pm.expect(image).to.have.property('productId');
        pm.expect(image).to.have.property('filename');
        pm.expect(image).to.have.property('url');
    });
    
    // Store first image ID if not already stored
    if (!pm.environment.get("sample_image_id")) {
        pm.environment.set("sample_image_id", image.id);
    }
}

console.log("Found", response.length, "images");
```

### 3. Get Image Metadata Request
**GET** `{{base_url}}/files/{{uploaded_image_id}}`

**Tests:**
```javascript
// Test 1: Verify successful response
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Test 2: Verify complete metadata
const response = pm.response.json();
pm.test("Image metadata is complete", function () {
    const requiredFields = [
        'id', 'productId', 'filename', 'originalName',
        'mimeType', 'size', 'width', 'height',
        'isPrimary', 'url', 'uploadedAt'
    ];
    
    requiredFields.forEach(field => {
        pm.expect(response).to.have.property(field);
    });
});

// Test 3: Verify URL is accessible
pm.test("Image URL is valid", function () {
    pm.expect(response.url).to.match(/^https?:\/\//);
});

// Test 4: Store URL for testing
pm.environment.set("image_url", response.url);

console.log("Image metadata retrieved for:", response.originalName);
```

### 4. Set Primary Image Request (Admin)
**PATCH** `{{base_url}}/files/{{uploaded_image_id}}/primary`

**Headers:**
```json
{
  "Authorization": "Bearer {{admin_access_token}}"
}
```

**Tests:**
```javascript
// Test 1: Verify successful update
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Test 2: Verify image is now primary
const response = pm.response.json();
pm.test("Image is marked as primary", function () {
    pm.expect(response.isPrimary).to.be.true;
});

// Test 3: Verify other fields unchanged
pm.test("Image ID unchanged", function () {
    pm.expect(response.id).to.equal(pm.environment.get("uploaded_image_id"));
});

console.log("Image set as primary:", response.originalName);
```

### 5. Delete Image Request (Admin)
**DELETE** `{{base_url}}/files/{{uploaded_image_id}}`

**Headers:**
```json
{
  "Authorization": "Bearer {{admin_access_token}}"
}
```

**Tests:**
```javascript
// Test 1: Verify successful deletion
pm.test("Status code is 204", function () {
    pm.response.to.have.status(204);
});

// Test 2: Verify image no longer exists
setTimeout(function() {
    pm.sendRequest({
        url: pm.environment.get("base_url") + "/files/" + pm.environment.get("uploaded_image_id"),
        method: 'GET'
    }, function (err, res) {
        pm.test("Image should return 404 after deletion", function() {
            pm.expect(res.code).to.equal(404);
        });
    });
}, 1000);

// Test 3: Clean up environment
pm.environment.unset("uploaded_image_id");
pm.environment.unset("image_url");

console.log("Image deleted successfully");
```

## Shopping Cart

### 1. Get Cart Request
**GET** `{{base_url}}/cart`

**Headers:**
```json
{
  "Authorization": "Bearer {{access_token}}"
}
```

**Tests:**
```javascript
// Test 1: Verify successful response
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Test 2: Verify cart structure
const response = pm.response.json();
pm.test("Cart has correct structure", function () {
    pm.expect(response).to.have.property('id');
    pm.expect(response).to.have.property('items');
    pm.expect(response).to.have.property('total');
    
    pm.expect(response.items).to.be.an('array');
    pm.expect(response.total).to.be.a('number');
});

// Test 3: Store cart data
pm.environment.set("cart_id", response.id);

// Test 4: Verify cart items structure
if (response.items.length > 0) {
    const item = response.items[0];
    pm.test("Cart item has required fields", function () {
        pm.expect(item).to.have.property('id');
        pm.expect(item).to.have.property('product_id');
        pm.expect(item).to.have.property('name');
        pm.expect(item).to.have.property('quantity');
        pm.expect(item).to.have.property('unit_price');
        
        // Store first item ID for later use
        pm.environment.set("cart_item_id", item.id);
    });
}

// Test 5: Calculate and verify total
if (response.items.length > 0) {
    const calculatedTotal = response.items.reduce((sum, item) => {
        return sum + (item.quantity * item.unit_price);
    }, 0);
    
    pm.test("Cart total matches item totals", function () {
        pm.expect(response.total).to.equal(calculatedTotal);
    });
}

console.log("Cart has", response.items.length, "items, total: $", response.total);
```

### 2. Add to Cart Request
**POST** `{{base_url}}/cart/items`

**Headers:**
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer {{access_token}}"
}
```

**Body:**
```json
{
  "product_id": "{{sample_product_id}}",
  "quantity": 2
}
```

**Pre-request Script:**
```javascript
// Use sample product if available, otherwise use test product
const productId = pm.environment.get("sample_product_id") || pm.environment.get("test_product_id");

pm.request.body.raw = JSON.stringify({
    product_id: productId,
    quantity: 2
});

console.log("Adding product to cart:", productId);
```

**Tests:**
```javascript
// Test 1: Verify successful addition
pm.test("Status code is 201", function () {
    pm.response.to.have.status(201);
});

// Test 2: Verify response structure
const response = pm.response.json();
pm.test("Cart item created with correct data", function () {
    pm.expect(response).to.have.property('id');
    pm.expect(response).to.have.property('product_id');
    pm.expect(response).to.have.property('quantity', 2);
});

// Test 3: Store cart item ID
pm.environment.set("cart_item_id", response.id);

// Test 4: Verify Location header
pm.test("Location header present", function () {
    pm.expect(pm.response.headers.get('Location')).to.include(response.id);
});

// Test 5: Verify cart was updated
setTimeout(function() {
    pm.sendRequest({
        url: pm.environment.get("base_url") + "/cart",
        method: 'GET',
        header: {
            'Authorization': 'Bearer ' + pm.environment.get("access_token")
        }
    }, function (err, res) {
        if (res.code === 200) {
            const cart = res.json();
            const itemExists = cart.items.some(item => item.id === response.id);
            pm.test("Item exists in cart", function() {
                pm.expect(itemExists).to.be.true;
            });
        }
    });
}, 500);

console.log("Item added to cart with ID:", response.id);
```

### 3. Update Cart Item Request
**PATCH** `{{base_url}}/cart/items/{{cart_item_id}}`

**Headers:**
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer {{access_token}}"
}
```

**Body:**
```json
{
  "quantity": 3
}
```

**Tests:**
```javascript
// Test 1: Verify successful update
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Test 2: Verify quantity was updated
const response = pm.response.json();
pm.test("Quantity updated correctly", function () {
    pm.expect(response).to.have.property('quantity', 3);
});

// Test 3: Verify other fields unchanged
pm.test("Product ID unchanged", function () {
    pm.expect(response.product_id).to.equal(pm.environment.get("sample_product_id") || pm.environment.get("test_product_id"));
});

// Test 4: Verify cart total updated
setTimeout(function() {
    pm.sendRequest({
        url: pm.environment.get("base_url") + "/cart",
        method: 'GET',
        header: {
            'Authorization': 'Bearer ' + pm.environment.get("access_token")
        }
    }, function (err, res) {
        if (res.code === 200) {
            const cart = res.json();
            const updatedItem = cart.items.find(item => item.id === response.id);
            pm.test("Item quantity in cart matches update", function() {
                pm.expect(updatedItem.quantity).to.equal(3);
            });
        }
    });
}, 500);

console.log("Cart item quantity updated to:", response.quantity);
```

### 4. Remove from Cart Request
**DELETE** `{{base_url}}/cart/items/{{cart_item_id}}`

**Headers:**
```json
{
  "Authorization": "Bearer {{access_token}}"
}
```

**Tests:**
```javascript
// Test 1: Verify successful removal
pm.test("Status code is 204", function () {
    pm.response.to.have.status(204);
});

// Test 2: Verify item no longer in cart
setTimeout(function() {
    pm.sendRequest({
        url: pm.environment.get("base_url") + "/cart",
        method: 'GET',
        header: {
            'Authorization': 'Bearer ' + pm.environment.get("access_token")
        }
    }, function (err, res) {
        if (res.code === 200) {
            const cart = res.json();
            const itemExists = cart.items.some(item => item.id === pm.environment.get("cart_item_id"));
            pm.test("Item should not exist in cart", function() {
                pm.expect(itemExists).to.be.false;
            });
        }
    });
}, 500);

// Test 3: Clean up environment
pm.environment.unset("cart_item_id");

console.log("Item removed from cart");
```

### 5. Clear Cart Request
**DELETE** `{{base_url}}/cart`

**Headers:**
```json
{
  "Authorization": "Bearer {{access_token}}"
}
```

**Tests:**
```javascript
// Test 1: Verify successful clearance
pm.test("Status code is 204", function () {
    pm.response.to.have.status(204);
});

// Test 2: Verify cart is empty
setTimeout(function() {
    pm.sendRequest({
        url: pm.environment.get("base_url") + "/cart",
        method: 'GET',
        header: {
            'Authorization': 'Bearer ' + pm.environment.get("access_token")
        }
    }, function (err, res) {
        if (res.code === 200) {
            const cart = res.json();
            pm.test("Cart should be empty", function() {
                pm.expect(cart.items).to.be.an('array').that.is.empty;
                pm.expect(cart.total).to.equal(0);
            });
        }
    });
}, 500);

console.log("Cart cleared successfully");
```

## Orders

### 1. Create Order Request
**POST** `{{base_url}}/orders`

**Headers:**
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer {{access_token}}"
}
```

**Body:**
```json
{
  "billingAddressId": "addr_1",
  "shippingAddressId": "addr_1",
  "paymentMethodToken": "pm_tok_abc123"
}
```

**Pre-request Script:**
```javascript
// Ensure cart has items before creating order
console.log("Creating order from current cart...");

// You might want to add items to cart first if empty
const productId = pm.environment.get("sample_product_id") || pm.environment.get("test_product_id");
if (productId) {
    // Add an item to cart first
    pm.sendRequest({
        url: pm.environment.get("base_url") + "/cart/items",
        method: 'POST',
        header: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + pm.environment.get("access_token")
        },
        body: {
            mode: 'raw',
            raw: JSON.stringify({
                product_id: productId,
                quantity: 1
            })
        }
    }, function (err, res) {
        console.log("Added item to cart for order creation");
    });
}
```

**Tests:**
```javascript
// Test 1: Verify successful order creation
pm.test("Status code is 201", function () {
    pm.response.to.have.status(201);
});

// Test 2: Verify order structure
const response = pm.response.json();
pm.test("Order has complete data", function () {
    pm.expect(response).to.have.property('id');
    pm.expect(response).to.have.property('status');
    pm.expect(response).to.have.property('total');
    pm.expect(response).to.have.property('billing_address_id');
    pm.expect(response).to.have.property('shipping_address_id');
    pm.expect(response).to.have.property('items');
    pm.expect(response).to.have.property('created_at');
    
    pm.expect(response.items).to.be.an('array');
    pm.expect(response.status).to.be.oneOf(['created', 'paid', 'shipped', 'canceled']);
});

// Test 3: Store order ID for later use
pm.environment.set("order_id", response.id);

// Test 4: Verify Location header
pm.test("Location header present", function () {
    pm.expect(pm.response.headers.get('Location')).to.include(response.id);
});

// Test 5: Verify cart is cleared after order
setTimeout(function() {
    pm.sendRequest({
        url: pm.environment.get("base_url") + "/cart",
        method: 'GET',
        header: {
            'Authorization': 'Bearer ' + pm.environment.get("access_token")
        }
    }, function (err, res) {
        if (res.code === 200) {
            const cart = res.json();
            pm.test("Cart should be empty after order", function() {
                pm.expect(cart.items).to.be.an('array').that.is.empty;
            });
        }
    });
}, 1000);

console.log("Order created with ID:", response.id, "Status:", response.status);
```

### 2. List Orders Request
**GET** `{{base_url}}/orders`

**Headers:**
```json
{
  "Authorization": "Bearer {{access_token}}"
}
```

**Query Parameters:**
| Parameter | Value | Description |
|-----------|-------|-------------|
| page | 1 | Page number |
| page_size | 20 | Items per page |

**Tests:**
```javascript
// Test 1: Verify successful response
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Test 2: Verify response structure
const response = pm.response.json();
pm.test("Response has pagination data", function () {
    pm.expect(response).to.have.property('items');
    pm.expect(response).to.have.property('total');
    pm.expect(response).to.have.property('page');
    pm.expect(response).to.have.property('page_size');
    
    pm.expect(response.items).to.be.an('array');
});

// Test 3: Verify order structure in list
if (response.items.length > 0) {
    const order = response.items[0];
    pm.test("Order in list has required fields", function () {
        pm.expect(order).to.have.property('id');
        pm.expect(order).to.have.property('status');
        pm.expect(order).to.have.property('total');
        pm.expect(order).to.have.property('created_at');
    });
    
    // Store first order ID if no order ID is set
    if (!pm.environment.get("order_id") && order.id) {
        pm.environment.set("order_id", order.id);
    }
}

// Test 4: Verify pagination
pm.test("Pagination values are valid", function () {
    pm.expect(response.page).to.be.at.least(1);
    pm.expect(response.page_size).to.be.at.least(1);
    pm.expect(response.total).to.be.at.least(0);
});

console.log("Found", response.total, "orders, showing", response.items.length, "on page", response.page);
```

### 3. Get Order Details Request
**GET** `{{base_url}}/orders/{{order_id}}`

**Headers:**
```json
{
  "Authorization": "Bearer {{access_token}}"
}
```

**Tests:**
```javascript
// Test 1: Verify successful response
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Test 2: Verify complete order details
const response = pm.response.json();
pm.test("Order has complete details", function () {
    const requiredFields = [
        'id', 'status', 'total', 'billing_address_id',
        'shipping_address_id', 'items', 'created_at'
    ];
    
    requiredFields.forEach(field => {
        pm.expect(response).to.have.property(field);
    });
    
    pm.expect(response.items).to.be.an('array');
    pm.expect(response.status).to.be.oneOf(['created', 'paid', 'shipped', 'canceled']);
});

// Test 3: Verify order items structure
if (response.items.length > 0) {
    const item = response.items[0];
    pm.test("Order item has required fields", function () {
        pm.expect(item).to.have.property('product_id');
        pm.expect(item).to.have.property('name');
        pm.expect(item).to.have.property('quantity');
        pm.expect(item).to.have.property('unit_price');
    });
}

// Test 4: Calculate and verify total
if (response.items.length > 0) {
    const calculatedTotal = response.items.reduce((sum, item) => {
        return sum + (item.quantity * item.unit_price);
    }, 0);
    
    pm.test("Order total matches item totals", function () {
        // Allow for small floating point differences
        pm.expect(response.total).to.be.closeTo(calculatedTotal, 0.01);
    });
}

// Test 5: Verify order ID matches
pm.test("Order ID matches requested ID", function () {
    pm.expect(response.id).to.equal(pm.environment.get("order_id"));
});

console.log("Order details retrieved for:", response.id, "Status:", response.status);
```

## Testing & Automation

### 1. Complete Shopping Flow Collection
Create a collection that simulates a complete shopping experience:

**Collection: Complete Shopping Flow**
```javascript
// Collection-level pre-request script
const baseUrl = pm.environment.get("base_url");

// Collection-level tests
pm.test("Collection completed successfully", function () {
    // This runs after all requests
    console.log("Complete shopping flow executed");
});

// Request 1: Register User
// Request 2: Login
// Request 3: Browse Products
// Request 4: Add to Cart
// Request 5: Update Cart
// Request 6: Create Order
// Request 7: Get Order Details
// Request 8: List Orders
```

### 2. Data-Driven Tests
Create a CSV file for data-driven testing:

**test_data.csv:**
```csv
product_name,price,stock,description,tags
Wireless Mouse,29.99,100,Ergonomic wireless mouse,"electronics,peripheral"
Mechanical Keyboard,129.99,50,RGB mechanical keyboard,"electronics,keyboard"
Laptop Stand,49.99,200,Adjustable laptop stand,"electronics,accessories"
```

**Test Script using CSV:**
```javascript
// Read data from CSV
const testData = pm.iterationData;

// Use data in request
pm.request.body.raw = JSON.stringify({
    name: testData.get("product_name"),
    price: parseFloat(testData.get("price")),
    stock: parseInt(testData.get("stock")),
    description: testData.get("description"),
    tags: testData.get("tags").split(",")
});

// Tests using data
pm.test(`Product ${testData.get("product_name")} created successfully`, function() {
    pm.response.to.have.status(201);
});
```

### 3. Monitor Collection
Create a monitoring collection for API health:

**Collection: API Health Monitor**
```javascript
// Request 1: Health Check
pm.test("Health check passed", function () {
    pm.response.to.have.status(200);
    const response = pm.response.json();
    pm.expect(response.status).to.equal("healthy");
});

// Request 2: Readiness Check
pm.test("Readiness check passed", function () {
    pm.response.to.have.status(200);
});

// Request 3: Service Info
pm.test("Service info available", function () {
    pm.response.to.have.status(200);
    const response = pm.response.json();
    pm.expect(response).to.have.property("version");
});

// Collection test: All checks passed
pm.test("All health checks passed", function () {
    // This would aggregate results from all requests
    pm.expect(pm.info.requestName).to.not.include("failed");
});
```

## Monitoring & Documentation

### 1. Collection Documentation
Add comprehensive documentation to your collection:

**Collection Description:**
```
# Ecommerce API Collection

Complete Postman collection for the Ecommerce API with product management, 
shopping cart, orders, and authentication.

## Prerequisites
1. Set up environment variables
2. Update base_url for your environment
3. Have valid user credentials

## Usage
1. Start with authentication requests
2. Use product endpoints for catalog management
3. Test shopping cart operations
4. Create and manage orders

## Authentication
All endpoints except public ones require Bearer token authentication.
Store tokens in environment variables after login.
```

### 2. Request Documentation
Add descriptions to each request:

**Request Description Template:**
```
## Create Product

Creates a new product in the catalog. Requires admin authentication.

### Headers
- Authorization: Bearer token
- Content-Type: application/json

### Body
- name: Product name (required)
- price: Product price (required)
- stock: Initial stock quantity
- description: Product description
- tags: Array of category tags
- images: Array of image URLs

### Responses
- 201: Product created successfully
- 400: Bad request (invalid data)
- 401: Unauthorized (missing/invalid token)
- 403: Forbidden (not admin)
- 422: Validation error

### Example
```json
{
    "name": "Wireless Keyboard",
    "price": 99.99,
    "stock": 50,
    "description": "Mechanical wireless keyboard",
    "tags": ["electronics", "keyboard"],
    "images": []
}
```
```

### 3. Environment Templates
Create environment templates for different scenarios:

**Development Environment Template:**
```json
{
  "id": "development",
  "name": "Development",
  "values": [
    {
      "key": "base_url",
      "value": "http://localhost:8000/api",
      "type": "default",
      "enabled": true
    },
    {
      "key": "admin_email",
      "value": "admin@example.com",
      "type": "secret",
      "enabled": true
    },
    {
      "key": "admin_password",
      "value": "AdminPass123!",
      "type": "secret",
      "enabled": true
    }
  ],
  "_postman_variable_scope": "environment"
}
```

## Best Practices

### 1. Security Best Practices
- Never commit sensitive data to version control
- Use environment variables for secrets
- Implement token refresh logic
- Validate responses before storing data
- Use different environments for dev/staging/prod

### 2. Testing Best Practices
- Write comprehensive test scripts
- Use environment variables for dynamic data
- Implement retry logic for flaky tests
- Test both success and error scenarios
- Validate response schemas

### 3. Organization Best Practices
- Group related requests in folders
- Use descriptive request names
- Add comprehensive documentation
- Create workflow collections
- Use data files for parameterized tests

### 4. Automation Best Practices
- Set up CI/CD integration
- Use Postman CLI for automation
- Implement monitoring collections
- Create performance tests
- Set up alerting for failures

### 5. Example: Complete Test Suite
```javascript
// Complete test suite for product endpoints
describe("Product API Tests", function () {
    
    before(function () {
        // Setup before all tests
        console.log("Starting product API tests");
    });
    
    beforeEach(function () {
        // Setup before each test
        pm.environment.set("test_timestamp", new Date().getTime());
    });
    
    it("should list products with pagination", function () {
        pm.sendRequest({
            url: pm.environment.get("base_url") + "/products?page=1&pageSize=10",
            method: 'GET'
        }, function (err, res) {
            pm.expect(res.code).to.equal(200);
            pm.expect(res.json()).to.have.property('items');
            pm.expect(res.json().items).to.be.an('array');
        });
    });
    
    it("should create a product with valid data", function () {
        const productData = {
            name: `Test Product ${pm.environment.get("test_timestamp")}`,
            price: 99.99,
            stock: 100,
            description: "Test product",
            tags: ["test"],
            images: []
        };
        
        pm.sendRequest({
            url: pm.environment.get("base_url") + "/products",
            method: 'POST',
            header: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + pm.environment.get("admin_access_token")
            },
            body: {
                mode: 'raw',
                raw: JSON.stringify(productData)
            }
        }, function (err, res) {
            pm.expect(res.code).to.equal(201);
            pm.expect(res.json()).to.have.property('id');
            
            // Store product ID for cleanup
            pm.environment.set("test_product_id", res.json().id);
        });
    });
    
    after(function () {
        // Cleanup after all tests
        const productId = pm.environment.get("test_product_id");
        if (productId) {
            pm.sendRequest({
                url: pm.environment.get("base_url") + "/products/" + productId,
                method: 'DELETE',
                header: {
                    'Authorization': 'Bearer ' + pm.environment.get("admin_access_token")
                }
            }, function (err, res) {
                console.log("Test product cleaned up");
            });
        }
    });
});
```