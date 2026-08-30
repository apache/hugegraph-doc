# AGENTS.md

This file provides guidance to AI coding assistants (Claude Code, Cursor, GitHub Copilot, etc.) when working with code in this repository.

## Project Overview

Apache HugeGraph documentation website built with Docusaurus (v3.x). The site is bilingual (Chinese/English) and covers the complete HugeGraph graph database ecosystem.

## Development Commands

```bash
# Install dependencies
npm install

# Start development server (auto-reload)
npm run start

# Build production site (output to ./build)
npm run build

# Prepare versioned docs from Git branches
npm run docs:versions:prepare

# Run all validations
npm run validate

# Content validation only
npm run validate:content
```

## Prerequisites

- **Node.js** v18+ and npm

## Architecture

```
content/
├── cn/          # Chinese documentation
│   ├── docs/    # Main documentation
│   ├── blog/    # Blog posts
│   ├── community/
│   └── download/
└── en/          # English documentation (parallel structure)

src/             # Docusaurus pages, custom CSS, React components
  components/    # Custom navbar items (DocumentationDropdown, LocaleAware, LanguageSwitcher)
  pages/         # Homepage, Team, Users, Download redirects
  data/          # versions.json, team.js, users.js
  sidebars/      # Sidebar builders
static/          # Static files (images, .htaccess)
scripts/         # Content validation and version preparation
docusaurus.config.js  # Site configuration + plugin setup
sidebars*.js     # Sidebar configuration
```

### Content Structure

Documentation sections in `content/{cn,en}/docs/`:
- `quickstart/` - Getting started guides for HugeGraph components
- `config/` - Configuration documentation
- `clients/` - Client API documentation (Gremlin, RESTful)
- `guides/` - User guides and tutorials
- `performance/` - Benchmarks and optimization
- `language/` - Query language docs
- `changelog/` - Release notes
- `download/` - Download instructions

Contribution guidelines moved to `content/{cn,en}/community/contribution-guidelines/`.

## Key Configuration Files

- `docusaurus.config.js` - Site-wide settings, plugins, navbar, theme
- `src/data/versions.json` - Documentation version metadata
- `sidebars.js` / `sidebars-cn.js` - Documentation sidebars (en/cn)
- `sidebars-community.js` / `sidebars-community-cn.js` - Community sidebars
- `package.json` - Node dependencies (Docusaurus, React, Mermaid, Playwright)

## Working with Content

When editing documentation:
1. Maintain parallel structure between `content/cn/` and `content/en/`
2. Use Markdown with standard front matter (title, weight, description)
3. For bilingual changes, update both Chinese and English versions
4. Include mermaid diagrams where appropriate (mermaid.js is configured)

## Documentation Versions

- `src/data/versions.json` defines all versions (stable, next, archived)
- `npm run docs:versions:prepare` generates versioned docs from configured Git source refs
- Source `release-*` branches map to `docusaurus-*` version routes
- Archived versions use `legacyCompatibility` config for pre-Docusaurus branch imports

## Deployment

- **CI/CD**: GitHub Actions (`.github/workflows/docusaurus.yml`)
- **Trigger**: Push to `master` branch or pull requests
- **Build**: `npm install && npm run build` with Node v20
- **Deploy**: Publishes to `asf-site` branch (GitHub Pages)
- **Staging**: ASF GitPubSub via `.asf.yaml` publishes `asf-staging` branch to https://hugegraph.staged.apache.org/

## HugeGraph Ecosystem Context

This documentation covers:
- **HugeGraph-Server** - Core graph database with REST API
- **HugeGraph-Store** - Distributed storage engine
- **HugeGraph-PD** - Placement Driver for metadata
- **Toolchain** - Client, Loader, Hubble (web UI), Tools
- **HugeGraph-Computer** - Distributed OLAP graph processing
- **HugeGraph-AI** - GNN, LLM/RAG components

## Troubleshooting

**Build errors related to missing versions**
- Run `npm run docs:versions:prepare` to generate versioned docs before building

**Docusaurus fails to start**
- Ensure Node.js v18+ is installed
- Run `npm install` to install dependencies
- Run `npm run clear` to clear Docusaurus cache
