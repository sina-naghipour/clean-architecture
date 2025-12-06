# Clear Cart

Remove all items from current user's cart.

**Endpoint:** `DELETE /cart`

## Authentication
Requires bearer token.

## Response (204 No Content)
Successful clearance returns no body.

## Errors
- **400** - Bad request
- **401** - Missing/invalid token
- **500** - Server error

## Example
```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/cart"
```

**Note:** Cart remains (empty) after clearing. Different from deleting individual items.