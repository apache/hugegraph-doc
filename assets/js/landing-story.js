/**
 * HugeGraph homepage: progressive stack-to-graph story from the reviewed D5 prototype.
 * The authored scene remains interactive; OINK continues to own navigation, language and appearance.
 */
(() => {
  'use strict';
  const landing = document.getElementById('hg-landing');
  if (!landing) return;
  landing.classList.add('js');
  landing.classList.toggle('live', !matchMedia('(prefers-reduced-motion: reduce)').matches);

/* HugeGraph isometric stack module (Stack v5). Exposes window.HGStack:
     setActive(index | id | null)   lift one layer and dim the others (same visual as hover); also clears any user hover
     setInteractive(bool)           false: ignore hover, focus and click activation and drop any user-made active state
                                    (a host that scrubs the stack owns it); true: listen again, but a resting pointer
                                    only counts once it really moves
     setSpread(value, immediate)    0 = collapsed block, 1 = exploded; pass immediate = true when scrubbing from scroll
     setPaused(bool)                stop or resume the idle loops
     layers                         [{ index, id, name, components, description }] bottom to top
     root                           the #hg-stack element
     geom                           the design geometry that stack.css uses (degrees and design units)
   Fires "hgstack:active" (detail: { index, id, layer }) on the root when the user changes the active layer.
   Slab faces and labels are click targets ([data-layer]); what a click does is up to the host page. */
(() => {
  const root = landing.querySelector('#hg-stack');
  if (!root) return;
  const $$ = s => [...root.querySelectorAll(s)];
  const layerEls = $$('.hgs-layer'), labs = $$('.hgs-lab');
  const text = (el, s) => { const n = el && el.querySelector(s); return n ? n.textContent.trim() : ''; };
  const layers = layerEls.map(el => {
    const lab = labs.find(l => l.dataset.layer === el.dataset.layer);
    return {
      index: Number(el.dataset.layer), id: el.dataset.id, name: text(lab, '.hgs-lab-name'),
      components: text(lab, '.hgs-lab-parts').split(',').map(s => s.trim()).filter(Boolean),
      description: text(lab, '.hgs-lab-desc'),
    };
  }).sort((a, b) => a.index - b.index);

  const norm = v => {
    if (v === null || v === undefined || v === '') return null;
    const hit = layers.find(l => l.index === Number(v) || l.id === v);
    return hit ? hit.index : null;
  };

  // Manual selection takes priority over the idle tour.
  const tour = [null, ...layers.map(layer => layer.index).reverse()];
  let tourStep = 0, tourTimer = 0, pointerInside = false;
  let base = null, hover = null, focused = null, shown;
  function render(fromUser) {
    const a = (interactive ? hover ?? focused : null) ?? base ?? tour[tourStep];
    if (a === shown) return;
    shown = a;
    root.classList.toggle('hgs-has-active', a !== null);
    root.dataset.active = a === null ? '' : layers[a].id;
    for (const el of [...layerEls, ...labs]) {
      const i = Number(el.dataset.layer);
      el.classList.toggle('is-active', i === a);
      el.classList.toggle('is-above', a !== null && i > a);
      el.classList.toggle('is-below', a !== null && i < a);
    }
    if (fromUser) {
      const layer = a === null ? null : layers[a];
      root.dispatchEvent(new CustomEvent('hgstack:active', { bubbles: true, detail: { index: a, id: layer ? layer.id : null, layer } }));
    }
  }
  const setActive = v => { base = norm(v); hover = null; drop(); render(false); };
  const userActive = v => { hover = norm(v); render(true); };

  /* Hover intent: a short dwell before a hover takes effect, so crossing a layer on the way to another one does not flicker.
     While the module is not interactive nothing the pointer or the keyboard does changes the active layer. After it becomes
     interactive again, a pointer that is merely resting on the stack does not count: it has to move first, so the stack does
     not jump when a page scrolls back under a parked pointer. */
  const hoverable = matchMedia('(hover: hover)').matches;
  const target = e => { const t = e.target.closest('[data-layer]'); return t && root.contains(t) ? t : null; };
  let want = null, timer = 0, pending = false, interactive = true, armed = true, px = -1, py = -1, ax = -1, ay = -1;
  const drop = () => { clearTimeout(timer); pending = false; };
  const intend = (v, delay) => { drop(); want = v; pending = true; timer = setTimeout(() => { pending = false; if (interactive) userActive(want); }, delay); };
  const now = v => { drop(); if (interactive) userActive(v); };
  const over = e => {
    if (!interactive || !armed) return;
    const t = target(e), idx = t ? norm(t.dataset.layer) : null;
    if (idx === hover) { drop(); return; }
    if (pending && want === idx) return;
    intend(idx, idx === null ? 140 : hover === null ? 40 : 75);
  };
  if (hoverable) {
    root.addEventListener('mouseenter', () => { pointerInside = true; syncTour(); });
    root.addEventListener('mousemove', e => {
      px = e.clientX; py = e.clientY;
      if (!armed) { if (Math.hypot(px - ax, py - ay) < 3) return; armed = true; }
      over(e);
    });
    root.addEventListener('mouseleave', () => {
      pointerInside = false;
      if (interactive && (hover !== null || pending)) intend(null, 140);
      syncTour();
    });
    addEventListener('mousemove', e => { px = e.clientX; py = e.clientY; }, { passive: true });
  }
  root.addEventListener('click', e => { const t = target(e); if (t) { armed = true; now(t.dataset.layer); } });
  if (!hoverable) document.addEventListener('click', e => { if (!target(e)) now(null); });
  labs.forEach(l => {
    l.addEventListener('focus', () => {
      focused = l.matches(':focus-visible') ? norm(l.dataset.layer) : null;
      if (focused !== null) now(null);
    });
    l.addEventListener('blur', () => {
      focused = null;
      if (!pointerInside) now(null);
      else render(true);
    });
  });
  root.addEventListener('focusin', syncTour);
  root.addEventListener('focusout', () => queueMicrotask(syncTour));

  function setInteractive(v) {
    v = Boolean(v);
    if (v === interactive) return;
    interactive = v;
    root.classList.toggle('hgs-inert', !v);
    drop();
    if (!v) { hover = null; render(false); }
    else { armed = false; ax = px; ay = py; }
    syncTour();
  }

  let scrubFrame = 0;
  function setSpread(value, immediate) {
    const v = Math.min(1, Math.max(0, Number(value) || 0));
    if (immediate) {
      root.classList.add('hgs-scrub');
      cancelAnimationFrame(scrubFrame);
      scrubFrame = requestAnimationFrame(() => requestAnimationFrame(() => root.classList.remove('hgs-scrub')));
    }
    root.style.setProperty('--spread', v.toFixed(4));
  }

  let userPaused = false, offscreen = false;
  function syncTour() {
    clearTimeout(tourTimer);
    if (!interactive || userPaused || offscreen || document.hidden) {
      tourStep = 0;
      render(false);
      return;
    }
    if (pointerInside || root.matches(':focus-within') || !root.classList.contains('hgs-live')) return;
    tourTimer = setTimeout(() => {
      tourStep = (tourStep + 1) % tour.length;
      render(false);
      syncTour();
    }, 3200);
  }
  document.addEventListener('visibilitychange', syncTour);
  const syncPaused = () => {
    root.classList.toggle('hgs-paused', userPaused || offscreen);
    syncTour();
  };
  const setPaused = v => { userPaused = Boolean(v); syncPaused(); };
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(([e]) => { offscreen = !e.isIntersecting; syncPaused(); }).observe(root);
  }

  // Assembly: plates settle in bottom first, then transitions lose their stagger.
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  requestAnimationFrame(() => requestAnimationFrame(() => {
    root.classList.add('hgs-ready');
    setTimeout(() => {
      root.classList.add('hgs-live');
      syncTour();
    }, reduce ? 0 : 1700);
  }));

  const geom = { tilt: 62, turn: 45, face: 380, gap: 95.25, slab: 16, cx: 300, cy: 428, box: [600, 600], labels: 192 };
  window.HGStack = { setActive, setInteractive, setSpread, setPaused, layers, root, geom };
})();


/* Concept D5 (stack v6, drawn glass; light and dark themes): one pinned scene. render(progress) = the graph lifts off the Graph Database plate, then the story pulls back.
   Timeline in scroll progress p (0..1 across the 720vh pinned section):
     0.000 - 0.0075 nothing moves: a small accidental scroll leaves the hero, and the stack's hover and click, as they were
     0.0075 - 0.036 the stack labels leave; hero copy fades as the first explanation arrives
     0.011 - 0.058  the other three plates drift slightly apart and fade, with the corner guides
     0.018 - 0.100  the plate turns from isometric to face-on (tilt only), at 1.0x to 1.3x of its hero size
     0.042 - 0.095  the Graph Database plate dissolves; its six-vertex graph is left floating on the page
     0.105 - 0.127  hand-off: the canvas draws the same graph in the same place and style, then the DOM stack fades out
     0.125 - 0.31   beat 1, Graph Database: further neighbours grow out of the first vertex, the camera starts to pull back
     0.31  - 0.53   beat 2, Toolchain: explore two labeled relationships in the sample graph
     0.53  - 0.80   beat 3, Graph Computing: community detection colors the surrounding graph
     0.80  - 1.00   beat 4, Graph AI: the camera holds, the field dims, one question path and its retrieved neighbours light up
   After the hand-off the camera only ever pulls back. render() is driven by a smoothed copy of the scroll position, so wheel
   notches do not step the camera. Once the lift-off starts the story owns the stack (HGStack.setInteractive(false)).
   Selecting a layer eases into its stop. Manual scrolling still plays the complete progression.
   Theme: the canvas reads site-owned CSS tokens and follows OINK appearance changes without replacing its theme controller.
   The graph scene and its text follow the native appearance setting. */
(() => {
  'use strict';
  const html = document.documentElement;
  const stillMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const printMedia = matchMedia('print');
  let printing = false, screenY = scrollY;
  const isPrinting = () => printing || printMedia.matches;
  function syncPrintLayout() {
    if (printMedia.matches) beforePrint();
    else afterPrint();
  }
  const $ = (s, r = landing) => r.querySelector(s), $$ = (s, r = landing) => [...r.querySelectorAll(s)];
  let config = {};
  try { config = JSON.parse(landing.dataset.hgStoryConfig || '{}'); } catch { /* use authored defaults */ }
  const readoutText = (key, fallback, values = {}) => {
    const template = typeof config.readouts?.[key] === 'string' ? config.readouts[key] : fallback;
    return template.replace(/\{(vertices|communities)\}/g, (_, name) => String(values[name] ?? ''));
  };
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const sstep = (a, b, v) => { const u = clamp((v - a) / (b - a), 0, 1); return u * u * (3 - 2 * u); };
  const lerp = (a, b, u) => a + (b - a) * u;

  /* ---------- world: the sample graph from the stack face, its neighbourhood, communities, then the field ---------- */
  let seed = 11;
  const R = () => { seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const gauss = () => (R() + R() + R() + R() - 2) / 0.577;
  /* One palette per theme, everything the canvas draws with. col = data colours (logo green, blue, violet + a neutral).
     Light: ink dots on paper. Dark: points of light on a night ground, so the same hues are lifted until they glow against
     #0a0d14 (each is above 8:1 on it), hulls become soft glows instead of filled discs, vertices get a small halo,
     and the field varies in brightness like a deep sky. All numbers are alphas or 0..1 switches, so two palettes can be mixed. */
  const THEMES = {
    light: { col: [[51, 188, 122], [34, 158, 250], [153, 72, 247], [100, 112, 125]], halo: [34, 158, 250], haloA: 0.5,
             hullA: 0.1, hullGlow: 0, glow: 0, star: 0, fieldLine: 0.13, fieldCol: 0.85, fieldNeutral: 0.6, fieldDim: 0.62,
             edgeA: 0.3, linkA: 0.2, tintA: 0.42, nodeA: 0.82, nameA: 0.72, pathW: 8, pathGlow: 0.12, nearA: 0.32, ringA: 0.75 },
    dark:  { col: [[98, 216, 162], [112, 188, 255], [184, 150, 255], [150, 162, 190]], halo: [143, 157, 255], haloA: 0.6,
             hullA: 0, hullGlow: 0.24, glow: 1, star: 1, fieldLine: 0.1, fieldCol: 0.8, fieldNeutral: 0.5, fieldDim: 0.72,
             edgeA: 0.36, linkA: 0.24, tintA: 0.5, nodeA: 0.92, nameA: 0.8, pathW: 12, pathGlow: 0.2, nearA: 0.42, ringA: 0.85 },
  };
  const themeNow = () => {
    const nativeTheme = html.getAttribute('data-bs-theme');
    return nativeTheme === 'dark' || (!nativeTheme && matchMedia('(prefers-color-scheme: dark)').matches) ? 'dark' : 'light';
  };
  const PAL = JSON.parse(JSON.stringify(THEMES[themeNow()]));
  const COL = PAL.col;
  /* Colours the canvas shares with the page and with the stack face. They are read from the CSS tokens (readTokens), so the
     canvas draws the sample graph exactly as the stack face does at the hand-off, in either theme. */
  const INK = [20, 26, 51], ACCENT = [67, 48, 212];
  const faceAccent = [138, 63, 240], faceRing = [166, 157, 240];
  const parseColor = v => {
    v = String(v || '').trim();
    let m = /^#([0-9a-f]{3})$/i.exec(v); if (m) return [...m[1]].map(c => parseInt(c + c, 16));
    m = /^#([0-9a-f]{6})/i.exec(v); if (m) return [0, 2, 4].map(i => parseInt(m[1].slice(i, i + 2), 16));
    m = /^rgba?\(([^)]+)\)/i.exec(v); if (m) return m[1].split(/[\s,\/]+/).slice(0, 3).map(Number);
    return null;
  };
  const TOK = [[INK, 0, '--ink'], [ACCENT, 0, '--accent'], [faceAccent, 1, '--hgs-accent'], [faceRing, 1, '--hgs-accent-soft']];
  const readTokens = () => {
    const st = $('.hgs-layer[data-id="database"]'), cs = [getComputedStyle(landing), st ? getComputedStyle(st) : null];
    return TOK.map(([dst, on, name]) => { const c = cs[on] && parseColor(cs[on].getPropertyValue(name)); return c && c.every(Number.isFinite) ? c : dst.slice(); });
  };
  /* Everything that changes with the theme, as one flat list of numbers, so a theme change can be interpolated. */
  const NUMS = Object.keys(THEMES.light).filter(k => typeof THEMES.light[k] === 'number');
  const flat = (pal, toks) => [].concat(...pal.col, pal.halo, NUMS.map(k => pal[k]), ...toks);
  const unflat = v => {
    let i = 0; const take = dst => { dst[0] = v[i++]; dst[1] = v[i++]; dst[2] = v[i++]; };
    PAL.col.forEach(take); take(PAL.halo); NUMS.forEach(k => { PAL[k] = v[i++]; }); TOK.forEach(t => take(t[0]));
  };
  const themeTarget = () => flat(THEMES[themeNow()], readTokens());
  let themeRaf = 0, onPalette = () => {};
  /* Bring the canvas palette to the current theme: at once, or interpolated over ms. onPalette redraws whatever is on screen. */
  function syncTheme(ms) {
    cancelAnimationFrame(themeRaf);
    const from = flat(PAL, TOK.map(t => t[0].slice())), to = themeTarget();
    if (!ms) { unflat(to); onPalette(); return; }
    const start = performance.now();
    const step = now => {
      const u = clamp((now - start) / ms, 0, 1), e = u * u * (3 - 2 * u);
      unflat(from.map((a, i) => a + (to[i] - a) * e)); onPalette();
      if (u < 1) themeRaf = requestAnimationFrame(step);
    };
    themeRaf = requestAnimationFrame(step);
  }
  unflat(themeTarget());
  const rgb = (c, a) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;
  const mix = (a, b, m) => [a[0] + (b[0] - a[0]) * m, a[1] + (b[1] - a[1]) * m, a[2] + (b[2] - a[2]) * m];

  /* The Graph Database face of the stack draws a six-vertex graph in a 380-unit space (see stack.html): r = 7.2 with a ring
     of r = 13.5 for the emphasised vertex, r = 5.6 for the rest, 2 wide edges. One face unit is U world units, and the world
     is the face turned 45deg (the stack's rotateZ), so the face-on stack and the canvas agree on every position and size
     at the hand-off. In the story the same vertices are only a little larger, so the hand-off is nearly invisible. */
  const U = 0.009, FACE = { marko: [167, 191], vadas: [148, 240], josh: [184, 136], lop: [128, 136], ripple: [232, 122], peter: [96, 185] };
  const F_MAIN = 7.2, F_RING = 13.5, F_NODE = 5.6, F_LINE = 2;   // the face drawing, in face units
  const S_MAIN = 0.082, S_NODE = 0.052;                           // the same vertices in the story, in world units
  const Z0 = 132;                                           // camera zoom the hand-off aims for (px per world unit at k = 1)
  const faceToWorld = k => { const dx = FACE[k][0] - FACE.marko[0], dy = FACE[k][1] - FACE.marko[1]; return [(dx - dy) * Math.SQRT1_2 * U, (dx + dy) * Math.SQRT1_2 * U]; };
  const N = [], E = [];
  const add = (x, y, r, lv, c, d, more) => N.push(Object.assign({ x, y, r, lv, c, d, ph: R() * 6.283 }, more)) - 1;
  const centre = add(0, 0, S_MAIN, 0, 0, 0, { name: 'marko', m: 1 });
  const named = {};
  [['vadas', 1], ['josh', 1], ['lop', 1], ['ripple', 2], ['peter', 2]].forEach(([k, lv]) => {
    const [wx, wy] = faceToWorld(k);
    named[k] = add(wx, wy, S_NODE, lv, 0, lv === 1 ? 0.35 : 0.9, { name: k, m: 1 });
  });
  [[centre, named.vadas, 1], [centre, named.josh, 1], [centre, named.lop, 1], [named.josh, named.lop, 2], [named.josh, named.ripple, 2], [named.peter, named.lop, 2]]
    .forEach(([a, b, lv]) => E.push({ a, b, lv, m: 1 }));
  const pathNodes = [centre, named.josh, named.ripple];
  const relations = ['knows', 'created'];
  const ring = [], home = Object.values(named);
  [28, 68, 110, 196].forEach((deg, i) => {                     // further neighbours, placed in the directions the sample graph leaves free
    const a = deg / 57.296 + (R() - 0.5) * 0.2, rad = 0.95 + R() * 0.35;
    const id = add(Math.cos(a) * rad, Math.sin(a) * rad, 0.05, 1, 0, 0.35);
    ring.push(id); home.push(id); E.push({ a: centre, b: id, lv: 1, i });
  });
  ring.forEach((id, i) => {
    const n = N[id], k = 1 + (R() * 2.4 | 0), base = Math.atan2(n.y, n.x);
    for (let j = 0; j < k; j++) {
      const a = base + (j - (k - 1) / 2) * 0.62 + (R() - 0.5) * 0.24, rad = 0.75 + R() * 0.5;
      const m = add(n.x + Math.cos(a) * rad, n.y + Math.sin(a) * rad, 0.04, 2, 0, 0.9, { ri: i });
      home.push(m); E.push({ a: id, b: m, lv: 2, i });
    }
  });
  E.push({ a: ring[0], b: ring[1], lv: 2, i: 0, x: 1 }, { a: ring[1], b: ring[2], lv: 2, i: 1, x: 1 });

  const CC = [[9, -6.5, 1], [11, 5, 2], [-1.5, 9.5, 3], [-9.5, 3.5, 2], [-7.5, -8, 1], [2, -13.5, 0], [18, -1.5, 3],
              [-18, -3, 0], [7, 14.5, 1], [-11, 14, 3], [16.5, -13, 2], [-4, -20, 2], [20, 10, 0]];
  const clusters = [{ cx: 0, cy: 0, ids: home }];
  const d2 = (a, b) => (N[a].x - N[b].x) ** 2 + (N[a].y - N[b].y) ** 2;
  CC.forEach(([cx, cy, c], ci) => {
    const n = 18 + (R() * 11 | 0), sig = 1.15 + R() * 0.45, ids = [];
    for (let j = 0; j < n; j++) {
      const gx = gauss() * sig, gy = gauss() * sig;
      ids.push(add(cx + gx, cy + gy, 0.06 + R() * 0.035, 3, c, Math.min(1, Math.hypot(gx, gy) / (sig * 2)) + ci * 0.11));
    }
    ids.forEach(a => ids.filter(b => b !== a).sort((p, q) => d2(a, p) - d2(a, q)).slice(0, 2 + (R() * 1.5 | 0)).forEach(b => E.push({ a, b, lv: 3 })));
    clusters.push({ cx, cy, ids, c, sig, d: ci * 0.11 });
  });
  const seen = new Set();
  clusters.forEach((A, i) => {
    clusters.map((B, j) => [j, (A.cx - B.cx) ** 2 + (A.cy - B.cy) ** 2]).filter(v => v[0] !== i).sort((p, q) => p[1] - q[1]).slice(0, 2).forEach(([j]) => {
      const key = i < j ? i + '-' + j : j + '-' + i; if (seen.has(key)) return; seen.add(key);
      const B = clusters[j], near = (S, T) => S.ids.reduce((m, id) => ((N[id].x - T.cx) ** 2 + (N[id].y - T.cy) ** 2 < (N[m].x - T.cx) ** 2 + (N[m].y - T.cy) ** 2 ? id : m), S.ids[0]);
      E.push({ a: near(A, B), b: near(B, A), lv: 4 });
    });
  });

  /* the field: clumps of points in the data colours. A clump may sit on the question path of the AI beat (role 1)
     or be one of the neighbours that path retrieves (role 2). */
  const clumps = [];
  for (let i = 0; i < 430; i++) {
    const a = R() * 6.283, rad = 27 + 360 * Math.pow(R(), 0.8), cx = Math.cos(a) * rad * 1.3, cy = Math.sin(a) * rad * 0.85;
    const col = R() * 4 | 0, sig = 4 + R() * 6, pts = new Float32Array(32);
    for (let j = 0; j < 32; j += 2) { pts[j] = cx + gauss() * sig; pts[j + 1] = cy + gauss() * sig; }
    clumps.push({ cx, cy, col, pts, role: 0, ord: 0 });
  }
  const FL = [];
  for (const source of clumps) {
    let nearest, second;
    let nearestDistance = Infinity, secondDistance = Infinity;
    for (const candidate of clumps) {
      if (candidate === source) continue;
      const distance = (source.cx - candidate.cx) ** 2 + (source.cy - candidate.cy) ** 2;
      if (distance < nearestDistance) {
        second = nearest;
        secondDistance = nearestDistance;
        nearest = candidate;
        nearestDistance = distance;
      } else if (distance < secondDistance) {
        second = candidate;
        secondDistance = distance;
      }
    }
    FL.push(source.cx, source.cy, nearest.cx, nearest.cy, source.cx, source.cy, second.cx, second.cy);
  }
  /* question path: a walk through neighbouring clumps across the visible field, plus the clumps it pulls in */
  const ROT_END = 0.47;                                             // camera rotation once the pull-back has finished
  const PATH = [], NEAR = [];
  {
    const ce = Math.cos(ROT_END), se = Math.sin(ROT_END);
    const toWorld = (sx, sy) => [sx * ce + sy * se, -sx * se + sy * ce];
    const dist = (c, x, y) => Math.hypot(c.cx - x, c.cy - y);
    const nearest = (x, y) => clumps.reduce((m, c) => (dist(c, x, y) < dist(m, x, y) ? c : m), clumps[0]);
    const [gx, gy] = toWorld(128, -62);
    let cur = nearest(...toWorld(-118, 58));
    const goal = nearest(gx, gy);
    cur.role = 1; PATH.push(cur);
    while (cur !== goal && PATH.length < 13) {
      const here = dist(cur, goal.cx, goal.cy);
      const cand = clumps.filter(c => c.role === 0 && dist(c, goal.cx, goal.cy) < here - 12);
      if (!cand.length) break;
      const next = cand.reduce((m, c) => (dist(c, cur.cx, cur.cy) < dist(m, cur.cx, cur.cy) ? c : m), cand[0]);
      next.role = 1; next.ord = PATH.length; PATH.push(next); cur = next;
    }
    PATH.forEach((pc, i) => clumps.forEach(c => { if (c.role === 0 && dist(c, pc.cx, pc.cy) < 30) { c.role = 2; c.ord = i; NEAR.push(c); } }));
  }

  /* ---------- camera: story progress q runs 0.06 (hand-off) to 1 (pull-back done), then 1 to 1.25 for the AI beat, where the
     camera holds. z0 is the zoom that matches the face-on stack; the first beat is defined relative to it, so the zoom never
     increases: the camera only pulls back. ---------- */
  const KF = [[0.06, 1], [0.2, 0.93], [0.36, 0.85], [0.62, 0.75], [0.78, 21], [0.93, 16], [1.05, 1.95]];
  const zoom = (q, z0) => {
    const first = z0 || Z0, val = i => (i < 4 ? KF[i][1] * first : KF[i][1]);
    if (q <= KF[0][0]) return first;
    for (let i = 1; i < KF.length; i++) if (q <= KF[i][0]) {
      const u = sstep(KF[i - 1][0], KF[i][0], q);
      return Math.exp(Math.log(val(i - 1)) + (Math.log(val(i)) - Math.log(val(i - 1))) * u);
    }
    return KF[KF.length - 1][1];
  };

  const SX = new Float32Array(N.length), SY = new Float32Array(N.length), AL = new Float32Array(N.length);

  /* Dark theme: vertices are points of light. The halo is a pre-rendered sprite per colour (ink + the four data colours),
     drawn with drawImage, so it costs no gradients or blur per vertex. Sprites are keyed by colour and rebuilt when it changes. */
  const SPR = new Map();
  function sprite(c) {
    const key = (c[0] | 0) + ',' + (c[1] | 0) + ',' + (c[2] | 0);
    let cv = SPR.get(key);
    if (!cv) {
      if (SPR.size > 24) SPR.clear();
      cv = document.createElement('canvas'); cv.width = cv.height = 64;
      const g = cv.getContext('2d'), gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
      gr.addColorStop(0, rgb(c, 0.55)); gr.addColorStop(0.3, rgb(c, 0.2)); gr.addColorStop(1, rgb(c, 0));
      g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
      SPR.set(key, cv);
    }
    return cv;
  }
  const hash = i => { let x = Math.imul(i + 1, 0x9E3779B1); x ^= x >>> 15; x = Math.imul(x, 0x85EBCA6B); x ^= x >>> 13; return (x >>> 0) / 4294967296; };

  /* Pure renderer: (story progress q, time t, camera o) -> one frame. Used by the live scene and by the static stills. */
  function draw(ctx, W, H, q, t, o) {
    const z = o.z, s = z * o.k, fx = o.fx * W, fy = o.fy * H;
    const rot = ROT_END * sstep(0.06, 1, q), cr = Math.cos(rot), sr = Math.sin(rot);   // eases in from the hand-off and out before the AI beat
    const X = (x, y) => fx + (x * cr - y * sr) * s, Y = (x, y) => fy + (x * sr + y * cr) * s;
    ctx.clearRect(0, 0, W, H);

    const mm = o.still ? 0 : 1 - sstep(0.07, 0.2, q);   // 1 = colours and sizes of the stack face, 0 = story ink
    const aHop2 = o.still ? 1 : sstep(0.125, 0.2, q);   // second hop arrives once the first has grown
    const aClu = o.still ? 1 : sstep(0.14, 0.3, q);     // other communities, still off screen at that point
    const aField = 1 - sstep(4.5, 13, z);        // the dense field
    const aEdge = sstep(2.4, 9, z);              // fine structure dissolves into points
    const drift = z > 8 && z < 150 ? (o.still ? 1 : sstep(0.1, 0.24, q)) : 0;   // vertices hold still through the hand-off, then start to breathe
    const grow = i => o.still ? 1 : sstep(0, 1, (q - 0.066 - i * 0.012) / 0.06);   // further neighbours draw out of the first vertex after the hand-off
    const grow2 = i => o.still ? 1 : sstep(0, 1, (q - 0.125 - i * 0.01) / 0.055);  // then their own neighbours
    const dim = sstep(1, 1.07, q);               // AI beat: the field steps back
    const ask = sstep(1.05, 1.17, q), reach = ask * (PATH.length - 1);   // and the question walks its path
    const quiet = 1 - 0.5 * dim;

    for (let i = 0; i < N.length; i++) {
      const n = N[i], dx = drift ? Math.sin(t * 0.7 + n.ph) * 0.04 * drift : 0, dy = drift ? Math.cos(t * 0.6 + n.ph * 1.7) * 0.04 * drift : 0;
      SX[i] = X(n.x + dx, n.y + dy); SY[i] = Y(n.x + dx, n.y + dy);
      AL[i] = n.m || n.lv < 2 ? 1 : n.lv === 2 ? aHop2 : aClu;
    }
    // Hubble-style neighborhood exploration isolates actual linked records in the TinkerPop sample.
    const explore = sstep(0.39, 0.5, q) * (1 - sstep(0.65, 0.75, q));
    if (explore > 0) {
      const step = Math.min(W * (o.still || o.mainOnly ? 0.29 : 0.13), 150);
      for (let i = 0; i < pathNodes.length; i++) {
        const id = pathNodes[i];
        SX[id] = lerp(SX[id], fx + (i - 1) * step, explore);
        SY[id] = lerp(SY[id], fy + (i === 1 ? -0.24 : 0.12) * step, explore);
      }
      for (let i = 0; i < N.length; i++) {
        if (!pathNodes.includes(i)) AL[i] *= 1 - 0.88 * explore;
      }
    }
    const tintM = n => sstep(0, 1, (q - 0.72 - n.d * 0.035) / 0.05);   // community detection: colour spreads from each cluster core
    const tint = n => { const m = tintM(n); return m <= 0 ? null : mix(INK, COL[n.c], m); };
    const glowOn = PAL.glow > 0.01, star = PAL.star;

    /* field: clump links, then points, one fill style per clump */
    if (aField > 0.01) {
      ctx.lineWidth = 0.6; ctx.strokeStyle = rgb(INK, PAL.fieldLine * aField * quiet); ctx.beginPath();
      for (let i = 0; i < FL.length; i += 4) { ctx.moveTo(X(FL[i], FL[i + 1]), Y(FL[i], FL[i + 1])); ctx.lineTo(X(FL[i + 2], FL[i + 3]), Y(FL[i + 2], FL[i + 3])); }
      ctx.stroke();
      const r = Math.max(0.95, 0.12 * s);
      for (let ci = 0; ci < clumps.length; ci++) {
        const cl = clumps[ci], x0 = X(cl.cx, cl.cy), y0 = Y(cl.cx, cl.cy), pad = 30 * s + 6;
        if (x0 < -pad || x0 > W + pad || y0 < -pad || y0 > H + pad) continue;
        let col = COL[cl.col], al = cl.col === 3 ? PAL.fieldNeutral : PAL.fieldCol, rr = r, lit = 0;
        if (dim > 0.001) {
          if (cl.role === 1) { lit = sstep(cl.ord - 0.6, cl.ord, reach) * sstep(0, 0.04, ask); al = lerp(al * (1 - 0.6 * dim), 1, lit); col = mix(col, ACCENT, lit); rr = r * (1 + 0.5 * lit); }
          else if (cl.role === 2) { lit = sstep(cl.ord, cl.ord + 0.8, reach); al = lerp(al * (1 - 0.6 * dim), 1, lit); rr = r * (1 + 0.25 * lit); }
          else al *= 1 - PAL.fieldDim * dim;
        }
        /* deep field (dark): each clump has its own brightness, and a few of its points are brighter and larger than the rest */
        const dimmer = lerp(1, 0.42 + 0.58 * hash(ci), star * (1 - lit)), P = cl.pts, big = star > 0.01 ? 3 + (hash(ci + 977) * 3 | 0) : 0;
        ctx.fillStyle = rgb(col, al * aField * dimmer);
        for (let i = big * 2; i < 32; i += 2) {
          const x = X(P[i], P[i + 1]), y = Y(P[i], P[i + 1]);
          if (rr < 1.4) ctx.fillRect(x - rr, y - rr, rr * 2, rr * 2);
          else { ctx.beginPath(); ctx.arc(x, y, rr, 0, 6.283); ctx.fill(); }
        }
        if (big) {
          const rb = rr * lerp(1, 1.55, star);
          const ba = Math.min(1, al * lerp(dimmer, 1.15, star)) * aField, halo = glowOn && ba > 0.3 ? sprite(COL[cl.col]) : null, hs = rb * 4.6;
          ctx.fillStyle = rgb(mix(col, INK, 0.35 * star), ba);
          for (let i = 0; i < big * 2; i += 2) {
            const x = X(P[i], P[i + 1]), y = Y(P[i], P[i + 1]);
            if (x < -8 || x > W + 8 || y < -8 || y > H + 8) continue;
            if (halo) { ctx.globalAlpha = 0.55 * PAL.glow * ba; ctx.drawImage(halo, x - hs, y - hs, hs * 2, hs * 2); ctx.globalAlpha = 1; }
            if (rb < 1.4) ctx.fillRect(x - rb, y - rb, rb * 2, rb * 2);
            else { ctx.beginPath(); ctx.arc(x, y, rb, 0, 6.283); ctx.fill(); }
          }
        }
      }
      /* AI beat: the question path and the subgraph it retrieves */
      if (ask > 0.001) {
        ctx.lineWidth = 0.9;
        for (const c of NEAR) {
          const lit = sstep(c.ord, c.ord + 0.8, reach); if (lit < 0.02) continue;
          const h = PATH[c.ord];
          ctx.strokeStyle = rgb(ACCENT, PAL.nearA * lit * aField); ctx.beginPath(); ctx.moveTo(X(h.cx, h.cy), Y(h.cx, h.cy)); ctx.lineTo(X(c.cx, c.cy), Y(c.cx, c.cy)); ctx.stroke();
        }
        const trace = (width, alpha) => {
          ctx.lineWidth = width; ctx.strokeStyle = rgb(ACCENT, alpha * aField); ctx.lineJoin = ctx.lineCap = 'round'; ctx.beginPath();
          ctx.moveTo(X(PATH[0].cx, PATH[0].cy), Y(PATH[0].cx, PATH[0].cy));
          for (let i = 1; i < PATH.length; i++) {
            const m = clamp(reach - (i - 1), 0, 1); if (m <= 0) break;
            const a = PATH[i - 1], b = PATH[i];
            ctx.lineTo(X(lerp(a.cx, b.cx, m), lerp(a.cy, b.cy, m)), Y(lerp(a.cx, b.cx, m), lerp(a.cy, b.cy, m)));
          }
          ctx.stroke();
        };
        if (glowOn) trace(PAL.pathW * 2.1, PAL.pathGlow * 0.3 * PAL.glow);   // dark: a second, wider and fainter pass makes the path a restrained light
        trace(PAL.pathW, PAL.pathGlow); trace(2.2, 0.95);
        ctx.lineCap = 'butt';
        PATH.forEach((c, i) => {
          const lit = sstep(i - 0.6, i, reach) * sstep(0, 0.04, ask); if (lit < 0.02) return;
          const x = X(c.cx, c.cy), y = Y(c.cx, c.cy), end = i === 0 || i === PATH.length - 1;
          ctx.fillStyle = rgb(ACCENT, lit); ctx.beginPath(); ctx.arc(x, y, (end ? 5.5 : 3.4) * lit, 0, 6.283); ctx.fill();
          if (end) { ctx.lineWidth = 1.6; ctx.strokeStyle = rgb(ACCENT, 0.55 * lit); ctx.beginPath(); ctx.arc(x, y, 10.5, 0, 6.283); ctx.stroke(); }
        });
        if (!o.still && ask > 0.98) {              // resolved: the answer travels back along the path
          const u = (t % 3.4) / 3.4, pos = (1 - u) * (PATH.length - 1), i = Math.min(PATH.length - 2, pos | 0), m = pos - i;
          const a = PATH[i], b = PATH[i + 1], wx = lerp(a.cx, b.cx, m), wy = lerp(a.cy, b.cy, m);
          ctx.fillStyle = rgb(ACCENT, Math.sin(u * Math.PI)); ctx.beginPath(); ctx.arc(X(wx, wy), Y(wx, wy), 4.2, 0, 6.283); ctx.fill();
          const g = PATH[0];
          ctx.lineWidth = 1.3; ctx.strokeStyle = rgb(ACCENT, 0.5 * (1 - u) * sstep(0.7, 1, u + 0.3)); ctx.beginPath(); ctx.arc(X(g.cx, g.cy), Y(g.cx, g.cy), 12 + u * 22, 0, 6.283); ctx.stroke();
        }
      }
    }

    /* detected communities get a soft hull in their colour */
    for (const cl of clusters) {
      if (cl.c === undefined) continue;
      const m = sstep(0, 1, (q - 0.74 - cl.d * 0.035) / 0.06) * aEdge;
      if (m < 0.02) continue;
      const hx = X(cl.cx, cl.cy), hy = Y(cl.cx, cl.cy), hr = cl.sig * 2.5 * s;
      if (PAL.hullA > 0.001) { ctx.fillStyle = rgb(COL[cl.c], PAL.hullA * m * quiet); ctx.beginPath(); ctx.arc(hx, hy, hr, 0, 6.283); ctx.fill(); }
      if (PAL.hullGlow > 0.001) {                // dark: a soft glow instead of a filled disc
        const gr = ctx.createRadialGradient(hx, hy, 0, hx, hy, hr * 1.45), a = PAL.hullGlow * m * quiet;
        gr.addColorStop(0, rgb(COL[cl.c], a)); gr.addColorStop(0.55, rgb(COL[cl.c], a * 0.45)); gr.addColorStop(1, rgb(COL[cl.c], 0));
        ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(hx, hy, hr * 1.45, 0, 6.283); ctx.fill();
      }
    }

    /* edges */
    const lw = clamp(s * 0.011, 0.6, 1.5);
    for (const e of E) {
      let al = Math.min(AL[e.a], AL[e.b]) * aEdge * quiet * (e.x ? aHop2 : 1), g = 1;
      if (!e.m) { if (e.lv === 1) g = grow(e.i); else if (e.lv === 2) g = grow2(e.i); }
      if (al < 0.02 || g <= 0) continue;
      const c = e.lv === 4 ? null : tint(N[e.b]), em = e.m ? mm : 0;   // sample-graph edges keep the face's stroke at the hand-off
      ctx.strokeStyle = c ? rgb(c, PAL.tintA * al) : rgb(mix(INK, faceAccent, em), lerp(e.lv === 4 ? PAL.linkA : PAL.edgeA, 0.55, em) * al);
      ctx.lineWidth = lerp(lw, F_LINE * U * s, em); ctx.lineCap = em > 0.02 ? 'round' : 'butt'; ctx.beginPath(); ctx.moveTo(SX[e.a], SY[e.a]);
      ctx.lineTo(SX[e.a] + (SX[e.b] - SX[e.a]) * g, SY[e.a] + (SY[e.b] - SY[e.a]) * g); ctx.stroke();
    }

    ctx.lineCap = 'butt';
    /* a traversal leaving the first vertex: hop one, then hop two */
    const aPulse = sstep(55, 86, z) * (1 - mm) * aHop2 * (1 - explore);
    if (!o.still && aPulse > 0.02 && grow(ring.length - 1) > 0.99) {
      const u = (t % 3.2) / 3.2;
      ctx.fillStyle = rgb(ACCENT, 1);
      for (const e of E) {
        if (e.lv > 2) continue;
        const v = e.lv === 1 ? u / 0.3 : (u - 0.3) / 0.3;
        if (v <= 0 || v >= 1 || (e.lv === 2 && AL[e.b] < 0.5)) continue;
        ctx.globalAlpha = aPulse * Math.sin(v * Math.PI);
        ctx.beginPath(); ctx.arc(SX[e.a] + (SX[e.b] - SX[e.a]) * v, SY[e.a] + (SY[e.b] - SY[e.a]) * v, clamp(s * 0.03, 2, 4), 0, 6.283); ctx.fill();
      }
      ctx.globalAlpha = 1;
    }

    /* vertices */
    for (let i = N.length - 1; i >= 0; i--) {
      const n = N[i]; let al = AL[i], r = n.r * s;
      if (n.lv === 1 && !n.m) { const g = grow(ring.indexOf(i)); al *= sstep(0.85, 1, g); r *= 0.6 + 0.4 * sstep(0.85, 1, g); }
      else if (n.ri !== undefined) { const g = grow2(n.ri); al *= sstep(0.8, 1, g); r *= 0.6 + 0.4 * sstep(0.8, 1, g); }
      if (al < 0.02) continue;
      const x = SX[i], y = SY[i];
      if (x < -60 || x > W + 60 || y < -60 || y > H + 60) continue;
      if (n.lv === 0) {
        const ha = o.still ? 1 : sstep(0.07, 0.16, q);
        if (ha > 0.01) {
          const halo = Math.max(r * (3.4 + 0.5 * Math.sin(t * 1.6)), 5), gr = ctx.createRadialGradient(x, y, r * 0.5, x, y, halo);
          gr.addColorStop(0, rgb(PAL.halo, PAL.haloA * ha)); gr.addColorStop(1, rgb(PAL.halo, 0));
          ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(x, y, halo, 0, 6.283); ctx.fill();
        }
        r = lerp(S_MAIN, F_MAIN * U, mm) * s;      // the emphasised vertex as drawn on the stack face, with its ring
        if (mm > 0.01) { ctx.strokeStyle = rgb(faceRing, mm); ctx.lineWidth = F_LINE * U * s; ctx.beginPath(); ctx.arc(x, y, F_RING * U * s, 0, 6.283); ctx.stroke(); }
        ctx.fillStyle = rgb(mix(INK, faceAccent, mm), quiet); ctx.beginPath(); ctx.arc(x, y, Math.max(r, 1.6), 0, 6.283); ctx.fill();
        continue;
      }
      const c = tint(n);
      if (n.m) r = lerp(S_NODE, F_NODE * U, mm) * s;   // the face's other vertices start as drawn on the stack, then settle into the story's ink
      const rv = Math.max(r, 0.95 + 1.2 * aEdge);
      if (glowOn && rv > 1.3) {                   // dark: a small halo, from a sprite, once the story has left the stack face behind
        const ga = PAL.glow * (n.m ? 1 - mm : 1) * al * quiet * aEdge, gs = rv * 4.2;
        if (ga > 0.02) { ctx.globalAlpha = ga; ctx.drawImage(sprite(c || INK), x - gs, y - gs, gs * 2, gs * 2); ctx.globalAlpha = 1; }
      }
      if (n.m) ctx.fillStyle = c ? rgb(c, 0.95 * quiet) : rgb(mix(INK, faceAccent, mm), lerp(PAL.nodeA, 1, mm) * al);
      else ctx.fillStyle = c ? rgb(c, 0.95 * al * quiet) : rgb(INK, PAL.nodeA * al * quiet);
      ctx.beginPath(); ctx.arc(x, y, rv, 0, 6.283); ctx.fill();
    }

    /* names of the sample graph: they arrive with the first beat's copy, well after the hand-off, and only while the camera is close */
    const la = (1 - explore) * (o.still ? 1 : sstep(0.13, 0.2, q)) * sstep(58, 84, z);
    if (la > 0.02) {
      ctx.font = '500 11.5px "Geist Mono", ui-monospace, monospace'; ctx.textAlign = 'center'; ctx.textBaseline = 'top';
      ctx.fillStyle = rgb(INK, PAL.nameA * la);
      for (const n of N) { if (!n.name || (o.mainOnly && n.lv)) continue; const i = N.indexOf(n); ctx.fillText(n.name, SX[i], SY[i] + (n.lv ? lerp(S_NODE, F_NODE * U, mm) : lerp(S_MAIN, F_MAIN * U, mm)) * s + 7); }
    }
    if (explore > 0.01) {
      ctx.save();
      ctx.globalAlpha = explore;
      ctx.font = '600 13px ui-monospace, monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      pathNodes.forEach((id, index) => {
        const x = SX[id], y = SY[id];
        ctx.fillStyle = rgb(ACCENT, 1);
        ctx.beginPath(); ctx.arc(x, y, 5, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = rgb(INK, 1);
        ctx.fillText(N[id].name, x, y + 13);
        if (index === 0) return;
        const from = pathNodes[index - 1];
        ctx.strokeStyle = rgb(ACCENT, 0.8); ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(SX[from], SY[from]); ctx.lineTo(x, y); ctx.stroke();
        ctx.fillText(relations[index - 1], (SX[from] + x) / 2, (SY[from] + y) / 2 - 22);
      });
      ctx.restore();
    }
  }

  /* ---------- static mode (reduced motion): one still per beat ---------- */
  function renderStills() {
    $$('.still').forEach(cv => {
      const W = cv.clientWidth, H = cv.clientHeight, dpr = Math.min(devicePixelRatio || 1, 2);
      if (!W) return;
      cv.width = W * dpr; cv.height = H * dpr;
      const ctx = cv.getContext('2d'); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      draw(ctx, W, H, +cv.dataset.q, 4, { z: zoom(+cv.dataset.q), fx: 0.5, fy: +cv.dataset.q < 0.4 ? 0.56 : 0.5, k: W / 900, still: true, mainOnly: W < 520 });   // on a narrow still only the first vertex is named
    });
  }

  /* ---------- live mode: pinned stage, scroll-driven lift-off and camera ---------- */
  function startLive(initialBeat) {
    const lifetime = new AbortController();
    const listen = (target, event, handler, options = {}) =>
      target.addEventListener(event, handler, { ...options, signal: lifetime.signal });
    const S = window.HGStack, sroot = S.root, GEO = S.geom;
    const story = $('#story'), stage = $('#stage'), hero = $('#hero'), copy = $('.hero-copy'), rig = $('#rig');
    const veil = $('#veil'), cv = $('#world'), ctx = cv.getContext('2d');
    const readout = $('#readout');
    const plane = $('.hgs-plane', sroot), scene = $('.hgs-scene', sroot), labels = $('.hgs-labels', sroot);
    const ground = $('.hgs-ground', sroot), guides = $$('.hgs-guide', sroot);
    const layer = id => $(`.hgs-layer[data-id="${id}"]`, sroot);
    const L = { database: layer('database'), toolchain: layer('toolchain'), computing: layer('computing'), ai: layer('ai') };
    const HOOKS = ['--hgs-drift', '--hgs-fade', '--hgs-plate'];
    const panels = $$('.panel');
    /* lift-off windows, in scroll progress p. Nothing moves before HERO_P (about 40 px of scroll): a small accidental scroll
       leaves the hero, and the stack's hover and click, exactly as they were. */
    const HERO_P = 0.0075;
    const T = { out: [HERO_P, 0.036], away: [0.011, 0.058], ground: [HERO_P, 0.048], turn: [0.018, 0.1], plate: [0.042, 0.095], move: [HERO_P, 0.105], size: [0.022, 0.105], cv: [0.105, 0.117], rig: [0.117, 0.127], gone: 0.13 };
    const heroExit = [0.02, 0.052], storyEntry = [0.042, 0.073];
    const PQ = [[0.125, 0.06], [0.2, 0.2], [0.31, 0.36], [0.41, 0.5], [0.53, 0.66], [0.66, 0.82], [0.8, 1], [1, 1.25]];   // scroll progress p -> story progress q
    /* Text is a stable reading surface. The graph keeps interpolating, while exactly one beat's copy is shown at full
       strength. Scrubbing or stopping between beats can never leave two headings or barely visible paragraphs stacked. */
    const beats = [
      { id: 'database', end: 0.42, stop: 0.25,
        note: readoutText('database', '{vertices} vertices, 1 neighborhood', { vertices: home.length + 1 }) },
      { id: 'toolchain', end: 0.72, stop: 0.58, note: readoutText('toolchain', 'Explore vertices and relationships') },
      { id: 'computing', end: 1.03, stop: 0.91,
        note: readoutText('computing', '{vertices} vertices, {communities} communities', { vertices: N.length, communities: clusters.length }) },
      { id: 'ai', end: Infinity, stop: 1.2, note: readoutText('ai', '1 question, 1 retrieved subgraph') },
    ];
    const qmap = p => {
      if (p <= PQ[0][0]) return PQ[0][1];
      for (let i = 1; i < PQ.length; i++) if (p <= PQ[i][0]) return lerp(PQ[i - 1][1], PQ[i][1], (p - PQ[i - 1][0]) / (PQ[i][0] - PQ[i - 1][0]));
      return PQ[PQ.length - 1][1];
    };
    const pOf = q => {                                        // inverse of qmap
      for (let i = 1; i < PQ.length; i++) if (q <= PQ[i][1]) return lerp(PQ[i - 1][0], PQ[i][0], (q - PQ[i - 1][1]) / (PQ[i][1] - PQ[i - 1][1]));
      return 1;
    };
    const narrow = matchMedia('(max-width:1023px)');
    const A0 = GEO.tilt * Math.PI / 180, B0 = GEO.turn * Math.PI / 180;   // the module's isometric plane: rotateX(tilt) rotateZ(turn)
    const G = {};                                             // rig geometry, measured on resize
    let W = 0, H = 0, small = false, ps = 0, running = false, raf = 0, note = '';
    let diving = false, gone = false, lastP = -1;
    let tau = 0.12, lastNow = 0, snapNext = true, travel = null;
    const t0 = performance.now();

    /* orthographic projection of a point on the plane after rotateX(a) rotateZ(b), relative to the plane centre */
    const proj = (a, b, x, y, z) => { const cb = Math.cos(b), sb = Math.sin(b); return [x * cb - y * sb, (x * sb + y * cb) * Math.cos(a) - z * Math.sin(a)]; };

    function size() {
      const dpr = Math.min(devicePixelRatio || 1, 2);
      W = stage.clientWidth; H = stage.clientHeight; small = narrow.matches;
      cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      /* measure the stack where the layout puts it, without the scroll transform */
      const keep = rig.style.transform; rig.style.transform = 'none';
      sroot.dataset.labels = 'side';
      if (small || sroot.getBoundingClientRect().width < 712) sroot.dataset.labels = 'none';   // the label column needs about 712 px
      const sr = stage.getBoundingClientRect(), rr = rig.getBoundingClientRect(), sc = scene.getBoundingClientRect();
      rig.style.transform = keep;
      const u = sc.width / GEO.box[0];                        // one design unit of the module, in px
      G.u = u; G.ox = rr.left - sr.left; G.oy = rr.top - sr.top;
      G.cx = sc.left - rr.left + GEO.cx * u; G.cy = sc.top - rr.top + GEO.cy * u;   // plane centre inside the rig
      G.fx = (FACE.marko[0] - GEO.face / 2) * u; G.fy = (FACE.marko[1] - GEO.face / 2) * u;   // the emphasised vertex on its face
      const p0 = proj(A0, B0, G.fx, G.fy, 0);
      G.hx = G.ox + G.cx + p0[0]; G.hy = G.oy + G.cy + p0[1]; // where that vertex sits in the hero
      G.k = small ? clamp(W / 760, 0.45, 0.95) : clamp(W / 1440, 0.7, 1.25);
      G.sc = clamp(Z0 * G.k * U / u, 0.92, 1.3);              // stack scale at the hand-off: close to its hero size, never above 1.3x
      G.s0 = u * G.sc / U;                                    // px per world unit at the hand-off
      G.z0 = G.s0 / G.k;
      G.mx = (small ? 0.5 : W < 1280 ? 0.74 : 0.71) * W; G.my = (small ? 0.31 : 0.54) * H;   // where that vertex lands, which is where the story keeps it
      lastP = -1;
    }

    function clearLift() {
      diving = false; stage.classList.remove('diving');
      for (const el of [rig, copy, labels, ground, hero]) el.removeAttribute('style');
      for (const el of guides) { el.style.removeProperty('opacity'); el.style.removeProperty('visibility'); }
      plane.style.removeProperty('--hgs-cos'); plane.style.removeProperty('--hgs-sin');
      for (const id in L) { HOOKS.forEach(k => L[id].style.removeProperty(k)); L[id].style.removeProperty('visibility'); }
      gone = false; S.setPaused(false);
      S.setActive(null); S.setInteractive(true);
    }

    /* The graph lifts off its layer: the other layers drift apart and fade, the plane turns face-on at about its hero size,
       the plate dissolves, and the emphasised vertex travels on one eased path to where the story keeps it. */
    function liftoff(p) {
      if (p <= HERO_P) { if (diving || lastP < 0) clearLift(); return; }
      if (!diving) {            // from here the story owns the stack: hover, focus and clicks on it are ignored, any lift is released
        diving = true; stage.classList.add('diving'); S.setInteractive(false); S.setActive(null); S.setPaused(true);
      }
      const off = p > T.gone; if (off !== gone) { gone = off; hero.style.visibility = off ? 'hidden' : 'visible'; }
      if (off) return;
      const w = k => sstep(T[k][0], T[k][1], p);
      const eOut = w('out'), eAway = w('away'), eG = w('ground'), eR = w('turn'), eP = w('plate'), eT = w('move'), eS = w('size');
      const copyExit = sstep(...heroExit, p);
      copy.style.opacity = (1 - copyExit).toFixed(3); copy.style.transform = `translateY(${(-24 * copyExit).toFixed(1)}px)`;
      labels.style.opacity = (1 - eOut).toFixed(3);
      ground.style.opacity = (1 - eG).toFixed(3);
      const fade = (1 - eAway).toFixed(3);
      L.toolchain.style.setProperty('--hgs-drift', (24 * eAway).toFixed(2));
      L.computing.style.setProperty('--hgs-drift', (12 * eAway).toFixed(2));
      L.ai.style.setProperty('--hgs-drift', (46 * eAway).toFixed(2));
      for (const id of ['toolchain', 'computing', 'ai']) L[id].style.setProperty('--hgs-fade', fade);
      for (const el of guides) el.style.opacity = fade;
      L.database.style.setProperty('--hgs-plate', (1 - eP).toFixed(3));
      /* once something has fully faded, stop painting it */
      const hide = (el, h) => { const v = h ? 'hidden' : ''; if (el.style.visibility !== v) el.style.visibility = v; };
      hide(ground, eG >= 1); hide(labels, eOut >= 1); hide(copy, copyExit >= 1);
      for (const el of guides) hide(el, eAway >= 1);
      for (const id of ['toolchain', 'computing', 'ai']) hide(L[id], eAway >= 1);
      /* tilt only: the diamond opens into a square standing on its corner, so nothing rotates on screen */
      const a = A0 * (1 - eR), sc = lerp(1, G.sc, eS), pl = proj(a, B0, G.fx, G.fy, 0);
      const tx = lerp(G.hx, G.mx, eT), ty = lerp(G.hy, G.my, eT);
      plane.style.setProperty('--hgs-cos', Math.cos(a).toFixed(5)); plane.style.setProperty('--hgs-sin', Math.sin(a).toFixed(5));
      rig.style.transform = `translate(${(tx - G.ox - sc * (G.cx + pl[0])).toFixed(2)}px,${(ty - G.oy - sc * (G.cy + pl[1])).toFixed(2)}px) scale(${sc.toFixed(5)})`;
      rig.style.opacity = (1 - w('rig')).toFixed(3);
    }

    /* One timeline: any progress value renders the correct frame, forwards or backwards. */
    function render(p, t) {
      if (isPrinting()) return;
      const changed = p !== lastP;
      if (changed) {
        // The background hand-off shares the graph timeline, including reverse
        // scrolling and direct layer navigation. Finish before the canvas appears.
        stage.style.setProperty('--scene-light', sstep(HERO_P, T.plate[1], p).toFixed(4));
        liftoff(p);
      }
      const q = qmap(p), aCv = sstep(T.cv[0], T.cv[1], p);
      if (changed) cv.style.opacity = aCv.toFixed(3);
      if (aCv > 0) {
        const e = sstep(0.06, 0.2, q), z = zoom(q, G.z0);
        const fx = lerp(G.mx / W, small ? 0.5 : W < 1280 ? 0.74 : 0.71, e), fy = lerp(G.my / H, small ? 0.31 : 0.54, e);
        draw(ctx, W, H, q, t, { z, k: G.k, fx, fy, mainOnly: small, clear: small ? (x, y) => y < H * 0.4 : x => x > W * 0.52 });
      }
      if (!changed) return;
      lastP = p;
      const ui = sstep(0.075, 0.14, q).toFixed(3);
      readout.style.opacity = ui;
      // While a layer shortcut moves past other stops, show only the departure and destination copy.
      let bi = beats.findIndex(beat => q < beat.end);
      if (travel) bi = travel.fraction < 0.5 ? travel.fromBeat : travel.toBeat;
      const entry = sstep(...storyEntry, p);
      veil.style.opacity = entry.toFixed(3);
      const currentBeat = entry > 0 && bi >= 0 ? beats[bi].id : null;
      let copyOpacity = entry;
      if (travel) {
        if (travel.fromBeat === travel.toBeat) {
          copyOpacity = lerp(travel.fromOpacity, 1, sstep(0, 1, travel.fraction));
        } else if (travel.fraction < 0.5) {
          copyOpacity = travel.fromOpacity * (1 - sstep(0, 0.5, travel.fraction));
        } else {
          copyOpacity = sstep(0.5, 1, travel.fraction);
        }
      }
      panels.forEach(el => {
        const active = el.id === 'beat-' + currentBeat;
        el.style.opacity = active ? copyOpacity.toFixed(3) : '0';
        el.style.setProperty('--dy', (12 * (1 - entry)).toFixed(1) + 'px');
        el.classList.toggle('on', active);
        el.style.visibility = active ? 'visible' : 'hidden';
        // Hidden panels already leave the accessibility tree through visibility.
        el.inert = active && copyOpacity < 0.5;
      });
      const txt = bi < 0 ? '' : beats[bi].note;
      if (txt !== note) readout.textContent = note = txt;
    }

    /* The scene follows a smoothed copy of the scroll position (frame-rate independent, time constant tau), so a wheel notch
       becomes a short glide instead of a step. It snaps once the difference is under a third of a pixel. */
    function frame(now) {
      raf = 0;
      if (!running || isPrinting()) return;
      const rect = story.getBoundingClientRect();
      const spanPx = Math.max(1, rect.height - innerHeight);
      const target = clamp(-rect.top / spanPx, 0, 1);
      const dt = clamp((now - lastNow) / 1000, 0.001, 0.1); lastNow = now;
      // A scrollbar drag or external navigation can move the page without a wheel or touch event.
      if (travel && Math.abs(scrollY - travel.scrollY) > 1) interrupt();
      const move = travel;
      if (move) {
        move.fraction = clamp((now - move.start) / move.duration, 0, 1);
        ps = lerp(move.from, move.to, sstep(0, 1, move.fraction));
        scrollTo({ top: scrollY + rect.top + ps * spanPx, behavior: 'instant' });
        move.scrollY = scrollY;
        snapNext = false;
      } else if (snapNext) { ps = target; snapNext = false; }
      else { ps += (target - ps) * (1 - Math.exp(-dt / tau)); if (Math.abs(target - ps) * spanPx < 0.34) ps = target; }
      render(ps, (now - t0) / 1000);
      if (move && move.fraction === 1) {
        travel = null;
        if (move.byKeyboard) $('#beat-' + move.id + ' .story-guide')?.focus({ preventScroll: true });
      }
      raf = requestAnimationFrame(frame);
    }
    const kick = () => { if (running && !raf) { snapNext = true; lastNow = performance.now(); raf = requestAnimationFrame(frame); } };
    const resize = new ResizeObserver(() => {
      if (lifetime.signal.aborted) return;
      syncPrintLayout();
      if (isPrinting()) return;
      size();
      if (running && !raf) kick();
    });
    resize.observe(stage);
    const visibility = new IntersectionObserver(es => { if (lifetime.signal.aborted) return; running = es[0].isIntersecting && !document.hidden; kick(); });
    visibility.observe(story);
    listen(document, 'visibilitychange', () => { if (document.hidden) running = false; else { const r = story.getBoundingClientRect(); running = r.bottom > 0 && r.top < innerHeight; kick(); } });
    if (!isPrinting()) size();

    // Use one clock for both the scroll position and camera. Re-targeting starts at the frame the reader
    // sees, and manual input takes over without a native smooth scroll or delayed callback racing it.
    function go(id, byKeyboard = false, animate = true) {
      const toBeat = beats.findIndex(beat => beat.id === id);
      if (id !== 'hero' && toBeat < 0) return;
      if (travel?.id === id) {
        travel.byKeyboard ||= byKeyboard;
        return;
      }
      const to = id === 'hero' ? 0 : pOf(beats[toBeat].stop);
      if (animate && Math.abs(to - ps) > 0.001 && running) {
        const visiblePanel = panels.find(panel => panel.classList.contains('on'));
        const fromBeat = visiblePanel ? beats.findIndex(beat => visiblePanel.id === 'beat-' + beat.id) : -1;
        const fromOpacity = visiblePanel ? Number(getComputedStyle(visiblePanel).opacity) : 0;
        travel = { id, from: ps, to, start: performance.now(), fraction: 0, fromBeat, fromOpacity, toBeat, byKeyboard, scrollY,
          duration: 360 + 120 * Math.abs(to - ps) };
        return;
      }
      travel = null;
      const rect = story.getBoundingClientRect();
      scrollTo({ top: scrollY + rect.top + to * Math.max(1, rect.height - innerHeight), behavior: 'instant' });
      ps = to;
      lastP = -1;
      render(to, (performance.now() - t0) / 1000);
      if (byKeyboard) $('#beat-' + id + ' .story-guide')?.focus({ preventScroll: true });
    }
    function interrupt() {
      if (!travel) return;
      travel = null;
      lastP = -1;
    }
    listen(sroot, 'click', e => {
      const hit = e.target.closest('[data-layer]');
      if (hit) go(S.layers[Number(hit.dataset.layer)].id, e.detail === 0);
    });
    listen(window, 'wheel', () => { tau = 0.12; interrupt(); }, { passive: true });
    listen(window, 'touchmove', () => { tau = 0.05; interrupt(); }, { passive: true });

    const scrollKeys = new Set(['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End', ' ']);
    listen(window, 'keydown', event => {
      if (event.key === ' ' && event.target.closest?.('button, a')) return;
      if (scrollKeys.has(event.key)) interrupt();
    });

    /* the palette changed: draw the current frame again now (a view transition snapshots the page right after), and keep the loop alive */
    onPalette = () => { if (running && W) { lastP = -1; render(ps, (performance.now() - t0) / 1000); } kick(); };
    if (initialBeat) go(initialBeat, false, false);
    return {
      beforePrint() {
        interrupt();
        for (const panel of panels) panel.inert = false;
      },
      afterPrint() {
        size();
        render(ps, (performance.now() - t0) / 1000);
        kick();
      },
      currentBeat: () => travel?.id ?? (ps < (storyEntry[0] + storyEntry[1]) / 2 ? 'hero' : beats.find(beat => qmap(ps) < beat.end).id),
      destroy() {
        lifetime.abort();
        resize.disconnect(); visibility.disconnect();
        running = false; cancelAnimationFrame(raf); raf = 0;
        clearLift();
        stage.style.removeProperty('--scene-light');
        for (const el of [cv, veil, readout]) {
          el.style.removeProperty('opacity'); el.style.removeProperty('visibility');
        }
        panels.forEach(el => {
          el.removeAttribute('style'); el.classList.remove('on');
          el.inert = false;
        });
        ctx.clearRect(0, 0, W, H);
        onPalette = () => {};
      },
    };
  }

  function startStatic() {
    const lifetime = new AbortController();
    onPalette = renderStills;
    renderStills();
    let rt = 0;
    const resize = new ResizeObserver(() => {
      if (lifetime.signal.aborted) return;
      syncPrintLayout();
      if (isPrinting()) return;
      clearTimeout(rt); rt = setTimeout(renderStills, 150);
    });
    resize.observe(landing);
    const sroot = window.HGStack?.root;
    if (sroot) sroot.addEventListener('click', e => {
      const hit = e.target.closest('[data-layer]'); if (!hit) return;
      const el = $('#beat-' + window.HGStack.layers[+hit.dataset.layer].id);
      if (!el) return;
      el.scrollIntoView({ behavior: 'instant', block: 'start' });
      if (e.detail === 0) el.querySelector('.story-guide')?.focus({ preventScroll: true });
    }, { signal: lifetime.signal });
    return {
      currentBeat() {
        const panels = $$('.panel');
        const padding = parseFloat(getComputedStyle(document.scrollingElement).scrollPaddingTop) || 0;
        const margin = panels.length ? parseFloat(getComputedStyle(panels[0]).scrollMarginTop) || 0 : 0;
        const readingLine = padding + margin + 2;
        const visible = panels.find(el => {
          const box = el.getBoundingClientRect();
          return box.bottom > readingLine && box.top < innerHeight * 0.65;
        });
        return visible ? visible.id.slice(5) : 'hero';
      },
      destroy() {
        lifetime.abort(); resize.disconnect(); clearTimeout(rt);
        onPalette = () => {};
      },
    };
  }

  // One active mode owns its observers, listeners and animation frame.
  // Preference changes retain the current explanation (or downstream position)
  // while swapping between the pinned story and ordinary document sections.
  let mode = null, reveal = null;
  // Print uses ordinary document flow. The shorter layout can clamp scrollY
  // before the media change fires, so retain the last screen scroll position.
  window.addEventListener('scroll', () => { if (!isPrinting()) screenY = scrollY; }, { passive: true });
  function beforePrint() {
    if (printing) return;
    if (!printMedia.matches) screenY = scrollY;
    printing = true;
    mode?.beforePrint?.();
  }
  function afterPrint() {
    if (!printing || printMedia.matches) return;
    printing = false;
    scrollTo({ top: screenY, behavior: 'instant' });
    mode?.afterPrint?.();
    updateMotion();
  }
  window.addEventListener('beforeprint', beforePrint);
  window.addEventListener('afterprint', afterPrint);
  printMedia.addEventListener('change', event => event.matches ? beforePrint() : afterPrint());
  function updateMotion() {
    const live = !stillMotion.matches && Boolean(window.HGStack);
    // Preserve the screen layout until its saved scroll position has been restored.
    if (mode && (isPrinting() || live === landing.classList.contains('live'))) return;
    const active = document.activeElement;
    const story = $('#story'), content = $('.landing-content');
    const box = story.getBoundingClientRect();
    // At the boundary, keep whichever section occupies the larger readable area.
    const headerSpace = parseFloat(getComputedStyle(document.scrollingElement).scrollPaddingTop) || 0;
    const readingCenter = (headerSpace + innerHeight) / 2;
    const withinStory = box.top < innerHeight && box.bottom >= readingCenter;
    const beat = mode && withinStory ? mode.currentBeat() : null;
    const contentTop = mode && !withinStory ? content.getBoundingClientRect().top : null;
    mode?.destroy(); reveal?.disconnect();
    cancelAnimationFrame(themeRaf);
    landing.classList.toggle('live', live);
    window.HGStack?.setPaused(!live);
    window.HGStack?.setInteractive(true);
    mode = live ? startLive(beat) : startStatic();
    if (live) {
      reveal = new IntersectionObserver(es => es.forEach(e => {
        if (e.isIntersecting) { e.target.classList.add('in'); reveal.unobserve(e.target); }
      }), { rootMargin: '0px 0px -12% 0px' });
      $$('.reveal').forEach(el => reveal.observe(el));
    } else if (beat) {
      const target = beat === 'hero' ? $('#hero') : $('#beat-' + beat);
      target?.scrollIntoView({ behavior: 'instant', block: 'start' });
    }
    if (contentTop !== null) {
      scrollBy({ top: content.getBoundingClientRect().top - contentTop, behavior: 'instant' });
    }
    // Keep focus with the reader when a motion mode change hides the old target.
    if (beat && active && landing.contains(active) && !active.getClientRects().length) {
      const target = beat === 'hero' ? $('#hero .btn-primary') : $('#beat-' + beat + ' .story-guide');
      target?.focus({ preventScroll: true });
    }
    syncTheme(0);
  }
  updateMotion();
  if (printMedia.matches) beforePrint();
  stillMotion.addEventListener('change', updateMotion);

  /* Follow OINK's resolved appearance, including changes to the system preference in auto mode. */
  const followNativeTheme = () => syncTheme(stillMotion.matches ? 0 : 260);
  new MutationObserver(followNativeTheme).observe(html, { attributes: true, attributeFilter: ['data-bs-theme'] });

  /* The navbar, language switching and mobile drawers stay in the native site shell. Only the homepage command is local. */
  const copyBtn = $('#copy'), cmd = $('#cmd'), label = $('#copy-label'), status = $('#copy-status');
  if (copyBtn && cmd && label && status) {
    const text = (name, fallback) => copyBtn.dataset[name] || fallback;
    let reset = 0;
    copyBtn.addEventListener('click', async () => {
      let ok = false;
      try { await navigator.clipboard.writeText(cmd.textContent); ok = true; }
      catch {
        const range = document.createRange(); range.selectNodeContents(cmd);
        const selection = getSelection();
        if (selection) { selection.removeAllRanges(); selection.addRange(range); }
        try { ok = document.execCommand('copy'); } catch { ok = false; }
      }
      copyBtn.classList.toggle('done', ok);
      label.textContent = ok ? text('copied', 'Copied') : text('copyFallback', 'Press Ctrl+C');
      status.textContent = ok ? text('copyStatus', 'Command copied to clipboard') : text('copyFallbackStatus', 'Command selected, press Ctrl+C to copy');
      clearTimeout(reset);
      reset = setTimeout(() => { copyBtn.classList.remove('done'); label.textContent = text('copy', 'Copy'); status.textContent = ''; }, 2000);
    });
  }
})();

})();
