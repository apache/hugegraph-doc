const hugoFrontMatter = require('./src/markdown/frontMatter');

const apacheLinks = [
  {label: 'Foundation', href: 'https://www.apache.org/'},
  {label: 'License', href: 'https://www.apache.org/licenses/'},
  {label: 'Events', href: 'https://www.apache.org/events/current-event.html'},
  {label: 'Privacy', href: 'https://privacy.apache.org/policies/privacy-policy-public.html'},
  {label: 'Security', href: 'https://www.apache.org/security/'},
  {label: 'Sponsorship', href: 'https://www.apache.org/foundation/sponsorship.html'},
  {label: 'Thanks', href: 'https://www.apache.org/foundation/thanks.html'},
  {label: 'Code of Conduct', href: 'https://www.apache.org/foundation/policies/conduct.html'},
];

const docsExclude = ['**/_*/**', '**/SUMMARY.md', '**/*.test.{js,jsx,ts,tsx}', '**/__tests__/**'];

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Apache HugeGraph',
  tagline: 'A full-stack graph database ecosystem for OLTP, OLAP, and AI',
  favicon: 'img/hugegraph-logo.svg',

  url: 'https://hugegraph.apache.org',
  baseUrl: '/',
  organizationName: 'apache',
  projectName: 'hugegraph-doc',
  trailingSlash: true,

  onBrokenLinks: 'throw',
  onBrokenAnchors: 'throw',
  onDuplicateRoutes: 'throw',

  markdown: {
    format: 'md',
    mermaid: true,
    parseFrontMatter: hugoFrontMatter,
    hooks: {
      onBrokenMarkdownLinks: 'throw',
      onBrokenMarkdownImages: 'throw',
    },
  },

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
          path: 'content/en/docs',
          routeBasePath: 'docs',
          sidebarPath: require.resolve('./sidebars.js'),
          exclude: docsExclude,
          editUrl: 'https://github.com/apache/hugegraph-doc/edit/master/',
          showLastUpdateAuthor: false,
          showLastUpdateTime: false,
        },
        blog: {
          path: 'content/en/blog',
          routeBasePath: 'blog',
          include: ['**/*.md', '**/*.mdx'],
          exclude: ['**/_index.md'],
          blogSidebarTitle: 'All posts',
          blogSidebarCount: 'ALL',
          showReadingTime: true,
          onUntruncatedBlogPosts: 'ignore',
          editUrl: 'https://github.com/apache/hugegraph-doc/edit/master/',
        },
        pages: {
          path: 'src/pages',
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  plugins: [
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'docs-cn',
        path: 'content/cn/docs',
        routeBasePath: 'cn/docs',
        sidebarPath: require.resolve('./sidebars-cn.js'),
        exclude: docsExclude,
        editUrl: 'https://github.com/apache/hugegraph-doc/edit/master/',
        showLastUpdateAuthor: false,
        showLastUpdateTime: false,
      },
    ],
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'community',
        path: 'content/en/community',
        routeBasePath: 'community',
        sidebarPath: require.resolve('./sidebars-community.js'),
        exclude: docsExclude,
        editUrl: 'https://github.com/apache/hugegraph-doc/edit/master/',
        showLastUpdateAuthor: false,
        showLastUpdateTime: false,
      },
    ],
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'community-cn',
        path: 'content/cn/community',
        routeBasePath: 'cn/community',
        sidebarPath: require.resolve('./sidebars-community-cn.js'),
        exclude: docsExclude,
        editUrl: 'https://github.com/apache/hugegraph-doc/edit/master/',
        showLastUpdateAuthor: false,
        showLastUpdateTime: false,
      },
    ],
    [
      '@docusaurus/plugin-content-blog',
      {
        id: 'blog-cn',
        path: 'content/cn/blog',
        routeBasePath: 'cn/blog',
        include: ['**/*.md', '**/*.mdx'],
        exclude: ['**/_index.md'],
        blogSidebarTitle: '所有文章',
        blogSidebarCount: 'ALL',
        showReadingTime: true,
        onUntruncatedBlogPosts: 'ignore',
        editUrl: 'https://github.com/apache/hugegraph-doc/edit/master/',
      },
    ],
  ],

  themes: ['@docusaurus/theme-mermaid'],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      colorMode: {
        defaultMode: 'light',
        respectPrefersColorScheme: true,
      },
      navbar: {
        title: 'Apache HugeGraph',
        logo: {
          alt: 'Apache HugeGraph logo',
          src: 'img/hugegraph-logo.svg',
        },
        items: [
          {to: '/docs/', label: 'Docs', position: 'left'},
          {to: '/blog/', label: 'Blog', position: 'left'},
          {to: '/community/', label: 'Community', position: 'left'},
          {to: '/docs/download/download/', label: 'Download', position: 'left'},
          {
            label: 'ASF',
            position: 'right',
            items: apacheLinks,
          },
          {
            label: 'Language',
            position: 'right',
            className: 'navbar-language-dropdown',
            items: [
              {label: 'English', to: '/'},
              {label: '中文', to: '/cn/'},
            ],
          },
          {
            href: 'https://github.com/apache/hugegraph',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        logo: {
          alt: 'Apache Software Foundation logo',
          src: 'img/apache-logo.svg',
          href: 'https://www.apache.org/',
          width: 220,
        },
        links: [
          {
            title: 'Project',
            items: [
              {label: 'Documentation', to: '/docs/'},
              {label: 'Download', to: '/docs/download/download/'},
              {label: 'GitHub', href: 'https://github.com/apache/hugegraph'},
              {label: 'Issue Tracker', href: 'https://github.com/apache/hugegraph/issues'},
            ],
          },
          {
            title: 'Community',
            items: [
              {label: 'Community', to: '/community/'},
              {label: 'Mailing List', href: 'mailto:dev@hugegraph.apache.org'},
              {label: 'ASF Slack', href: 'https://the-asf.slack.com/archives/C059UU2FJ23'},
            ],
          },
          {
            title: 'ASF',
            items: apacheLinks,
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} The Apache Software Foundation. Licensed under the Apache License, Version 2.0. Apache HugeGraph, HugeGraph, Apache, the Apache feather logo, and the Apache HugeGraph project logo are either registered trademarks or trademarks of The Apache Software Foundation in the United States and other countries.`,
      },
      prism: {
        additionalLanguages: ['bash', 'java', 'json', 'python', 'yaml'],
      },
      tableOfContents: {
        minHeadingLevel: 2,
        maxHeadingLevel: 4,
      },
    }),
};

module.exports = config;
