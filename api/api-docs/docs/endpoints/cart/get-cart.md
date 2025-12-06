# Get Cart

Retrieve current user's shopping cart.

**Endpoint:** `GET /cart`

## Authentication
Requires bearer token.

## Response (200 OK)
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

## Example
```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/cart"
```

**Note:** Returns empty items array if cart is empty. Each user has exactly one cart.