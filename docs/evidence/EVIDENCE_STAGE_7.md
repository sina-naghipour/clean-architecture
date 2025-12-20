# EVIDENCE_GENERAL_FORMAT.md
## gRPC Payment Service Implementation

### Pattern
- **Location**: `payment_grpc_server.py` + `payment_grpc_client.py`  
- **Technology**: Bidirectional async gRPC with OpenTelemetry, Circuit Breaker pattern  
- **Purpose**: Complete payment service communication with client resilience and server idempotency  

### Evidence Structure
```python
# Server-side implementation
class PaymentGRPCServer(payments_pb2_grpc.PaymentServiceServicer):
    @trace_service_operation("grpc_create_payment")
    async def CreatePayment(self, request, context):
        # Idempotency key extraction from metadata
        # Existing payment detection by order_id
        # Payment creation via internal service
        # Response transformation to protobuf

# Client-side implementation        
class PaymentGRPCClient:
    @trace_service_operation("create_payment_grpc")
    async def create_payment(self, order_id, amount, user_id, payment_method_token):
        # Circuit breaker state management
        # Retry logic with exponential backoff
        # Idempotency key generation and metadata attachment
        # Distributed tracing per attempt
```

### Key Features
- **Bidirectional Idempotency**: Server detects duplicates via order_id, client provides idempotency-key metadata  
- **Circuit Breaker Pattern**: 5-failure threshold with 30-second cooldown prevents cascade failures  
- **End-to-End Tracing**: OpenTelemetry spans track both client attempts and server processing
---

## 2. Payment Webhook Handler

### Pattern
- **Location**: `order_service.py` + `order_routes.py`  
- **Technology**: FastAPI with decorator-based error handling, idempotent webhook processing  
- **Purpose**: Process payment status updates with duplicate detection and state validation  

### Evidence Structure
```python
@OrderServiceDecorators.handle_payment_webhook_errors
@trace_service_operation("handle_payment_webhook")
async def handle_payment_webhook(self, request, payment_data: dict):
    # Idempotency key validation
    # Payment status to order status mapping
    # State change validation and persistence
    # Idempotency key storage for duplicate prevention

@router.post('/webhooks/payment-updates')
async def payment_webhook(api_key: str = Header(...)):
    # Internal API key validation
    # Dependency injection of order service
    # Error handling through decorators
```

### Key Features
- **Idempotent Webhook Processing**: Duplicate request detection via X-Idempotency-Key header  
- **State Transition Validation**: Prevents redundant updates when order already in target state  
- **Internal API Authentication**: Secure webhook endpoint with environment-based API key validation

---

## 3. Service-to-Service gRPC Contracts

### Pattern
- **Location**: `orders.proto` + `payments.proto`  
- **Technology**: Protocol Buffers v3 with bidirectional service definitions  
- **Purpose**: Define cross-service communication contracts for payment lifecycle  

### Evidence Structure
```proto
// Order Service Contract (Payment → Order)
service OrderService {
  rpc UpdateOrderPaymentStatus(UpdateOrderPaymentRequest) 
      returns (UpdateOrderPaymentResponse);
}

// Payment Service Contract (Order → Payment)  
service PaymentService {
  rpc CreatePayment(CreatePaymentRequest) returns (PaymentResponse);
  rpc GetPayment(GetPaymentRequest) returns (PaymentResponse);
  rpc ProcessRefund(RefundRequest) returns (RefundResponse);
}

// Bidirectional message types with UUID references
message UpdateOrderPaymentRequest { string order_id = 1; string payment_id = 2; }
message CreatePaymentRequest { string order_id = 1; string user_id = 2; double amount = 3; }
message PaymentResponse { string payment_id = 1; string order_id = 2; string client_secret = 9; }
```

### Key Features
- **Bidirectional Service Definitions**: Order ↔ Payment with clear request/response flows  
- **Consistent UUID Referencing**: Cross-service entity linking via order_id and payment_id fields  
- **Stripe Integration Support**: External payment provider fields with client_secret for frontend

---
## 4. Payment Processing Service

### Pattern
- **Location**: `stripe_service.py` + `payment_service.py`  
- **Technology**: Stripe integration with async webhook processing, cross-service notifications  
- **Purpose**: End-to-end payment processing with external provider integration and order synchronization  

### Evidence Structure
```python
# External payment provider integration
class StripeService:
    async def create_payment_intent(self, amount, currency, payment_method_token):
        # Stripe API calls with OpenTelemetry tracing
        # Status mapping to internal payment states
        # Webhook signature verification

# Internal payment orchestration        
class PaymentService:
    async def create_payment(self, payment_data: PaymentCreate):
        # Idempotent payment creation by order_id
        # Stripe payment intent creation
        # Database persistence with status tracking
        # Order service notification with retry logic

    async def process_webhook(self, request: Request, payload: bytes, sig_header: str):
        # Webhook signature validation
        # Payment status update based on Stripe events
        # Order service synchronization
```

### Key Features
- **Stripe Payment Provider Integration**: Payment intent creation, refund processing, webhook verification  
- **Cross-Service Synchronization**: HTTP webhook notifications to Order service with idempotency keys  
- **End-to-End Tracing**: OpenTelemetry spans track payment flow from creation to webhook processing
---

## 5. Payment Service Core Business Logic

### Pattern
- **Location**: `payment_service.py`  
- **Technology**: FastAPI service layer with Stripe integration, OpenTelemetry tracing  
- **Purpose**: Orchestrate payment lifecycle with external provider and cross-service synchronization  

### Evidence Structure
```python
class PaymentService:
    async def create_payment(self, payment_data: PaymentCreate):
        # Idempotent payment creation by order_id
        # Stripe payment intent generation with metadata
        # Database persistence with status tracking
        # Client secret storage for frontend integration

    async def process_webhook(self, request: Request, payload: bytes, sig_header: str):
        # Webhook signature validation
        # Payment status update based on Stripe events
        # Cross-service notification with retry logic
        # Receipt URL handling for successful charges

    async def _notify_orders_service(self, payment_id: UUID, status: str, receipt_url: str = None):
        # Retry logic with exponential backoff (1s, 2s, 4s)
        # Idempotency key generation per notification
        # HTTP POST with internal API key authentication
        # Distributed tracing of notification attempts
```

### Key Features
- **Stripe Webhook Processing**: Event-driven payment status updates with signature verification  
- **Cross-Service Synchronization**: HTTP notifications to Order service with 3-retry exponential backoff  
- **Idempotent Payment Creation**: Duplicate prevention via order_id lookup before Stripe API calls

--- 
## 6. OpenTelemetry Collector Configuration

### Pattern
- **Location**: `otel-collector-config.yaml`  
- **Technology**: OpenTelemetry Collector with OTLP receivers, Jaeger/Prometheus exporters  
- **Purpose**: Centralized telemetry collection and distribution for microservices observability  

### Evidence Structure
```yaml
receivers:
  otlp:
    protocols:
      http: 0.0.0.0:4318    # HTTP OTLP endpoint
      grpc: 0.0.0.0:4317    # gRPC OTLP endpoint

exporters:
  otlp/jaeger:              # Jaeger distributed tracing backend
    endpoint: jaeger:4317
    tls: {insecure: true}
  prometheus:               # Prometheus metrics endpoint
    endpoint: "0.0.0.0:8889"

service:
  pipelines:
    traces:                 # Trace processing pipeline
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp/jaeger, debug]
    metrics:                # Metrics processing pipeline  
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus, debug]

scrape_configs:
  - job_name: 'otel-collector'  # Prometheus collector self-scraping
    static_configs:
      - targets: ['otel-collector:8889']
```

### Key Features
- **Dual Protocol Support**: HTTP and gRPC OTLP endpoints for flexible instrumentation  
- **Multi-Export Pipeline**: Traces to Jaeger, metrics to Prometheus with debug output  
- **Self-Monitoring**: Prometheus scrape configuration includes collector metrics endpoint
---

## 7. JWT Authentication Middleware

### Pattern
- **Location**: `auth_middleware.py`  
- **Technology**: FastAPI middleware with JWT validation, RFC 7807 error responses  
- **Purpose**: Centralized authentication and authorization with role-based access control  

### Evidence Structure
```python
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        # Public path bypass (health, docs, openapi.json)
        # Bearer token extraction from Authorization header
        # JWT validation with expiration and field checks
        # Role-based authorization against ALLOWED_ROLES list
        # RFC 7807 problem responses for auth failures
        # User data attachment to request.state for downstream use
```

### Key Features
- **JWT Token Validation**: Expiration checks, required field validation, token type verification  
- **Role-Based Access Control**: Configurable ALLOWED_ROLES list with admin-only default  
- **RFC 7807 Error Responses**: Structured problem details for authentication/authorization failures

---

## 8. Distributed Tracing Decorators

### Pattern
- **Location**: `trace_decorator.py`  
- **Technology**: OpenTelemetry decorators with domain-specific span attributes  
- **Purpose**: Automatic instrumentation across repository, service, and client layers  

### Evidence Structure
```python
def trace_repository_operation(operation_name: str):
    # Repository layer tracing
    # Automatic model name extraction from class name
    # Operation-specific attributes (product.id, repository.skip, etc.)
    # MongoDB database tagging

def trace_client_operation(operation_name: str):
    # Client layer tracing  
    # Service operation context (ProductImageClient)
    # File upload metadata (filename, content_type, count)
    # URL and subdirectory context for external calls

def trace_service_operation(operation_name: str):
    # Service layer tracing
    # Business operation context (ProductService)
    # Domain-specific attributes (product.price, tags_count, images_count)
    # Query parameter capture for search operations
```

### Key Features
- **Layer-Specific Instrumentation**: Repository, Service, and Client tracing with appropriate context  
- **Automatic Attribute Capture**: Operation-specific parameters extracted from method arguments  
- **Domain Context Enrichment**: Product, payment, and image metadata attached to spans for observability

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