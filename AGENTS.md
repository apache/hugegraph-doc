# AGENTS.md

This file provides guidance to AI coding assistants (Claude Code, Cursor, GitHub Copilot, etc.) when working with code in this repository.

## Project Overview

Apache HugeGraph documentation website built with Hugo static site generator and the Docsy theme. The site is bilingual (Chinese/English) and covers the complete HugeGraph graph database ecosystem.

## Development Commands

```bash
# Install dependencies
npm install

# Start development server (auto-reload enabled)
hugo server

# Build production site (output to ./public)
hugo --minify

# Clean build
rm -rf public/

# Production build with garbage collection
HUGO_ENV="production" hugo --gc

# Custom server configuration
hugo server -b http://127.0.0.1 -p 80 --bind=0.0.0.0
```

## Prerequisites

- **Hugo Extended** v0.95.0 recommended (v0.102.3 in CI) - must be the "extended" version for SASS/SCSS support
- **Node.js** v16+ and npm
- Download Hugo from: https://github.com/gohugoio/hugo/releases

## Architecture

```
content/
├── cn/          # Chinese documentation (default language)
│   ├── docs/    # Main documentation
│   ├── blog/    # Blog posts
│   ├── community/
│   └── about/
└── en/          # English documentation (parallel structure)

themes/docsy/    # Docsy theme (submodule)
layouts/         # Custom template overrides
assets/          # Processed assets (SCSS, images)
static/          # Static files served directly
config.toml      # Main site configuration
```

### Content Structure

Documentation sections in `content/{cn,en}/docs/`:
- `quickstart/` - Getting started guides for HugeGraph components
- `config/` - Configuration documentation
- `clients/` - Client API documentation (Gremlin, RESTful)
- `guides/` - User guides and tutorials
- `performance/` - Benchmarks and optimization
- `language/` - Query language docs
- `contribution-guidelines/` - Contributing guides
- `changelog/` - Release notes
- `download/` - Download instructions

## Key Configuration Files

- `config.toml` - Site-wide settings, language config, menu structure, version (currently 0.13)
- `package.json` - Node dependencies for CSS processing (postcss, autoprefixer, mermaid)
- `.editorconfig` - UTF-8, LF line endings, spaces for indentation

## Working with Content

When editing documentation:
1. Maintain parallel structure between `content/cn/` and `content/en/`
2. Use Markdown with Hugo front matter (title, weight, description)
3. For bilingual changes, update both Chinese and English versions
4. Include mermaid diagrams where appropriate (mermaid.js is available)

## Deployment

- **CI/CD**: GitHub Actions (`.github/workflows/hugo.yml`)
- **Trigger**: Push to `master` branch or pull requests
- **Build**: `npm i && hugo --minify` with Node v16 and Hugo v0.102.3 extended
- **Deploy**: Publishes to `asf-site` branch (GitHub Pages)
- **PR Requirements**: Include screenshots showing before/after changes

## HugeGraph Ecosystem Context

This documentation covers:
- **HugeGraph-Server** - Core graph database with REST API
- **HugeGraph-Store** - Distributed storage engine
- **HugeGraph-PD** - Placement Driver for metadata
- **Toolchain** - Client, Loader, Hubble (web UI), Tools
- **HugeGraph-Computer** - Distributed OLAP graph processing
- **HugeGraph-AI** - GNN, LLM/RAG components

## Troubleshooting

**"TOCSS: failed to transform scss/main.scss"**
- Install Hugo Extended (not standard Hugo)

**Theme/module not found**
- Run: `git submodule update --init --recursive`

**CI build fails but works locally**
- Match Hugo version (v0.102.3) and Node.js (v16)
- Verify npm dependencies are installed
