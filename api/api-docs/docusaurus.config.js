// docusaurus.config.js

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Your Site Title',
  tagline: 'Your Tagline',
  url: 'https://your-site.com',
  baseUrl: '/',
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',
  favicon: 'img/favicon.ico',
  
  organizationName: 'your-org',
  projectName: 'your-project',
  
  presets: [
    [
      '@docusaurus/preset-classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          docItemComponent: '@theme/ApiItem', // Derived from docusaurus-theme-openapi
        },
        blog: false, // Disable blog if not needed
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  plugins: [
    [
      'docusaurus-plugin-openapi-docs',
      /** @type {import('docusaurus-plugin-openapi-docs').PluginOptions} */
      ({
        id: 'api', // plugin id
        docsPluginId: 'classic', // configured for preset-classic
        config: {
          ecommerce: {
            specPath: 'api_contract.yaml',
            outputDir: 'docs/ecommerce',
            sidebarOptions: {
              groupPathsBy: 'tag',
            },
          },
        },
      }),
    ],
  ],
  
  themes: ['docusaurus-theme-openapi-docs'], // export theme components

  // Additional configuration (customize as needed)
  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      navbar: {
        title: 'My Site',
        items: [
          {
            type: 'doc',
            docId: 'intro',
            position: 'left',
            label: 'API Docs',
          },
        ],
      },
      footer: {
        style: 'dark',
        copyright: `Copyright © ${new Date().getFullYear()} Your Company.`,
      },
    }),
};

module.exports = config;