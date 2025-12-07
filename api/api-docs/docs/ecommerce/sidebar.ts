import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

const sidebar: SidebarsConfig = {
  apisidebar: [
    {
      type: "doc",
      id: "ecommerce/ecommerce-api",
    },
    {
      type: "category",
      label: "Health",
      items: [
        {
          type: "doc",
          id: "ecommerce/health-check",
          label: "Health check",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "ecommerce/readiness-check",
          label: "Readiness check",
          className: "api-method get",
        },
      ],
    },
    {
      type: "category",
      label: "Root",
      items: [
        {
          type: "doc",
          id: "ecommerce/service-information",
          label: "Service information",
          className: "api-method get",
        },
      ],
    },
    {
      type: "category",
      label: "Auth",
      items: [
        {
          type: "doc",
          id: "ecommerce/register-new-user",
          label: "Register new user",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "ecommerce/login-user-returns-access-refresh-tokens",
          label: "Login user (returns access + refresh tokens)",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "ecommerce/refresh-access-token-using-refresh-token",
          label: "Refresh access token using refresh token",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "ecommerce/logout-user-revoke-refresh-token",
          label: "Logout user (revoke refresh token)",
          className: "api-method post",
        },
      ],
    },
    {
      type: "category",
      label: "Products",
      items: [
        {
          type: "doc",
          id: "ecommerce/list-products-supports-paging-filtering",
          label: "List products (supports paging & filtering)",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "ecommerce/create-product-admin",
          label: "Create product (admin)",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "ecommerce/get-product-details",
          label: "Get product details",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "ecommerce/replace-product-full-update-admin-only",
          label: "Replace product (full update) — admin only",
          className: "api-method put",
        },
        {
          type: "doc",
          id: "ecommerce/partially-update-product-admin",
          label: "Partially update product (admin)",
          className: "api-method patch",
        },
        {
          type: "doc",
          id: "ecommerce/delete-product-admin",
          label: "Delete product (admin)",
          className: "api-method delete",
        },
        {
          type: "doc",
          id: "ecommerce/update-product-stock-admin-idempotent",
          label: "Update product stock (admin) — idempotent",
          className: "api-method patch",
        },
      ],
    },
    {
      type: "category",
      label: "Product Images",
      items: [
        {
          type: "doc",
          id: "ecommerce/upload-product-image-admin",
          label: "Upload product image (admin)",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "ecommerce/list-product-images",
          label: "List product images",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "ecommerce/get-product-image-metadata",
          label: "Get product image metadata",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "ecommerce/delete-product-image-admin",
          label: "Delete product image (admin)",
          className: "api-method delete",
        },
        {
          type: "doc",
          id: "ecommerce/set-image-as-primary-for-product-admin",
          label: "Set image as primary for product (admin)",
          className: "api-method patch",
        },
      ],
    },
    {
      type: "category",
      label: "Cart",
      items: [
        {
          type: "doc",
          id: "ecommerce/get-current-users-cart",
          label: "Get current user's cart",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "ecommerce/clear-cart",
          label: "Clear cart",
          className: "api-method delete",
        },
        {
          type: "doc",
          id: "ecommerce/add-item-to-cart",
          label: "Add item to cart",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "ecommerce/update-cart-item-quantity-partial-idempotent",
          label: "Update cart item quantity (partial, idempotent)",
          className: "api-method patch",
        },
        {
          type: "doc",
          id: "ecommerce/remove-cart-item",
          label: "Remove cart item",
          className: "api-method delete",
        },
      ],
    },
    {
      type: "category",
      label: "Orders",
      items: [
        {
          type: "doc",
          id: "ecommerce/create-order-checkout-current-cart",
          label: "Create order (checkout current cart)",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "ecommerce/list-users-orders-paginated",
          label: "List user's orders (paginated)",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "ecommerce/get-order-details",
          label: "Get order details",
          className: "api-method get",
        },
      ],
    },
  ],
};

export default sidebar.apisidebar;
