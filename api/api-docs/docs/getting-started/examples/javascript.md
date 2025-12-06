# JavaScript Examples

Complete JavaScript examples for the Ecommerce API using modern JavaScript (ES6+).

## Table of Contents
- [Setup & Installation](#setup-installation)
- [Authentication](#authentication)
- [Products](#products)
- [Product Images](#product-images)
- [Shopping Cart](#shopping-cart)
- [Orders](#orders)
- [Error Handling](#error-handling)
- [Complete Shopping Flow](#complete-shopping-flow)
- [React Hook Examples](#react-hook-examples)

## Setup & Installation

### Install Dependencies
```bash
npm install axios
# or
yarn add axios
```

### Basic API Client Setup
```javascript
// api-client.js
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

class EcommerceAPI {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  setupInterceptors() {
    // Request interceptor - add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const newToken = await this.refreshAccessToken();
            this.setAccessToken(newToken);
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            this.clearTokens();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Token management
  getAccessToken() {
    return localStorage.getItem('accessToken');
  }

  setAccessToken(token) {
    localStorage.setItem('accessToken', token);
  }

  getRefreshToken() {
    return localStorage.getItem('refreshToken');
  }

  setRefreshToken(token) {
    localStorage.setItem('refreshToken', token);
  }

  clearTokens() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  }

  // API Methods will be defined below
}

export default new EcommerceAPI();
```

## Authentication

### 1. User Registration
```javascript
// auth-service.js
import api from './api-client';

export const authService = {
  async register(userData) {
    try {
      const response = await api.client.post('/auth/register', userData);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  },

  // Example usage
  async registerUser() {
    const userData = {
      email: 'alice@example.com',
      password: 'S3cureP@ss123',
      name: 'Alice Johnson',
    };

    const result = await this.register(userData);
    
    if (result.success) {
      console.log('User registered:', result.data);
      return result.data;
    } else {
      console.error('Registration failed:', result.error);
      throw new Error(result.error);
    }
  },

  handleError(error) {
    if (error.response) {
      // Server responded with error
      return {
        success: false,
        error: error.response.data.detail || 'An error occurred',
        status: error.response.status,
      };
    } else if (error.request) {
      // No response received
      return {
        success: false,
        error: 'Network error - please check your connection',
      };
    } else {
      // Request setup error
      return {
        success: false,
        error: error.message,
      };
    }
  },
};
```

### 2. User Login
```javascript
// auth-service.js (continued)
export const authService = {
  async login(credentials) {
    try {
      const response = await api.client.post('/auth/login', credentials);
      
      // Store tokens
      api.setAccessToken(response.data.accessToken);
      api.setRefreshToken(response.data.refreshToken);
      
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  },

  async loginUser() {
    const credentials = {
      email: 'alice@example.com',
      password: 'S3cureP@ss123',
    };

    const result = await this.login(credentials);
    
    if (result.success) {
      console.log('Login successful');
      // Redirect to dashboard or update UI
      return result.data;
    } else {
      console.error('Login failed:', result.error);
      // Show error message to user
      throw new Error(result.error);
    }
  },

  // Refresh token
  async refreshAccessToken() {
    try {
      const refreshToken = api.getRefreshToken();
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await api.client.post('/auth/refresh-token', {
        refreshToken,
      });

      api.setAccessToken(response.data.accessToken);
      return response.data.accessToken;
    } catch (error) {
      api.clearTokens();
      throw error;
    }
  },

  // Logout
  async logout() {
    try {
      await api.client.post('/auth/logout');
      api.clearTokens();
      
      // Redirect to login page
      window.location.href = '/login';
      
      return { success: true };
    } catch (error) {
      console.error('Logout failed:', error);
      // Still clear tokens even if API call fails
      api.clearTokens();
      window.location.href = '/login';
      return this.handleError(error);
    }
  },
};
```

## Products

### 1. Product Service
```javascript
// product-service.js
import api from './api-client';

export const productService = {
  // List products with filters
  async getProducts(filters = {}) {
    try {
      const params = new URLSearchParams();
      
      // Add pagination
      if (filters.page) params.append('page', filters.page);
      if (filters.pageSize) params.append('pageSize', filters.pageSize);
      
      // Add search
      if (filters.q) params.append('q', filters.q);
      
      // Add filters
      if (filters.tags) {
        if (Array.isArray(filters.tags)) {
          filters.tags.forEach(tag => params.append('tags', tag));
        } else {
          params.append('tags', filters.tags);
        }
      }
      
      if (filters.min_price) params.append('min_price', filters.min_price);
      if (filters.max_price) params.append('max_price', filters.max_price);
      
      const response = await api.client.get(`/products?${params}`);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  },

  // Example: Get first page of electronics products
  async getElectronicsProducts() {
    return this.getProducts({
      tags: ['electronics'],
      page: 1,
      pageSize: 20,
    });
  },

  // Example: Search for products
  async searchProducts(query, options = {}) {
    return this.getProducts({
      q: query,
      ...options,
    });
  },

  // Get single product
  async getProduct(productId) {
    try {
      const response = await api.client.get(`/products/${productId}`);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  },

  // Create product (admin only)
  async createProduct(productData) {
    try {
      const response = await api.client.post('/products', productData);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  },

  // Example: Add a new product
  async addNewProduct() {
    const productData = {
      name: 'Wireless Mechanical Keyboard',
      price: 129.99,
      stock: 50,
      description: 'RGB mechanical keyboard with wireless connectivity',
      tags: ['electronics', 'keyboard', 'peripheral'],
      images: [],
    };

    const result = await this.createProduct(productData);
    
    if (result.success) {
      console.log('Product created:', result.data);
      return result.data;
    } else {
      console.error('Failed to create product:', result.error);
      throw new Error(result.error);
    }
  },

  // Update product (partial update)
  async updateProduct(productId, updates) {
    try {
      const response = await api.client.patch(`/products/${productId}`, updates);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  },

  // Example: Update product price
  async updateProductPrice(productId, newPrice) {
    return this.updateProduct(productId, { price: newPrice });
  },

  // Update product stock
  async updateStock(productId, stock) {
    try {
      const response = await api.client.patch(
        `/products/${productId}/inventory`,
        { stock }
      );
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  },

  // Delete product
  async deleteProduct(productId) {
    try {
      await api.client.delete(`/products/${productId}`);
      return { success: true };
    } catch (error) {
      return this.handleError(error);
    }
  },

  // Handle errors
  handleError(error) {
    if (error.response) {
      return {
        success: false,
        error: error.response.data.detail || 'An error occurred',
        status: error.response.status,
        data: error.response.data,
      };
    } else if (error.request) {
      return {
        success: false,
        error: 'Network error - please check your connection',
      };
    } else {
      return {
        success: false,
        error: error.message,
      };
    }
  },
};
```

### 2. Using Product Service
```javascript
// product-examples.js
import { productService } from './product-service';

// Example 1: Browse products with pagination
async function browseProducts() {
  try {
    const result = await productService.getProducts({
      page: 1,
      pageSize: 10,
    });
    
    if (result.success) {
      const { items, total, page, pageSize } = result.data;
      console.log(`Showing ${items.length} of ${total} products`);
      console.log(`Page ${page} of ${Math.ceil(total / pageSize)}`);
      
      // Render products
      items.forEach(product => {
        console.log(`- ${product.name}: $${product.price} (${product.stock} in stock)`);
      });
    }
  } catch (error) {
    console.error('Failed to load products:', error);
  }
}

// Example 2: Search and filter
async function searchAndFilter() {
  const result = await productService.getProducts({
    q: 'wireless',
    tags: ['electronics', 'computer'],
    min_price: 20,
    max_price: 200,
    pageSize: 25,
  });
  
  if (result.success) {
    return result.data.items;
  }
}

// Example 3: Product detail page
async function loadProductDetail(productId) {
  const result = await productService.getProduct(productId);
  
  if (result.success) {
    const product = result.data;
    
    // Display product information
    return {
      name: product.name,
      price: product.price,
      description: product.description,
      images: product.images,
      stock: product.stock > 0 ? `In Stock (${product.stock})` : 'Out of Stock',
      canAddToCart: product.stock > 0,
    };
  } else {
    throw new Error(`Failed to load product: ${result.error}`);
  }
}
```

## Product Images

### 1. Image Upload Service
```javascript
// image-service.js
import api from './api-client';

export const imageService = {
  // Upload product image
  async uploadImage(file, isPrimary = false) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('is_primary', isPrimary);
      
      const response = await api.client.post('/files', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  },

  // Example: Upload multiple images
  async uploadProductImages(productId, files) {
    const uploadPromises = files.map((file, index) =>
      this.uploadImage(file, index === 0) // First image as primary
    );
    
    const results = await Promise.allSettled(uploadPromises);
    
    const successfulUploads = results
      .filter(result => result.status === 'fulfilled' && result.value.success)
      .map(result => result.value.data);
    
    const failedUploads = results
      .filter(result => result.status === 'rejected' || !result.value.success);
    
    return {
      successful: successfulUploads,
      failed: failedUploads,
    };
  },

  // List all images
  async listImages() {
    try {
      const response = await api.client.get('/files');
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  },

  // Get image metadata
  async getImage(imageId) {
    try {
      const response = await api.client.get(`/files/${imageId}`);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  },

  // Set image as primary
  async setPrimaryImage(imageId) {
    try {
      const response = await api.client.patch(`/files/${imageId}/primary`);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  },

  // Delete image
  async deleteImage(imageId) {
    try {
      await api.client.delete(`/files/${imageId}`);
      return { success: true };
    } catch (error) {
      return this.handleError(error);
    }
  },

  // Handle file selection in browser
  handleFileSelect(event, onFilesSelected) {
    const files = Array.from(event.target.files);
    
    // Validate file types
    const validFiles = files.filter(file => {
      const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
      return validTypes.includes(file.type);
    });
    
    // Validate file size (max 5MB)
    const sizeValidFiles = validFiles.filter(file => file.size <= 5 * 1024 * 1024);
    
    if (sizeValidFiles.length !== files.length) {
      console.warn('Some files were rejected due to size or type restrictions');
    }
    
    if (onFilesSelected) {
      onFilesSelected(sizeValidFiles);
    }
    
    return sizeValidFiles;
  },

  // Preview image before upload
  createImagePreview(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = (e) => reject(e);
      reader.readAsDataURL(file);
    });
  },

  handleError(error) {
    if (error.response) {
      const { status, data } = error.response;
      
      if (status === 413) {
        return {
          success: false,
          error: 'File too large. Maximum size is 5MB.',
        };
      } else if (status === 415) {
        return {
          success: false,
          error: 'Unsupported file type. Only JPEG, PNG, and WebP are allowed.',
        };
      }
      
      return {
        success: false,
        error: data.detail || 'Upload failed',
        status,
        data,
      };
    } else if (error.request) {
      return {
        success: false,
        error: 'Network error - please check your connection',
      };
    } else {
      return {
        success: false,
        error: error.message,
      };
    }
  },
};
```

### 2. Image Upload Component Example
```javascript
// ImageUpload.jsx
import React, { useState } from 'react';
import { imageService } from './image-service';

function ImageUpload({ productId, onUploadComplete }) {
  const [files, setFiles] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleFileChange = async (event) => {
    const selectedFiles = imageService.handleFileSelect(event);
    setFiles(selectedFiles);
    
    // Create previews
    const previewPromises = selectedFiles.map(file =>
      imageService.createImagePreview(file)
    );
    
    const previewUrls = await Promise.all(previewPromises);
    setPreviews(previewUrls);
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    
    setUploading(true);
    setProgress(0);
    
    try {
      const result = await imageService.uploadProductImages(productId, files);
      
      if (onUploadComplete) {
        onUploadComplete(result);
      }
      
      // Reset form
      setFiles([]);
      setPreviews([]);
      setProgress(100);
      
      setTimeout(() => setProgress(0), 1000);
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="image-upload">
      <input
        type="file"
        multiple
        accept="image/jpeg,image/png,image/webp"
        onChange={handleFileChange}
        disabled={uploading}
      />
      
      {previews.length > 0 && (
        <div className="preview-grid">
          {previews.map((preview, index) => (
            <img
              key={index}
              src={preview}
              alt={`Preview ${index + 1}`}
              className="preview-image"
            />
          ))}
        </div>
      )}
      
      {files.length > 0 && (
        <button onClick={handleUpload} disabled={uploading}>
          {uploading ? 'Uploading...' : `Upload ${files.length} image(s)`}
        </button>
      )}
      
      {uploading && (
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
}
```

## Shopping Cart

### 1. Cart Service
```javascript
// cart-service.js
import api from './api-client';

export const cartService = {
  // Get current cart
  async getCart() {
    try {
      const response = await api.client.get('/cart');
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  },

  // Add item to cart
  async addToCart(productId, quantity = 1) {
    try {
      const response = await api.client.post('/cart/items', {
        product_id: productId,
        quantity,
      });
      
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  },

  // Update cart item quantity
  async updateCartItem(itemId, quantity) {
    try {
      const response = await api.client.patch(`/cart/items/${itemId}`, {
        quantity,
      });
      
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  },

  // Remove item from cart
  async removeCartItem(itemId) {
    try {
      await api.client.delete(`/cart/items/${itemId}`);
      return { success: true };
    } catch (error) {
      return this.handleError(error);
    }
  },

  // Clear entire cart
  async clearCart() {
    try {
      await api.client.delete('/cart');
      return { success: true };
    } catch (error) {
      return this.handleError(error);
    }
  },

  // Calculate cart summary
  calculateCartSummary(cart) {
    if (!cart || !cart.items) {
      return {
        itemCount: 0,
        totalPrice: 0,
        isEmpty: true,
      };
    }

    const itemCount = cart.items.reduce((sum, item) => sum + item.quantity, 0);
    const totalPrice = cart.items.reduce(
      (sum, item) => sum + item.quantity * item.unit_price,
      0
    );

    return {
      itemCount,
      totalPrice: parseFloat(totalPrice.toFixed(2)),
      isEmpty: cart.items.length === 0,
      items: cart.items,
    };
  },

  // Example: Add multiple items
  async addMultipleToCart(items) {
    const promises = items.map(item =>
      this.addToCart(item.productId, item.quantity)
    );
    
    const results = await Promise.allSettled(promises);
    
    const successful = results
      .filter(r => r.status === 'fulfilled' && r.value.success)
      .map(r => r.value.data);
    
    const failed = results
      .filter(r => r.status === 'rejected' || !r.value.success);
    
    return { successful, failed };
  },

  handleError(error) {
    if (error.response) {
      const { status, data } = error.response;
      
      if (status === 404) {
        return {
          success: false,
          error: 'Product not found or out of stock',
        };
      }
      
      return {
        success: false,
        error: data.detail || 'Cart operation failed',
        status,
        data,
      };
    } else if (error.request) {
      return {
        success: false,
        error: 'Network error - please check your connection',
      };
    } else {
      return {
        success: false,
        error: error.message,
      };
    }
  },
};
```

### 2. Cart Component Example
```javascript
// ShoppingCart.jsx
import React, { useState, useEffect } from 'react';
import { cartService } from './cart-service';

function ShoppingCart() {
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCart();
  }, []);

  const loadCart = async () => {
    try {
      setLoading(true);
      const result = await cartService.getCart();
      
      if (result.success) {
        setCart(result.data);
        setError(null);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Failed to load cart');
    } finally {
      setLoading(false);
    }
  };

  const handleAddItem = async (productId) => {
    try {
      const result = await cartService.addToCart(productId, 1);
      
      if (result.success) {
        await loadCart(); // Refresh cart
      }
    } catch (err) {
      console.error('Failed to add item:', err);
    }
  };

  const handleUpdateQuantity = async (itemId, newQuantity) => {
    if (newQuantity < 1) {
      await handleRemoveItem(itemId);
      return;
    }

    try {
      const result = await cartService.updateCartItem(itemId, newQuantity);
      
      if (result.success) {
        await loadCart();
      }
    } catch (err) {
      console.error('Failed to update quantity:', err);
    }
  };

  const handleRemoveItem = async (itemId) => {
    try {
      const result = await cartService.removeCartItem(itemId);
      
      if (result.success) {
        await loadCart();
      }
    } catch (err) {
      console.error('Failed to remove item:', err);
    }
  };

  const handleClearCart = async () => {
    if (window.confirm('Are you sure you want to clear your cart?')) {
      try {
        const result = await cartService.clearCart();
        
        if (result.success) {
          setCart(null);
        }
      } catch (err) {
        console.error('Failed to clear cart:', err);
      }
    }
  };

  if (loading) return <div>Loading cart...</div>;
  if (error) return <div>Error: {error}</div>;
  
  const summary = cartService.calculateCartSummary(cart);

  return (
    <div className="shopping-cart">
      <h2>Shopping Cart ({summary.itemCount} items)</h2>
      
      {summary.isEmpty ? (
        <p>Your cart is empty</p>
      ) : (
        <>
          <div className="cart-items">
            {cart.items.map(item => (
              <div key={item.id} className="cart-item">
                <div className="item-info">
                  <h4>{item.name}</h4>
                  <p>${item.unit_price} each</p>
                </div>
                
                <div className="quantity-controls">
                  <button 
                    onClick={() => handleUpdateQuantity(item.id, item.quantity - 1)}
                  >
                    -
                  </button>
                  <span>{item.quantity}</span>
                  <button 
                    onClick={() => handleUpdateQuantity(item.id, item.quantity + 1)}
                  >
                    +
                  </button>
                </div>
                
                <div className="item-total">
                  ${(item.quantity * item.unit_price).toFixed(2)}
                </div>
                
                <button 
                  onClick={() => handleRemoveItem(item.id)}
                  className="remove-btn"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
          
          <div className="cart-summary">
            <div className="total">
              <strong>Total: ${summary.totalPrice}</strong>
            </div>
            
            <div className="cart-actions">
              <button onClick={handleClearCart} className="secondary-btn">
                Clear Cart
              </button>
              <button className="primary-btn">
                Proceed to Checkout
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
```

## Orders

### 1. Order Service
```javascript
// order-service.js
import api from './api-client';

export const orderService = {
  // Create order from cart
  async createOrder(orderData = {}) {
    try {
      const response = await api.client.post('/orders', orderData);
      
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  },

  // Example: Checkout with address and payment
  async checkout(billingAddressId, shippingAddressId, paymentToken) {
    const orderData = {
      billingAddressId,
      shippingAddressId,
      paymentMethodToken: paymentToken,
    };

    const result = await this.createOrder(orderData);
    
    if (result.success) {
      // Clear cart after successful checkout
      // await cartService.clearCart();
      
      return {
        success: true,
        order: result.data,
      };
    } else {
      throw new Error(result.error);
    }
  },

  // List user's orders
  async getOrders(page = 1, pageSize = 20) {
    try {
      const response = await api.client.get('/orders', {
        params: { page, page_size: pageSize },
      });
      
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  },

  // Get single order
  async getOrder(orderId) {
    try {
      const response = await api.client.get(`/orders/${orderId}`);
      
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  },

  // Format order for display
  formatOrder(order) {
    return {
      id: order.id,
      status: this.formatStatus(order.status),
      total: `$${order.total.toFixed(2)}`,
      date: new Date(order.created_at).toLocaleDateString(),
      itemCount: order.items.reduce((sum, item) => sum + item.quantity, 0),
      items: order.items,
    };
  },

  formatStatus(status) {
    const statusMap = {
      created: 'Created',
      paid: 'Paid',
      shipped: 'Shipped',
      canceled: 'Canceled',
    };
    
    return statusMap[status] || status;
  },

  handleError(error) {
    if (error.response) {
      const { status, data } = error.response;
      
      if (status === 409) {
        return {
          success: false,
          error: 'Order already exists or cart is empty',
        };
      }
      
      return {
        success: false,
        error: data.detail || 'Order operation failed',
        status,
        data,
      };
    } else if (error.request) {
      return {
        success: false,
        error: 'Network error - please check your connection',
      };
    } else {
      return {
        success: false,
        error: error.message,
      };
    }
  },
};
```

### 2. Complete Shopping Flow Example
```javascript
// shopping-flow.js
import { authService } from './auth-service';
import { productService } from './product-service';
import { cartService } from './cart-service';
import { orderService } from './order-service';

class ShoppingFlow {
  constructor() {
    this.currentUser = null;
    this.cart = null;
  }

  async completeShoppingFlow() {
    try {
      // 1. Login
      console.log('Step 1: Logging in...');
      await this.login();
      
      // 2. Browse products
      console.log('Step 2: Browsing products...');
      const products = await this.browseProducts();
      
      // 3. Add items to cart
      console.log('Step 3: Adding items to cart...');
      await this.addItemsToCart(products.slice(0, 2));
      
      // 4. View cart
      console.log('Step 4: Viewing cart...');
      await this.viewCart();
      
      // 5. Checkout
      console.log('Step 5: Checking out...');
      const order = await this.checkout();
      
      console.log('✅ Shopping completed successfully!');
      console.log(`Order #${order.id} created with total: $${order.total}`);
      
      return order;
      
    } catch (error) {
      console.error('❌ Shopping flow failed:', error.message);
      throw error;
    }
  }

  async login() {
    const credentials = {
      email: 'alice@example.com',
      password: 'S3cureP@ss123',
    };
    
    const result = await authService.login(credentials);
    
    if (!result.success) {
      throw new Error(`Login failed: ${result.error}`);
    }
    
    this.currentUser = { email: credentials.email };
    console.log('Logged in as:', credentials.email);
  }

  async browseProducts() {
    const result = await productService.getProducts({
      tags: ['electronics'],
      pageSize: 5,
    });
    
    if (!result.success) {
      throw new Error(`Failed to load products: ${result.error}`);
    }
    
    console.log(`Found ${result.data.items.length} products`);
    return result.data.items;
  }

  async addItemsToCart(products) {
    const promises = products.map(product =>
      cartService.addToCart(product.id, 1)
    );
    
    const results = await Promise.allSettled(promises);
    
    const successful = results.filter(r => 
      r.status === 'fulfilled' && r.value.success
    );
    
    console.log(`Added ${successful.length} items to cart`);
  }

  async viewCart() {
    const result = await cartService.getCart();
    
    if (!result.success) {
      throw new Error(`Failed to load cart: ${result.error}`);
    }
    
    this.cart = result.data;
    const summary = cartService.calculateCartSummary(this.cart);
    
    console.log(`Cart contains ${summary.itemCount} items`);
    console.log(`Cart total: $${summary.totalPrice}`);
  }

  async checkout() {
    // In a real app, you'd get these from user input
    const billingAddressId = 'addr_1';
    const shippingAddressId = 'addr_1';
    const paymentToken = 'pm_tok_abc123';
    
    const result = await orderService.checkout(
      billingAddressId,
      shippingAddressId,
      paymentToken
    );
    
    if (!result.success) {
      throw new Error(`Checkout failed: ${result.error}`);
    }
    
    return result.order;
  }
}

// Usage
const shoppingFlow = new ShoppingFlow();
shoppingFlow.completeShoppingFlow()
  .then(order => {
    console.log('Order created:', order);
  })
  .catch(error => {
    console.error('Error in shopping flow:', error);
  });
```

## Error Handling

### 1. Comprehensive Error Handler
```javascript
// error-handler.js
export class APIError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.data = data;
  }
}

export const errorHandler = {
  handleAPIError(error) {
    if (error.response) {
      // Server responded with error
      const { status, data } = error.response;
      
      switch (status) {
        case 400:
          return new APIError(
            data.detail || 'Bad request',
            status,
            data
          );
          
        case 401:
          return new APIError(
            'Authentication required. Please login again.',
            status,
            data
          );
          
        case 403:
          return new APIError(
            'You do not have permission to perform this action.',
            status,
            data
          );
          
        case 404:
          return new APIError(
            data.detail || 'Resource not found',
            status,
            data
          );
          
        case 409:
          return new APIError(
            data.detail || 'Conflict - resource already exists',
            status,
            data
          );
          
        case 422:
          const validationErrors = this.formatValidationErrors(data);
          return new APIError(
            'Validation failed',
            status,
            { ...data, validationErrors }
          );
          
        case 500:
          return new APIError(
            'Server error. Please try again later.',
            status,
            data
          );
          
        default:
          return new APIError(
            data.detail || `API error (${status})`,
            status,
            data
          );
      }
    } else if (error.request) {
      // No response received
      return new APIError(
        'Network error. Please check your connection.',
        0,
        null
      );
    } else {
      // Request setup error
      return new APIError(
        error.message || 'Unknown error occurred',
        0,
        null
      );
    }
  },

  formatValidationErrors(data) {
    if (data.errors) {
      return Object.entries(data.errors).map(([field, messages]) => ({
        field,
        messages: Array.isArray(messages) ? messages : [messages],
      }));
    }
    return [];
  },

  // User-friendly error messages
  getUserMessage(error) {
    if (error instanceof APIError) {
      return error.message;
    }
    return 'An unexpected error occurred. Please try again.';
  },

  // Log error for debugging
  logError(error, context = '') {
    console.error(`[${context}] Error:`, {
      message: error.message,
      status: error.status,
      data: error.data,
      stack: error.stack,
    });
  },
};
```

### 2. Using Error Handler
```javascript
// example-with-error-handling.js
import { errorHandler, APIError } from './error-handler';

async function safeAPICall(apiFunction, ...args) {
  try {
    const result = await apiFunction(...args);
    
    if (result.success) {
      return { success: true, data: result.data };
    } else {
      const error = errorHandler.handleAPIError(result);
      errorHandler.logError(error, apiFunction.name);
      return { success: false, error };
    }
  } catch (error) {
    const apiError = errorHandler.handleAPIError(error);
    errorHandler.logError(apiError, apiFunction.name);
    return { success: false, error: apiError };
  }
}

// Usage example
async function getProductsSafely() {
  const result = await safeAPICall(productService.getProducts);
  
  if (result.success) {
    console.log('Products loaded:', result.data);
  } else {
    console.error('Failed to load products:', errorHandler.getUserMessage(result.error));
    
    // Show user-friendly message
    alert(errorHandler.getUserMessage(result.error));
  }
  
  return result;
}
```

## React Hook Examples

### 1. Custom Hooks for API Calls
```javascript
// hooks/useProducts.js
import { useState, useEffect, useCallback } from 'react';
import { productService } from '../services/product-service';

export function useProducts(filters = {}) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 20,
    total: 0,
  });

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await productService.getProducts({
        ...filters,
        page: pagination.page,
        pageSize: pagination.pageSize,
      });
      
      if (result.success) {
        setProducts(result.data.items);
        setPagination(prev => ({
          ...prev,
          total: result.data.total,
        }));
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [filters, pagination.page, pagination.pageSize]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const goToPage = (page) => {
    setPagination(prev => ({ ...prev, page }));
  };

  const changePageSize = (pageSize) => {
    setPagination(prev => ({ ...prev, pageSize, page: 1 }));
  };

  return {
    products,
    loading,
    error,
    pagination,
    refetch: fetchProducts,
    goToPage,
    changePageSize,
  };
}

// Usage in component
function ProductList() {
  const [filters, setFilters] = useState({
    tags: ['electronics'],
    min_price: 0,
    max_price: 1000,
  });
  
  const { 
    products, 
    loading, 
    error, 
    pagination, 
    goToPage, 
    changePageSize 
  } = useProducts(filters);
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <div>
      <div className="products-grid">
        {products.map(product => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
      
      <Pagination
        currentPage={pagination.page}
        totalPages={Math.ceil(pagination.total / pagination.pageSize)}
        onPageChange={goToPage}
        pageSize={pagination.pageSize}
        onPageSizeChange={changePageSize}
      />
    </div>
  );
}
```

### 2. Authentication Hook
```javascript
// hooks/useAuth.js
import { useState, useEffect } from 'react';
import { authService } from '../services/auth-service';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    setLoading(true);
    try {
      // Check if token exists and is valid
      const token = localStorage.getItem('accessToken');
      if (token) {
        // Optional: Validate token with backend
        // For now, just set user from localStorage
        const userData = localStorage.getItem('user');
        if (userData) {
          setUser(JSON.parse(userData));
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await authService.login({ email, password });
      
      if (result.success) {
        const userData = { email };
        setUser(userData);
        localStorage.setItem('user', JSON.stringify(userData));
        return { success: true };
      } else {
        setError(result.error);
        return { success: false, error: result.error };
      }
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    
    try {
      await authService.logout();
      setUser(null);
      localStorage.removeItem('user');
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await authService.register(userData);
      
      if (result.success) {
        // Auto-login after registration
        const loginResult = await login(userData.email, userData.password);
        return loginResult;
      } else {
        setError(result.error);
        return { success: false, error: result.error };
      }
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  };

  return {
    user,
    loading,
    error,
    login,
    logout,
    register,
    isAuthenticated: !!user,
  };
}

// Usage in component
function LoginForm() {
  const { login, loading, error } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await login(email, password);
    
    if (result.success) {
      // Redirect to dashboard
      window.location.href = '/dashboard';
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && <div className="error">{error}</div>}
      
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
        disabled={loading}
      />
      
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
        disabled={loading}
      />
      
      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}
```

### 3. Cart Hook
```javascript
// hooks/useCart.js
import { useState, useEffect, useCallback } from 'react';
import { cartService } from '../services/cart-service';

export function useCart() {
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchCart = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await cartService.getCart();
      
      if (result.success) {
        setCart(result.data);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  const addToCart = async (productId, quantity = 1) => {
    setLoading(true);
    
    try {
      const result = await cartService.addToCart(productId, quantity);
      
      if (result.success) {
        await fetchCart(); // Refresh cart
        return { success: true };
      } else {
        setError(result.error);
        return { success: false, error: result.error };
      }
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  };

  const updateQuantity = async (itemId, quantity) => {
    try {
      const result = await cartService.updateCartItem(itemId, quantity);
      
      if (result.success) {
        await fetchCart();
        return { success: true };
      } else {
        return { success: false, error: result.error };
      }
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  const removeItem = async (itemId) => {
    try {
      const result = await cartService.removeCartItem(itemId);
      
      if (result.success) {
        await fetchCart();
        return { success: true };
      } else {
        return { success: false, error: result.error };
      }
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  const clearCart = async () => {
    try {
      const result = await cartService.clearCart();
      
      if (result.success) {
        setCart(null);
        return { success: true };
      } else {
        return { success: false, error: result.error };
      }
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  const cartSummary = cart ? cartService.calculateCartSummary(cart) : {
    itemCount: 0,
    totalPrice: 0,
    isEmpty: true,
  };

  return {
    cart,
    loading,
    error,
    cartSummary,
    addToCart,
    updateQuantity,
    removeItem,
    clearCart,
    refreshCart: fetchCart,
  };
}

// Usage in component
function AddToCartButton({ productId, stock }) {
  const { addToCart, loading } = useCart();
  const [adding, setAdding] = useState(false);

  const handleClick = async () => {
    if (stock < 1) return;
    
    setAdding(true);
    const result = await addToCart(productId, 1);
    setAdding(false);
    
    if (result.success) {
      alert('Added to cart!');
    } else {
      alert(`Failed to add to cart: ${result.error}`);
    }
  };

  return (
    <button 
      onClick={handleClick} 
      disabled={stock < 1 || loading || adding}
    >
      {stock < 1 ? 'Out of Stock' : 
       loading || adding ? 'Adding...' : 'Add to Cart'}
    </button>
  );
}
```

## Best Practices

### 1. Configuration Management
```javascript
// config.js
const config = {
  development: {
    apiUrl: 'http://localhost:8000/api',
    timeout: 10000,
    retryAttempts: 3,
  },
  staging: {
    apiUrl: 'https://staging-api.example.com/api',
    timeout: 15000,
    retryAttempts: 2,
  },
  production: {
    apiUrl: 'https://api.example.com/api',
    timeout: 20000,
    retryAttempts: 1,
  },
};

export const getConfig = () => {
  const env = process.env.NODE_ENV || 'development';
  return config[env];
};
```

### 2. Request/Response Logging
```javascript
// api-logger.js
export const apiLogger = {
  logRequest(config) {
    console.log('[API Request]', {
      method: config.method,
      url: config.url,
      data: config.data,
      headers: config.headers,
    });
  },

  logResponse(response) {
    console.log('[API Response]', {
      status: response.status,
      data: response.data,
      headers: response.headers,
    });
  },

  logError(error) {
    console.error('[API Error]', {
      message: error.message,
      config: error.config,
      response: error.response,
    });
  },
};

// Add to axios interceptors
client.interceptors.request.use(
  (config) => {
    apiLogger.logRequest(config);
    return config;
  },
  (error) => {
    apiLogger.logError(error);
    return Promise.reject(error);
  }
);

client.interceptors.response.use(
  (response) => {
    apiLogger.logResponse(response);
    return response;
  },
  (error) => {
    apiLogger.logError(error);
    return Promise.reject(error);
  }
);
```

### 3. Performance Optimizations
```javascript
// cache-service.js
class APICache {
  constructor() {
    this.cache = new Map();
    this.defaultTTL = 5 * 60 * 1000; // 5 minutes
  }

  set(key, data, ttl = this.defaultTTL) {
    const item = {
      data,
      expiry: Date.now() + ttl,
    };
    this.cache.set(key, item);
  }

  get(key) {
    const item = this.cache.get(key);
    
    if (!item) return null;
    
    if (Date.now() > item.expiry) {
      this.cache.delete(key);
      return null;
    }
    
    return item.data;
  }

  delete(key) {
    this.cache.delete(key);
  }

  clear() {
    this.cache.clear();
  }
}

export const cacheService = new APICache();

// Usage with product service
export const cachedProductService = {
  async getProducts(filters, useCache = true) {
    const cacheKey = `products:${JSON.stringify(filters)}`;
    
    if (useCache) {
      const cached = cacheService.get(cacheKey);
      if (cached) {
        console.log('Returning cached products');
        return cached;
      }
    }
    
    const result = await productService.getProducts(filters);
    
    if (result.success) {
      cacheService.set(cacheKey, result, 2 * 60 * 1000); // 2 minutes cache
    }
    
    return result;
  },
  
  invalidateCache() {
    cacheService.clear();
  },
};
```

This comprehensive JavaScript examples file provides everything from basic API calls to advanced patterns like custom hooks, error handling, and performance optimizations. Next, I'll create the Python examples file.