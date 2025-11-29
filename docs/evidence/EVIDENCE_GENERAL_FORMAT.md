# EVIDENCE_GENERAL_FORMAT.md

## 1. Domain Models & Data Contracts

### Pattern
- **Location**: `{service}/app/database/models.py`
- **Technology**: Pydantic BaseModel with validation
- **Purpose**: Define data structures, validation rules, and serialization

### Evidence Structure
```python
class {Entity}Request(BaseModel):
    field: Type = Field(validation_rules)
    
    @field_validator('*', mode='before')
    def validation_method(cls, v):
        # validation logic
        return v

class {Entity}Response(BaseModel):
    id: str
    field: Type
    
    model_config = ConfigDict(from_attributes=True)
```

### Key Features
- Type hints for static analysis
- Field validators for business rules
- Config for ORM compatibility
- Optional/mandatory field definitions

---

## 2. Business Logic Layer

### Pattern
- **Location**: `{service}/app/services/{service}_services.py`
- **Architecture**: Service classes with dependency injection
- **Purpose**: Encapsulate business rules and workflows

### Evidence Structure
```python
class {Service}Service:
    def __init__(self, logger):
        self.logger = logger
        # data storage/connections

    async def {operation}_method(
        self,
        request: Request,
        entity_data: models.EntityRequest
    ):
        # Validation logic
        # Business rules
        # Data transformation
        # Response formatting
```

### Key Features
- Async/await for performance
- Comprehensive logging
- Error handling with problem details
- Data validation before processing

---

## 3. Core Tools & Utilities

### Pattern
- **Location**: `{service}/tools.py` or domain-specific tool files
- **Purpose**: Reusable algorithms, security utilities, data transformations

### Evidence Structure
```python
class {Domain}Tools:
    def __init__(self):
        pass

    @Decorators.handle_errors
    def core_algorithm(self, input_data: Type) -> OutputType:
        # Algorithm implementation
        return result

    def validation_method(self, data: Type) -> bool:
        # Validation logic
        return is_valid
```

### Key Features
- Decorator-based error handling
- Input validation
- Algorithm isolation for testing
- Type-safe interfaces

---

## 4. Error Handling & Decorators

### Pattern
- **Location**: `{service}/app/decorators/{service}_routes_decorators.py`
- **Purpose**: Centralized exception handling and response formatting

### Evidence Structure
```python
class {Service}ErrorDecorators:
    
    @staticmethod
    def handle_{operation}_errors(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                return _handle_specific_exception(e, request)
        return wrapper
    
    @staticmethod
    def _handle_{type}_exception(exception: Exception, request: Request):
        return create_problem_response(
            status_code=code,
            error_type="error-category",
            title="Human Readable Title",
            detail="Specific error details",
            instance=str(request.url)
        )
```

### Key Features
- RFC 7807 Problem Details compliance
- Exception type mapping
- Request context preservation
- Consistent error formatting

---

## 5. API Routes with Dependency Injection

### Pattern
- **Location**: `{service}/routes/{service}_routes.py`
- **Framework**: FastAPI with OpenAPI documentation
- **Purpose**: HTTP endpoint definitions with validation

### Evidence Structure
```python
@router.{http_method}(
    'path',
    response_model=models.ResponseModel,
    status_code=200,
    summary="API summary"
)
@ErrorDecorators.handle_operation_errors
async def api_operation(
    request: Request,
    input_data: models.RequestModel,
    user_id: str = Depends(authentication_method),
    service: ServiceClass = Depends(get_service),
) -> models.ResponseModel:
    return await service.operation_method(request, input_data, user_id)
```

### Key Features
- OpenAPI documentation generation
- Dependency injection for services
- Authentication integration
- Response model typing
- Error handling decorators

---

## 6. API Contract Definition

### Pattern
- **Location**: `./api/openapi.yaml`
- **Standard**: OpenAPI 3.0 with reusable components
- **Purpose**: API specification and contract testing

### Evidence Structure
```yaml
components:
  schemas:
    Entity:
      type: object
      properties:
        id:
          type: string
        field:
          type: string
      required: [id]

  parameters:
    EntityId:
      name: entityId
      in: path
      required: true
      schema:
        type: string

  responses:
    ErrorResponse:
      description: Standard error response
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ProblemDetails"
```

### Key Features
- Reusable component definitions
- RFC 7807 error schemas
- Parameter validation
- Security scheme definitions

---

## 7. Comprehensive Testing

### Pattern
- **Location**: `{service}/tests/test_*.py`
- **Frameworks**: pytest, parameterized tests
- **Coverage**: Contract, service, unit, integration tests

### Evidence Structure
```python
@pytest.mark.parametrize("input1,input2,expected_output", test_cases)
def test_method_scenario(input1, input2, expected_output):
    # Setup
    service = ServiceUnderTest()
    
    # Execution
    result = service.method(input1, input2)
    
    # Assertion
    assert result == expected_output

class TestServiceIntegration:
    def setup_method(self):
        # Test fixtures
        self.service = configured_service()
    
    def test_business_scenario(self):
        # Complex workflow testing
        result = await self.service.full_workflow()
        assert result.expected_property == expected_value
```

### Key Features
- Parameterized test cases
- High test coverage (>90%)
- Mock dependencies
- Contract validation
- Error scenario testing

---

## 8. CI/CD & Quality Tools

### Pattern
- **Location**: `.github/workflows/`, configuration files
- **Tools**: ruff, mypy, pytest, coverage
- **Purpose**: Automated quality assurance

### Evidence Structure
```yaml
# GitHub Actions example
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pytest --cov=src --cov-report=xml
      - name: Type checking
        run: mypy src/
      - name: Linting
        run: ruff check src/
```

### Key Features
- Automated testing on commits
- Quality gate enforcement
- Coverage reporting
- Type safety validation
- Code style consistency

---

## 9. Documentation & Error Catalog

### Pattern
- **Location**: `./api/errors.md`, README files
- **Format**: Markdown with code examples
- **Purpose**: API consumer guidance

### Evidence Structure
```markdown
## {HTTP Status} — {Error Title}

- **Type (URI):** `https://api.example.com/errors/error-type`  
- **Title:** {Human Readable Title}  
- **Description:** {When this error occurs}  
- **Example:**
```json
{
  "type": "error-uri",
  "title": "Error Title",
  "status": 400,
  "detail": "Specific error context",
  "instance": "/api/endpoint"
}
```

### Key Features
- RFC 7807 compliance
- Consumer-friendly documentation
- Example payloads
- Troubleshooting guidance

---

## Key Architecture Benefits

1. **Testability**: Each layer can be tested independently
2. **Maintainability**: Clear separation of concerns
3. **Scalability**: Stateless services, horizontal scaling
4. **Security**: Multiple validation layers, proper error handling
5. **Standards Compliance**: RESTful patterns, RFC specifications
6. **Developer Experience**: Comprehensive documentation, type safety
7. **Operational Excellence**: Logging, monitoring, error tracking

This format ensures consistent evidence presentation across different projects and technologies while maintaining the core principles of clean architecture, testability, and professional software development practices.