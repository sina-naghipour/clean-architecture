# Get Order

Retrieve specific order details.

**Endpoint:** `GET /orders/{orderId}`

## Path Parameters
| Parameter | Required | Description |
|-----------|----------|-------------|
| orderId   | Yes      | Order UUID  |

## Authentication
Requires bearer token.

## Response (200 OK)
```json
{
  "id": "order_1001",
  "status": "created",
  "total": 59.98,
  "billing_address_id": "addr_1",
  "shipping_address_id": "addr_1",
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

## Errors
- **401** - Missing/invalid token
- **404** - Order not found
- **500** - Server error

## Example
```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/orders/order_1001"
```

**Note:** Users can only access their own orders. Order status: created, paid, shipped, canceled.