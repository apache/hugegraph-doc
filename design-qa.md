# Homepage design QA

Date: 2026-11-15 (Asia/Singapore).

## Scope and visual truth

The selected transition reference is the task image
`/workspace/generated_images/exec-da63ee44-1442-41c5-b2c5-e337f24343fd.png`
(1254 × 1254 pixels). The supplied D5 HTML is the source of the interactive
stack, graph evolution and camera timeline. The user explicitly requested that
the first viewport remain a complete hero, that later content appear on scroll,
and that the gradual graph changes remain intact. In the follow-up review, the
user specified that the blue-to-white transition belongs at the beginning of
scrolling and that all evolving graph scenes should use the original white ground.

This PR applies the chosen blue → pale-blue → near-white surface and fixes the
confirmed usability defects. The concept's compressed document composition is
not a requirement to expose the next section in the initial viewport. Native
OINK navigation, language, appearance, search, versions and AI consent remain in
place; the diagram remains live instead of becoming a raster illustration.

## Evidence and normalization

- Browser: Chromium; viewport 1440 × 1000 CSS pixels, deviceScaleFactor 1.
  Additional captures: 390 × 844, 320 × 844, 320 × 568, 844 × 390, 1200 × 900 and 1440 × 700; both EN and CN.
- Full-view comparison: `/workspace/landing-review/design-comparison.png` puts
  the selected source and the original hero/exit states in one comparison input.
  Both sides use equal display widths; the source's composite document and the
  runtime's separate scroll states are labelled. No pixel-difference claim is
  made across those intentionally different compositions.
- Focused evidence: four layer labels at 320/390px and 844 × 390; stopped
  Database/Toolchain/Computing/AI panels; the entry gradient; native Print media.
- [Before desktop](tests/e2e/screenshots/landing/before-en-1440.jpg) /
  [after desktop](tests/e2e/screenshots/landing/after-en-1440.jpg).
- [Before 320px](tests/e2e/screenshots/landing/before-en-320.jpg) /
  [after 320px](tests/e2e/screenshots/landing/after-en-320.jpg).
- [Short portrait](tests/e2e/screenshots/landing/after-en-short.jpg).
- [Chinese](tests/e2e/screenshots/landing/after-cn-1440.jpg),
  [graph toolchain](tests/e2e/screenshots/landing/after-toolchain.jpg),
  [entry transition](tests/e2e/screenshots/landing/after-transition.jpg).
- Real browser recording: `/workspace/landing-review/animation.webm` (15 s).

## Comparison history and fixes

1. Initial integration had inherited section padding, clipped mobile labels,
   and a selector-specificity error hiding the text veil and story navigation.
   Reset the authored story padding, restore label geometry, and use a
   low-specificity initial hidden rule. Fresh captures confirm a complete first
   viewport, four visible layer names and readable text over the moving graph.
2. Native Print retained the pinned scene and hid its inactive explanations.
   Print now uses natural flow, exposes all four explanations and hides the
   animated canvas/controls. Browser Print-media inspection confirms all four
   panels have opacity 1 and visible text, with a static stage and white ground.
3. The small-screen AI launcher overlapped the restored layer legend. Its
   homepage-only position now uses the safe bottom edge; the final 390px capture
   shows separated hit areas. Documentation pages retain their existing layout.
4. The follow-up places the gradient in the initial lift-off (scroll progress
   0.0075–0.095), before the canvas appears at 0.105. A pale-to-white background
   rises behind the existing geometry and reverses with scrolling. All four
   graph scenes use the original ink-on-white palette, with a matching white
   text veil and pale floating controls. The delayed exit gradient is removed.
5. CI exposed current-only component links in archived Markdown homepages.
   Archived homes now retain their native documentation/LLMS index, while the
   current homepage retains its full catalogue. Regression checks cover all
   four archived releases in both languages without weakening link validation.
6. Independent review found clipped labels at 320 × 568 and launcher overlap
   after compacting the diagram. Short portrait now uses compact spacing, a
   full-width label grid independent of the diagram, and separates the launcher
   from the labels. Compact labels also appear at desktop widths when the
   diagram lacks room for side labels; they sit above plate hit areas.
   Regressions check visibility, launcher intersections and left/center/right
   hit targets, including 1200 × 900 and 1440 × 700.
7. Layer buttons use a white keyboard focus outline on the blue hero. Changing
   reduced-motion preference while the page is open now disposes the previous
   mode's listeners, observers and animation frame, switches to
   readable static scenes, and restores the current explanation when animation
   is enabled again. The page does not reload. The Docker example binds only
   to loopback for local development.

## Required fidelity surfaces

- **Fonts and typography:** retain the site's Inter heading and native body
  stacks, with a 700-weight display heading, readable body copy and localized
  Chinese fallbacks. Hero wrapping and controls remain readable at tested sizes.
  This deliberately reuses site fonts instead of embedding prototype fonts.
- **Spacing and rhythm:** complete initial viewport; aligned copy, diagram and
  downstream sections; all layer names fit on narrow and short screens. The
  blue-to-white transition completes before the progressive graph story.
- **Colors and tokens:** vivid violet/blue hero, white primary action, fixed
  semantic layer colors and white graph scenes. Dark appearance retains this
  authored scene palette and uses the native dark reading background.
- **Image and diagram quality:** existing brand assets and icon library are
  reused. The supplied live vector/canvas geometry is retained for real graph
  morphing, with consistent material and semantic accents. A static generated
  diagram would remove functionality explicitly required by the user.
- **Copy and content:** EN/CN cover every new visible section and feedback state.
  Components link to their own guides; the command uses the documented image
  with loopback-only port binding and offers the next step. Semantic Markdown and native printing retain content.

## Interaction verification

The new browser regressions cover first-viewport CTA/section placement, genuine
language navigation and persistence, eight component destinations, complete
clipboard content/status, reduced motion, 320px drawer reachability/Escape/focus,
visible layer names including landscape, and distinct nonempty graph frames
with one readable explanation at every sampled stop. The entry transition is
also checked before canvas hand-off, throughout all four scenes and in reverse.
Selecting a layer eases the camera to its stop. Reduced motion opens the corresponding explanation immediately.
Browser checks cover clicks on the slab itself,
rapid switches, keyboard focus and scrolling immediately after selection. Motion-preference regressions check
absence of hidden canvas painting, static navigation, repeated mode switches
and preservation of the current explanation and downstream reading position. Native theme, search and
AI enabled/disabled fixtures are checked by the existing browser suites.

Independent review confirmed the fixes. Browser checks cover the progression
from the database through toolchain and computing to AI, localized
Chinese counts, dark appearance and reduced-motion canvases, without page errors
or failed main-page requests. All assets load locally; the new runtime does not
make third-party requests. Native AI consent behavior is unchanged.

## Follow-up polish and limits

- The first Concept B prototype supplies the opaque faces and colored edges. The toolchain layer depicts data import and exploration.
  With the pointer at rest, the database traces edges, the toolchain imports rows, the compute layer scans and the AI nodes pulse.
  System reduced motion disables all four loops. The database face keeps its central vertices aligned with the scroll-driven graph.
- Device checks use Chromium emulation, not real-device Safari or a complete
  screen-reader certification.

## Implementation checklist

- [x] Keep the complete blue first viewport and progressive graph story.
- [x] Apply the selected transition at the start, before graph evolution.
- [x] Fix text overlap, narrow/short viewport failures and layer-label clipping.
- [x] Reuse native language, theme, navigation and consent controls.
- [x] Add component guide links, copy feedback and the next action.
- [x] Preserve bilingual Markdown, reduced motion and native printing.
- [x] Compare source and rendered evidence; resolve actionable P1/P2 findings.

final result: passed
