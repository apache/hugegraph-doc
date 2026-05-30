const path = require('path');
const {DEFAULT_PARSE_FRONT_MATTER} = require('@docusaurus/utils');

function indexSlug(filePath) {
  if (path.basename(filePath) !== '_index.md') {
    return undefined;
  }

  const normalized = filePath.split(path.sep).join('/');
  const match = normalized.match(
    /(?:content\/(?:en|cn)\/(?:docs|community)|(?:versioned_docs|docs-cn_versioned_docs)\/version-[^/]+)\/(.*)_index\.md$/,
  );
  if (!match) {
    return undefined;
  }

  const slug = match[1].replace(/\/$/, '');
  return slug ? `/${slug}` : '/';
}

function slugify(value) {
  return String(value)
    .trim()
    .toLowerCase()
    .replace(/&/g, ' and ')
    .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function blogSlug(filePath, frontMatter) {
  const normalized = filePath.split(path.sep).join('/');
  if (!normalized.includes('/content/en/blog/') && !normalized.includes('/content/cn/blog/')) {
    return undefined;
  }
  if (!frontMatter.date) {
    return undefined;
  }

  const date =
    frontMatter.date instanceof Date
      ? frontMatter.date.toISOString().slice(0, 10)
      : String(frontMatter.date).slice(0, 10);
  const match = date.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) {
    return undefined;
  }

  const [, year, month, day] = match;
  const fallback = path.basename(filePath).replace(/\.mdx?$/i, '');
  return `/${year}/${month}/${day}/${slugify(frontMatter.title || fallback)}`;
}

function applyPlaceholderDefaults(frontMatter) {
  if (frontMatter.placeholder !== true) {
    return;
  }

  if (frontMatter.unlisted === undefined) {
    frontMatter.unlisted = true;
  }
  if (frontMatter.noindex === undefined) {
    frontMatter.noindex = true;
  }
  if (frontMatter.description === undefined) {
    frontMatter.description = 'Reserved route for upcoming Apache HugeGraph content.';
  }
}

module.exports = async function parseHugoFrontMatter(args) {
  const parsed = await DEFAULT_PARSE_FRONT_MATTER(args);
  parsed.frontMatter = parsed.frontMatter || {};
  const slug = indexSlug(args.filePath);

  if (slug && parsed.frontMatter.slug === undefined) {
    parsed.frontMatter.slug = slug;
  }

  const postSlug = blogSlug(args.filePath, parsed.frontMatter);
  if (postSlug && parsed.frontMatter.slug === undefined) {
    parsed.frontMatter.slug = postSlug;
  }

  if (parsed.frontMatter.linkTitle && parsed.frontMatter.sidebar_label === undefined) {
    parsed.frontMatter.sidebar_label = parsed.frontMatter.linkTitle;
  }

  applyPlaceholderDefaults(parsed.frontMatter);

  return parsed;
};
