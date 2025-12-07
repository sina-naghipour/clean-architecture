# Error Catalog

This document lists all API error responses using the [Problem Details](https://www.rfc-editor.org/rfc/rfc7807) format (`application/problem+json`).  
It is based on the OpenAPI specification of the Ecommerce API.

---

# 207 — Multi-Status (Partial Success)

* **Type (URI):** `https://example.com/errors/multi-status`
* **Title:** Multi-Status
* **Description:** Batch operation completed with mixed results. Some items succeeded while others failed. Returned for batch uploads where some files uploaded successfully and others failed.
* **Example:**
```json
{
  "type": "https://example.com/errors/multi-status",
  "title": "Multi-Status",
  "status": 207,
  "detail": "Batch operation completed with partial success",
  "instance": "/products/prod_42/images/batch",
  "successful_count": 3,
  "failed_count": 2,
  "success": [
    {
      "filename": "image1.jpg",
      "id": "img_123",
      "url": "/static/img/products/prod_42/img_123.jpg"
    }
  ],
  "failed": [
    {
      "filename": "image5.gif",
      "error": "Unsupported image format",
      "status_code": 415
    }
  ]
}
```

## 400 — Bad Request

- **Type (URI):** `https://example.com/errors/bad-request`  
- **Title:** Bad Request  
- **Description:** Malformed JSON body or invalid request payload. Returned when the request cannot be parsed.  
- **Example:**

```json
{
  "type": "https://example.com/errors/bad-request",
  "title": "Bad Request",
  "status": 400,
  "detail": "Malformed JSON body.",
  "instance": "/products"
}
```

---

## 401 — Unauthorized

* **Type (URI):** `https://example.com/errors/unauthorized`
* **Title:** Unauthorized
* **Description:** Missing or invalid Authorization header/token. Returned when authentication fails.
* **Example:**

```json
{
  "type": "https://example.com/errors/unauthorized",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Missing or invalid Authorization header.",
  "instance": "/auth/login"
}
```

---

## 403 — Forbidden

* **Type (URI):** `https://example.com/errors/forbidden`
* **Title:** Forbidden
* **Description:** Insufficient permissions to perform the action. Returned for admin-only actions when the user is unauthorized.
* **Example:**

```json
{
  "type": "https://example.com/errors/forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "Insufficient permissions.",
  "instance": "/products"
}
```

---

## 404 — Not Found

* **Type (URI):** `https://example.com/errors/not-found`
* **Title:** Not Found
* **Description:** Resource does not exist. Returned for missing products, orders, users, or addresses.
* **Example:**

```json
{
  "type": "https://example.com/errors/not-found",
  "title": "Not Found",
  "status": 404,
  "detail": "Resource not found.",
  "instance": "/products/prod_999"
}
```

---

## 409 — Conflict

* **Type (URI):** `https://example.com/errors/conflict`
* **Title:** Conflict
* **Description:** Duplicate resource detected. Returned when trying to register an existing user, or duplicate product creation.
* **Example:**

```json
{
  "type": "https://example.com/errors/conflict",
  "title": "Conflict",
  "status": 409,
  "detail": "Duplicate resource.",
  "instance": "/auth/register"
}
```

---

## 413 — File Too Large

* **Type (URI):** `https://example.com/errors/file-too-large`
* **Title:** File Too Large
* **Description:** Uploaded file exceeds the maximum allowed size. Returned when image upload exceeds 5MB limit.
* **Example:**

```json
{
  "type": "https://example.com/errors/file-too-large",
  "title": "File Too Large",
  "status": 413,
  "detail": "File size exceeds maximum allowed size of 5MB",
  "instance": "/products/prod_42/images"
}
```

---

## 415 — Unsupported Media Type

* **Type (URI):** `https://example.com/errors/unsupported-media-type`
* **Title:** Unsupported Media Type
* **Description:** Uploaded file format is not supported. Returned when non-image files or unsupported image formats are uploaded.
* **Example:**

```json
{
  "type": "https://example.com/errors/unsupported-media-type",
  "title": "Unsupported Media Type",
  "status": 415,
  "detail": "Only JPEG, PNG, and WebP images are supported",
  "instance": "/products/prod_42/images"
}
```

---

## 422 — Unprocessable Entity / Validation Failed

* **Type (URI):** `https://example.com/errors/validation`
* **Title:** Validation Failed
* **Description:** Input validation error. Returned when required fields are missing, invalid, or fail constraints (e.g., email format, password length).
* **Example:**

```json
{
  "type": "https://example.com/errors/validation",
  "title": "Validation failed",
  "status": 422,
  "detail": "Field 'email' is required.",
  "instance": "/auth/register"
}
```
## **429 — Too Many Requests (Rate Limit Exceeded)**

* **Type (URI):** `https://example.com/errors/rate-limit-exceeded`
* **Title:** Too Many Requests
* **Description:** Rate limit exceeded. Returned when the client has sent too many requests in a given time period.
* **Headers included:**
  * `Retry-After: 60` (seconds until retry is allowed)
  * `X-RateLimit-Limit: 100` (requests allowed per minute)
  * `X-RateLimit-Remaining: 0` (requests remaining in current window)
  * `X-RateLimit-Reset: 1640995200` (UNIX timestamp when limit resets)
* **Example:**

```json
{
  "type": "https://example.com/errors/rate-limit-exceeded",
  "title": "Too Many Requests",
  "status": 429,
  "detail": "Rate limit exceeded. Please try again in 60 seconds.",
  "instance": "/api/products",
  "limit": 100,
  "window": "minute",
  "retry_after": 60,
  "reset_timestamp": 1640995200
}
```

---

## 500 — Internal Server Error

* **Type (URI):** `https://example.com/errors/internal`
* **Title:** Internal Server Error
* **Description:** Unexpected server-side error. Returned when an operation fails due to internal issues (e.g., database down, exception in code).
* **Example:**

```json
{
  "type": "https://example.com/errors/internal",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "Unexpected server error.",
  "instance": "/orders"
}
```

---

**Note:** All error responses follow the `application/problem+json` standard and include:

* `type` (URI identifying the error type)
* `title` (short human-readable summary)
* `status` (HTTP status code)
* `detail` (detailed human-readable explanation)
* `instance` (URI of the request that caused the error)