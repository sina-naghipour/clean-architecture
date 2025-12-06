# Delete Product Image

Delete a product image (admin only).

**Endpoint:** `DELETE /files/{fileId}`

## Path Parameters
| Parameter | Required | Description |
|-----------|----------|-------------|
| fileId    | Yes      | Image ID    |

## Authentication
Requires bearer token with admin privileges.

## Response (204 No Content)
Successful deletion returns no body.

## Errors
- **401** - Missing/invalid token
- **403** - Insufficient permissions (not admin)
- **404** - Image not found
- **500** - Server error

## Example
```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/files/img_123..."
```

**Note:** Deleting a primary image may affect product display.