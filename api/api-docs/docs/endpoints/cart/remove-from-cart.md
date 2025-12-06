# Remove from Cart

Delete item from shopping cart.

**Endpoint:** `DELETE /cart/items/{itemId}`

## Path Parameters
| Parameter | Required | Description |
|-----------|----------|-------------|
| itemId    | Yes      | Cart item ID |

## Authentication
Requires bearer token.

## Response (204 No Content)
Successful removal returns no body.

## Errors
- **400** - Bad request
- **401** - Missing/invalid token
- **404** - Item not found
- **500** - Server error

## Example
```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/cart/items/item_1"
```

**Note:** Also can remove by setting quantity to 0 via PATCH. Cart persists even when empty.