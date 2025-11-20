# Evidence: Stage 2 - Python Backend Development


## 1. Feature Implementation / Calculation

**File**: `./api/openapi.yaml`

### Reusable Parameters :
```yaml

  parameters:
    ProductId:
      name: productId
      in: path
      required: true
      schema:
        type: string
    ItemId:
      name: itemId
      in: path
      required: true
      schema:
        type: string
```
### Reusable Response Scheme:

```yaml
  schemas:
    ProblemDetails:
      title: ProblemDetails
      type: object
      properties:
        type:
          type: string
          format: uri
        title:
          type: string
        status:
          type: integer
        detail:
          type: string
        instance:
          type: string
          format: uri
      required:
        - type
        - title
        - status
```

### Neat and readable Path Definition:
```yaml
  /cart/items/{itemId}:
    parameters:
      - $ref: "#/components/parameters/ItemId"
    patch:
      tags: [Cart]
      summary: Update cart item quantity (partial, idempotent)
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/CartItemUpdate"
      responses:
        "200":
          description: Item updated
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/CartItemResponse"
        "400": 
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "404":
          $ref: "#/components/responses/NotFound"
        "422":
          $ref: "#/components/responses/UnprocessableEntity"
        "500":
          $ref: "#/components/responses/InternalError"
```
---

## 2. Clear and Easy to Understand Error Catalog

**File**: `./api/errors.md`

each error is defined based on [Problem Details](https://www.rfc-editor.org/rfc/rfc7807) RFC.
```markdown
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
````

```

---

## 3. Key Improvements / Notes

* **Clean Architecture / Modularization**: Built an API Contract based on a microservice API.
* **Small Methods / Functions**: Reusable Components used in API Contract.
* **Type Safety**: Validated `./api/openapi.yaml` through `openapi-spec-validator` module.

---

## 8. CI / Tooling

* **Linting**: `ruff`
* **Type checks**: `mypy`
* **Tests**: `pytest`
* **CI/CD**: `GitHub Actions`