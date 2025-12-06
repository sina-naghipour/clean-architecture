# Get Product Image

Get metadata for a specific product image.

**Endpoint:** `GET /files/{fileId}`

## Path Parameters
| Parameter | Required | Description |
|-----------|----------|-------------|
| fileId    | Yes      | Image ID    |

## Response (200 OK)
```json
{
  "id": "img_123...",
  "productId": "prod_42",
  "filename": "prod_42_abc123.jpg",
  "originalName": "mouse.jpg",
  "mimeType": "image/jpeg",
  "size": 2048576,
  "width": 800,
  "height": 600,
  "isPrimary": true,
  "url": "/static/img/products/prod_42/prod_42_abc123.jpg",
  "uploadedAt": "2023-10-01T12:00:00Z"
}
```

## Example
```bash
curl -X GET "http://localhost:8000/api/files/img_123..."
```

**Note:** Returns metadata only, not the actual image file. Use the `url` field to access the image.