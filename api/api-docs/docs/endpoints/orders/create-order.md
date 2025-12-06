# Create Order

Checkout current cart to create order.

**Endpoint:** `POST /orders`

## Authentication
Requires bearer token.

## Request Body (Optional)
```json
{
  "billingAddressId": "addr_1",
  "shippingAddressId": "addr_1",
  "paymentMethodToken": "pm_tok_abc"
}
```

## Response (201 Created)
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
- **400/422** - Invalid data
- **401** - Missing/invalid token
- **409** - Empty cart or stock issues
- **500** - Server error

## Example
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"paymentMethodToken":"pm_tok_abc"}' \
  "http://localhost:8000/api/orders"
```

**Note:** Uses cart items, clears cart on success. Checks product stock availability.