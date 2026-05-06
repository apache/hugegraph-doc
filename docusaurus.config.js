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

const docsVersionOptions = {
  lastVersion: 'stable',
  includeCurrentVersion: true,
  versions: {
    current: {
      label: 'Next',
      path: 'next',
      banner: 'unreleased',
      badge: true,
      noIndex: true,
    },
    stable: {
      label: 'Stable (1.7.0)',
      path: '',
      banner: 'none',
      badge: true,
    },
    'v1.3.0': {
      label: 'v1.3.0',
      path: 'v1.3.0',
      banner: 'unmaintained',
      badge: true,
      noIndex: true,
    },
  },
};

const docsCnVersionOptions = {
  ...docsVersionOptions,
  versions: {
    current: {
      ...docsVersionOptions.versions.current,
      label: '开发版',
    },
    stable: {
      ...docsVersionOptions.versions.stable,
      label: '稳定版 (1.7.0)',
    },
    'v1.3.0': docsVersionOptions.versions['v1.3.0'],
  },
};

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
          ...docsVersionOptions,
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
        ...docsCnVersionOptions,
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
      '@docusaurus/plugin-content-pages',
      {
        id: 'download',
        path: 'content/en/download',
        routeBasePath: 'download',
        include: ['**/*.md', '**/*.mdx'],
        editUrl: 'https://github.com/apache/hugegraph-doc/edit/master/',
      },
    ],
    [
      '@docusaurus/plugin-content-pages',
      {
        id: 'download-cn',
        path: 'content/cn/download',
        routeBasePath: 'cn/download',
        include: ['**/*.md', '**/*.mdx'],
        editUrl: 'https://github.com/apache/hugegraph-doc/edit/master/',
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
          {
            type: 'custom-localeAwareLink',
            enTo: '/docs/',
            cnTo: '/cn/docs/',
            label: 'Docs',
            cnLabel: '文档',
            activeBasePath: '/docs/',
            cnActiveBasePath: '/cn/docs/',
            position: 'left',
          },
          {
            type: 'custom-localeAwareDocsVersionDropdown',
            position: 'left',
            dropdownActiveClassDisabled: true,
          },
          {
            type: 'custom-localeAwareLink',
            enTo: '/blog/',
            cnTo: '/cn/blog/',
            label: 'Blog',
            cnLabel: '博客',
            activeBasePath: '/blog/',
            cnActiveBasePath: '/cn/blog/',
            position: 'left',
          },
          {
            type: 'custom-localeAwareLink',
            enTo: '/community/',
            cnTo: '/cn/community/',
            label: 'Community',
            cnLabel: '社区',
            activeBasePath: '/community/',
            cnActiveBasePath: '/cn/community/',
            position: 'left',
          },
          {
            type: 'custom-localeAwareLink',
            enTo: '/team/',
            cnTo: '/cn/team/',
            label: 'Team',
            cnLabel: '团队',
            activeBasePath: '/team/',
            cnActiveBasePath: '/cn/team/',
            position: 'left',
          },
          {
            type: 'custom-localeAwareLink',
            enTo: '/users/',
            cnTo: '/cn/users/',
            label: 'Users',
            cnLabel: '用户',
            activeBasePath: '/users/',
            cnActiveBasePath: '/cn/users/',
            position: 'left',
          },
          {
            type: 'custom-localeAwareLink',
            enTo: '/download/',
            cnTo: '/cn/download/',
            label: 'Download',
            cnLabel: '下载',
            activeBasePath: '/download/',
            cnActiveBasePath: '/cn/download/',
            position: 'left',
          },
          {
            label: 'ASF',
            position: 'right',
            items: apacheLinks,
          },
          {
            type: 'custom-languageSwitcher',
            label: 'Language',
            position: 'right',
            className: 'navbar-language-dropdown',
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
          width: 180,
        },
        links: [
          {
            title: 'Project',
            items: [
              {label: 'Documentation', to: '/docs/'},
              {label: 'Download', to: '/download/'},
              {label: 'Team', to: '/team/'},
              {label: 'Users', to: '/users/'},
              {label: 'GitHub', href: 'https://github.com/apache/hugegraph'},
              {label: 'Issue Tracker', href: 'https://github.com/apache/hugegraph/issues'},
            ],
          },
          {
            title: 'Community',
            items: [
              {label: 'Community', to: '/community/'},
              {label: 'Contributor Guide', to: '/community/contribution-guidelines/'},
              {label: 'Mailing List', href: 'mailto:dev@hugegraph.apache.org'},
              {label: 'ASF Slack', href: 'https://the-asf.slack.com/archives/C059UU2FJ23'},
            ],
          },
          {
            title: 'ASF',
            items: apacheLinks,
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} The Apache Software Foundation. Licensed under the Apache License, Version 2.0. Apache HugeGraph, HugeGraph, Apache, and related logos are trademarks of The Apache Software Foundation.`,
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
