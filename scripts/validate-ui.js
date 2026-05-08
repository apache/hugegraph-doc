#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const {spawn, spawnSync} = require('child_process');
const {chromium} = require('playwright');

const repoRoot = path.resolve(__dirname, '..');
const buildDir = path.join(repoRoot, 'build');
const artifactDir = path.join(repoRoot, 'artifacts', 'playwright');
const port = Number(process.env.DOCUSAURUS_TEST_PORT || 4173);
const baseUrl = `http://127.0.0.1:${port}`;

function ensureBuild() {
  if (fs.existsSync(path.join(buildDir, 'index.html'))) {
    return;
  }
  const result = spawnSync('npm', ['run', 'build'], {cwd: repoRoot, stdio: 'inherit'});
  if (result.status !== 0) {
    process.exit(result.status || 1);
  }
}

async function waitForServer(server) {
  const deadline = Date.now() + 30000;
  while (Date.now() < deadline) {
    if (server.exitCode !== null) {
      throw new Error(`Docusaurus server exited with code ${server.exitCode}`);
    }
    try {
      const response = await fetch(baseUrl);
      if (response.ok) {
        return;
      }
    } catch {
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
  }
  throw new Error('Timed out waiting for Docusaurus test server');
}

async function expectVisible(locator, label) {
  try {
    await locator.first().waitFor({state: 'visible', timeout: 5000});
  } catch {
    throw new Error(`${label} is not visible`);
  }
}

async function assertShell(page) {
  await page.goto(`${baseUrl}/`, {waitUntil: 'networkidle'});
  await expectVisible(page.locator('nav.navbar'), 'top navigation');

  const asfDropdown = page.locator('.navbar__item.dropdown', {hasText: 'ASF'}).first();
  await asfDropdown.hover();
  await page.waitForTimeout(200);
  const asfText = await asfDropdown.textContent();
  for (const label of ['Foundation', 'License', 'Events', 'Privacy', 'Security', 'Sponsorship', 'Thanks', 'Code of Conduct']) {
    if (!asfText.includes(label)) {
      throw new Error(`ASF dropdown is missing ${label}`);
    }
  }

  const footer = page.locator('footer.footer');
  await footer.scrollIntoViewIfNeeded();
  await expectVisible(footer.locator('img[alt*="Apache Software Foundation"]'), 'Apache/ASF footer logo');
  const footerText = await footer.textContent();
  for (const text of ['Copyright', 'Apache License, Version 2.0', 'trademarks', 'The Apache Software Foundation']) {
    if (!footerText.includes(text)) {
      throw new Error(`Footer is missing "${text}"`);
    }
  }
}

async function assertDocs(page) {
  await page.goto(`${baseUrl}/docs/`, {waitUntil: 'networkidle'});
  const navbar = page.locator('nav.navbar');
  const navbarText = await navbar.textContent();
  for (const label of ['Documentation', 'Next', 'Stable (1.7.0)', '1.5.0', '1.3.0', '1.2.0', '1.0.0', '0.11', '0.10']) {
    if (!navbarText.includes(label)) {
      throw new Error(`Docs navbar is missing version label ${label}`);
    }
  }

  await page.goto(`${baseUrl}/docs/quickstart/hugegraph/hugegraph-server/`, {waitUntil: 'networkidle'});
  const sidebar = page.locator('aside.theme-doc-sidebar-container');
  await expectVisible(sidebar, 'docs sidebar');
  const quickStart = sidebar.getByText('Quick Start').first();
  await expectVisible(quickStart, 'docs sidebar Quick Start item');

  await page.goto(`${baseUrl}/docs/next/`, {waitUntil: 'networkidle'});
  await expectVisible(page.getByText('This is unreleased documentation'), 'next docs unreleased banner');
}

async function assertArchivedDocsPruned(page) {
  for (const versionPath of ['docusaurus-1.5.0', 'docusaurus-1.3.0', 'docusaurus-1.0.0', 'docusaurus-0.11']) {
    await page.goto(`${baseUrl}/docs/${versionPath}/`, {waitUntil: 'networkidle'});
    const sidebarText = await page.locator('aside.theme-doc-sidebar-container').textContent();
    for (const duplicateSection of ['Contribution Guidelines', 'Download', 'CLA']) {
      if (sidebarText.includes(duplicateSection)) {
        throw new Error(`Archived docs ${versionPath} still shows duplicate ${duplicateSection} section`);
      }
    }
  }

  for (const route of [
    '/docs/docusaurus-1.5.0/download/',
    '/docs/docusaurus-1.5.0/CLA/',
    '/docs/docusaurus-1.5.0/contribution-guidelines/',
    '/docs/docusaurus-0.11/download/',
  ]) {
    const response = await page.goto(`${baseUrl}${route}`, {waitUntil: 'networkidle'});
    if (!response || response.status() !== 404) {
      throw new Error(`Archived duplicate docs route should be removed: ${route}`);
    }
  }
}

async function assertDocumentationDropdown(page) {
  await page.setViewportSize({width: 1440, height: 900});
  await page.goto(`${baseUrl}/docs/`, {waitUntil: 'networkidle'});

  const dropdown = page.locator('.documentationDropdown').first();
  const button = dropdown.locator('button').first();
  const menu = dropdown.locator('.documentationDropdown__menu').first();
  const nextItem = dropdown.getByRole('menuitem', {name: 'Next'});

  await button.hover();
  await expectVisible(nextItem, 'Documentation dropdown Next item');

  const buttonBox = await button.boundingBox();
  const nextItemBox = await nextItem.boundingBox();
  if (!buttonBox || !nextItemBox) {
    throw new Error('Documentation dropdown bounding boxes are unavailable');
  }

  await page.mouse.move(buttonBox.x + buttonBox.width / 2, buttonBox.y + buttonBox.height - 1);
  await page.mouse.move(nextItemBox.x + nextItemBox.width / 2, nextItemBox.y + nextItemBox.height / 2, {steps: 8});
  await page.waitForTimeout(240);
  await expectVisible(nextItem, 'Documentation dropdown remains open while moving into menu');

  await button.click();
  await page.mouse.move(20, 240);
  await page.waitForTimeout(240);
  await expectVisible(nextItem, 'Documentation dropdown remains open after click');

  await page.mouse.click(20, 240);
  await menu.waitFor({state: 'hidden', timeout: 2000});
}

async function assertCommunityPages(page) {
  await page.goto(`${baseUrl}/team/`, {waitUntil: 'networkidle'});
  await expectVisible(page.getByRole('heading', {name: 'Apache HugeGraph Team'}), 'team page heading');
  await expectVisible(page.getByText('PMC Members').first(), 'team page PMC section');

  await page.goto(`${baseUrl}/users/`, {waitUntil: 'networkidle'});
  await expectVisible(page.getByRole('heading', {name: 'HugeGraph User Showcase'}), 'users page heading');
  await expectVisible(page.getByText('Baidu').first(), 'users page case card');
}

async function assertMobileMenu(page) {
  await page.setViewportSize({width: 390, height: 844});
  await page.goto(`${baseUrl}/`, {waitUntil: 'networkidle'});
  await page.locator('.navbar__toggle').click();
  const sidebar = page.locator('.navbar-sidebar');
  await expectVisible(sidebar, 'mobile navbar sidebar');
  const text = await sidebar.textContent();
  for (const label of ['Documentation', 'Blog', 'Community', 'Team', 'Users', 'ASF']) {
    if (!text.includes(label)) {
      throw new Error(`Mobile menu is missing ${label}`);
    }
  }

  const dropdown = sidebar.locator('.documentationDropdown').first();
  const button = dropdown.locator('button').first();
  const menu = dropdown.locator('.documentationDropdown__menu').first();
  await button.click();

  for (const label of ['Next', 'Stable (1.7.0)', '1.5.0', '1.3.0', '1.2.0', '1.0.0', '0.11', '0.10']) {
    await expectVisible(dropdown.getByRole('menuitem', {name: label}), `mobile Documentation dropdown ${label} item`);
  }

  const buttonBox = await button.boundingBox();
  const menuBox = await menu.boundingBox();
  if (!buttonBox || !menuBox) {
    throw new Error('Mobile Documentation dropdown bounding boxes are unavailable');
  }
  if (menuBox.y < buttonBox.y + buttonBox.height - 1) {
    throw new Error('Mobile Documentation dropdown is not positioned under its nav item');
  }
  if (menuBox.width > 220 || menuBox.height > 260) {
    throw new Error(`Mobile Documentation dropdown is too large: ${Math.round(menuBox.width)}x${Math.round(menuBox.height)}`);
  }
  if (menuBox.x < 0 || menuBox.x + menuBox.width > 390 || menuBox.y + menuBox.height > 844) {
    throw new Error('Mobile Documentation dropdown overflows the viewport');
  }
  const overflowY = await menu.evaluate((element) => window.getComputedStyle(element).overflowY);
  if (overflowY !== 'auto') {
    throw new Error(`Mobile Documentation dropdown should be scrollable when needed, got overflow-y=${overflowY}`);
  }
}

async function captureScreenshots(page) {
  fs.mkdirSync(artifactDir, {recursive: true});
  const viewports = [
    ['desktop', {width: 1440, height: 900}],
    ['mobile', {width: 390, height: 844}],
  ];
  const pages = [
    ['homepage', '/'],
    ['docs-landing', '/docs/'],
    ['deep-docs', '/docs/quickstart/hugegraph/hugegraph-server/'],
    ['team', '/team/'],
    ['users', '/users/'],
  ];

  for (const [viewportName, viewport] of viewports) {
    await page.setViewportSize(viewport);
    for (const [name, route] of pages) {
      await page.goto(`${baseUrl}${route}`, {waitUntil: 'networkidle'});
      await page.screenshot({
        path: path.join(artifactDir, `${name}-${viewportName}.png`),
        fullPage: false,
      });
    }

    await page.goto(`${baseUrl}/`, {waitUntil: 'networkidle'});
    await page.locator('footer.footer').scrollIntoViewIfNeeded();
    await page.screenshot({
      path: path.join(artifactDir, `footer-${viewportName}.png`),
      fullPage: false,
    });
  }
}

async function main() {
  ensureBuild();

  const bin = path.join(repoRoot, 'node_modules', '.bin', 'docusaurus');
  const server = spawn(bin, ['serve', '--host', '127.0.0.1', '--port', String(port)], {
    cwd: repoRoot,
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  server.stdout.on('data', (data) => process.stdout.write(data));
  server.stderr.on('data', (data) => process.stderr.write(data));

  try {
    await waitForServer(server);
    const browser = await chromium.launch();
    const page = await browser.newPage({viewport: {width: 1440, height: 900}});
    await assertShell(page);
    await assertDocs(page);
    await assertArchivedDocsPruned(page);
    await assertDocumentationDropdown(page);
    await assertCommunityPages(page);
    await assertMobileMenu(page);
    await captureScreenshots(page);
    await browser.close();
  } finally {
    server.kill('SIGTERM');
  }

  console.log(`UI validation OK. Screenshots: ${path.relative(repoRoot, artifactDir)}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
