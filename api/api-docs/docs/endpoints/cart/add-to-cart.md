# Add to Cart

Add item to current user's shopping cart.

**Endpoint:** `POST /cart/items`

## Authentication
Requires bearer token.

## Request Body
```json
{
  "product_id": "prod_42",
  "quantity": 2
}
```

| Field       | Type    | Required | Description      |
|-------------|---------|----------|------------------|
| product_id  | string  | Yes      | Product ID       |
| quantity    | integer | Yes      | Minimum: 1       |

## Response (201 Created)
```json
{
  "id": "item_1",
  "product_id": "prod_42",
  "quantity": 2
}
```

## Errors
- **400/422** - Invalid data
- **401** - Missing/invalid token
- **404** - Product not found
- **500** - Server error

## Example
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id":"prod_42","quantity":2}' \
  "http://localhost:8000/api/cart/items"
```

**Note:** Will create new cart if user doesn't have one. Quantity validation against stock happens at checkout.