const {themes} = require('prism-react-renderer');
const Color = require('color');

// Function to generate color variations
const generateColorPalette = (baseColor) => {
  const color = Color(baseColor);
  return {
    base: color.hex(),
    light: color.lighten(0.2).hex(),
    lighter: color.lighten(0.4).hex(),
    dark: color.darken(0.2).hex(),
    darker: color.darken(0.4).hex(),
    alpha10: color.alpha(0.1).hexa(),
    alpha20: color.alpha(0.2).hexa(),
  };
};

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Ecommerce API Documentation',
  tagline: 'Complete API for ecommerce platform with product image management',
  favicon: 'img/favicon.ico',

  url: 'https://your-api-docs.com',
  baseUrl: '/',

  organizationName: 'sina-naghipour',
  projectName: 'ecommerce-api',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
          editUrl: 'https://github.com/your-repo/docs/edit/main/',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],


  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      colorMode: {
        defaultMode: 'dark',
        disableSwitch: false,
        respectPrefersColorScheme: true,
      },
      navbar: {
        title: 'Ecommerce API',
        logo: {
          alt: 'Ecommerce API Logo',
          src: 'img/logo.svg',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'docsSidebar',
            position: 'left',
            label: 'Documentation',
          },
          {
            to: '/docs/api',
            label: 'API Reference',
            position: 'left',
          },
          {
            href: 'https://github.com/your-repo/ecommerce-api',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              {
                label: 'Getting Started',
                to: '/docs/getting-started/overview',
              },
              {
                label: 'Authentication',
                to: '/docs/getting-started/authentication',
              },
              {
                label: 'API Reference',
                to: '/docs/api',
              },
            ],
          },
          {
            title: 'Community',
            items: [
              {
                label: 'Stack Overflow',
                href: 'https://stackoverflow.com/questions/tagged/ecommerce-api',
              },
              {
                label: 'Discord',
                href: 'https://discord.gg/your-server',
              },
              {
                label: 'Twitter',
                href: 'https://twitter.com/your-twitter',
              },
            ],
          },
          {
            title: 'More',
            items: [
              {
                label: 'GitHub',
                href: 'https://github.com/your-repo/ecommerce-api',
              },
              {
                label: 'Changelog',
                href: 'https://github.com/your-repo/ecommerce-api/releases',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} Your Company. Built with Docusaurus.`,
      },
      prism: {
        theme: themes.github,
        darkTheme: themes.dracula,
        additionalLanguages: ['bash', 'json', 'yaml'],
      },
      docs: {
        sidebar: {
          hideable: true,
        },
      },
      algolia: {
        appId: 'YOUR_APP_ID',
        apiKey: 'YOUR_SEARCH_API_KEY',
        indexName: 'YOUR_INDEX_NAME',
        contextualSearch: true,
      },
    }),

    stylesheets: [
      {
        href: 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap',
      },
    ],
};

module.exports = config;