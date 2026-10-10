#!/usr/bin/env node
// Renders mock-up frames (PNG) and short silent clips (MP4) of scene types in two
// visual styles, so the team can compare looks before any pipeline code exists.
//
//   node render.mjs                 # stills for every scene x style -> out/*.png
//   node render.mjs --video         # also 10 s draw-on clips of the diagram scene -> out/*.mp4
//   node render.mjs --only=diagram  # restrict to one scene id
//
// Everything is inlined into one HTML document (fonts as data URIs, Mermaid from
// node_modules) so the page needs no network and no file:// cross-loading. A frame
// is posed deterministically with window.__seek(t), which is how Remotion would
// drive the same components later: time in, pixels out.

import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const require = createRequire(import.meta.url);
const { chromium } = require('/opt/node22/lib/node_modules/playwright');

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const outDir = path.join(here, 'out');
fs.mkdirSync(outDir, { recursive: true });

const args = new Set(process.argv.slice(2));
const DO_VIDEO = args.has('--video');
const ONLY = [...args].find((a) => a.startsWith('--only='))?.slice(7);
const FPS = 30;
const CLIP_SECONDS = 10;

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const readB64 = (p) => fs.readFileSync(p).toString('base64');
const fontFace = (family, file, weight) => {
  const p = path.join(here, 'node_modules/@fontsource', file);
  if (!fs.existsSync(p)) return '';
  return `@font-face{font-family:'${family}';font-style:normal;font-weight:${weight};src:url(data:font/woff2;base64,${readB64(p)}) format('woff2');}`;
};
const FONTS_CSS = [
  ['Inter', 'inter/files/inter-latin-400-normal.woff2', 400],
  ['Inter', 'inter/files/inter-latin-500-normal.woff2', 500],
  ['Inter', 'inter/files/inter-latin-600-normal.woff2', 600],
  ['Inter', 'inter/files/inter-latin-700-normal.woff2', 700],
  ['Caveat', 'caveat/files/caveat-latin-500-normal.woff2', 500],
  ['Caveat', 'caveat/files/caveat-latin-700-normal.woff2', 700],
].map((a) => fontFace(...a)).join('\n');
const MERMAID_JS = fs.readFileSync(path.join(here, 'node_modules/mermaid/dist/mermaid.min.js'), 'utf8');
const TEMPLATE = fs.readFileSync(path.join(here, 'frame.html'), 'utf8');
const ILLUSTRATION_SVG = fs.readFileSync(path.join(here, 'illustration-lights-out.svg'), 'utf8');

// Two looks, one Mermaid source. Only the Mermaid config and the CSS theme differ.
const STYLES = {
  clean: {
    cls: 'clean',
    mermaid: {
      startOnLoad: false, look: 'classic', theme: 'base', fontFamily: 'Inter', markdownAutoWrap: false,
      themeVariables: {
        fontFamily: 'Inter', fontSize: '26px',
        primaryColor: '#E9F0FF', primaryBorderColor: '#2F6FE4', primaryTextColor: '#16213A',
        lineColor: '#51607A', secondaryColor: '#FFFFFF', tertiaryColor: '#F5F7FB', edgeLabelBackground: '#F5F7FB',
      },
      flowchart: { curve: 'basis', nodeSpacing: 44, rankSpacing: 80, padding: 20, wrappingWidth: 320 },
    },
  },
  sketch: {
    cls: 'sketch',
    mermaid: {
      startOnLoad: false, look: 'handDrawn', handDrawnSeed: 3, theme: 'base', fontFamily: 'Caveat', markdownAutoWrap: false,
      themeVariables: {
        fontFamily: 'Caveat', fontSize: '34px',
        primaryColor: '#FFF1B8', primaryBorderColor: '#1F1A14', primaryTextColor: '#1F1A14',
        lineColor: '#1F1A14', secondaryColor: '#FFFDF7', tertiaryColor: '#FBF6EA', edgeLabelBackground: '#FBF6EA',
      },
      flowchart: { curve: 'basis', nodeSpacing: 44, rankSpacing: 80, padding: 20, wrappingWidth: 320 },
    },
  },
};

const HOSTS = [{ name: 'Maya', initial: 'M' }, { name: 'Sam', initial: 'S' }];

const HOOK_LINE = "Okay, here's the thing I've never understood. I hit save, the lights go out. Is my data there or not?";
const SCENES = [
  {
    id: 'diagram', kind: 'diagram', chapter: 'Chapter 3 · Durability', title: 'The write-ahead log flips the order',
    diagram: 'diagrams/ch03/wal-flow.mmd', reveal: ['app', 'db', 'log', 'pages'], highlight: 'log', source: 'ch03 ¶7–8',
    speaker: 'Sam', progress: [50, 56],
    caption: 'Before the database touches its main data files, it appends a description of the change to a sequential log and forces that to disk.',
    // Timeline (seconds). In the real pipeline captionAt/highlightAt come from word timestamps;
    // here the caption is paced uniformly at wordsPerSecond and the highlight lands on "log".
    timeline: { revealStart: 0.4, revealEvery: 0.9, revealDur: 0.7, captionAt: 0.5, wordsPerSecond: 2.8, highlightAt: 6.5 },
  },
  {
    id: 'title', kind: 'title', chapter: 'Chapter 3 · Durability', title: '', source: 'bridge · no claim',
    speaker: 'Maya', progress: [4, 4], big: 'What happens to your data when the power goes out?', caption: HOOK_LINE,
  },
  {
    id: 'illustration', kind: 'illustration', chapter: 'Chapter 3 · Durability', title: '', source: 'decorative · no claim',
    speaker: 'Maya', progress: [4, 4], big: 'What happens to your data when the power goes out?', caption: HOOK_LINE,
  },
];

function buildHtml(style, scene) {
  const bars = '<span class="bars"><i style="--h:8px"></i><i style="--h:16px"></i><i style="--h:11px"></i><i style="--h:18px"></i><i style="--h:9px"></i></span>';
  const hostsHtml = HOSTS.map((h) => {
    const active = h.name === scene.speaker;
    return `<div class="host ${active ? 'active' : ''}"><span class="dot">${h.initial}</span>${h.name}${active ? bars : ''}</div>`;
  }).join('');
  let stage = '';
  if (scene.kind === 'title') {
    stage = `<div class="titlecard"><div class="big">${esc(scene.big)}</div><div class="rule"></div></div>`;
  } else if (scene.kind === 'illustration') {
    stage = `<div class="illus"><div class="pic">${ILLUSTRATION_SVG}</div><div class="side">${esc(scene.big)}<div class="tag">illustration · decorative</div></div></div>`;
  }
  const captionHtml = scene.caption.split(' ').map((w) => `<span class="w">${esc(w)}</span>`).join(' ');
  let html = TEMPLATE;
  for (const [k, v] of Object.entries({
    STYLE_CLASS: style.cls, FONTS_CSS, CHAPTER: esc(scene.chapter), SCENE_TITLE: esc(scene.title),
    SOURCE: esc(scene.source), STAGE_HTML: stage, SPEAKER_INITIAL: HOSTS.find((h) => h.name === scene.speaker).initial,
    SPEAKER_NAME: esc(scene.speaker), CAPTION: captionHtml, HOSTS_HTML: hostsHtml, PROGRESS: String(scene.progress[1]),
  })) html = html.replace(`{{${k}}}`, () => v);
  return html;
}

// Runs inside the page: render Mermaid into #stage, then install window.__seek(t).
async function mountDiagram(page, style, scene) {
  await page.addScriptTag({ content: MERMAID_JS });
  const src = fs.readFileSync(path.join(root, scene.diagram), 'utf8');
  await page.evaluate(async ({ cfg, src, scene }) => {
    await document.fonts.ready;
    await Promise.all([document.fonts.load('26px Inter'), document.fonts.load('34px Caveat')]);
    mermaid.initialize(cfg);
    const { svg } = await mermaid.render('mock', src);
    const stage = document.getElementById('stage');
    stage.innerHTML = svg;
    const s = stage.querySelector('svg');
    for (const a of ['style', 'width', 'height']) s.removeAttribute(a);

    const clamp = (x) => Math.max(0, Math.min(1, x));
    const ease = (u) => 1 - Math.pow(1 - u, 3);
    const tl = scene.timeline;

    // Nodes: shape geometry (rect/polygon in the classic look, rough.js paths in the
    // hand-drawn look) draws on with stroke-dashoffset; the label fades in after.
    const nodes = scene.reveal.map((id, i) => {
      const g = s.querySelector(`g[id*="flowchart-${id}-"]`);
      const shapes = [...g.querySelectorAll('rect, polygon, path')].filter((el) => !el.closest('g.label'));
      for (const el of shapes) { const L = el.getTotalLength(); el.dataset.len = L; el.style.strokeDasharray = `${L}`; }
      return { id, g, shapes, label: g.querySelector('g.label'), start: tl.revealStart + i * tl.revealEvery, dur: tl.revealDur };
    });
    const startOf = Object.fromEntries(nodes.map((n) => [n.id, n.start]));

    // Edges: id "<render-id>-L_<src>_<dst>_<n>"; an edge appears once both ends exist.
    const edges = [...s.querySelectorAll('path.flowchart-link')].map((p) => {
      const m = p.id.match(/L_([A-Za-z0-9]+)_([A-Za-z0-9]+)_(\d+)$/);
      const dotted = /edge-pattern-dotted/.test(p.getAttribute('class') || '');
      const L = p.getTotalLength();
      if (!dotted) p.style.strokeDasharray = `${L}`;
      const marker = p.style.markerEnd || p.getAttribute('marker-end') || '';
      const labelInner = s.querySelector(`g.label[data-id="${p.id.replace(/^mock-/, '')}"]`);
      const label = labelInner ? labelInner.closest('g.edgeLabel') : null;
      const start = Math.max(startOf[m[1]] ?? 0, startOf[m[2]] ?? 0) + 0.25;
      return { p, L, dotted, marker, label, start, dur: 0.6 };
    });

    const hl = s.querySelector(`g[id*="flowchart-${scene.highlight}-"]`);
    const words = [...document.querySelectorAll('#caption-text .w')];
    const bars = [...document.querySelectorAll('.host.active .bars i')];
    const progress = document.querySelector('.progress i');

    window.__seek = (t) => {
      for (const n of nodes) {
        const u = ease(clamp((t - n.start) / n.dur));
        n.g.style.opacity = t < n.start ? '0' : '1';
        for (const el of n.shapes) {
          el.style.strokeDashoffset = `${Number(el.dataset.len) * (1 - u)}`;
          el.style.fillOpacity = `${clamp((u - 0.45) / 0.55)}`;
        }
        if (n.label) n.label.style.opacity = `${clamp((u - 0.55) / 0.45)}`;
      }
      for (const e of edges) {
        const u = ease(clamp((t - e.start) / e.dur));
        e.p.style.opacity = t < e.start ? '0' : '1';
        if (e.dotted) e.p.style.opacity = `${u}`; else e.p.style.strokeDashoffset = `${e.L * (1 - u)}`;
        e.p.style.markerEnd = u >= 0.98 ? e.marker : 'none';
        if (e.label) e.label.style.opacity = `${clamp((u - 0.6) / 0.4)}`;
      }
      if (hl) {
        const on = t >= tl.highlightAt;
        hl.classList.toggle('is-highlighted', on);
        const pulse = on ? 14 + 8 * Math.sin((t - tl.highlightAt) * 4) : 0;
        hl.style.filter = on ? `drop-shadow(0 0 ${pulse}px rgba(232,89,12,.6))` : '';
      }
      const spoken = Math.floor((t - tl.captionAt) * tl.wordsPerSecond);
      words.forEach((w, i) => { w.style.opacity = i < spoken ? '1' : '0.28'; });
      bars.forEach((b, i) => { b.style.height = `${7 + 11 * Math.abs(Math.sin(t * 7.3 + i * 1.7))}px`; });
      const [p0, p1] = scene.progress;
      progress.style.width = `${p0 + (p1 - p0) * clamp(t / 10)}%`;
    };
    window.__seek(0);
  }, { cfg: style.mermaid, src, scene });
}

async function encode(framesDir, mp4) {
  const r = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(framesDir, 'f%04d.jpg'),
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-movflags', '+faststart', mp4], { stdio: 'inherit' });
  if (r.status !== 0) throw new Error('ffmpeg failed');
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  for (const scene of SCENES) {
    if (ONLY && scene.id !== ONLY) continue;
    for (const style of Object.values(STYLES)) {
      await page.setContent(buildHtml(style, scene), { waitUntil: 'load' });
      await page.evaluate(() => document.fonts.ready);
      if (scene.kind === 'diagram') {
        await mountDiagram(page, style, scene);
        if (DO_VIDEO) {
          const framesDir = path.join(outDir, `frames-${style.cls}`);
          fs.rmSync(framesDir, { recursive: true, force: true });
          fs.mkdirSync(framesDir, { recursive: true });
          const n = CLIP_SECONDS * FPS;
          for (let f = 0; f < n; f++) {
            await page.evaluate((t) => window.__seek(t), f / FPS);
            await page.screenshot({ path: path.join(framesDir, `f${String(f).padStart(4, '0')}.jpg`), type: 'jpeg', quality: 90 });
          }
          const mp4 = path.join(outDir, `scene-${scene.id}-${style.cls}.mp4`);
          await encode(framesDir, mp4);
          fs.rmSync(framesDir, { recursive: true, force: true });
          console.log('wrote', path.relative(root, mp4));
        }
        await page.evaluate((t) => window.__seek(t), CLIP_SECONDS);
      }
      const still = path.join(outDir, `scene-${scene.id}-${style.cls}.png`);
      await page.screenshot({ path: still, type: 'png' });
      console.log('wrote', path.relative(root, still));
    }
  }
  await browser.close();
}

main().catch((e) => { console.error(e); process.exit(1); });
