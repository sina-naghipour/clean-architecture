# Update Cart Item

Change quantity of item in cart (idempotent).

**Endpoint:** `PATCH /cart/items/{itemId}`

## Path Parameters
| Parameter | Required | Description |
|-----------|----------|-------------|
| itemId    | Yes      | Cart item ID |

## Authentication
Requires bearer token.

## Request Body
```json
{
  "quantity": 3
}
```

| Field    | Type    | Required | Description |
|----------|---------|----------|-------------|
| quantity | integer | Yes      | Minimum: 1  |

## Response (200 OK)
```json
{
  "id": "item_1",
  "product_id": "prod_42",
  "name": "Wireless Mouse",
  "quantity": 3,
  "unit_price": 29.99
}
```

## Errors
- **400/422** - Invalid data
- **401** - Missing/invalid token
- **404** - Item not found
- **500** - Server error

## Example
```bash
curl -X PATCH \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"quantity":3}' \
  "http://localhost:8000/api/cart/items/item_1"
```

**Note:** Same request always gives same result (idempotent). Set quantity to 0 to remove (or use DELETE).