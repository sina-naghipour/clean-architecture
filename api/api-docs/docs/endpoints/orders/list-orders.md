# List Orders

Get paginated list of user's orders.

**Endpoint:** `GET /orders`

## Authentication
Requires bearer token.

## Query Parameters
| Parameter | Type    | Required | Default | Description |
|-----------|---------|----------|---------|-------------|
| page      | integer | No       | 1       | Page number |
| page_size | integer | No       | 20      | Items per page (1-100) |

## Response (200 OK)
```json
{
  "items": [
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
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

## Example
```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/orders?page=1&page_size=10"
```

**Note:** Returns empty items array if no orders. Orders sorted newest first.