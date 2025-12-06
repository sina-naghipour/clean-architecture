# Python Examples

Complete Python examples for the Ecommerce API using modern Python (3.8+).

## Table of Contents
- [Setup & Installation](#setup-installation)
- [Authentication](#authentication)
- [Products](#products)
- [Product Images](#product-images)
- [Shopping Cart](#shopping-cart)
- [Orders](#orders)
- [Error Handling](#error-handling)
- [Async/Await Examples](#asyncawait-examples)
- [Testing](#testing)
- [Django Integration](#django-integration)
- [Flask Integration](#flask-integration)

## Setup & Installation

### Install Required Packages
```bash
pip install requests python-dotenv pillow
# or for async support
pip install aiohttp httpx
```

### Environment Configuration
```python
# config.py
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class APIConfig:
    base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000/api")
    timeout: int = int(os.getenv("API_TIMEOUT", "10"))
    max_retries: int = int(os.getenv("API_MAX_RETRIES", "3"))
    
    @property
    def auth_url(self) -> str:
        return f"{self.base_url}/auth"
    
    @property
    def products_url(self) -> str:
        return f"{self.base_url}/products"
    
    @property
    def cart_url(self) -> str:
        return f"{self.base_url}/cart"
    
    @property
    def orders_url(self) -> str:
        return f"{self.base_url}/orders"
    
    @property
    def files_url(self) -> str:
        return f"{self.base_url}/files"

config = APIConfig()
```

### Base API Client
```python
# api_client.py
import json
import time
from typing import Any, Dict, Optional, Tuple, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dataclasses import dataclass
from config import config


@dataclass
class APIResponse:
    success: bool
    data: Optional[Dict[str, Any]]
    status_code: int
    error: Optional[str] = None


class EcommerceAPIClient:
    """Base client for Ecommerce API operations"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or config.base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        
        # Configure session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "EcommercePythonClient/1.0.0"
        })
    
    def _build_url(self, endpoint: str) -> str:
        """Build complete URL from endpoint"""
        return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    def _handle_response(self, response: requests.Response) -> APIResponse:
        """Handle API response and convert to standardized format"""
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = {"detail": response.text} if response.text else {}
        
        if response.status_code >= 200 and response.status_code < 300:
            return APIResponse(
                success=True,
                data=response_data,
                status_code=response.status_code
            )
        else:
            return APIResponse(
                success=False,
                data=response_data,
                status_code=response.status_code,
                error=response_data.get("detail", "Unknown error")
            )
    
    def _request(self, method: str, endpoint: str, **kwargs) -> APIResponse:
        """Make HTTP request with error handling"""
        url = self._build_url(endpoint)
        
        # Add authentication if token exists
        if self.access_token:
            headers = kwargs.get("headers", {})
            headers["Authorization"] = f"Bearer {self.access_token}"
            kwargs["headers"] = headers
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=config.timeout,
                **kwargs
            )
            return self._handle_response(response)
            
        except requests.exceptions.Timeout:
            return APIResponse(
                success=False,
                data=None,
                status_code=408,
                error="Request timeout"
            )
        except requests.exceptions.ConnectionError:
            return APIResponse(
                success=False,
                data=None,
                status_code=0,
                error="Connection error"
            )
        except Exception as e:
            return APIResponse(
                success=False,
                data=None,
                status_code=0,
                error=str(e)
            )
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> APIResponse:
        return self._request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> APIResponse:
        return self._request("POST", endpoint, json=data)
    
    def put(self, endpoint: str, data: Optional[Dict] = None) -> APIResponse:
        return self._request("PUT", endpoint, json=data)
    
    def patch(self, endpoint: str, data: Optional[Dict] = None) -> APIResponse:
        return self._request("PATCH", endpoint, json=data)
    
    def delete(self, endpoint: str) -> APIResponse:
        return self._request("DELETE", endpoint)
    
    def set_tokens(self, access_token: str, refresh_token: str):
        """Store authentication tokens"""
        self.access_token = access_token
        self.refresh_token = refresh_token
    
    def clear_tokens(self):
        """Clear authentication tokens"""
        self.access_token = None
        self.refresh_token = None


# Singleton instance
api_client = EcommerceAPIClient()
```

## Authentication

### 1. Authentication Service
```python
# auth_service.py
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from api_client import api_client
from config import config


@dataclass
class User:
    id: str
    email: str
    name: str


class AuthService:
    """Handle authentication operations"""
    
    def __init__(self):
        self.current_user: Optional[User] = None
    
    def register(self, email: str, password: str, name: str) -> Tuple[bool, Optional[User], Optional[str]]:
        """
        Register a new user
        
        Returns:
            Tuple of (success, user_data, error_message)
        """
        data = {
            "email": email,
            "password": password,
            "name": name
        }
        
        response = api_client.post("auth/register", data)
        
        if response.success:
            user_data = response.data
            self.current_user = User(
                id=user_data["id"],
                email=user_data["email"],
                name=user_data["name"]
            )
            return True, self.current_user, None
        else:
            return False, None, response.error
    
    def login(self, email: str, password: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Login user and obtain tokens
        
        Returns:
            Tuple of (success, tokens, error_message)
        """
        data = {
            "email": email,
            "password": password
        }
        
        response = api_client.post("auth/login", data)
        
        if response.success:
            tokens = response.data
            api_client.set_tokens(
                access_token=tokens["accessToken"],
                refresh_token=tokens["refreshToken"]
            )
            
            # Optionally fetch user profile
            user_response = self.get_current_user()
            if user_response[0]:
                self.current_user = user_response[1]
            
            return True, tokens, None
        else:
            return False, None, response.error
    
    def refresh_access_token(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Refresh access token using refresh token
        
        Returns:
            Tuple of (success, new_access_token, error_message)
        """
        if not api_client.refresh_token:
            return False, None, "No refresh token available"
        
        data = {
            "refreshToken": api_client.refresh_token
        }
        
        response = api_client.post("auth/refresh-token", data)
        
        if response.success:
            new_token = response.data["accessToken"]
            api_client.access_token = new_token
            return True, new_token, None
        else:
            # Clear tokens on refresh failure
            api_client.clear_tokens()
            self.current_user = None
            return False, None, response.error
    
    def logout(self) -> Tuple[bool, Optional[str]]:
        """
        Logout user and revoke tokens
        
        Returns:
            Tuple of (success, error_message)
        """
        response = api_client.post("auth/logout")
        
        # Clear tokens regardless of API response
        api_client.clear_tokens()
        self.current_user = None
        
        if response.success:
            return True, None
        else:
            return False, response.error
    
    def get_current_user(self) -> Tuple[bool, Optional[User], Optional[str]]:
        """
        Get current user profile
        
        Returns:
            Tuple of (success, user_data, error_message)
        """
        # In a real implementation, you'd call a /profile endpoint
        # For now, we'll return the stored user
        if self.current_user:
            return True, self.current_user, None
        else:
            return False, None, "No user logged in"
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return api_client.access_token is not None and self.current_user is not None


# Singleton instance
auth_service = AuthService()
```

### 2. Authentication Examples
```python
# auth_examples.py
from auth_service import auth_service


def example_registration():
    """Example: Register a new user"""
    print("=== User Registration Example ===")
    
    success, user, error = auth_service.register(
        email="alice@example.com",
        password="S3cureP@ss123",
        name="Alice Johnson"
    )
    
    if success:
        print(f"✅ Registration successful!")
        print(f"   User ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Name: {user.name}")
    else:
        print(f"❌ Registration failed: {error}")
    
    return success, user, error


def example_login():
    """Example: Login with credentials"""
    print("\n=== User Login Example ===")
    
    success, tokens, error = auth_service.login(
        email="alice@example.com",
        password="S3cureP@ss123"
    )
    
    if success:
        print("✅ Login successful!")
        print(f"   Access Token: {tokens['accessToken'][:20]}...")
        print(f"   Refresh Token: {tokens['refreshToken'][:20]}...")
        
        # Check authentication status
        if auth_service.is_authenticated():
            print("   ✅ User is authenticated")
            print(f"   👤 Current user: {auth_service.current_user.name}")
    else:
        print(f"❌ Login failed: {error}")
    
    return success, tokens, error


def example_token_refresh():
    """Example: Refresh access token"""
    print("\n=== Token Refresh Example ===")
    
    success, new_token, error = auth_service.refresh_access_token()
    
    if success:
        print("✅ Token refresh successful!")
        print(f"   New Access Token: {new_token[:20]}...")
    else:
        print(f"❌ Token refresh failed: {error}")
    
    return success, new_token, error


def example_logout():
    """Example: Logout user"""
    print("\n=== User Logout Example ===")
    
    success, error = auth_service.logout()
    
    if success:
        print("✅ Logout successful!")
        print(f"   Authentication status: {auth_service.is_authenticated()}")
    else:
        print(f"⚠️  Logout completed (API error: {error})")
    
    return success, error


def complete_auth_flow():
    """Complete authentication flow example"""
    print("\n=== Complete Authentication Flow ===")
    
    # 1. Register new user
    reg_success, user, reg_error = example_registration()
    
    if not reg_success:
        print("Stopping flow due to registration failure")
        return False
    
    # 2. Login with new credentials
    login_success, tokens, login_error = example_login()
    
    if not login_success:
        print("Stopping flow due to login failure")
        return False
    
    # 3. Refresh token
    refresh_success, new_token, refresh_error = example_token_refresh()
    
    # 4. Logout
    logout_success, logout_error = example_logout()
    
    print("\n=== Authentication Flow Complete ===")
    return all([reg_success, login_success, logout_success])


# Run examples
if __name__ == "__main__":
    complete_auth_flow()
```

## Products

### 1. Product Service
```python
# product_service.py
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from api_client import api_client
from config import config


@dataclass
class Product:
    id: str
    name: str
    price: float
    stock: int
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    images: Optional[List[str]] = None
    primary_image_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @property
    def is_in_stock(self) -> bool:
        return self.stock > 0
    
    @property
    def formatted_price(self) -> str:
        return f"${self.price:.2f}"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Product':
        """Create Product instance from API response dictionary"""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            price=data.get("price", 0.0),
            stock=data.get("stock", 0),
            description=data.get("description"),
            tags=data.get("tags", []),
            images=data.get("images", []),
            primary_image_id=data.get("primaryImageId"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


@dataclass
class ProductList:
    items: List[Product]
    total: int
    page: int
    page_size: int
    
    @property
    def total_pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size
    
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages
    
    @property
    def has_previous(self) -> bool:
        return self.page > 1


class ProductService:
    """Handle product-related operations"""
    
    def list_products(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> Tuple[bool, Optional[ProductList], Optional[str]]:
        """
        List products with filtering and pagination
        
        Returns:
            Tuple of (success, product_list, error_message)
        """
        params = {
            "page": page,
            "pageSize": page_size
        }
        
        if search:
            params["q"] = search
        
        if tags:
            if isinstance(tags, list):
                for tag in tags:
                    params.append("tags", tag)
            else:
                params["tags"] = tags
        
        if min_price is not None:
            params["min_price"] = min_price
        
        if max_price is not None:
            params["max_price"] = max_price
        
        response = api_client.get("products", params=params)
        
        if response.success:
            data = response.data
            products = [Product.from_dict(item) for item in data.get("items", [])]
            
            product_list = ProductList(
                items=products,
                total=data.get("total", 0),
                page=data.get("page", 1),
                page_size=data.get("pageSize", 20)
            )
            
            return True, product_list, None
        else:
            return False, None, response.error
    
    def get_product(self, product_id: str) -> Tuple[bool, Optional[Product], Optional[str]]:
        """
        Get single product by ID
        
        Returns:
            Tuple of (success, product, error_message)
        """
        response = api_client.get(f"products/{product_id}")
        
        if response.success:
            product = Product.from_dict(response.data)
            return True, product, None
        else:
            return False, None, response.error
    
    def create_product(
        self,
        name: str,
        price: float,
        stock: int = 0,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        images: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[Product], Optional[str]]:
        """
        Create new product (admin only)
        
        Returns:
            Tuple of (success, created_product, error_message)
        """
        data = {
            "name": name,
            "price": price,
            "stock": stock
        }
        
        if description:
            data["description"] = description
        
        if tags:
            data["tags"] = tags
        
        if images:
            data["images"] = images
        
        response = api_client.post("products", data)
        
        if response.success:
            product = Product.from_dict(response.data)
            return True, product, None
        else:
            return False, None, response.error
    
    def update_product(
        self,
        product_id: str,
        **updates
    ) -> Tuple[bool, Optional[Product], Optional[str]]:
        """
        Partially update product (admin only)
        
        Args:
            product_id: Product ID to update
            **updates: Fields to update (name, price, stock, description, tags, images)
        
        Returns:
            Tuple of (success, updated_product, error_message)
        """
        response = api_client.patch(f"products/{product_id}", updates)
        
        if response.success:
            product = Product.from_dict(response.data)
            return True, product, None
        else:
            return False, None, response.error
    
    def update_stock(
        self,
        product_id: str,
        stock: int
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Update product stock (admin only)
        
        Returns:
            Tuple of (success, response_data, error_message)
        """
        data = {"stock": stock}
        response = api_client.patch(f"products/{product_id}/inventory", data)
        
        if response.success:
            return True, response.data, None
        else:
            return False, None, response.error
    
    def delete_product(self, product_id: str) -> Tuple[bool, Optional[str]]:
        """
        Delete product (admin only)
        
        Returns:
            Tuple of (success, error_message)
        """
        response = api_client.delete(f"products/{product_id}")
        
        if response.success:
            return True, None
        else:
            return False, response.error
    
    def search_products(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[bool, Optional[ProductList], Optional[str]]:
        """
        Search products by query
        
        Returns:
            Tuple of (success, product_list, error_message)
        """
        return self.list_products(
            page=page,
            page_size=page_size,
            search=query
        )
    
    def get_products_by_tags(
        self,
        tags: List[str],
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[bool, Optional[ProductList], Optional[str]]:
        """
        Get products by tags
        
        Returns:
            Tuple of (success, product_list, error_message)
        """
        return self.list_products(
            page=page,
            page_size=page_size,
            tags=tags
        )


# Singleton instance
product_service = ProductService()
```

### 2. Product Examples
```python
# product_examples.py
from typing import List
from product_service import product_service, Product, ProductList


def example_list_products():
    """Example: List products with pagination"""
    print("=== List Products Example ===")
    
    success, product_list, error = product_service.list_products(
        page=1,
        page_size=5
    )
    
    if success:
        print(f"✅ Found {product_list.total} products")
        print(f"   Page {product_list.page} of {product_list.total_pages}")
        print(f"   Showing {len(product_list.items)} products")
        
        for i, product in enumerate(product_list.items, 1):
            print(f"\n   {i}. {product.name}")
            print(f"      Price: {product.formatted_price}")
            print(f"      Stock: {product.stock}")
            print(f"      In Stock: {'Yes' if product.is_in_stock else 'No'}")
            if product.tags:
                print(f"      Tags: {', '.join(product.tags)}")
    else:
        print(f"❌ Failed to list products: {error}")
    
    return success, product_list, error


def example_search_products():
    """Example: Search for products"""
    print("\n=== Search Products Example ===")
    
    success, product_list, error = product_service.search_products(
        query="wireless",
        page_size=3
    )
    
    if success:
        print(f"✅ Search results for 'wireless':")
        print(f"   Found {product_list.total} products")
        
        for product in product_list.items:
            print(f"\n   • {product.name}")
            print(f"     {product.description[:50]}..." if product.description else "")
    else:
        print(f"❌ Search failed: {error}")
    
    return success, product_list, error


def example_filter_by_tags():
    """Example: Filter products by tags"""
    print("\n=== Filter by Tags Example ===")
    
    success, product_list, error = product_service.get_products_by_tags(
        tags=["electronics", "computer"],
        page_size=4
    )
    
    if success:
        print(f"✅ Electronics & Computer products:")
        print(f"   Found {product_list.total} products")
        
        for product in product_list.items:
            print(f"   • {product.name} - {product.formatted_price}")
    else:
        print(f"❌ Filter failed: {error}")
    
    return success, product_list, error


def example_get_product():
    """Example: Get single product details"""
    print("\n=== Get Product Details Example ===")
    
    # First, list products to get an ID
    success, product_list, error = product_service.list_products(page_size=1)
    
    if not success or not product_list.items:
        print("❌ No products available")
        return False, None, error
    
    product_id = product_list.items[0].id
    
    # Get product details
    success, product, error = product_service.get_product(product_id)
    
    if success:
        print(f"✅ Product details:")
        print(f"   ID: {product.id}")
        print(f"   Name: {product.name}")
        print(f"   Price: {product.formatted_price}")
        print(f"   Stock: {product.stock}")
        print(f"   Description: {product.description}")
        print(f"   Created: {product.created_at}")
        
        if product.tags:
            print(f"   Tags: {', '.join(product.tags)}")
        
        if product.images:
            print(f"   Images: {len(product.images)} available")
    else:
        print(f"❌ Failed to get product: {error}")
    
    return success, product, error


def example_create_product():
    """Example: Create a new product (requires admin auth)"""
    print("\n=== Create Product Example ===")
    
    success, product, error = product_service.create_product(
        name="Python Programming Book",
        price=49.99,
        stock=100,
        description="Learn Python programming with practical examples",
        tags=["books", "programming", "python"],
        images=[]
    )
    
    if success:
        print(f"✅ Product created successfully!")
        print(f"   ID: {product.id}")
        print(f"   Name: {product.name}")
        print(f"   Price: {product.formatted_price}")
        print(f"   Stock: {product.stock}")
    else:
        print(f"❌ Failed to create product: {error}")
        print(f"   Note: This requires admin authentication")
    
    return success, product, error


def example_update_product():
    """Example: Update product information"""
    print("\n=== Update Product Example ===")
    
    # First, get a product to update
    success, product_list, error = product_service.list_products(page_size=1)
    
    if not success:
        print("❌ No products available to update")
        return False, None, error
    
    product_id = product_list.items[0].id
    
    # Update the product
    success, updated_product, error = product_service.update_product(
        product_id=product_id,
        price=39.99,  # New price
        description="Updated description with new features"
    )
    
    if success:
        print(f"✅ Product updated successfully!")
        print(f"   New price: {updated_product.formatted_price}")
        print(f"   Description: {updated_product.description}")
    else:
        print(f"❌ Failed to update product: {error}")
    
    return success, updated_product, error


def example_update_stock():
    """Example: Update product stock"""
    print("\n=== Update Stock Example ===")
    
    # First, get a product to update
    success, product_list, error = product_service.list_products(page_size=1)
    
    if not success:
        print("❌ No products available")
        return False, None, error
    
    product_id = product_list.items[0].id
    new_stock = 150
    
    success, response_data, error = product_service.update_stock(
        product_id=product_id,
        stock=new_stock
    )
    
    if success:
        print(f"✅ Stock updated successfully!")
        print(f"   Product ID: {response_data.get('id')}")
        print(f"   New stock: {response_data.get('stock')}")
    else:
        print(f"❌ Failed to update stock: {error}")
    
    return success, response_data, error


def example_product_management_flow():
    """Complete product management flow"""
    print("\n=== Complete Product Management Flow ===")
    
    # 1. List products
    print("1. Listing products...")
    list_success, product_list, list_error = example_list_products()
    
    if not list_success:
        print("Stopping flow due to list failure")
        return False
    
    # 2. Search products
    print("\n2. Searching products...")
    search_success, _, search_error = example_search_products()
    
    # 3. Get product details
    print("\n3. Getting product details...")
    detail_success, _, detail_error = example_get_product()
    
    # 4. Filter by tags
    print("\n4. Filtering by tags...")
    filter_success, _, filter_error = example_filter_by_tags()
    
    print("\n=== Product Management Flow Complete ===")
    return all([list_success, search_success, detail_success, filter_success])


# Run examples
if __name__ == "__main__":
    # Run individual examples
    # example_list_products()
    # example_search_products()
    # example_filter_by_tags()
    # example_get_product()
    # example_create_product()  # Requires admin auth
    # example_update_product()   # Requires admin auth
    # example_update_stock()     # Requires admin auth
    
    # Or run complete flow
    example_product_management_flow()
```

## Product Images

### 1. Image Service
```python
# image_service.py
import os
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
import requests
from PIL import Image
from api_client import api_client
from config import config


@dataclass
class ProductImage:
    id: str
    product_id: str
    filename: str
    original_name: str
    mime_type: str
    size: int
    width: int
    height: int
    is_primary: bool
    url: str
    uploaded_at: str
    
    @property
    def file_size_mb(self) -> float:
        return self.size / (1024 * 1024)
    
    @property
    def dimensions(self) -> str:
        return f"{self.width}x{self.height}"
    
    @property
    def file_extension(self) -> str:
        return Path(self.original_name).suffix.lower()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProductImage':
        """Create ProductImage instance from API response dictionary"""
        return cls(
            id=data.get("id", ""),
            product_id=data.get("productId", ""),
            filename=data.get("filename", ""),
            original_name=data.get("originalName", ""),
            mime_type=data.get("mimeType", ""),
            size=data.get("size", 0),
            width=data.get("width", 0),
            height=data.get("height", 0),
            is_primary=data.get("isPrimary", False),
            url=data.get("url", ""),
            uploaded_at=data.get("uploadedAt", "")
        )


class ImageService:
    """Handle product image operations"""
    
    VALID_MIME_TYPES = {
        "image/jpeg": [".jpg", ".jpeg"],
        "image/png": [".png"],
        "image/webp": [".webp"]
    }
    
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    def upload_image(
        self,
        file_path: str,
        is_primary: bool = False
    ) -> Tuple[bool, Optional[ProductImage], Optional[str]]:
        """
        Upload product image
        
        Args:
            file_path: Path to image file
            is_primary: Whether to set as primary image
        
        Returns:
            Tuple of (success, image_data, error_message)
        """
        # Validate file
        validation_result = self._validate_image_file(file_path)
        if not validation_result[0]:
            return False, None, validation_result[1]
        
        try:
            # Prepare file for upload
            with open(file_path, 'rb') as file:
                files = {
                    'file': (os.path.basename(file_path), file),
                    'is_primary': (None, str(is_primary).lower())
                }
                
                # Make request with proper headers for multipart/form-data
                url = api_client._build_url("files")
                headers = {}
                
                if api_client.access_token:
                    headers["Authorization"] = f"Bearer {api_client.access_token}"
                
                response = requests.post(
                    url,
                    files=files,
                    headers=headers,
                    timeout=config.timeout
                )
                
                # Handle response
                if response.status_code == 201:
                    image_data = response.json()
                    product_image = ProductImage.from_dict(image_data)
                    return True, product_image, None
                else:
                    error_data = response.json()
                    return False, None, error_data.get("detail", "Upload failed")
                    
        except FileNotFoundError:
            return False, None, f"File not found: {file_path}"
        except Exception as e:
            return False, None, str(e)
    
    def list_images(self) -> Tuple[bool, Optional[List[ProductImage]], Optional[str]]:
        """
        List all product images
        
        Returns:
            Tuple of (success, images_list, error_message)
        """
        response = api_client.get("files")
        
        if response.success:
            images = [ProductImage.from_dict(item) for item in response.data]
            return True, images, None
        else:
            return False, None, response.error
    
    def get_image(self, image_id: str) -> Tuple[bool, Optional[ProductImage], Optional[str]]:
        """
        Get image metadata by ID
        
        Returns:
            Tuple of (success, image_data, error_message)
        """
        response = api_client.get(f"files/{image_id}")
        
        if response.success:
            image = ProductImage.from_dict(response.data)
            return True, image, None
        else:
            return False, None, response.error
    
    def set_primary_image(self, image_id: str) -> Tuple[bool, Optional[ProductImage], Optional[str]]:
        """
        Set image as primary for its product
        
        Returns:
            Tuple of (success, image_data, error_message)
        """
        response = api_client.patch(f"files/{image_id}/primary")
        
        if response.success:
            image = ProductImage.from_dict(response.data)
            return True, image, None
        else:
            return False, None, response.error
    
    def delete_image(self, image_id: str) -> Tuple[bool, Optional[str]]:
        """
        Delete product image
        
        Returns:
            Tuple of (success, error_message)
        """
        response = api_client.delete(f"files/{image_id}")
        
        if response.success:
            return True, None
        else:
            return False, response.error
    
    def _validate_image_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate image file before upload
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if file exists
        if not os.path.exists(file_path):
            return False, f"File does not exist: {file_path}"
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > self.MAX_FILE_SIZE:
            return False, f"File too large: {file_size:,} bytes (max: {self.MAX_FILE_SIZE:,} bytes)"
        
        # Check file extension
        file_ext = Path(file_path).suffix.lower()
        valid_extensions = []
        for extensions in self.VALID_MIME_TYPES.values():
            valid_extensions.extend(extensions)
        
        if file_ext not in valid_extensions:
            return False, f"Invalid file extension: {file_ext}. Valid: {', '.join(valid_extensions)}"
        
        # Try to open image to validate it's actually an image
        try:
            with Image.open(file_path) as img:
                img.verify()  # Verify it's a valid image
                
                # Check dimensions
                img = Image.open(file_path)  # Reopen after verify
                width, height = img.size
                
                if width < 10 or height < 10:
                    return False, f"Image dimensions too small: {width}x{height}"
                
                if width > 10000 or height > 10000:
                    return False, f"Image dimensions too large: {width}x{height}"
                
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"
        
        return True, None
    
    def get_image_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get image information without uploading
        
        Returns:
            Dictionary with image information
        """
        info = {
            "path": file_path,
            "exists": os.path.exists(file_path),
            "valid": False,
            "errors": []
        }
        
        if info["exists"]:
            # File size
            info["size"] = os.path.getsize(file_path)
            info["size_mb"] = info["size"] / (1024 * 1024)
            
            # File extension
            info["extension"] = Path(file_path).suffix.lower()
            
            # Try to get image dimensions
            try:
                with Image.open(file_path) as img:
                    info["width"], info["height"] = img.size
                    info["format"] = img.format
                    info["mode"] = img.mode
            except Exception as e:
                info["errors"].append(str(e))
            
            # Validate
            is_valid, error = self._validate_image_file(file_path)
            info["valid"] = is_valid
            if error:
                info["errors"].append(error)
        
        return info


# Singleton instance
image_service = ImageService()
```

### 2. Image Examples
```python
# image_examples.py
import tempfile
from pathlib import Path
from PIL import Image
from image_service import image_service, ProductImage


def create_sample_image():
    """Create a sample image for testing"""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        # Create a simple test image
        img = Image.new('RGB', (800, 600), color='red')
        img.save(tmp.name, 'PNG')
        return tmp.name


def example_validate_image():
    """Example: Validate image before upload"""
    print("=== Image Validation Example ===")
    
    # Create a sample image
    sample_image = create_sample_image()
    print(f"Created sample image: {sample_image}")
    
    # Get image info
    info = image_service.get_image_info(sample_image)
    
    print(f"Image Information:")
    print(f"  Path: {info['path']}")
    print(f"  Size: {info.get('size', 0):,} bytes ({info.get('size_mb', 0):.2f} MB)")
    print(f"  Dimensions: {info.get('width', 0)}x{info.get('height', 0)}")
    print(f"  Format: {info.get('format', 'Unknown')}")
    print(f"  Valid: {'✅ Yes' if info['valid'] else '❌ No'}")
    
    if info['errors']:
        print(f"  Errors: {', '.join(info['errors'])}")
    
    # Clean up
    Path(sample_image).unlink()
    
    return info['valid']


def example_upload_image():
    """Example: Upload product image (requires auth)"""
    print("\n=== Upload Image Example ===")
    
    # Create a sample image
    sample_image = create_sample_image()
    print(f"Uploading sample image: {sample_image}")
    
    # Upload image
    success, product_image, error = image_service.upload_image(
        file_path=sample_image,
        is_primary=True
    )
    
    if success:
        print("✅ Image uploaded successfully!")
        print(f"   Image ID: {product_image.id}")
        print(f"   Filename: {product_image.filename}")
        print(f"   Original: {product_image.original_name}")
        print(f"   Size: {product_image.file_size_mb:.2f} MB")
        print(f"   Dimensions: {product_image.dimensions}")
        print(f"   URL: {product_image.url}")
        print(f"   Is Primary: {'Yes' if product_image.is_primary else 'No'}")
    else:
        print(f"❌ Upload failed: {error}")
        print(f"   Note: This requires authentication")
    
    # Clean up
    Path(sample_image).unlink()
    
    return success, product_image, error


def example_list_images():
    """Example: List all product images"""
    print("\n=== List Images Example ===")
    
    success, images, error = image_service.list_images()
    
    if success:
        print(f"✅ Found {len(images)} images")
        
        for i, image in enumerate(images, 1):
            print(f"\n   {i}. {image.original_name}")
            print(f"      ID: {image.id}")
            print(f"      Product: {image.product_id}")
            print(f"      Size: {image.file_size_mb:.2f} MB")
            print(f"      Dimensions: {image.dimensions}")
            print(f"      Primary: {'✅' if image.is_primary else '❌'}")
            print(f"      Uploaded: {image.uploaded_at}")
    else:
        print(f"❌ Failed to list images: {error}")
    
    return success, images, error


def example_set_primary_image():
    """Example: Set image as primary (requires auth)"""
    print("\n=== Set Primary Image Example ===")
    
    # First, list images to get an ID
    success, images, error = image_service.list_images()
    
    if not success or not images:
        print("❌ No images available")
        return False, None, error
    
    # Use the first image
    image_id = images[0].id
    
    success, updated_image, error = image_service.set_primary_image(image_id)
    
    if success:
        print(f"✅ Image set as primary!")
        print(f"   Image ID: {updated_image.id}")
        print(f"   Filename: {updated_image.filename}")
        print(f"   Is Primary: {'✅ Yes' if updated_image.is_primary else '❌ No'}")
    else:
        print(f"❌ Failed to set primary image: {error}")
    
    return success, updated_image, error


def example_batch_upload():
    """Example: Upload multiple images"""
    print("\n=== Batch Upload Example ===")
    
    # Create multiple sample images
    sample_images = []
    for i in range(3):
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img = Image.new('RGB', (800, 600), color=f'hsl({i*120}, 100%, 50%)')
            img.save(tmp.name, 'PNG')
            sample_images.append(tmp.name)
    
    print(f"Created {len(sample_images)} sample images")
    
    # Upload each image
    results = []
    for i, image_path in enumerate(sample_images, 1):
        print(f"\n  Uploading image {i}/{len(sample_images)}...")
        success, product_image, error = image_service.upload_image(
            file_path=image_path,
            is_primary=(i == 1)  # First image as primary
        )
        
        if success:
            print(f"    ✅ Success: {product_image.original_name}")
            results.append((True, product_image, None))
        else:
            print(f"    ❌ Failed: {error}")
            results.append((False, None, error))
        
        # Clean up
        Path(image_path).unlink()
    
    # Summary
    successful = sum(1 for r in results if r[0])
    failed = len(results) - successful
    
    print(f"\n📊 Batch Upload Summary:")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    
    return results


def example_image_management_flow():
    """Complete image management flow"""
    print("\n=== Complete Image Management Flow ===")
    
    # 1. Validate image
    print("1. Validating image...")
    validation_success = example_validate_image()
    
    if not validation_success:
        print("Stopping flow due to validation failure")
        return False
    
    # Note: Skip upload examples as they require authentication
    # In a real flow, you would:
    # 2. Upload image
    # 3. List images
    # 4. Set primary image
    
    print("\n=== Image Management Flow Complete (Authentication Required for Full Flow) ===")
    return True


# Run examples
if __name__ == "__main__":
    # Run validation example (no auth required)
    example_validate_image()
    
    # Run other examples (require authentication)
    # example_upload_image()
    # example_list_images()
    # example_set_primary_image()
    # example_batch_upload()
    
    # Or run complete flow
    # example_image_management_flow()
```

## Shopping Cart

### 1. Cart Service
```python
# cart_service.py
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from api_client import api_client
from config import config


@dataclass
class CartItem:
    id: str
    product_id: str
    name: str
    quantity: int
    unit_price: float
    
    @property
    def total_price(self) -> float:
        return self.quantity * self.unit_price
    
    @property
    def formatted_unit_price(self) -> str:
        return f"${self.unit_price:.2f}"
    
    @property
    def formatted_total_price(self) -> str:
        return f"${self.total_price:.2f}"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CartItem':
        """Create CartItem instance from API response dictionary"""
        return cls(
            id=data.get("id", ""),
            product_id=data.get("product_id", ""),
            name=data.get("name", ""),
            quantity=data.get("quantity", 0),
            unit_price=data.get("unit_price", 0.0)
        )


@dataclass
class Cart:
    id: str
    items: List[CartItem]
    total: float
    
    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)
    
    @property
    def formatted_total(self) -> str:
        return f"${self.total:.2f}"
    
    @property
    def is_empty(self) -> bool:
        return len(self.items) == 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Cart':
        """Create Cart instance from API response dictionary"""
        items = [CartItem.from_dict(item) for item in data.get("items", [])]
        return cls(
            id=data.get("id", ""),
            items=items,
            total=data.get("total", 0.0)
        )


class CartService:
    """Handle shopping cart operations"""
    
    def get_cart(self) -> Tuple[bool, Optional[Cart], Optional[str]]:
        """
        Get current user's shopping cart
        
        Returns:
            Tuple of (success, cart, error_message)
        """
        response = api_client.get("cart")
        
        if response.success:
            cart = Cart.from_dict(response.data)
            return True, cart, None
        else:
            return False, None, response.error
    
    def add_to_cart(
        self,
        product_id: str,
        quantity: int = 1
    ) -> Tuple[bool, Optional[CartItem], Optional[str]]:
        """
        Add item to shopping cart
        
        Returns:
            Tuple of (success, cart_item, error_message)
        """
        data = {
            "product_id": product_id,
            "quantity": quantity
        }
        
        response = api_client.post("cart/items", data)
        
        if response.success:
            cart_item = CartItem.from_dict(response.data)
            return True, cart_item, None
        else:
            return False, None, response.error
    
    def update_cart_item(
        self,
        item_id: str,
        quantity: int
    ) -> Tuple[bool, Optional[CartItem], Optional[str]]:
        """
        Update cart item quantity
        
        Returns:
            Tuple of (success, cart_item, error_message)
        """
        data = {"quantity": quantity}
        response = api_client.patch(f"cart/items/{item_id}", data)
        
        if response.success:
            cart_item = CartItem.from_dict(response.data)
            return True, cart_item, None
        else:
            return False, None, response.error
    
    def remove_cart_item(self, item_id: str) -> Tuple[bool, Optional[str]]:
        """
        Remove item from cart
        
        Returns:
            Tuple of (success, error_message)
        """
        response = api_client.delete(f"cart/items/{item_id}")
        
        if response.success:
            return True, None
        else:
            return False, response.error
    
    def clear_cart(self) -> Tuple[bool, Optional[str]]:
        """
        Clear entire shopping cart
        
        Returns:
            Tuple of (success, error_message)
        """
        response = api_client.delete("cart")
        
        if response.success:
            return True, None
        else:
            return False, response.error
    
    def calculate_cart_summary(self, cart: Cart) -> Dict[str, Any]:
        """
        Calculate cart summary statistics
        
        Returns:
            Dictionary with cart summary
        """
        if not cart or not cart.items:
            return {
                "item_count": 0,
                "total_price": 0.0,
                "is_empty": True,
                "items": []
            }
        
        item_count = sum(item.quantity for item in cart.items)
        total_price = cart.total
        
        # Group items by product category (if available)
        items_by_product = {}
        for item in cart.items:
            items_by_product[item.product_id] = items_by_product.get(item.product_id, 0) + item.quantity
        
        return {
            "item_count": item_count,
            "total_price": total_price,
            "formatted_total": f"${total_price:.2f}",
            "is_empty": len(cart.items) == 0,
            "unique_products": len(items_by_product),
            "items": cart.items
        }
    
    def add_multiple_to_cart(
        self,
        items: List[Dict[str, Any]]
    ) -> Tuple[bool, List[Tuple[bool, Optional[CartItem], Optional[str]]], Optional[str]]:
        """
        Add multiple items to cart
        
        Args:
            items: List of dictionaries with product_id and quantity
        
        Returns:
            Tuple of (overall_success, results_list, error_message)
        """
        results = []
        
        for item in items:
            result = self.add_to_cart(
                product_id=item["product_id"],
                quantity=item.get("quantity", 1)
            )
            results.append(result)
        
        # Check if all operations succeeded
        all_success = all(r[0] for r in results)
        return all_success, results, None
    
    def sync_cart_with_local(self, local_items: List[Dict[str, Any]]) -> Tuple[bool, Optional[Cart], Optional[str]]:
        """
        Sync local cart with server cart
        
        Args:
            local_items: List of local cart items
        
        Returns:
            Tuple of (success, cart, error_message)
        """
        # First, get current server cart
        success, server_cart, error = self.get_cart()
        if not success:
            return False, None, error
        
        # Merge local and server carts
        # This is a simplified example - real implementation would be more complex
        merged_items = []
        
        # Add server items
        for server_item in server_cart.items:
            merged_items.append({
                "product_id": server_item.product_id,
                "quantity": server_item.quantity
            })
        
        # Add local items (could handle conflicts here)
        for local_item in local_items:
            merged_items.append(local_item)
        
        # Clear cart and add merged items
        clear_success, clear_error = self.clear_cart()
        if not clear_success:
            return False, None, clear_error
        
        # Add merged items
        add_success, results, add_error = self.add_multiple_to_cart(merged_items)
        if not add_success:
            return False, None, add_error
        
        # Get updated cart
        return self.get_cart()


# Singleton instance
cart_service = CartService()
```

### 2. Cart Examples
```python
# cart_examples.py
from typing import List, Dict
from cart_service import cart_service, Cart, CartItem


def example_get_cart():
    """Example: Get current shopping cart"""
    print("=== Get Shopping Cart Example ===")
    
    success, cart, error = cart_service.get_cart()
    
    if success:
        summary = cart_service.calculate_cart_summary(cart)
        
        print(f"✅ Shopping Cart:")
        print(f"   Cart ID: {cart.id}")
        print(f"   Items: {summary['item_count']}")
        print(f"   Unique Products: {summary['unique_products']}")
        print(f"   Total: {summary['formatted_total']}")
        print(f"   Empty: {'Yes' if summary['is_empty'] else 'No'}")
        
        if not summary['is_empty']:
            print(f"\n   Cart Items:")
            for i, item in enumerate(cart.items, 1):
                print(f"\n     {i}. {item.name}")
                print(f"        Product ID: {item.product_id}")
                print(f"        Quantity: {item.quantity}")
                print(f"        Price each: {item.formatted_unit_price}")
                print(f"        Total: {item.formatted_total_price}")
    else:
        print(f"❌ Failed to get cart: {error}")
        print(f"   Note: This requires authentication")
    
    return success, cart, error


def example_add_to_cart():
    """Example: Add item to cart (requires auth)"""
    print("\n=== Add to Cart Example ===")
    
    # Note: You need a valid product ID for this example
    # In a real application, you'd get this from product listing
    product_id = "prod_42"  # Example product ID
    
    success, cart_item, error = cart_service.add_to_cart(
        product_id=product_id,
        quantity=2
    )
    
    if success:
        print("✅ Item added to cart!")
        print(f"   Item ID: {cart_item.id}")
        print(f"   Product ID: {cart_item.product_id}")
        print(f"   Name: {cart_item.name}")
        print(f"   Quantity: {cart_item.quantity}")
        print(f"   Unit Price: {cart_item.formatted_unit_price}")
        print(f"   Total Price: {cart_item.formatted_total_price}")
    else:
        print(f"❌ Failed to add to cart: {error}")
    
    return success, cart_item, error


def example_update_cart_item():
    """Example: Update cart item quantity"""
    print("\n=== Update Cart Item Example ===")
    
    # First, get cart to find an item ID
    success, cart, error = cart_service.get_cart()
    
    if not success or cart.is_empty:
        print("❌ Cart is empty, cannot update item")
        return False, None, "Cart is empty"
    
    # Use the first item in cart
    item_id = cart.items[0].id
    new_quantity = 3
    
    success, updated_item, error = cart_service.update_cart_item(
        item_id=item_id,
        quantity=new_quantity
    )
    
    if success:
        print("✅ Cart item updated!")
        print(f"   Item ID: {updated_item.id}")
        print(f"   New Quantity: {updated_item.quantity}")
        print(f"   New Total: {updated_item.formatted_total_price}")
    else:
        print(f"❌ Failed to update cart item: {error}")
    
    return success, updated_item, error


def example_remove_cart_item():
    """Example: Remove item from cart"""
    print("\n=== Remove Cart Item Example ===")
    
    # First, get cart to find an item ID
    success, cart, error = cart_service.get_cart()
    
    if not success or cart.is_empty:
        print("❌ Cart is empty, cannot remove item")
        return False, "Cart is empty"
    
    # Use the first item in cart
    item_id = cart.items[0].id
    
    success, error = cart_service.remove_cart_item(item_id)
    
    if success:
        print("✅ Item removed from cart!")
        print(f"   Removed Item ID: {item_id}")
    else:
        print(f"❌ Failed to remove cart item: {error}")
    
    return success, error


def example_clear_cart():
    """Example: Clear entire shopping cart"""
    print("\n=== Clear Cart Example ===")
    
    success, error = cart_service.clear_cart()
    
    if success:
        print("✅ Cart cleared successfully!")
    else:
        print(f"❌ Failed to clear cart: {error}")
    
    return success, error


def example_add_multiple_items():
    """Example: Add multiple items to cart"""
    print("\n=== Add Multiple Items Example ===")
    
    # Example items to add
    items_to_add = [
        {"product_id": "prod_42", "quantity": 2},
        {"product_id": "prod_43", "quantity": 1},
        {"product_id": "prod_44", "quantity": 3}
    ]
    
    print(f"Adding {len(items_to_add)} items to cart...")
    
    success, results, error = cart_service.add_multiple_to_cart(items_to_add)
    
    if success:
        print("✅ All items added successfully!")
        
        for i, (item_success, cart_item, item_error) in enumerate(results, 1):
            if item_success:
                print(f"   {i}. ✅ {cart_item.name} x{cart_item.quantity}")
            else:
                print(f"   {i}. ❌ Failed: {item_error}")
    else:
        print(f"❌ Some items failed to add: {error}")
    
    return success, results, error


def example_cart_summary():
    """Example: Calculate cart summary"""
    print("\n=== Cart Summary Example ===")
    
    success, cart, error = cart_service.get_cart()
    
    if success:
        summary = cart_service.calculate_cart_summary(cart)
        
        print("📊 Cart Summary:")
        print(f"   Total Items: {summary['item_count']}")
        print(f"   Unique Products: {summary['unique_products']}")
        print(f"   Cart Total: {summary['formatted_total']}")
        print(f"   Empty Cart: {'Yes' if summary['is_empty'] else 'No'}")
        
        if not summary['is_empty']:
            print(f"\n   Item Breakdown:")
            for item in summary['items']:
                print(f"     • {item.name}: {item.quantity} x {item.formatted_unit_price} = {item.formatted_total_price}")
    else:
        print(f"❌ Failed to get cart for summary: {error}")
    
    return success, summary if success else None, error


def example_shopping_flow():
    """Complete shopping cart flow example"""
    print("\n=== Complete Shopping Cart Flow ===")
    
    # Note: This is a simulated flow since we don't have actual product IDs
    print("This example demonstrates the complete shopping cart flow:")
    print("1. Get current cart")
    print("2. Add items to cart")
    print("3. Update item quantities")
    print("4. Calculate cart summary")
    print("5. Clear cart")
    print("\nNote: Actual product IDs are required for full execution.")
    
    # 1. Get cart
    print("\n1. Getting current cart...")
    get_success, cart, get_error = example_get_cart()
    
    if not get_success and "authentication" in str(get_error).lower():
        print("   ⚠️  Authentication required for cart operations")
        return False
    
    # 2. Add items (simulated)
    print("\n2. Simulating adding items to cart...")
    print("   In a real application, you would:")
    print("   - Browse products")
    print("   - Select product IDs")
    print("   - Call cart_service.add_to_cart()")
    
    # 3. Update item (if cart has items)
    if get_success and not cart.is_empty:
        print("\n3. Updating cart item...")
        update_success, _, update_error = example_update_cart_item()
    else:
        print("\n3. Skipping update (cart is empty)")
    
    # 4. Cart summary
    print("\n4. Calculating cart summary...")
    summary_success, _, summary_error = example_cart_summary()
    
    # 5. Clear cart (optional)
    print("\n5. Clearing cart...")
    clear_success, clear_error = example_clear_cart()
    
    print("\n=== Shopping Cart Flow Complete ===")
    return True


# Run examples
if __name__ == "__main__":
    # Run individual examples
    # example_get_cart()  # Requires auth
    # example_add_to_cart()  # Requires auth and valid product ID
    # example_update_cart_item()  # Requires auth and items in cart
    # example_remove_cart_item()  # Requires auth and items in cart
    # example_clear_cart()  # Requires auth
    # example_add_multiple_items()  # Requires auth and valid product IDs
    # example_cart_summary()  # Requires auth
    
    # Or run complete flow
    example_shopping_flow()
```

## Orders

### 1. Order Service
```python
# order_service.py
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
from api_client import api_client
from config import config


@dataclass
class OrderItem:
    product_id: str
    name: str
    quantity: int
    unit_price: float
    
    @property
    def total_price(self) -> float:
        return self.quantity * self.unit_price
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderItem':
        """Create OrderItem instance from API response dictionary"""
        return cls(
            product_id=data.get("product_id", ""),
            name=data.get("name", ""),
            quantity=data.get("quantity", 0),
            unit_price=data.get("unit_price", 0.0)
        )


@dataclass
class Order:
    id: str
    status: str
    total: float
    billing_address_id: str
    shipping_address_id: str
    items: List[OrderItem]
    created_at: str
    
    @property
    def formatted_total(self) -> str:
        return f"${self.total:.2f}"
    
    @property
    def formatted_date(self) -> str:
        """Format created_at date for display"""
        try:
            dt = datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
            return dt.strftime("%B %d, %Y at %I:%M %p")
        except (ValueError, AttributeError):
            return self.created_at
    
    @property
    def status_display(self) -> str:
        """Get display-friendly status"""
        status_map = {
            "created": "Created",
            "paid": "Paid",
            "shipped": "Shipped",
            "canceled": "Canceled"
        }
        return status_map.get(self.status, self.status.title())
    
    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        """Create Order instance from API response dictionary"""
        items = [OrderItem.from_dict(item) for item in data.get("items", [])]
        return cls(
            id=data.get("id", ""),
            status=data.get("status", ""),
            total=data.get("total", 0.0),
            billing_address_id=data.get("billing_address_id", ""),
            shipping_address_id=data.get("shipping_address_id", ""),
            items=items,
            created_at=data.get("created_at", "")
        )


@dataclass
class OrderList:
    items: List[Order]
    total: int
    page: int
    page_size: int
    
    @property
    def total_pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size
    
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages
    
    @property
    def has_previous(self) -> bool:
        return self.page > 1


class OrderService:
    """Handle order-related operations"""
    
    def create_order(
        self,
        billing_address_id: str,
        shipping_address_id: str,
        payment_method_token: str
    ) -> Tuple[bool, Optional[Order], Optional[str]]:
        """
        Create order from current cart (checkout)
        
        Returns:
            Tuple of (success, order, error_message)
        """
        data = {
            "billingAddressId": billing_address_id,
            "shippingAddressId": shipping_address_id,
            "paymentMethodToken": payment_method_token
        }
        
        response = api_client.post("orders", data)
        
        if response.success:
            order = Order.from_dict(response.data)
            return True, order, None
        else:
            return False, None, response.error
    
    def list_orders(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[bool, Optional[OrderList], Optional[str]]:
        """
        List user's orders with pagination
        
        Returns:
            Tuple of (success, order_list, error_message)
        """
        params = {
            "page": page,
            "page_size": page_size
        }
        
        response = api_client.get("orders", params=params)
        
        if response.success:
            data = response.data
            orders = [Order.from_dict(item) for item in data.get("items", [])]
            
            order_list = OrderList(
                items=orders,
                total=data.get("total", 0),
                page=data.get("page", 1),
                page_size=data.get("page_size", 20)
            )
            
            return True, order_list, None
        else:
            return False, None, response.error
    
    def get_order(self, order_id: str) -> Tuple[bool, Optional[Order], Optional[str]]:
        """
        Get order details by ID
        
        Returns:
            Tuple of (success, order, error_message)
        """
        response = api_client.get(f"orders/{order_id}")
        
        if response.success:
            order = Order.from_dict(response.data)
            return True, order, None
        else:
            return False, None, response.error
    
    def get_order_summary(self, order: Order) -> Dict[str, Any]:
        """
        Generate order summary for display
        
        Returns:
            Dictionary with order summary
        """
        return {
            "id": order.id,
            "status": order.status_display,
            "total": order.formatted_total,
            "date": order.formatted_date,
            "item_count": order.item_count,
            "items": order.items,
            "billing_address": order.billing_address_id,
            "shipping_address": order.shipping_address_id
        }
    
    def calculate_order_totals(self, order: Order) -> Dict[str, Any]:
        """
        Calculate detailed order totals
        
        Returns:
            Dictionary with detailed totals
        """
        subtotal = sum(item.total_price for item in order.items)
        
        # In a real implementation, you might calculate:
        # - Tax
        # - Shipping
        # - Discounts
        
        return {
            "subtotal": subtotal,
            "tax": 0.0,  # Placeholder
            "shipping": 0.0,  # Placeholder
            "discount": 0.0,  # Placeholder
            "total": order.total,
            "item_count": order.item_count
        }
    
    def export_order_to_csv(self, order: Order, filepath: str) -> bool:
        """
        Export order to CSV file
        
        Returns:
            Boolean indicating success
        """
        try:
            import csv
            
            with open(filepath, 'w', newline='') as csvfile:
                fieldnames = ['Product ID', 'Name', 'Quantity', 'Unit Price', 'Total']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                for item in order.items:
                    writer.writerow({
                        'Product ID': item.product_id,
                        'Name': item.name,
                        'Quantity': item.quantity,
                        'Unit Price': f"${item.unit_price:.2f}",
                        'Total': f"${item.total_price:.2f}"
                    })
                
                # Add summary row
                writer.writerow({})
                writer.writerow({
                    'Product ID': 'TOTAL',
                    'Name': '',
                    'Quantity': order.item_count,
                    'Unit Price': '',
                    'Total': order.formatted_total
                })
            
            return True
            
        except Exception as e:
            print(f"Error exporting order to CSV: {e}")
            return False
    
    def generate_order_receipt(self, order: Order) -> str:
        """
        Generate text receipt for order
        
        Returns:
            Formatted receipt string
        """
        summary = self.get_order_summary(order)
        totals = self.calculate_order_totals(order)
        
        receipt = f"""
        ╔══════════════════════════════════════════╗
        ║               ORDER RECEIPT              ║
        ╚══════════════════════════════════════════╝
        
        Order ID: {order.id}
        Date: {summary['date']}
        Status: {summary['status']}
        
        ───────────────────────────────────────────
        
        ITEMS:
        """
        
        for i, item in enumerate(order.items, 1):
            receipt += f"""
        {i}. {item.name}
           Product ID: {item.product_id}
           Quantity: {item.quantity}
           Unit Price: ${item.unit_price:.2f}
           Total: ${item.total_price:.2f}
            """
        
        receipt += f"""
        ───────────────────────────────────────────
        
        SUMMARY:
        Items: {totals['item_count']}
        Subtotal: ${totals['subtotal']:.2f}
        Tax: ${totals['tax']:.2f}
        Shipping: ${totals['shipping']:.2f}
        Discount: -${totals['discount']:.2f}
        
        ═══════════════════════════════════════════
        
        TOTAL: {order.formatted_total}
        
        ───────────────────────────────────────────
        
        Billing Address: {order.billing_address_id}
        Shipping Address: {order.shipping_address_id}
        
        Thank you for your order!
        """
        
        return receipt


# Singleton instance
order_service = OrderService()
```

### 2. Order Examples
```python
# order_examples.py
import tempfile
from pathlib import Path
from order_service import order_service, Order, OrderList


def example_create_order():
    """Example: Create order (checkout)"""
    print("=== Create Order Example ===")
    
    # Note: This requires valid addresses and payment token
    billing_address_id = "addr_1"
    shipping_address_id = "addr_1"
    payment_token = "pm_tok_abc123"
    
    success, order, error = order_service.create_order(
        billing_address_id=billing_address_id,
        shipping_address_id=shipping_address_id,
        payment_method_token=payment_token
    )
    
    if success:
        print("✅ Order created successfully!")
        summary = order_service.get_order_summary(order)
        
        print(f"   Order ID: {order.id}")
        print(f"   Status: {summary['status']}")
        print(f"   Total: {summary['total']}")
        print(f"   Date: {summary['date']}")
        print(f"   Items: {summary['item_count']}")
        
        print(f"\n   Order Items:")
        for i, item in enumerate(order.items, 1):
            print(f"\n     {i}. {item.name}")
            print(f"        Product ID: {item.product_id}")
            print(f"        Quantity: {item.quantity}")
            print(f"        Unit Price: ${item.unit_price:.2f}")
            print(f"        Total: ${item.total_price:.2f}")
    else:
        print(f"❌ Failed to create order: {error}")
        print(f"   Note: This requires authentication and items in cart")
    
    return success, order, error


def example_list_orders():
    """Example: List user's orders"""
    print("\n=== List Orders Example ===")
    
    success, order_list, error = order_service.list_orders(
        page=1,
        page_size=5
    )
    
    if success:
        print(f"✅ Found {order_list.total} orders")
        print(f"   Page {order_list.page} of {order_list.total_pages}")
        print(f"   Showing {len(order_list.items)} orders")
        
        for i, order in enumerate(order_list.items, 1):
            summary = order_service.get_order_summary(order)
            
            print(f"\n   {i}. Order #{order.id}")
            print(f"      Status: {summary['status']}")
            print(f"      Total: {summary['total']}")
            print(f"      Date: {summary['date']}")
            print(f"      Items: {summary['item_count']}")
            
            if order_list.total_pages > 1 and i == len(order_list.items):
                print(f"\n   ... and {order_list.total - len(order_list.items)} more orders")
    else:
        print(f"❌ Failed to list orders: {error}")
        print(f"   Note: This requires authentication")
    
    return success, order_list, error


def example_get_order():
    """Example: Get order details"""
    print("\n=== Get Order Details Example ===")
    
    # First, list orders to get an order ID
    success, order_list, error = order_service.list_orders(page_size=1)
    
    if not success or not order_list.items:
        print("❌ No orders available")
        return False, None, error
    
    order_id = order_list.items[0].id
    
    # Get order details
    success, order, error = order_service.get_order(order_id)
    
    if success:
        print("✅ Order details:")
        summary = order_service.get_order_summary(order)
        totals = order_service.calculate_order_totals(order)
        
        print(f"   Order ID: {order.id}")
        print(f"   Status: {summary['status']}")
        print(f"   Date: {summary['date']}")
        
        print(f"\n   Order Summary:")
        print(f"     Items: {totals['item_count']}")
        print(f"     Subtotal: ${totals['subtotal']:.2f}")
        print(f"     Tax: ${totals['tax']:.2f}")
        print(f"     Shipping: ${totals['shipping']:.2f}")
        print(f"     Total: {order.formatted_total}")
        
        print(f"\n   Order Items:")
        for i, item in enumerate(order.items, 1):
            print(f"\n     {i}. {item.name}")
            print(f"        Quantity: {item.quantity}")
            print(f"        Unit Price: ${item.unit_price:.2f}")
            print(f"        Total: ${item.total_price:.2f}")
        
        print(f"\n   Addresses:")
        print(f"     Billing: {order.billing_address_id}")
        print(f"     Shipping: {order.shipping_address_id}")
    else:
        print(f"❌ Failed to get order: {error}")
    
    return success, order, error


def example_generate_receipt():
    """Example: Generate order receipt"""
    print("\n=== Generate Order Receipt Example ===")
    
    # First, get an order
    success, order_list, error = order_service.list_orders(page_size=1)
    
    if not success or not order_list.items:
        print("❌ No orders available")
        return False, None, error
    
    order_id = order_list.items[0].id
    success, order, error = order_service.get_order(order_id)
    
    if not success:
        print(f"❌ Failed to get order: {error}")
        return False, None, error
    
    # Generate receipt
    receipt = order_service.generate_order_receipt(order)
    
    print("📄 Order Receipt:")
    print(receipt)
    
    return True, receipt, None


def example_export_order_csv():
    """Example: Export order to CSV"""
    print("\n=== Export Order to CSV Example ===")
    
    # First, get an order
    success, order_list, error = order_service.list_orders(page_size=1)
    
    if not success or not order_list.items:
        print("❌ No orders available")
        return False, None, error
    
    order_id = order_list.items[0].id
    success, order, error = order_service.get_order(order_id)
    
    if not success:
        print(f"❌ Failed to get order: {error}")
        return False, None, error
    
    # Create temp file for CSV
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
        csv_path = tmp.name
    
    # Export to CSV
    export_success = order_service.export_order_to_csv(order, csv_path)
    
    if export_success:
        print(f"✅ Order exported to CSV: {csv_path}")
        
        # Display first few lines
        with open(csv_path, 'r') as f:
            lines = f.readlines()[:10]
            print("\nCSV Preview:")
            for line in lines:
                print(f"  {line.rstrip()}")
        
        # Clean up
        Path(csv_path).unlink()
    else:
        print("❌ Failed to export order to CSV")
    
    return export_success, csv_path if export_success else None, error


def example_order_analytics():
    """Example: Order analytics and statistics"""
    print("\n=== Order Analytics Example ===")
    
    # Get multiple orders for analysis
    success, order_list, error = order_service.list_orders(page_size=50)
    
    if not success or not order_list.items:
        print("❌ No orders available for analysis")
        return False, None, error
    
    orders = order_list.items
    
    # Calculate statistics
    total_orders = len(orders)
    total_revenue = sum(order.total for order in orders)
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Count by status
    status_counts = {}
    for order in orders:
        status_counts[order.status] = status_counts.get(order.status, 0) + 1
    
    # Find most recent order
    most_recent = max(orders, key=lambda o: o.created_at) if orders else None
    
    # Find largest order
    largest_order = max(orders, key=lambda o: o.total) if orders else None
    
    print("📊 Order Analytics:")
    print(f"   Total Orders: {total_orders}")
    print(f"   Total Revenue: ${total_revenue:.2f}")
    print(f"   Average Order Value: ${average_order_value:.2f}")
    
    print(f"\n   Orders by Status:")
    for status, count in status_counts.items():
        percentage = (count / total_orders) * 100
        print(f"     • {status.title()}: {count} orders ({percentage:.1f}%)")
    
    if most_recent:
        print(f"\n   Most Recent Order:")
        print(f"     ID: {most_recent.id}")
        print(f"     Date: {most_recent.formatted_date}")
        print(f"     Total: {most_recent.formatted_total}")
    
    if largest_order:
        print(f"\n   Largest Order:")
        print(f"     ID: {largest_order.id}")
        print(f"     Total: {largest_order.formatted_total}")
        print(f"     Items: {largest_order.item_count}")
    
    return True, {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "average_order_value": average_order_value,
        "status_counts": status_counts,
        "most_recent": most_recent,
        "largest_order": largest_order
    }, None


def example_order_management_flow():
    """Complete order management flow"""
    print("\n=== Complete Order Management Flow ===")
    
    print("This example demonstrates the complete order management flow:")
    print("1. List orders")
    print("2. Get order details")
    print("3. Generate receipt")
    print("4. Export to CSV")
    print("5. Analytics")
    print("\nNote: Orders must exist for this flow to work.")
    
    # 1. List orders
    print("\n1. Listing orders...")
    list_success, order_list, list_error = example_list_orders()
    
    if not list_success:
        print("   ⚠️  Authentication required or no orders exist")
        print("   Skipping remaining steps...")
        return False
    
    if not order_list or order_list.total == 0:
        print("   ⚠️  No orders found")
        print("   Skipping remaining steps...")
        return False
    
    # 2. Get order details
    print("\n2. Getting order details...")
    detail_success, _, detail_error = example_get_order()
    
    # 3. Generate receipt
    print("\n3. Generating receipt...")
    receipt_success, _, receipt_error = example_generate_receipt()
    
    # 4. Export to CSV
    print("\n4. Exporting to CSV...")
    export_success, _, export_error = example_export_order_csv()
    
    # 5. Analytics
    print("\n5. Running analytics...")
    analytics_success, _, analytics_error = example_order_analytics()
    
    print("\n=== Order Management Flow Complete ===")
    return True


# Run examples
if __name__ == "__main__":
    # Run individual examples
    # example_create_order()  # Requires auth and items in cart
    # example_list_orders()  # Requires auth
    # example_get_order()  # Requires auth and existing orders
    # example_generate_receipt()  # Requires auth and existing orders
    # example_export_order_csv()  # Requires auth and existing orders
    # example_order_analytics()  # Requires auth and existing orders
    
    # Or run complete flow
    example_order_management_flow()
```
# Error Handling

## 1. Comprehensive Error Handling System

```python
# error_handling.py
import json
import logging
from typing import Dict, Any, Optional, Union, Type
from dataclasses import dataclass
from functools import wraps
from requests.exceptions import RequestException


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class APIErrorDetail:
    """Detailed error information"""
    type: str
    title: str
    status: int
    detail: str
    instance: str
    validation_errors: Optional[Dict[str, Any]] = None


class EcommerceAPIError(Exception):
    """Base exception for Ecommerce API errors"""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_detail: Optional[APIErrorDetail] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_detail = error_detail
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.error_detail:
            return f"{self.message} (Status: {self.error_detail.status}) - {self.error_detail.detail}"
        return f"{self.message} (Status: {self.status_code})"


class ValidationError(EcommerceAPIError):
    """Raised when request validation fails"""
    pass


class AuthenticationError(EcommerceAPIError):
    """Raised when authentication fails"""
    pass


class AuthorizationError(EcommerceAPIError):
    """Raised when user lacks permissions"""
    pass


class ResourceNotFoundError(EcommerceAPIError):
    """Raised when a resource is not found"""
    pass


class ConflictError(EcommerceAPIError):
    """Raised when there's a resource conflict"""
    pass


class RateLimitError(EcommerceAPIError):
    """Raised when rate limit is exceeded"""
    pass


class ServerError(EcommerceAPIError):
    """Raised for server errors (5xx)"""
    pass


class NetworkError(EcommerceAPIError):
    """Raised for network-related errors"""
    pass


class ErrorHandler:
    """Centralized error handling for API operations"""
    
    ERROR_CLASS_MAP = {
        400: ValidationError,
        401: AuthenticationError,
        403: AuthorizationError,
        404: ResourceNotFoundError,
        409: ConflictError,
        422: ValidationError,
        429: RateLimitError,
    }
    
    @classmethod
    def handle_api_response(
        cls,
        response,
        context: str = "API Request"
    ) -> Union[Dict[str, Any], None]:
        """
        Handle API response and raise appropriate exceptions
        
        Args:
            response: requests.Response object
            context: Context for error messages
        
        Returns:
            Parsed response data if successful
        
        Raises:
            Appropriate EcommerceAPIError subclass
        """
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = {"detail": response.text} if response.text else {}
        
        if response.status_code >= 200 and response.status_code < 300:
            return response_data
        
        # Create error detail
        error_detail = cls._create_error_detail(response, response_data)
        
        # Log error
        cls._log_error(response, response_data, context)
        
        # Raise appropriate exception
        raise cls._create_exception(response.status_code, error_detail, context)
    
    @staticmethod
    def _create_error_detail(
        response,
        response_data: Dict[str, Any]
    ) -> APIErrorDetail:
        """Create structured error detail from response"""
        return APIErrorDetail(
            type=response_data.get("type", "about:blank"),
            title=response_data.get("title", "Unknown Error"),
            status=response.status_code,
            detail=response_data.get("detail", "No details provided"),
            instance=response_data.get("instance", response.url),
            validation_errors=response_data.get("errors")
        )
    
    @staticmethod
    def _log_error(
        response,
        response_data: Dict[str, Any],
        context: str
    ) -> None:
        """Log error details"""
        error_msg = (
            f"{context} failed with status {response.status_code}: "
            f"{response_data.get('detail', 'Unknown error')}"
        )
        
        if response.status_code >= 500:
            logger.error(error_msg)
        else:
            logger.warning(error_msg)
        
        # Log additional details for debugging
        logger.debug(f"Error response: {response_data}")
        logger.debug(f"Request URL: {response.request.url}")
        logger.debug(f"Request method: {response.request.method}")
    
    @classmethod
    def _create_exception(
        cls,
        status_code: int,
        error_detail: APIErrorDetail,
        context: str
    ) -> EcommerceAPIError:
        """Create appropriate exception based on status code"""
        error_class = cls.ERROR_CLASS_MAP.get(status_code, EcommerceAPIError)
        
        # Create user-friendly message
        if status_code == 400:
            message = f"{context}: Bad request - {error_detail.detail}"
        elif status_code == 401:
            message = f"{context}: Authentication required. Please login."
        elif status_code == 403:
            message = f"{context}: You don't have permission to perform this action."
        elif status_code == 404:
            message = f"{context}: Resource not found - {error_detail.detail}"
        elif status_code == 409:
            message = f"{context}: Conflict - {error_detail.detail}"
        elif status_code == 422:
            message = f"{context}: Validation failed - {error_detail.detail}"
        elif status_code == 429:
            message = f"{context}: Rate limit exceeded. Please try again later."
        elif status_code >= 500:
            message = f"{context}: Server error. Please try again later."
        else:
            message = f"{context}: API error (Status: {status_code})"
        
        return error_class(message, status_code, error_detail)
    
    @classmethod
    def handle_request_exception(
        cls,
        error: RequestException,
        context: str = "API Request"
    ) -> EcommerceAPIError:
        """Handle requests library exceptions"""
        if isinstance(error, TimeoutError):
            return NetworkError(
                f"{context}: Request timed out. Please check your connection.",
                status_code=408
            )
        elif isinstance(error, ConnectionError):
            return NetworkError(
                f"{context}: Connection failed. Please check your network.",
                status_code=0
            )
        else:
            return EcommerceAPIError(
                f"{context}: Network error - {str(error)}",
                status_code=0
            )
    
    @classmethod
    def format_validation_errors(
        cls,
        validation_errors: Dict[str, Any]
    ) -> str:
        """Format validation errors for display"""
        if not validation_errors:
            return ""
        
        formatted_errors = []
        for field, errors in validation_errors.items():
            if isinstance(errors, list):
                for error in errors:
                    formatted_errors.append(f"{field}: {error}")
            else:
                formatted_errors.append(f"{field}: {errors}")
        
        return "\n".join(formatted_errors)
    
    @classmethod
    def get_user_friendly_message(
        cls,
        error: EcommerceAPIError
    ) -> str:
        """Get user-friendly error message"""
        if error.error_detail and error.error_detail.validation_errors:
            validation_errors = cls.format_validation_errors(
                error.error_detail.validation_errors
            )
            return f"Please fix the following errors:\n{validation_errors}"
        
        return error.message


# Decorator for automatic error handling
def handle_api_errors(func):
    """Decorator to handle API errors automatically"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except EcommerceAPIError:
            # Re-raise known API errors
            raise
        except RequestException as e:
            # Convert requests exceptions
            raise ErrorHandler.handle_request_exception(
                e,
                context=func.__name__
            )
        except Exception as e:
            # Handle unexpected errors
            logger.exception(f"Unexpected error in {func.__name__}: {e}")
            raise EcommerceAPIError(
                f"An unexpected error occurred: {str(e)}",
                status_code=0
            )
    return wrapper


# Retry decorator with error handling
def retry_on_error(
    max_retries: int = 3,
    retry_on: tuple = (429, 500, 502, 503, 504)
):
    """Decorator to retry on specific errors"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except EcommerceAPIError as e:
                    last_error = e
                    
                    # Check if we should retry
                    should_retry = (
                        e.status_code in retry_on or
                        isinstance(e, NetworkError)
                    )
                    
                    if not should_retry or attempt == max_retries - 1:
                        raise
                    
                    # Wait before retrying (exponential backoff)
                    wait_time = 2 ** attempt
                    logger.info(
                        f"Retry attempt {attempt + 1}/{max_retries} "
                        f"after error: {e.message}. Waiting {wait_time}s..."
                    )
                    import time
                    time.sleep(wait_time)
            
            # This should not be reached, but just in case
            raise last_error if last_error else EcommerceAPIError(
                "Max retries exceeded",
                status_code=0
            )
        return wrapper
    return decorator
```

## 2. Using Error Handling in Services

```python
# error_handling_examples.py
from error_handling import (
    ErrorHandler,
    handle_api_errors,
    retry_on_error,
    EcommerceAPIError,
    ValidationError,
    AuthenticationError,
    ResourceNotFoundError,
    NetworkError
)
from api_client import api_client
from product_service import product_service
from cart_service import cart_service
from order_service import order_service


class SafeAPIClient:
    """API client with built-in error handling"""
    
    @handle_api_errors
    @retry_on_error(max_retries=3)
    def safe_get(self, endpoint: str, **kwargs):
        """Safe GET request with error handling and retry"""
        response = api_client.session.get(
            api_client._build_url(endpoint),
            **kwargs
        )
        return ErrorHandler.handle_api_response(
            response,
            context=f"GET {endpoint}"
        )
    
    @handle_api_errors
    @retry_on_error(max_retries=3)
    def safe_post(self, endpoint: str, data: Dict[str, Any], **kwargs):
        """Safe POST request with error handling and retry"""
        response = api_client.session.post(
            api_client._build_url(endpoint),
            json=data,
            **kwargs
        )
        return ErrorHandler.handle_api_response(
            response,
            context=f"POST {endpoint}"
        )
    
    @handle_api_errors
    @retry_on_error(max_retries=3)
    def safe_patch(self, endpoint: str, data: Dict[str, Any], **kwargs):
        """Safe PATCH request with error handling and retry"""
        response = api_client.session.patch(
            api_client._build_url(endpoint),
            json=data,
            **kwargs
        )
        return ErrorHandler.handle_api_response(
            response,
            context=f"PATCH {endpoint}"
        )
    
    @handle_api_errors
    @retry_on_error(max_retries=3)
    def safe_delete(self, endpoint: str, **kwargs):
        """Safe DELETE request with error handling and retry"""
        response = api_client.session.delete(
            api_client._build_url(endpoint),
            **kwargs
        )
        return ErrorHandler.handle_api_response(
            response,
            context=f"DELETE {endpoint}"
        )


# Enhanced services with error handling
class SafeProductService:
    """Product service with comprehensive error handling"""
    
    def __init__(self):
        self.client = SafeAPIClient()
    
    @handle_api_errors
    def get_product(self, product_id: str) -> Dict[str, Any]:
        """Get product with error handling"""
        return self.client.safe_get(f"products/{product_id}")
    
    @handle_api_errors
    def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create product with error handling"""
        return self.client.safe_post("products", product_data)
    
    @handle_api_errors
    def update_product(
        self,
        product_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update product with error handling"""
        return self.client.safe_patch(f"products/{product_id}", updates)
    
    @handle_api_errors
    def delete_product(self, product_id: str) -> None:
        """Delete product with error handling"""
        self.client.safe_delete(f"products/{product_id}")


# Example usage patterns
def example_error_handling_patterns():
    """Demonstrate different error handling patterns"""
    
    print("=== Error Handling Examples ===")
    
    # Pattern 1: Basic try-except
    print("\n1. Basic Try-Except Pattern:")
    try:
        # This would fail without authentication
        result = product_service.get_product("nonexistent")
        print(f"✅ Success: {result}")
    except EcommerceAPIError as e:
        print(f"❌ API Error: {ErrorHandler.get_user_friendly_message(e)}")
    except Exception as e:
        print(f"⚠️  Unexpected error: {e}")
    
    # Pattern 2: Using decorator
    print("\n2. Using @handle_api_errors Decorator:")
    
    @handle_api_errors
    def get_product_safe(product_id: str):
        return product_service.get_product(product_id)
    
    try:
        result = get_product_safe("invalid_id")
        print(f"✅ Success: {result}")
    except ValidationError as e:
        print(f"❌ Validation Error: {e}")
    except ResourceNotFoundError as e:
        print(f"❌ Not Found: {e}")
    except AuthenticationError as e:
        print(f"❌ Auth Error: {e}")
    except EcommerceAPIError as e:
        print(f"❌ API Error: {e}")
    
    # Pattern 3: Retry on error
    print("\n3. Using @retry_on_error Decorator:")
    
    @retry_on_error(max_retries=2)
    @handle_api_errors
    def unreliable_operation():
        """Simulate an unreliable operation"""
        import random
        if random.random() < 0.7:
            raise EcommerceAPIError("Temporary failure", status_code=503)
        return "Success after retry"
    
    try:
        result = unreliable_operation()
        print(f"✅ {result}")
    except EcommerceAPIError as e:
        print(f"❌ Failed after retries: {e}")
    
    # Pattern 4: Graceful degradation
    print("\n4. Graceful Degradation Pattern:")
    
    def get_product_with_fallback(product_id: str):
        """Get product with cache fallback"""
        cache = {}  # Simulated cache
        
        try:
            # Try to get from API
            product = product_service.get_product(product_id)
            cache[product_id] = product  # Update cache
            return product, "fresh"
        except (ResourceNotFoundError, ValidationError) as e:
            # Don't cache errors
            raise e
        except EcommerceAPIError as e:
            # Use cache if available
            if product_id in cache:
                print(f"⚠️  Using cached data due to: {e.message}")
                return cache[product_id], "cached"
            else:
                raise e
        except Exception as e:
            raise EcommerceAPIError(f"Unexpected error: {e}")
    
    try:
        product, source = get_product_with_fallback("prod_123")
        print(f"✅ Got product from {source} source")
    except EcommerceAPIError as e:
        print(f"❌ Failed to get product: {e}")


def example_error_scenarios():
    """Demonstrate handling different error scenarios"""
    
    print("\n=== Error Scenarios ===")
    
    scenarios = [
        {
            "name": "Validation Error",
            "code": 422,
            "error": ValidationError(
                "Validation failed",
                status_code=422,
                error_detail=APIErrorDetail(
                    type="https://example.com/errors/validation",
                    title="Validation Error",
                    status=422,
                    detail="Field 'email' is required",
                    instance="/auth/register",
                    validation_errors={"email": ["This field is required"]}
                )
            )
        },
        {
            "name": "Authentication Error",
            "code": 401,
            "error": AuthenticationError(
                "Authentication required",
                status_code=401,
                error_detail=APIErrorDetail(
                    type="https://example.com/errors/unauthorized",
                    title="Unauthorized",
                    status=401,
                    detail="Missing or invalid Authorization header",
                    instance="/cart"
                )
            )
        },
        {
            "name": "Resource Not Found",
            "code": 404,
            "error": ResourceNotFoundError(
                "Resource not found",
                status_code=404,
                error_detail=APIErrorDetail(
                    type="https://example.com/errors/not-found",
                    title="Not Found",
                    status=404,
                    detail="Product not found",
                    instance="/products/prod_999"
                )
            )
        },
        {
            "name": "Network Error",
            "code": 0,
            "error": NetworkError(
                "Connection failed",
                status_code=0
            )
        },
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']} (Code: {scenario['code']}):")
        
        error = scenario['error']
        
        # Show error message
        print(f"  Error: {error}")
        
        # Show user-friendly message
        user_msg = ErrorHandler.get_user_friendly_message(error)
        print(f"  User Message: {user_msg}")
        
        # Show what action to take
        if isinstance(error, ValidationError):
            print("  Action: Fix the validation errors and try again")
        elif isinstance(error, AuthenticationError):
            print("  Action: Login and obtain a valid token")
        elif isinstance(error, ResourceNotFoundError):
            print("  Action: Check the resource ID and try again")
        elif isinstance(error, NetworkError):
            print("  Action: Check your internet connection and try again")
        elif error.status_code >= 500:
            print("  Action: Wait a moment and try again, or contact support")


def example_error_recovery():
    """Demonstrate error recovery strategies"""
    
    print("\n=== Error Recovery Strategies ===")
    
    # Strategy 1: Exponential backoff
    print("\n1. Exponential Backoff:")
    
    import time
    
    def exponential_backoff(attempt: int, base_delay: float = 1.0) -> float:
        """Calculate delay for exponential backoff"""
        return min(base_delay * (2 ** attempt), 60.0)  # Max 60 seconds
    
    for attempt in range(5):
        delay = exponential_backoff(attempt)
        print(f"  Attempt {attempt + 1}: Wait {delay:.1f}s")
    
    # Strategy 2: Circuit breaker
    print("\n2. Circuit Breaker Pattern:")
    
    class CircuitBreaker:
        def __init__(self, failure_threshold: int = 3, reset_timeout: int = 60):
            self.failure_threshold = failure_threshold
            self.reset_timeout = reset_timeout
            self.failure_count = 0
            self.last_failure_time = None
            self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
        def call(self, func, *args, **kwargs):
            if self.state == "OPEN":
                if self._can_reset():
                    self.state = "HALF_OPEN"
                else:
                    raise EcommerceAPIError("Circuit breaker is OPEN", status_code=0)
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except EcommerceAPIError as e:
                self._on_failure()
                raise e
        
        def _on_success(self):
            self.failure_count = 0
            self.last_failure_time = None
            self.state = "CLOSED"
        
        def _on_failure(self):
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
        
        def _can_reset(self) -> bool:
            if not self.last_failure_time:
                return True
            return time.time() - self.last_failure_time > self.reset_timeout
    
    # Strategy 3: Bulkhead pattern
    print("\n3. Bulkhead Pattern:")
    
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import queue
    
    class BulkheadExecutor:
        def __init__(self, max_workers: int = 3, max_queue: int = 10):
            self.executor = ThreadPoolExecutor(max_workers=max_workers)
            self.task_queue = queue.Queue(maxsize=max_queue)
        
        def submit(self, func, *args, **kwargs):
            """Submit task with queue limit"""
            try:
                self.task_queue.put_nowait((func, args, kwargs))
            except queue.Full:
                raise EcommerceAPIError("Task queue is full", status_code=0)
            
            return self.executor.submit(self._execute_task)
        
        def _execute_task(self):
            func, args, kwargs = self.task_queue.get()
            try:
                return func(*args, **kwargs)
            finally:
                self.task_queue.task_done()
        
        def shutdown(self):
            self.executor.shutdown(wait=True)
    
    # Demonstrate bulkhead
    print("  Creating bulkhead executor with 2 workers and queue of 5")
    executor = BulkheadExecutor(max_workers=2, max_queue=5)
    
    def mock_api_call(id: int):
        time.sleep(0.1)
        return f"Result {id}"
    
    # Submit tasks
    futures = []
    for i in range(10):
        try:
            future = executor.submit(mock_api_call, i)
            futures.append(future)
            print(f"  Submitted task {i}")
        except EcommerceAPIError as e:
            print(f"  Failed to submit task {i}: {e}")
    
    # Get results
    for future in as_completed(futures):
        try:
            result = future.result()
            print(f"  Got result: {result}")
        except Exception as e:
            print(f"  Task failed: {e}")
    
    executor.shutdown()


def example_logging_and_monitoring():
    """Demonstrate logging and monitoring for errors"""
    
    print("\n=== Logging and Monitoring ===")
    
    # Configure structured logging
    import json
    
    class StructuredLogger:
        def __init__(self, name: str):
            self.logger = logging.getLogger(name)
        
        def log_api_error(
            self,
            error: EcommerceAPIError,
            context: str,
            extra: Dict[str, Any] = None
        ):
            """Log API error with structured data"""
            log_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "level": "ERROR" if error.status_code >= 500 else "WARNING",
                "context": context,
                "error_type": error.__class__.__name__,
                "status_code": error.status_code,
                "message": error.message,
                "user_message": ErrorHandler.get_user_friendly_message(error),
            }
            
            if error.error_detail:
                log_data.update({
                    "error_detail": error.error_detail.detail,
                    "error_instance": error.error_detail.instance,
                })
            
            if extra:
                log_data.update(extra)
            
            # Log as JSON for easy parsing
            self.logger.error(json.dumps(log_data))
    
    # Create logger
    logger = StructuredLogger("ecommerce_api")
    
    # Log some errors
    print("Logging example errors...")
    
    test_error = ValidationError(
        "Validation failed",
        status_code=422,
        error_detail=APIErrorDetail(
            type="https://example.com/errors/validation",
            title="Validation Error",
            status=422,
            detail="Invalid email format",
            instance="/auth/register"
        )
    )
    
    logger.log_api_error(
        test_error,
        context="user_registration",
        extra={"user_id": "user_123", "email": "invalid-email"}
    )
    
    # Metrics collection
    print("\nError Metrics Collection:")
    
    class ErrorMetrics:
        def __init__(self):
            self.error_counts = {}
            self.total_requests = 0
            self.successful_requests = 0
        
        def record_request(self, success: bool, status_code: int = None):
            self.total_requests += 1
            if success:
                self.successful_requests += 1
            elif status_code:
                self.error_counts[status_code] = self.error_counts.get(status_code, 0) + 1
        
        def get_success_rate(self) -> float:
            if self.total_requests == 0:
                return 0.0
            return (self.successful_requests / self.total_requests) * 100
        
        def get_error_distribution(self) -> Dict[int, float]:
            if self.total_requests == 0:
                return {}
            
            distribution = {}
            for status_code, count in self.error_counts.items():
                distribution[status_code] = (count / self.total_requests) * 100
            
            return distribution
    
    # Demonstrate metrics
    metrics = ErrorMetrics()
    
    # Simulate some requests
    request_outcomes = [
        (True, 200), (False, 400), (True, 200), (False, 500),
        (True, 201), (False, 404), (True, 200), (False, 429)
    ]
    
    for success, status_code in request_outcomes:
        metrics.record_request(success, None if success else status_code)
    
    print(f"  Total Requests: {metrics.total_requests}")
    print(f"  Success Rate: {metrics.get_success_rate():.1f}%")
    print(f"  Error Distribution:")
    for status_code, percentage in metrics.get_error_distribution().items():
        print(f"    {status_code}: {percentage:.1f}%")


def example_error_handling_in_workflow():
    """Demonstrate error handling in a complete workflow"""
    
    print("\n=== Error Handling in Complete Workflow ===")
    
    @handle_api_errors
    def complete_purchase_workflow(
        product_id: str,
        quantity: int,
        billing_address: str,
        shipping_address: str,
        payment_token: str
    ) -> Dict[str, Any]:
        """Complete purchase workflow with comprehensive error handling"""
        
        workflow_steps = []
        
        try:
            # Step 1: Add to cart
            print("1. Adding item to cart...")
            cart_item = cart_service.add_to_cart(product_id, quantity)
            workflow_steps.append(("add_to_cart", "success"))
            
            # Step 2: Create order
            print("2. Creating order...")
            order = order_service.create_order(
                billing_address_id=billing_address,
                shipping_address_id=shipping_address,
                payment_method_token=payment_token
            )
            workflow_steps.append(("create_order", "success"))
            
            # Step 3: Clear cart
            print("3. Clearing cart...")
            cart_service.clear_cart()
            workflow_steps.append(("clear_cart", "success"))
            
            # Step 4: Generate receipt
            print("4. Generating receipt...")
            receipt = order_service.generate_order_receipt(order)
            workflow_steps.append(("generate_receipt", "success"))
            
            return {
                "success": True,
                "order": order,
                "receipt": receipt,
                "workflow_steps": workflow_steps
            }
            
        except ValidationError as e:
            workflow_steps.append(("validation_error", str(e)))
            print(f"❌ Validation error in workflow: {e}")
            
            # Try to recover - clear invalid cart
            try:
                cart_service.clear_cart()
            except:
                pass
            
            raise e
            
        except AuthenticationError as e:
            workflow_steps.append(("authentication_error", str(e)))
            print(f"❌ Authentication error in workflow: {e}")
            
            # Can't recover from auth errors
            raise e
            
        except ResourceNotFoundError as e:
            workflow_steps.append(("not_found_error", str(e)))
            print(f"❌ Resource not found in workflow: {e}")
            
            # Check if product exists
            try:
                product_service.get_product(product_id)
                print("✅ Product exists, something else went wrong")
            except ResourceNotFoundError:
                print("❌ Product doesn't exist")
            
            raise e
            
        except EcommerceAPIError as e:
            workflow_steps.append(("api_error", str(e)))
            print(f"❌ API error in workflow: {e}")
            
            # Attempt partial recovery
            if "cart" in str(e).lower():
                print("⚠️  Attempting to clear cart for recovery...")
                try:
                    cart_service.clear_cart()
                    print("✅ Cart cleared successfully")
                except Exception as clear_error:
                    print(f"❌ Failed to clear cart: {clear_error}")
            
            raise e
            
        except Exception as e:
            workflow_steps.append(("unexpected_error", str(e)))
            print(f"❌ Unexpected error in workflow: {e}")
            
            # Log detailed error for debugging
            import traceback
            traceback.print_exc()
            
            raise EcommerceAPIError(
                f"Unexpected error in purchase workflow: {str(e)}",
                status_code=0
            )
    
    # Test the workflow with error scenarios
    print("Testing workflow with different scenarios...")
    
    test_scenarios = [
        {
            "name": "Successful Purchase",
            "product_id": "prod_42",
            "quantity": 2,
            "billing_address": "addr_1",
            "shipping_address": "addr_1",
            "payment_token": "pm_tok_abc123",
            "should_succeed": True
        },
        {
            "name": "Invalid Product",
            "product_id": "nonexistent",
            "quantity": 1,
            "billing_address": "addr_1",
            "shipping_address": "addr_1",
            "payment_token": "pm_tok_abc123",
            "should_succeed": False
        },
        {
            "name": "Invalid Quantity",
            "product_id": "prod_42",
            "quantity": 0,  # Invalid
            "billing_address": "addr_1",
            "shipping_address": "addr_1",
            "payment_token": "pm_tok_abc123",
            "should_succeed": False
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\nTesting: {scenario['name']}")
        print("-" * 40)
        
        try:
            result = complete_purchase_workflow(
                product_id=scenario["product_id"],
                quantity=scenario["quantity"],
                billing_address=scenario["billing_address"],
                shipping_address=scenario["shipping_address"],
                payment_token=scenario["payment_token"]
            )
            
            if scenario["should_succeed"]:
                print("✅ Test passed: Expected success, got success")
            else:
                print("❌ Test failed: Expected failure, got success")
                
        except EcommerceAPIError as e:
            if not scenario["should_succeed"]:
                print(f"✅ Test passed: Expected failure, got: {e.__class__.__name__}")
            else:
                print(f"❌ Test failed: Expected success, got: {e.__class__.__name__}")
                print(f"   Error: {e}")
        
        except Exception as e:
            print(f"⚠️  Unexpected error type: {e.__class__.__name__}: {e}")


if __name__ == "__main__":
    # Run all error handling examples
    example_error_handling_patterns()
    example_error_scenarios()
    example_error_recovery()
    example_logging_and_monitoring()
    example_error_handling_in_workflow()
    
    print("\n=== Error Handling Examples Complete ===")
```

# Async/Await Examples

## 1. Async API Client

```python
# async_client.py
import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from contextlib import asynccontextmanager
from error_handling import ErrorHandler, EcommerceAPIError, handle_api_errors


@dataclass
class AsyncAPIResponse:
    success: bool
    data: Optional[Dict[str, Any]]
    status_code: int
    error: Optional[str] = None


class AsyncEcommerceAPIClient:
    """Async client for Ecommerce API"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000/api",
        timeout: int = 30,
        max_connections: int = 100
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_connections = max_connections
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
    
    @asynccontextmanager
    async def get_session(self):
        """Get or create a session"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(limit=self.max_connections)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "AsyncEcommerceClient/1.0.0"
                }
            )
        
        yield self.session
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _build_url(self, endpoint: str) -> str:
        """Build complete URL from endpoint"""
        return f"{self.base_url}/{endpoint.lstrip('/')}"
    
    async def _handle_response(
        self,
        response: aiohttp.ClientResponse
    ) -> AsyncAPIResponse:
        """Handle async API response"""
        try:
            response_data = await response.json()
        except (json.JSONDecodeError, aiohttp.ContentTypeError):
            text = await response.text()
            response_data = {"detail": text} if text else {}
        
        if response.status >= 200 and response.status < 300:
            return AsyncAPIResponse(
                success=True,
                data=response_data,
                status_code=response.status
            )
        else:
            return AsyncAPIResponse(
                success=False,
                data=response_data,
                status_code=response.status,
                error=response_data.get("detail", "Unknown error")
            )
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> AsyncAPIResponse:
        """Make async HTTP request"""
        url = self._build_url(endpoint)
        
        # Add authentication if token exists
        headers = kwargs.get("headers", {})
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        kwargs["headers"] = headers
        
        async with self.get_session() as session:
            try:
                async with session.request(method, url, **kwargs) as response:
                    return await self._handle_response(response)
                    
            except asyncio.TimeoutError:
                return AsyncAPIResponse(
                    success=False,
                    data=None,
                    status_code=408,
                    error="Request timeout"
                )
            except aiohttp.ClientError as e:
                return AsyncAPIResponse(
                    success=False,
                    data=None,
                    status_code=0,
                    error=f"Client error: {str(e)}"
                )
            except Exception as e:
                return AsyncAPIResponse(
                    success=False,
                    data=None,
                    status_code=0,
                    error=str(e)
                )
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> AsyncAPIResponse:
        return await self._request("GET", endpoint, params=params)
    
    async def post(
        self,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> AsyncAPIResponse:
        return await self._request("POST", endpoint, json=data)
    
    async def put(
        self,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> AsyncAPIResponse:
        return await self._request("PUT", endpoint, json=data)
    
    async def patch(
        self,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> AsyncAPIResponse:
        return await self._request("PATCH", endpoint, json=data)
    
    async def delete(self, endpoint: str) -> AsyncAPIResponse:
        return await self._request("DELETE", endpoint)
    
    async def post_form(
        self,
        endpoint: str,
        data: Dict[str, Any]
    ) -> AsyncAPIResponse:
        """Post form data (for file uploads)"""
        async with self.get_session() as session:
            try:
                form_data = aiohttp.FormData()
                for key, value in data.items():
                    if hasattr(value, 'read'):  # File-like object
                        form_data.add_field(
                            key,
                            value,
                            filename=getattr(value, 'name', 'file')
                        )
                    else:
                        form_data.add_field(key, str(value))
                
                async with session.post(
                    self._build_url(endpoint),
                    data=form_data
                ) as response:
                    return await self._handle_response(response)
                    
            except Exception as e:
                return AsyncAPIResponse(
                    success=False,
                    data=None,
                    status_code=0,
                    error=str(e)
                )
    
    def set_tokens(self, access_token: str, refresh_token: str):
        """Store authentication tokens"""
        self.access_token = access_token
        self.refresh_token = refresh_token
    
    def clear_tokens(self):
        """Clear authentication tokens"""
        self.access_token = None
        self.refresh_token = None


# Singleton async client
async_client = AsyncEcommerceAPIClient()


# Async error handling decorator
def handle_async_errors(func):
    """Decorator to handle async API errors"""
    @handle_api_errors
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except aiohttp.ClientError as e:
            raise EcommerceAPIError(
                f"Network error: {str(e)}",
                status_code=0
            )
    return wrapper
```

## 2. Async Services

```python
# async_services.py
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from async_client import async_client, AsyncAPIResponse, handle_async_errors


@dataclass
class AsyncProduct:
    id: str
    name: str
    price: float
    stock: int
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    images: Optional[List[str]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AsyncProduct':
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            price=data.get("price", 0.0),
            stock=data.get("stock", 0),
            description=data.get("description"),
            tags=data.get("tags", []),
            images=data.get("images", [])
        )


class AsyncProductService:
    """Async product service"""
    
    @handle_async_errors
    async def list_products(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> Tuple[bool, Optional[List[AsyncProduct]], Optional[str]]:
        """List products async"""
        params = {"page": page, "pageSize": page_size}
        
        if search:
            params["q"] = search
        if tags:
            params["tags"] = tags
        if min_price:
            params["min_price"] = min_price
        if max_price:
            params["max_price"] = max_price
        
        response = await async_client.get("products", params=params)
        
        if response.success:
            products = [
                AsyncProduct.from_dict(item)
                for item in response.data.get("items", [])
            ]
            return True, products, None
        else:
            return False, None, response.error
    
    @handle_async_errors
    async def get_product(
        self,
        product_id: str
    ) -> Tuple[bool, Optional[AsyncProduct], Optional[str]]:
        """Get single product async"""
        response = await async_client.get(f"products/{product_id}")
        
        if response.success:
            product = AsyncProduct.from_dict(response.data)
            return True, product, None
        else:
            return False, None, response.error
    
    @handle_async_errors
    async def create_product(
        self,
        product_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[AsyncProduct], Optional[str]]:
        """Create product async"""
        response = await async_client.post("products", product_data)
        
        if response.success:
            product = AsyncProduct.from_dict(response.data)
            return True, product, None
        else:
            return False, None, response.error


class AsyncCartService:
    """Async cart service"""
    
    @handle_async_errors
    async def get_cart(self) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Get cart async"""
        response = await async_client.get("cart")
        return response.success, response.data, response.error
    
    @handle_async_errors
    async def add_to_cart(
        self,
        product_id: str,
        quantity: int = 1
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Add to cart async"""
        data = {"product_id": product_id, "quantity": quantity}
        response = await async_client.post("cart/items", data)
        return response.success, response.data, response.error


class AsyncOrderService:
    """Async order service"""
    
    @handle_async_errors
    async def create_order(
        self,
        order_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Create order async"""
        response = await async_client.post("orders", order_data)
        return response.success, response.data, response.error
    
    @handle_async_errors
    async def list_orders(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[bool, Optional[List[Dict]], Optional[str]]:
        """List orders async"""
        params = {"page": page, "page_size": page_size}
        response = await async_client.get("orders", params=params)
        
        if response.success:
            orders = response.data.get("items", [])
            return True, orders, None
        else:
            return False, None, response.error


class AsyncImageService:
    """Async image service"""
    
    @handle_async_errors
    async def upload_image(
        self,
        file_path: str,
        is_primary: bool = False
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Upload image async"""
        try:
            with open(file_path, 'rb') as f:
                data = {
                    "file": f,
                    "is_primary": str(is_primary).lower()
                }
                response = await async_client.post_form("files", data)
                return response.success, response.data, response.error
        except Exception as e:
            return False, None, str(e)
    
    @handle_async_errors
    async def list_images(self) -> Tuple[bool, Optional[List[Dict]], Optional[str]]:
        """List images async"""
        response = await async_client.get("files")
        
        if response.success:
            images = response.data if isinstance(response.data, list) else []
            return True, images, None
        else:
            return False, None, response.error
```

## 3. Async Examples and Patterns

```python
# async_examples.py
import asyncio
import time
from typing import List, Dict, Any
from async_services import (
    AsyncProductService,
    AsyncCartService,
    AsyncOrderService,
    AsyncImageService
)
from error_handling import EcommerceAPIError


async def example_async_basic():
    """Basic async example"""
    print("=== Basic Async Example ===")
    
    product_service = AsyncProductService()
    
    # Get products async
    success, products, error = await product_service.list_products(
        page=1,
        page_size=5
    )
    
    if success:
        print(f"✅ Found {len(products)} products")
        for product in products[:3]:  # Show first 3
            print(f"  • {product.name}: ${product.price:.2f}")
    else:
        print(f"❌ Error: {error}")


async def example_async_concurrent():
    """Concurrent async requests"""
    print("\n=== Concurrent Async Requests ===")
    
    product_service = AsyncProductService()
    
    # Create multiple concurrent requests
    tasks = [
        product_service.list_products(page=1, page_size=3),
        product_service.list_products(page=2, page_size=3),
        product_service.list_products(page=3, page_size=3)
    ]
    
    print("Fetching 3 pages concurrently...")
    start_time = time.time()
    
    # Run all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    elapsed_time = time.time() - start_time
    print(f"Completed in {elapsed_time:.2f} seconds")
    
    # Process results
    total_products = 0
    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"❌ Page {i} failed: {result}")
        else:
            success, products, error = result
            if success:
                count = len(products) if products else 0
                total_products += count
                print(f"✅ Page {i}: {count} products")
            else:
                print(f"❌ Page {i} error: {error}")
    
    print(f"\nTotal products fetched: {total_products}")


async def example_async_sequential_vs_concurrent():
    """Compare sequential vs concurrent execution"""
    print("\n=== Sequential vs Concurrent Comparison ===")
    
    product_service = AsyncProductService()
    product_ids = ["prod_1", "prod_2", "prod_3", "prod_4", "prod_5"]
    
    # Sequential execution
    print("1. Sequential Execution:")
    start_time = time.time()
    
    for product_id in product_ids:
        success, product, error = await product_service.get_product(product_id)
        if success:
            print(f"  Got product: {product.name}")
        else:
            print(f"  Failed: {error}")
        # Simulate delay between requests
        await asyncio.sleep(0.1)
    
    sequential_time = time.time() - start_time
    print(f"  Sequential time: {sequential_time:.2f}s")
    
    # Concurrent execution
    print("\n2. Concurrent Execution:")
    start_time = time.time()
    
    tasks = [
        product_service.get_product(product_id)
        for product_id in product_ids
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    concurrent_time = time.time() - start_time
    print(f"  Concurrent time: {concurrent_time:.2f}s")
    
    # Show speedup
    speedup = sequential_time / concurrent_time if concurrent_time > 0 else 0
    print(f"\n  Speedup: {speedup:.1f}x faster")


async def example_async_batch_operations():
    """Batch operations with async"""
    print("\n=== Async Batch Operations ===")
    
    product_service = AsyncProductService()
    cart_service = AsyncCartService()
    
    # Get multiple products concurrently
    print("Fetching multiple products...")
    
    product_tasks = [
        product_service.get_product(f"prod_{i}")
        for i in range(1, 6)
    ]
    
    product_results = await asyncio.gather(
        *product_tasks,
        return_exceptions=True
    )
    
    # Filter successful results
    successful_products = []
    for result in product_results:
        if not isinstance(result, Exception):
            success, product, error = result
            if success and product:
                successful_products.append(product)
    
    print(f"✅ Successfully fetched {len(successful_products)} products")
    
    # Add successful products to cart concurrently
    print("\nAdding products to cart...")
    
    cart_tasks = [
        cart_service.add_to_cart(product.id, 1)
        for product in successful_products
    ]
    
    cart_results = await asyncio.gather(
        *cart_tasks,
        return_exceptions=True
    )
    
    # Count successes
    cart_successes = sum(
        1 for result in cart_results
        if not isinstance(result, Exception) and result[0]
    )
    
    print(f"✅ Added {cart_successes} products to cart")


async def example_async_with_timeout():
    """Async operations with timeout"""
    print("\n=== Async with Timeout ===")
    
    product_service = AsyncProductService()
    
    # Create a task with timeout
    try:
        # This will timeout if it takes more than 2 seconds
        async with asyncio.timeout(2.0):
            success, products, error = await product_service.list_products()
            
            if success:
                print(f"✅ Got {len(products)} products within timeout")
            else:
                print(f"❌ API error: {error}")
                
    except asyncio.TimeoutError:
        print("❌ Operation timed out after 2 seconds")
    
    # Multiple operations with individual timeouts
    print("\nMultiple operations with timeouts:")
    
    async def fetch_with_timeout(product_id: str, timeout: float):
        try:
            async with asyncio.timeout(timeout):
                return await product_service.get_product(product_id)
        except asyncio.TimeoutError:
            return False, None, f"Timeout after {timeout}s"
        except Exception as e:
            return False, None, str(e)
    
    tasks = [
        fetch_with_timeout("prod_1", 1.0),
        fetch_with_timeout("prod_2", 2.0),
        fetch_with_timeout("nonexistent", 1.5)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"  {i}. Exception: {result}")
        else:
            success, product, error = result
            if success:
                print(f"  {i}. ✅ Success: {product.name}")
            else:
                print(f"  {i}. ❌ Failed: {error}")


async def example_async_semaphore():
    """Rate limiting with semaphore"""
    print("\n=== Rate Limiting with Semaphore ===")
    
    product_service = AsyncProductService()
    
    # Create semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(3)  # Max 3 concurrent requests
    
    async def limited_fetch(product_id: str):
        async with semaphore:
            print(f"  Starting fetch for {product_id}")
            await asyncio.sleep(0.5)  # Simulate network delay
            return await product_service.get_product(product_id)
    
    # Create many tasks
    print("Fetching 10 products with max 3 concurrent...")
    tasks = [
        limited_fetch(f"prod_{i}")
        for i in range(1, 11)
    ]
    
    start_time = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    elapsed_time = time.time() - start_time
    
    print(f"\nCompleted in {elapsed_time:.2f} seconds")
    
    # Count results
    successes = sum(
        1 for result in results
        if not isinstance(result, Exception) and result[0]
    )
    
    print(f"✅ Successful: {successes}")
    print(f"❌ Failed: {len(results) - successes}")


async def example_async_error_handling():
    """Async error handling patterns"""
    print("\n=== Async Error Handling ===")
    
    product_service = AsyncProductService()
    
    # Pattern 1: Individual error handling
    print("1. Individual Error Handling:")
    
    try:
        success, product, error = await product_service.get_product("invalid_id")
        if not success:
            print(f"  ❌ API Error: {error}")
    except EcommerceAPIError as e:
        print(f"  ❌ Handled API Error: {e}")
    except Exception as e:
        print(f"  ⚠️  Unexpected: {e}")
    
    # Pattern 2: Error handling with gather
    print("\n2. Error Handling with asyncio.gather:")
    
    tasks = [
        product_service.get_product("prod_1"),
        product_service.get_product("invalid_id"),
        product_service.get_product("prod_3")
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"  {i}. Exception: {result}")
        else:
            success, product, error = result
            if success:
                print(f"  {i}. ✅ Success")
            else:
                print(f"  {i}. ❌ API Error: {error}")
    
    # Pattern 3: Using as_completed for streaming results
    print("\n3. Streaming Results with as_completed:")
    
    async def process_results():
        tasks = [
            product_service.get_product(f"prod_{i}")
            for i in range(1, 6)
        ]
        
        # Process results as they complete
        for future in asyncio.as_completed(tasks):
            try:
                success, product, error = await future
                if success:
                    print(f"  ✅ Got product: {product.name}")
                else:
                    print(f"  ❌ Failed: {error}")
            except Exception as e:
                print(f"  ⚠️  Exception: {e}")
    
    await process_results()


async def example_async_complete_workflow():
    """Complete async shopping workflow"""
    print("\n=== Complete Async Shopping Workflow ===")
    
    product_service = AsyncProductService()
    cart_service = AsyncCartService()
    order_service = AsyncOrderService()
    
    print("Starting async shopping workflow...")
    
    try:
        # Step 1: Browse products concurrently
        print("\n1. Browsing products...")
        
        # Get multiple pages concurrently
        browse_tasks = [
            product_service.list_products(page=1, page_size=5),
            product_service.list_products(page=2, page_size=5)
        ]
        
        browse_results = await asyncio.gather(*browse_tasks)
        
        # Combine products
        all_products = []
        for success, products, error in browse_results:
            if success and products:
                all_products.extend(products)
        
        print(f"   Found {len(all_products)} products")
        
        # Step 2: Add selected products to cart
        print("\n2. Adding products to cart...")
        
        # Select first 3 products
        selected_products = all_products[:3]
        
        # Add to cart concurrently
        cart_tasks = [
            cart_service.add_to_cart(product.id, 1)
            for product in selected_products
        ]
        
        cart_results = await asyncio.gather(*cart_tasks)
        
        added_count = sum(1 for success, _, _ in cart_results if success)
        print(f"   Added {added_count} products to cart")
        
        # Step 3: Get cart summary
        print("\n3. Getting cart summary...")
        
        cart_success, cart_data, cart_error = await cart_service.get_cart()
        
        if cart_success:
            item_count = len(cart_data.get("items", []))
            total = cart_data.get("total", 0)
            print(f"   Cart has {item_count} items")
            print(f"   Cart total: ${total:.2f}")
        else:
            print(f"   ❌ Failed to get cart: {cart_error}")
        
        # Step 4: Create order (checkout)
        print("\n4. Creating order...")
        
        order_data = {
            "billingAddressId": "addr_1",
            "shippingAddressId": "addr_1",
            "paymentMethodToken": "pm_tok_abc123"
        }
        
        order_success, order, order_error = await order_service.create_order(order_data)
        
        if order_success:
            print(f"   ✅ Order created!")
            print(f"   Order ID: {order.get('id')}")
            print(f"   Status: {order.get('status')}")
            print(f"   Total: ${order.get('total', 0):.2f}")
        else:
            print(f"   ❌ Failed to create order: {order_error}")
        
        print("\n=== Async Shopping Workflow Complete ===")
        
    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()


async def example_async_performance_benchmark():
    """Performance benchmark for async operations"""
    print("\n=== Async Performance Benchmark ===")
    
    product_service = AsyncProductService()
    
    # Test with different batch sizes
    batch_sizes = [1, 5, 10, 20, 50]
    
    for batch_size in batch_sizes:
        print(f"\nTesting with batch size: {batch_size}")
        
        # Create tasks
        tasks = [
            product_service.list_products(page=1, page_size=1)
            for _ in range(batch_size)
        ]
        
        # Time execution
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed_time = time.time() - start_time
        
        # Count successes
        successes = sum(
            1 for result in results
            if not isinstance(result, Exception) and result[0]
        )
        
        print(f"  Time: {elapsed_time:.2f}s")
        print(f"  Success rate: {successes}/{batch_size}")
        print(f"  Requests per second: {batch_size/elapsed_time:.1f}")


async def example_async_with_retry():
    """Async operations with retry logic"""
    print("\n=== Async with Retry Logic ===")
    
    from error_handling import retry_on_error
    
    product_service = AsyncProductService()
    
    # Custom retry decorator for async functions
    def async_retry_on_error(max_retries: int = 3):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                last_error = None
                
                for attempt in range(max_retries):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_error = e
                        
                        if attempt == max_retries - 1:
                            raise
                        
                        # Wait before retrying
                        wait_time = 2 ** attempt
                        print(f"  Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                        await asyncio.sleep(wait_time)
                
                raise last_error if last_error else Exception("Max retries exceeded")
            return wrapper
        return decorator
    
    @async_retry_on_error(max_retries=3)
    async def unreliable_operation():
        """Simulate unreliable operation"""
        import random
        if random.random() < 0.6:
            raise Exception("Temporary failure")
        return "Success"
    
    # Test retry
    print("Testing retry logic...")
    
    try:
        result = await unreliable_operation()
        print(f"  ✅ {result}")
    except Exception as e:
        print(f"  ❌ Failed after retries: {e}")


async def main():
    """Run all async examples"""
    print("Running Async Examples")
    print("=" * 50)
    
    await example_async_basic()
    await example_async_concurrent()
    await example_async_sequential_vs_concurrent()
    await example_async_batch_operations()
    await example_async_with_timeout()
    await example_async_semaphore()
    await example_async_error_handling()
    await example_async_complete_workflow()
    await example_async_performance_benchmark()
    await example_async_with_retry()
    
    print("\n" + "=" * 50)
    print("All async examples completed!")


if __name__ == "__main__":
    # Run async examples
    asyncio.run(main())
```

## 4. Advanced Async Patterns

```python
# advanced_async.py
import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import random


class AsyncPattern(Enum):
    """Async programming patterns"""
    FAN_OUT = "fan_out"
    FAN_IN = "fan_in"
    PIPELINE = "pipeline"
    WORKER_POOL = "worker_pool"
    PUB_SUB = "pub_sub"


@dataclass
class AsyncTask:
    id: str
    data: Dict[str, Any]
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0


class AsyncPatterns:
    """Implementation of various async patterns"""
    
    @staticmethod
    async def fan_out(
        tasks: List[AsyncTask],
        worker: Callable[[AsyncTask], Any],
        max_concurrent: int = 10
    ) -> List[AsyncTask]:
        """
        Fan-out pattern: Distribute tasks to multiple workers
        
        Args:
            tasks: List of tasks to process
            worker: Async function to process each task
            max_concurrent: Maximum concurrent workers
        
        Returns:
            List of completed tasks
        """
        print(f"Fan-out pattern with {len(tasks)} tasks, max {max_concurrent} concurrent")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_task(task: AsyncTask) -> AsyncTask:
            async with semaphore:
                task.start_time = time.time()
                try:
                    task.result = await worker(task)
                    task.status = "completed"
                except Exception as e:
                    task.status = "failed"
                    task.error = str(e)
                finally:
                    task.end_time = time.time()
                
                return task
        
        # Process all tasks concurrently with limits
        completed_tasks = await asyncio.gather(
            *[process_task(task) for task in tasks]
        )
        
        return completed_tasks
    
    @staticmethod
    async def pipeline(
        stages: List[Callable[[Any], Any]],
        initial_data: Any,
        buffer_size: int = 10
    ) -> Any:
        """
        Pipeline pattern: Process data through multiple stages
        
        Args:
            stages: List of async processing functions
            initial_data: Initial data to process
            buffer_size: Size of buffers between stages
        
        Returns:
            Final processed result
        """
        print(f"Pipeline pattern with {len(stages)} stages")
        
        # Create queues between stages
        queues = [asyncio.Queue(maxsize=buffer_size) for _ in range(len(stages) + 1)]
        
        # Put initial data in first queue
        await queues[0].put(initial_data)
        
        async def process_stage(stage_index: int):
            """Process a single pipeline stage"""
            stage_func = stages[stage_index]
            
            while True:
                try:
                    # Get data from previous stage
                    data = await queues[stage_index].get()
                    
                    # Process data
                    result = await stage_func(data)
                    
                    # Pass to next stage
                    await queues[stage_index + 1].put(result)
                    
                    # Mark task as done
                    queues[stage_index].task_done()
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"Stage {stage_index} error: {e}")
                    break
        
        # Start all stages
        stage_tasks = [
            asyncio.create_task(process_stage(i))
            for i in range(len(stages))
        ]
        
        # Wait for processing to complete
        try:
            # Get final result from last queue
            final_result = await queues[-1].get()
            
            # Wait for all queues to empty
            for queue in queues:
                await queue.join()
            
            return final_result
            
        finally:
            # Cancel all stage tasks
            for task in stage_tasks:
                task.cancel()
            
            # Wait for cancellation
            await asyncio.gather(*stage_tasks, return_exceptions=True)
    
    @staticmethod
    async def worker_pool(
        tasks: List[AsyncTask],
        worker_count: int = 4
    ) -> List[AsyncTask]:
        """
        Worker pool pattern: Fixed number of workers processing tasks
        
        Args:
            tasks: List of tasks to process
            worker_count: Number of worker processes
        
        Returns:
            List of completed tasks
        """
        print(f"Worker pool pattern with {worker_count} workers")
        
        task_queue = asyncio.Queue()
        result_queue = asyncio.Queue()
        
        # Add all tasks to queue
        for task in tasks:
            await task_queue.put(task)
        
        async def worker(worker_id: int):
            """Worker process"""
            print(f"  Worker {worker_id} started")
            
            while True:
                try:
                    # Get task from queue
                    task = await task_queue.get()
                    
                    # Process task
                    task.start_time = time.time()
                    await asyncio.sleep(random.uniform(0.1, 0.5))  # Simulate work
                    task.result = f"Processed by worker {worker_id}"
                    task.status = "completed"
                    task.end_time = time.time()
                    
                    # Put result
                    await result_queue.put(task)
                    
                    # Mark task as done
                    task_queue.task_done()
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"Worker {worker_id} error: {e}")
                    break
        
        # Start workers
        worker_tasks = [
            asyncio.create_task(worker(i))
            for i in range(worker_count)
        ]
        
        # Wait for all tasks to be processed
        await task_queue.join()
        
        # Stop workers
        for task in worker_tasks:
            task.cancel()
        
        await asyncio.gather(*worker_tasks, return_exceptions=True)
        
        # Collect results
        completed_tasks = []
        while not result_queue.empty():
            completed_tasks.append(await result_queue.get())
        
        return completed_tasks
    
    @staticmethod
    async def pub_sub(
        publishers: List[Callable],
        subscribers: List[Callable],
        message_count: int = 10
    ):
        """
        Publish-Subscribe pattern
        
        Args:
            publishers: List of publisher functions
            subscribers: List of subscriber functions
            message_count: Number of messages to publish
        """
        print(f"Pub-Sub pattern with {len(publishers)} publishers and {len(subscribers)} subscribers")
        
        message_queue = asyncio.Queue()
        
        async def publisher(pub_id: int):
            """Publisher function"""
            for i in range(message_count):
                message = f"Message {i} from publisher {pub_id}"
                await message_queue.put(message)
                await asyncio.sleep(0.1)  # Publish rate limit
        
        async def subscriber(sub_id: int):
            """Subscriber function"""
            messages_received = 0
            
            while messages_received < message_count * len(publishers):
                try:
                    message = await message_queue.get()
                    print(f"  Subscriber {sub_id} received: {message}")
                    messages_received += 1
                    message_queue.task_done()
                except Exception as e:
                    print(f"Subscriber {sub_id} error: {e}")
                    break
        
        # Start publishers and subscribers
        pub_tasks = [
            asyncio.create_task(publisher(i))
            for i in range(len(publishers))
        ]
        
        sub_tasks = [
            asyncio.create_task(subscriber(i))
            for i in range(len(subscribers))
        ]
        
        # Wait for all messages to be published
        await asyncio.gather(*pub_tasks)
        
        # Wait for all messages to be processed
        await message_queue.join()
        
        # Cancel subscribers
        for task in sub_tasks:
            task.cancel()
        
        await asyncio.gather(*sub_tasks, return_exceptions=True)


# Example usage of async patterns
async def example_async_patterns():
    """Demonstrate different async patterns"""
    print("=== Advanced Async Patterns ===")
    
    patterns = AsyncPatterns()
    
    # Example tasks
    tasks = [
        AsyncTask(id=f"task_{i}", data={"value": i})
        for i in range(20)
    ]
    
    # 1. Fan-out pattern
    print("\n1. Fan-out Pattern:")
    
    async def sample_worker(task: AsyncTask) -> str:
        """Sample worker function"""
        await asyncio.sleep(random.uniform(0.1, 0.3))
        return f"Processed {task.id}"
    
    completed_tasks = await patterns.fan_out(
        tasks[:5],
        sample_worker,
        max_concurrent=2
    )
    
    for task in completed_tasks:
        print(f"  {task.id}: {task.status} in {task.duration:.2f}s")
    
    # 2. Pipeline pattern
    print("\n2. Pipeline Pattern:")
    
    async def stage1(data: int) -> int:
        await asyncio.sleep(0.1)
        return data * 2
    
    async def stage2(data: int) -> str:
        await asyncio.sleep(0.1)
        return f"Result: {data}"
    
    async def stage3(data: str) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {"final": data.upper()}
    
    pipeline_result = await patterns.pipeline(
        [stage1, stage2, stage3],
        initial_data=42
    )
    
    print(f"  Pipeline result: {pipeline_result}")
    
    # 3. Worker pool pattern
    print("\n3. Worker Pool Pattern:")
    
    pool_tasks = [
        AsyncTask(id=f"pool_task_{i}", data={"index": i})
        for i in range(8)
    ]
    
    pool_results = await patterns.worker_pool(pool_tasks, worker_count=3)
    
    print(f"  Processed {len(pool_results)} tasks")
    
    # 4. Pub-Sub pattern
    print("\n4. Pub-Sub Pattern:")
    
    await patterns.pub_sub(
        publishers=[lambda: None, lambda: None],  # Dummy functions
        subscribers=[lambda: None, lambda: None, lambda: None],
        message_count=3
    )
    
    print("\nAll async patterns demonstrated!")


async def example_async_with_database():
    """Async operations with database simulation"""
    print("\n=== Async with Database Simulation ===")
    
    # Simulated database
    class AsyncDatabase:
        def __init__(self):
            self.data = {}
            self.lock = asyncio.Lock()
        
        async def get(self, key: str) -> Optional[Any]:
            """Async get with simulated delay"""
            await asyncio.sleep(0.05)  # Simulate network latency
            return self.data.get(key)
        
        async def set(self, key: str, value: Any):
            """Async set with simulated delay"""
            await asyncio.sleep(0.05)  # Simulate network latency
            async with self.lock:
                self.data[key] = value
        
        async def delete(self, key: str):
            """Async delete with simulated delay"""
            await asyncio.sleep(0.05)  # Simulate network latency
            async with self.lock:
                if key in self.data:
                    del self.data[key]
    
    # Create database instance
    db = AsyncDatabase()
    
    # Example: Concurrent database operations
    print("Performing concurrent database operations...")
    
    async def db_operation(user_id: str):
        """Simulated database operation"""
        # Read
        data = await db.get(f"user_{user_id}")
        
        if data is None:
            # Write if not exists
            await db.set(f"user_{user_id}", {"id": user_id, "visits": 1})
        else:
            # Update if exists
            data["visits"] += 1
            await db.set(f"user_{user_id}", data)
        
        return await db.get(f"user_{user_id}")
    
    # Run concurrent operations
    user_ids = [str(i) for i in range(10)]
    tasks = [db_operation(user_id) for user_id in user_ids]
    
    results = await asyncio.gather(*tasks)
    
    print(f"Completed {len(results)} database operations")
    
    # Show some results
    for i, result in enumerate(results[:3]):
        print(f"  User {i}: {result}")


async def example_async_cache():
    """Async caching pattern"""
    print("\n=== Async Caching Pattern ===")
    
    class AsyncCache:
        def __init__(self, ttl: float = 60.0):
            self.cache = {}
            self.ttl = ttl
        
        async def get(self, key: str) -> Optional[Any]:
            """Get from cache if not expired"""
            if key in self.cache:
                entry = self.cache[key]
                if time.time() - entry["timestamp"] < self.ttl:
                    return entry["data"]
                else:
                    # Expired, remove from cache
                    del self.cache[key]
            return None
        
        async def set(self, key: str, data: Any):
            """Set cache entry"""
            self.cache[key] = {
                "data": data,
                "timestamp": time.time()
            }
        
        async def get_or_set(
            self,
            key: str,
            fetch_func: Callable[[], Any]
        ) -> Any:
            """
            Get from cache or fetch and set
            
            Args:
                key: Cache key
                fetch_func: Async function to fetch data if not in cache
            """
            # Try cache first
            cached = await self.get(key)
            if cached is not None:
                print(f"  Cache hit for {key}")
                return cached
            
            # Fetch and cache
            print(f"  Cache miss for {key}, fetching...")
            data = await fetch_func()
            await self.set(key, data)
            return data
    
    # Create cache
    cache = AsyncCache(ttl=5.0)  # 5 second TTL
    
    # Simulate expensive operation
    call_count = 0
    
    async def expensive_operation(key: str) -> str:
        """Simulate expensive API call"""
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.5)  # Simulate slow operation
        return f"Result for {key}"
    
    # Test cache
    print("Testing async cache...")
    
    # First call - cache miss
    result1 = await cache.get_or_set("test_key", lambda: expensive_operation("test_key"))
    print(f"  Result 1: {result1}, API calls: {call_count}")
    
    # Second call - cache hit (within TTL)
    result2 = await cache.get_or_set("test_key", lambda: expensive_operation("test_key"))
    print(f"  Result 2: {result2}, API calls: {call_count}")
    
    # Wait for cache to expire
    print("  Waiting for cache to expire...")
    await asyncio.sleep(6)
    
    # Third call - cache miss (expired)
    result3 = await cache.get_or_set("test_key", lambda: expensive_operation("test_key"))
    print(f"  Result 3: {result3}, API calls: {call_count}")
    
    print(f"\nTotal API calls made: {call_count}")
    print(f"Cache hits saved: {2 - call_count} calls")


async def run_all_async_examples():
    """Run all advanced async examples"""
    print("Running Advanced Async Examples")
    print("=" * 50)
    
    await example_async_patterns()
    await example_async_with_database()
    await example_async_cache()
    
    print("\n" + "=" * 50)
    print("All advanced async examples completed!")


if __name__ == "__main__":
    asyncio.run(run_all_async_examples())
```