/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docsSidebar: [
    {
      type: 'doc',
      id: 'intro',
      label: 'Introduction',
    },
    {
      type: 'category',
      label: 'Getting Started',
      collapsed: false,
      items: [
        'getting-started/overview',
        'getting-started/authentication',
        {
          type: 'category',
          label: 'Code Examples',
          items: [
            'getting-started/examples/curl',
            'getting-started/examples/javascript',
            'getting-started/examples/python',
            'getting-started/examples/postman',
          ],
        },
      ],
    },
    {
      type: 'category',
      label: 'API Endpoints',
      collapsed: false,
      items: [
        {
          type: 'category',
          label: 'Health & Root',
          items: [
            'endpoints/health',
          ],
        },
        {
          type: 'category',
          label: 'Authentication',
          items: [
            'endpoints/auth/register',
            'endpoints/auth/login',
            'endpoints/auth/refresh-token',
            'endpoints/auth/logout',
          ],
        },
        {
          type: 'category',
          label: 'Products',
          items: [
            'endpoints/products/list-products',
            'endpoints/products/get-product',
            'endpoints/products/create-product',
            'endpoints/products/update-product',
            'endpoints/products/delete-product',
            'endpoints/products/inventory',
          ],
        },
        {
          type: 'category',
          label: 'Product Images',
          items: [
            'endpoints/images/upload-image',
            'endpoints/images/list-images',
            'endpoints/images/get-image',
            'endpoints/images/delete-image',
          ],
        },
        {
          type: 'category',
          label: 'Shopping Cart',
          items: [
            'endpoints/cart/get-cart',
            'endpoints/cart/add-to-cart',
            'endpoints/cart/update-cart-item',
            'endpoints/cart/remove-from-cart',
            'endpoints/cart/clear-cart',
          ],
        },
        {
          type: 'category',
          label: 'Orders',
          items: [
            'endpoints/orders/create-order',
            'endpoints/orders/list-orders',
            'endpoints/orders/get-order',
          ],
        },
      ],
    },
    {
      type: 'doc',
      id: 'errors',
      label: 'Error Handling',
    },
    {
      type: 'link',
      label: 'API Reference (OpenAPI)',
      href: '/docs/api',
    },
  ],
};

module.exports = sidebars;