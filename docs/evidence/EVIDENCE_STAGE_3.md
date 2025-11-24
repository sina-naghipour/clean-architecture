# Evidence: Authentication Service

## 1. Domain Models & Data Contracts
**File**: `auth/app/database/models.py:57-65`

```python
class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, description="Name cannot be empty")
    phone: Optional[str] = Field(None, min_length=1, description="Phone cannot be empty")

    @field_validator('*', mode='before')
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v
```

**File**: `products/app/database/models.py:32-46`

```python
class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    stock: int
    description: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class ProductList(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
```

## 2. Business Logic
**File**: `cart/app/services/cart_services.py:126-170`

```python
    async def update_cart_item(
        self,
        request: Request,
        user_id: str,
        item_id: str,
        update_data: models.CartItemUpdate
    ):
        self.logger.info(f"Update item attempt for user: {user_id}, item: {item_id}")
        
        cart_data = self.carts.get(user_id)
        
        if not cart_data:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Cart not found",
                instance=str(request.url)
            )
        
        # Find the item
        target_item = None
        for item in cart_data['items']:
            if item['id'] == item_id:
                target_item = item
                break
        
        if not target_item:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Cart item not found",
                instance=str(request.url)
            )
        
        # Update quantity
        target_item['quantity'] = update_data.quantity
        target_item['updated_at'] = datetime.now()
        cart_data['updated_at'] = datetime.now()
        
        response_item = models.CartItemResponse(**target_item)
        
        self.logger.info(f"Item updated successfully: {item_id}")
        return response_item
```

**File**: `product/app/services/product_services.py:7-40`

```python
class ProductService:
    def __init__(self, logger):
        self.logger = logger
        # Mock data storage
        self.products = {}
        self.next_id = 1

    async def create_product(
        self,
        request: Request,
        product_data: models.ProductRequest
    ):
        self.logger.info(f"Product creation attempt: {product_data.name}")
        
        for product in self.products.values():
            if product['name'].lower() == product_data.name.lower():
                return create_problem_response(
                    status_code=409,
                    error_type="conflict",
                    title="Conflict",
                    detail="Product with this name already exists",
                    instance=str(request.url)
                )
        
        # Create product
        product_id = f"prod_{self.next_id}"
        
        product = models.ProductResponse(
            id=product_id,
            name=product_data.name,
            price=product_data.price,
            stock=product_data.stock,
            description=product_data.description
        )
```
## 3. Core Tools
**File**: `authentication/tools.py:12-37`

```python
class PasswordTools:
    def __init__(self):
        pass

    @PasswordToolsDecorators.handle_encode_error
    def encode_password(self, plain_password: str) -> str:
        if plain_password is None:
            raise ValueError('password cannot be None.')
        
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt).decode('utf-8')
        return hashed

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        if plain_password is None:
            raise ValueError('password cannot be None.')
       
        if not hashed_password or not isinstance(hashed_password, str):
            raise ValueError("Invalid hashed password")
        
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except (ValueError, TypeError) as e:
            raise ValueError('Invalid hashed password format')
        except Exception as e:
            PasswordErrorHandler.handle_verify_error(e)
```

## 4. Error Handling & Decorators
**File**: `profile/app/decorators/profile_routes_decorators.py:15-45`

```python
class ProfileErrorDecorators:
    
    @staticmethod
    def handle_get_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            user_id: str,
            profile_service: ProfileService = Depends(),
        ) -> Any:
            try:
                return await func(request, user_id, profile_service)
            except Exception as e:
                return ProfileErrorDecorators._handle_get_exception(e, request)
        return wrapper
    
    @staticmethod
    def handle_update_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            profile_data: Any,
            user_id: str,
            profile_service: ProfileService = Depends(),
        ) -> Any:
            try:
                return await func(request, profile_data, user_id, profile_service)
            except Exception as e:
                return ProfileErrorDecorators._handle_update_exception(e, request)
        return wrapper
```

## 5. API Routes with Dependency Injection
**File**: `orders/routes/order_routes.py:23-55`

```python
@router.post(
    '',
    response_model=models.OrderResponse,
    status_code=201,
    summary="Create order (checkout current cart)"
)
@OrderErrorDecorators.handle_create_errors
async def create_order(
    request: Request,
    order_data: models.OrderCreate,
    user_id: str = Depends(get_user_id),
    order_service: OrderService = Depends(get_order_service),
) -> models.OrderResponse:
    return await order_service.create_order(request, order_data, user_id)

@router.get(
    '',
    response_model=models.OrderList,
    summary="List user's orders (paginated)"
)
@OrderErrorDecorators.handle_list_errors
async def list_orders(
    request: Request,
    user_id: str = Depends(get_user_id),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Page size"),
    order_service: OrderService = Depends(get_order_service),
) -> models.OrderList:
    query_params = models.OrderQueryParams(
        page=page,
        page_size=page_size
    )
    return await order_service.list_orders(request, user_id, query_params)
```

## 6. Comprehensive Test Coverage
an example of a test coverage.

```bash
---------- coverage: platform win32, python 3.12.4-final-0 -----------
Name                                   Stmts   Miss  Cover
----------------------------------------------------------
__init__.py                                0      0   100%
database\__init__.py                       0      0   100%
database\models.py                        39      1    97%
decorators\__init__.py                     0      0   100%
decorators\cart_routes_decorators.py      89     39    56%
main.py                                   45      8    82%
routes\__init__.py                         0      0   100%
routes\cart_routes.py                     37      1    97%
services\__init__.py                       0      0   100%
services\cart_helpers.py                   4      0   100%
services\cart_services.py                110      2    98%
tests\__init__.py                          0      0   100%
tests\test_cart_contract.py              138      8    94%
tests\test_cart_services.py              147      0   100%
----------------------------------------------------------
TOTAL                                    609     59    90%
```

## Key Architecture Patterns

### 1. **Clean Separation of Concerns**
- **Domain Layer**: Pydantic models in `database/models.py`
- **Business Logic**: `Service` classes in `services/service-name_services.py`
- **Presentation**: FastAPI routes in `routes/service-name_routes.py`

### 2. **Error Handling Strategy**
- **Decorator Pattern**: Centralized error handling in `ErrorDecorators`
- **Problem Details**: RFC 7807 compliant error responses
- **Type Safety**: Pydantic validation throughout

### 3. **Security Implementation**
- **Password Hashing**: bcrypt with proper salt generation
- **JWT Tokens**: Access & refresh token patterns
- **Input Validation**: Comprehensive password strength rules
- **Token Validation**: Proper JWT decoding and expiration checks

### 4. **Testing Strategy**
- **Contract Testing**: API endpoint compliance
- **Service Testing**: Business logic isolation
- **Tool Testing**: Core algorithm validation
- **Mock Dependencies**: Proper dependency injection for testing


## Architecture Benefits

1. **Testability**: Each layer can be tested independently with mocked dependencies
2. **Maintainability**: Clear separation makes changes localized and safe
3. **Scalability**: Stateless services allow horizontal scaling
4. **Security**: Multiple layers of validation and proper error handling
5. **Standards Compliance**: Follows RESTful patterns and RFC specifications
