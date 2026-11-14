# Homepage design and verification

## Interaction and appearance

The first viewport holds the introduction, primary action and four selectable graph layers.
On scroll, the database plate unfolds into a graph. The six central vertices keep their positions as the canvas takes over.
Scrolling forward or backward moves between the database, toolchain, computing and AI explanations.
Selecting a layer moves directly to its explanation. Keyboard activation places focus on its guide link.

The entry gradient settles on the same surface as the overview and scrolled header, pale gray in light mode and navy in dark mode.
The canvas follows the native appearance control, including when the reader changes themes midway through a scene.
On narrow or short screens the layer names move into a compact legend.
Reduced motion presents the four explanations in document order. Print uses the same reading order on a white background.

## Content and implementation

- Edit localized headings, descriptions, metrics and destinations in the [English](data/landing/en.yaml) and [Chinese](data/landing/cn.yaml) data files.
  The [homepage template](layouts/_partials/landing/story.html) renders the story, metrics, feature cards, platform logos, component guides and quick start.
- Keep platform names and logo IDs aligned between the [platform list](data/landing/platforms.yaml) and [SVG sprite](assets/img/landing-platforms.svg).
- The [stylesheet](assets/css/landing-story.css) defines the stack, hero decorations, responsive layout, themes and print view.
  The [interaction script](assets/js/landing-story.js) handles layer selection, scroll progress, canvas drawing and changes to motion preferences.
- The [Markdown homepage](layouts/index.md) reads the same data. Archived Markdown homepages link to documentation available in their own release.

## Verification

Run the [strict build](contribution.md#strict-production-build) after editing homepage templates or assets.
With `SITE_ROOT` set to the absolute path of a freshly built site, run the focused Chromium checks from `tests/e2e`:

```sh
npm test -- landing.spec.js landing-motion.spec.js
```

The [homepage tests](tests/e2e/landing.spec.js) cover bilingual navigation, component links, command copying, small viewports and the graph transition.
The [motion tests](tests/e2e/landing-motion.spec.js) exercise focus and hover, switching motion preferences, canvas colors and printing.
Changes to historical Markdown also need the [versioning tests](tests/e2e/versioning.spec.js) against an assembled site with archived releases.

For visual changes, capture the desktop and narrow layouts before and after the change. Include the affected scroll position and theme in the pull request.
The [visual checks](tests/e2e/visual.spec.js) write screenshots to the workflow artifact.
