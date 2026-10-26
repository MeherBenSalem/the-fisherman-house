// Renders the reel's frames (marketing/reel/build/out/00000.jpg ...): the captured footage (build/frames/, from
// capture.py) with the motion graphics on top, one frame at a time, so every animation is exact at 30 fps.
// Timing comes from timeline.json, which the audio uses too. Usage (from the repository root):
//   NODE_PATH="$(npm root -g)" node marketing/reel/edit.cjs [from-second to-second]
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..', '..');
const build = path.join(__dirname, 'build');
const frames = path.join(build, 'frames');
const out = path.join(build, 'out');
const fonts = path.join(root, 'marketing', 'source', 'fonts');
const textures = path.join(root, 'tools', 'assets', 'textures');
const timeline = JSON.parse(fs.readFileSync(path.join(__dirname, 'timeline.json'), 'utf8'));
const url = (file) => 'file://' + file;

// The listing palette (marketing/source/render.cjs).
const C = {
  deep: '#0b2233', sea: '#123a55', foam: '#f4efe2', sand: '#ead8b0', rope: '#c9a66b', lantern: '#f5b544',
  buoy: '#e04a3a', kelp: '#6fbf73', ice: '#9fd8f0', swamp: '#7fae5a',
};

// Every clip's frames, so the page can pick one by index.
const sources = {};
for (const clip of timeline.clips) {
  if (clip.name === 'end') continue;
  const dir = clip.still ? path.join(frames, 'stills') : path.join(frames, clip.name);
  sources[clip.name] = clip.still
    ? [url(path.join(dir, `${clip.file || clip.name}.jpg`))]
    : fs.readdirSync(dir).filter((f) => f.endsWith('.jpg')).sort().map((f) => url(path.join(dir, f)));
}
sources.end = [sources.beach[0]];

const item = (name) => url(path.join(textures, 'item', name + '.png'));
const icon = url(path.join(root, 'marketing', 'images', 'icon.png'));

const html = `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face { font-family: Display; font-weight: 900; src: url('${url(path.join(fonts, 'playfair-900.woff2'))}'); }
@font-face { font-family: Display; font-weight: 900; font-style: italic; src: url('${url(path.join(fonts, 'playfair-900-italic.woff2'))}'); }
@font-face { font-family: Body; font-weight: 500; src: url('${url(path.join(fonts, 'barlow-500.woff2'))}'); }
@font-face { font-family: Body; font-weight: 700; src: url('${url(path.join(fonts, 'barlow-700.woff2'))}'); }
@font-face { font-family: Body; font-weight: 800; src: url('${url(path.join(fonts, 'barlow-800.woff2'))}'); }
@font-face { font-family: Cond; font-weight: 700; src: url('${url(path.join(fonts, 'barlow-condensed-700.woff2'))}'); }
* { box-sizing: border-box; margin: 0; }
html, body { width: 1080px; height: 1920px; overflow: hidden; background: #000; }
#stage { position: absolute; inset: 0; overflow: hidden; }
#bg { position: absolute; inset: 0; width: 1080px; height: 1920px; object-fit: cover; transform-origin: 50% 50%; }
#bgFill { position: absolute; inset: 0; width: 1080px; height: 1920px; object-fit: cover; transform: scale(1.25);
          filter: blur(30px) brightness(.4) saturate(1.2); display: none; }
#veil { position: absolute; inset: 0; background: ${C.deep}; opacity: 0; }
#flash { position: absolute; inset: 0; background: #fff; opacity: 0; }
/* Legibility: a soft vignette, and shades behind the text bands. */
#vignette { position: absolute; inset: 0; background: radial-gradient(ellipse 80% 60% at 50% 50%, rgba(0,0,0,0) 55%, rgba(0,0,0,.42) 100%); }
.shade { position: absolute; left: 0; right: 0; opacity: 0; }
#shadeTop { top: 0; height: 900px; background: linear-gradient(180deg, rgba(5,16,26,.72) 0%, rgba(5,16,26,.45) 45%, rgba(5,16,26,0) 100%); }
#shadeBottom { bottom: 0; height: 1100px; background: linear-gradient(0deg, rgba(5,16,26,.86) 0%, rgba(5,16,26,.6) 40%, rgba(5,16,26,0) 100%); }
.el { position: absolute; left: 0; right: 0; display: flex; flex-direction: column; align-items: center; text-align: center;
      opacity: 0; will-change: transform, opacity; }
.cap { font-family: Cond, sans-serif; font-weight: 700; text-transform: uppercase; color: #fff; line-height: .98;
       -webkit-text-stroke: 14px rgba(6,18,28,.95); paint-order: stroke fill; letter-spacing: .01em;
       filter: drop-shadow(0 8px 0 rgba(6,18,28,.55)); }
.word { display: inline-block; margin: 0 .12em; transform-origin: 50% 80%; }
.box { display: inline-block; padding: .02em .16em .06em; border-radius: .12em; background: ${C.buoy};
       -webkit-text-stroke: 0; color: #fff; box-shadow: 0 10px 0 rgba(6,18,28,.55); }
.display { font-family: Display, serif; font-weight: 900; letter-spacing: -.01em; line-height: .95; }
.gold { background: linear-gradient(180deg, #fffaf0 0%, ${C.sand} 55%, #c9a66b 100%); -webkit-background-clip: text;
        background-clip: text; color: transparent; filter: drop-shadow(0 7px 0 rgba(6,18,28,.9)) drop-shadow(0 0 36px rgba(0,0,0,.5)); }
.kicker { font-family: Cond, sans-serif; font-weight: 700; text-transform: uppercase; letter-spacing: .28em;
          color: ${C.lantern}; font-size: 44px; filter: drop-shadow(0 4px 0 rgba(6,18,28,.9)); }
.sub { font-family: Body, sans-serif; font-weight: 800; color: ${C.foam}; font-size: 58px; line-height: 1.1;
       -webkit-text-stroke: 10px rgba(6,18,28,.9); paint-order: stroke fill; }
.chip { display: inline-flex; align-items: center; gap: 18px; padding: 14px 18px 14px 30px; border-radius: 999px;
        background: rgba(11,34,51,.88); border: 4px solid rgba(234,216,176,.5); box-shadow: 0 16px 40px rgba(0,0,0,.45);
        font-family: Cond, sans-serif; font-weight: 700; font-size: 46px; letter-spacing: .1em; color: ${C.foam}; text-transform: uppercase; }
.count { display: inline-block; min-width: 118px; padding: 6px 16px 4px; border-radius: 999px; background: ${C.lantern};
         color: ${C.deep}; letter-spacing: .02em; }
.name { font-family: Cond, sans-serif; font-weight: 700; text-transform: uppercase; color: #fff; font-size: 116px; line-height: 1;
        -webkit-text-stroke: 14px rgba(6,18,28,.95); paint-order: stroke fill; white-space: nowrap;
        filter: drop-shadow(0 8px 0 rgba(6,18,28,.55)); }
.where { display: inline-flex; align-items: center; gap: 16px; margin-top: 18px; padding: 10px 28px 10px 22px; border-radius: 999px;
         background: rgba(11,34,51,.88); font-family: Body, sans-serif; font-weight: 700; font-size: 44px; color: ${C.foam}; }
.dot { width: 26px; height: 26px; border-radius: 50%; box-shadow: 0 0 0 4px rgba(244,239,226,.9); }
.tiles { display: flex; gap: 26px; }
.tile { width: 280px; padding: 26px 12px 22px; border-radius: 26px; background: rgba(11,34,51,.92); border: 5px solid var(--c);
        display: flex; flex-direction: column; align-items: center; gap: 12px; box-shadow: 0 20px 44px rgba(0,0,0,.5); }
.tile img { width: 128px; height: 128px; image-rendering: pixelated; }
.tile .n { font-family: Display, serif; font-weight: 900; font-size: 40px; color: ${C.foam}; line-height: 1; }
.tile .s { font-family: Cond, sans-serif; font-weight: 700; font-size: 40px; color: var(--c); text-transform: uppercase; letter-spacing: .04em; }
.pill { display: inline-block; padding: 12px 30px 10px; border-radius: 999px; font-family: Cond, sans-serif; font-weight: 700;
        font-size: 50px; letter-spacing: .06em; text-transform: uppercase; color: ${C.deep}; background: ${C.foam};
        box-shadow: 0 12px 30px rgba(0,0,0,.45); }
.cta { display: inline-flex; align-items: center; gap: 22px; padding: 26px 46px 24px; border-radius: 999px; background: ${C.lantern};
       color: ${C.deep}; font-family: Body, sans-serif; font-weight: 800; font-size: 50px; box-shadow: 0 18px 44px rgba(0,0,0,.5); }
.rope { width: 520px; height: 10px; border-radius: 5px; margin: 26px 0 24px;
        background: repeating-linear-gradient(135deg, ${C.rope} 0 9px, #8a6a3a 9px 14px); box-shadow: 0 4px 0 rgba(6,18,28,.7); }
.iconimg { width: 250px; height: 250px; border-radius: 52px; box-shadow: 0 0 0 6px rgba(6,18,28,.85), 0 24px 60px rgba(0,0,0,.6); }
</style></head><body><div id="stage">
<img id="bgFill">
<img id="bg">
<div id="vignette"></div>
<div id="shadeTop" class="shade"></div>
<div id="shadeBottom" class="shade"></div>
<div id="veil"></div>

<!-- 0-2 s: the hook, readable from the first frame and without sound -->
<div id="hook" class="el cap" style="top: 470px; font-size: 150px;">
  <div><span class="word" id="w1">Minecraft</span></div>
  <div><span class="word" id="w2">beaches</span> <span class="word" id="w3">are</span></div>
  <div style="margin-top: 22px"><span class="word box" id="w4">boring.</span></div>
</div>

<!-- 2-3 s: the turn -->
<div id="turn" class="el" style="top: 520px;">
  <div class="display" style="font-style: italic; font-size: 190px; color: ${C.lantern}; -webkit-text-stroke: 16px rgba(6,18,28,.95);
       paint-order: stroke fill; filter: drop-shadow(0 10px 0 rgba(6,18,28,.6));">Not<br>anymore.</div>
</div>

<!-- 3-5 s: who is talking -->
<div id="title" class="el" style="top: 930px;">
  <img class="iconimg" id="titleIcon" src="${icon}">
  <div class="kicker" id="titleKicker" style="margin-top: 34px;">The Minecraft mod</div>
  <div class="display gold" id="titleName" style="font-size: 132px; margin-top: 10px;">Fisherman's Coast</div>
  <div class="sub" id="titleTag" style="margin-top: 26px;">7 places, one for every shore</div>
</div>

<!-- 5-16 s: the seven places (the Cottage is the 1.x house, repaired; the other six are new) -->
<div id="chip" class="el" style="top: 300px;"><div class="chip"><span>7 coastal places</span><span class="count" id="count">1/7</span></div></div>
<div id="label" class="el" style="top: 1190px;">
  <div class="name" id="labelName">Name</div>
  <div class="where"><span class="dot" id="labelDot"></span><span id="labelWhere">where</span></div>
</div>

<!-- 16-18 s: Crab Pots -->
<div id="pots" class="el" style="top: 330px;">
  <div class="kicker">New block</div>
  <div class="display gold" style="font-size: 170px; margin-top: 8px;">Crab Pots</div>
  <div class="sub" style="margin-top: 22px;">catch fish while you're AFK</div>
</div>
<div id="potsFoot" class="el" style="top: 1300px;"><div class="pill">by biome · hopper-ready · 2× in rain</div></div>

<!-- 18-19.5 s: bait -->
<div id="bait" class="el" style="top: 330px;">
  <div class="kicker">Add bait</div>
  <div class="display gold" style="font-size: 150px; margin-top: 8px;">Faster.<br>Luckier.</div>
</div>
<div id="baitTiles" class="el" style="top: 820px;"><div class="tiles">
  <div class="tile" id="t1" style="--c:${C.sand}"><img src="${item('fish_bait')}"><div class="n">Fish Bait</div><div class="s">2× faster</div></div>
  <div class="tile" id="t2" style="--c:${C.buoy}"><img src="${item('chum')}"><div class="n">Chum</div><div class="s">3× faster</div></div>
  <div class="tile" id="t3" style="--c:${C.ice}"><img src="${item('glow_bait')}"><div class="n">Glow Bait</div><div class="s">+ treasure</div></div>
</div></div>

<!-- 19.5-21 s: residents -->
<div id="trades" class="el" style="top: 330px;">
  <div class="kicker">6 named fishermen</div>
  <div class="display gold" style="font-size: 150px; margin-top: 8px;">Exclusive<br>trades</div>
</div>
<div id="tradesFoot" class="el" style="top: 1320px;"><div class="pill">pots · bait · nets · bottles</div></div>

<!-- 21-22.5 s: Messages in a Bottle -->
<div id="bottle" class="el" style="top: 330px;">
  <div class="kicker">Messages in a bottle</div>
  <div class="display gold" style="font-size: 150px; margin-top: 8px;">Treasure<br>maps</div>
  <div class="sub" style="margin-top: 22px;">to sunken trawlers</div>
</div>

<!-- 22.5-26 s: the end card, which loops back into the first frame -->
<div id="end" class="el" style="top: 330px;">
  <img class="iconimg" id="endIcon" src="${icon}" style="width: 270px; height: 270px;">
  <div class="kicker" id="endKicker" style="margin-top: 40px;">Free Minecraft mod</div>
  <div class="display gold" id="endName" style="font-size: 140px; margin-top: 12px;">Fisherman's<br>Coast</div>
  <div class="rope" id="endRope"></div>
  <div id="endLoaders" style="display: flex; gap: 18px;"><span class="pill">Fabric</span><span class="pill">NeoForge</span><span class="pill">Forge</span></div>
  <div class="sub" id="endVersions" style="margin-top: 26px; font-size: 52px;">Minecraft 1.20.1 → 26.3</div>
  <div class="cta" id="endCta" style="margin-top: 70px;">
    <svg width="56" height="56" viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2z" fill="${C.deep}"/></svg>
    Send this to your fishing duo
  </div>
  <div class="sub" id="endWhere" style="margin-top: 30px; font-size: 44px; color: ${C.sand};">CurseForge & Modrinth</div>
</div>

<div id="flash"></div>
</div>
<script>
const T = ${JSON.stringify(timeline)};
const SRC = ${JSON.stringify(sources)};
const C = ${JSON.stringify(C)};
const $ = (id) => document.getElementById(id);
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const prog = (t, t0, d) => clamp((t - t0) / d);
const easeOut = (x) => 1 - Math.pow(1 - x, 3);
const easeIn = (x) => x * x * x;
const back = (x) => { const c1 = 2.2, c3 = c1 + 1; return x <= 0 ? 0 : 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };

// An element that pops in (scale from \`from\`, with overshoot) at t0 and fades out over \`outD\` before t1.
function pop(el, t, t0, t1, opt = {}) {
  const { d = 0.22, from = 0.4, outD = 0.12, dy = 0, rot = 0, exitScale = 1.08 } = opt;
  if (t < t0 || t >= t1) { el.style.opacity = 0; return; }
  const i = prog(t, t0, d), o = prog(t, t1 - outD, outD);
  const s = (from + (1 - from) * back(i)) * (1 + (exitScale - 1) * easeIn(o));
  el.style.opacity = clamp(i * 4) * (1 - o);
  el.style.transform = 'translateY(' + (dy * (1 - easeOut(i))) + 'px) scale(' + s + ') rotate(' + (rot * (1 - easeOut(i))) + 'deg)';
}
// An element that slides up into place.
function rise(el, t, t0, t1, opt = {}) {
  const { d = 0.25, dy = 60, outD = 0.12 } = opt;
  if (t < t0 || t >= t1) { el.style.opacity = 0; return; }
  const i = easeOut(prog(t, t0, d)), o = prog(t, t1 - outD, outD);
  el.style.opacity = i * (1 - o);
  el.style.transform = 'translateY(' + (dy * (1 - i) - 30 * easeIn(o)) + 'px)';
}
function clipAt(t) { return T.clips.find((c) => t >= c.start && t < c.end) || T.clips[T.clips.length - 1]; }
function shade(id, v) { $(id).style.opacity = v; }

const loaded = {};
async function setBg(src, still) {
  const bg = $('bg'), fill = $('bgFill');
  fill.style.display = still ? 'block' : 'none';
  if (bg.dataset.src === src) return;
  bg.src = src; bg.dataset.src = src;
  if (still) { fill.src = src; await fill.decode(); }
  await bg.decode();
}
// How each still is framed (from the GUI's position in the capture): zoom about the GUI, move, blur behind cards.
const STILL = {
  bait: { scale: 1.15, x: 0, y: 0, blur: 6, bright: 0.7 },         // the baited pots, blurred behind the bait cards
  trades: { scale: 1.15, x: -40, y: 50, blur: 0, bright: 1 },     // the trades GUI under the title, clear of the buttons on the right
  bottle: { scale: 1.0, x: 0, y: -400, blur: 0, bright: 1 },      // the note in chat and the map, above the caption bar
};

window.renderFrame = async (t) => {
  const c = clipAt(t);
  const local = t - c.start, len = c.end - c.start;
  const list = SRC[c.name];
  const index = Math.min(list.length - 1, Math.floor(local * T.fps + 1e-6));
  await setBg(list[index], !!c.still);

  // Background motion: zoom punches at every cut, a shake on the drop, Ken Burns on the stills, the end card's blur.
  let scale = 1, blur = 0, dx = 0, dy = 0, bright = 1;
  const next = T.clips.find((k) => k.start === c.end);
  if (next && c.end - t < 0.1 && next.name !== 'end') { const p = 1 - (c.end - t) / 0.1; scale *= 1 + 0.22 * easeIn(p); blur = 12 * p; }
  if (local < 0.14 && c.name !== 'beach' && c.name !== 'end') { const p = local / 0.14; scale *= 1.22 - 0.22 * easeOut(p); blur = Math.max(blur, 12 * (1 - p)); }
  if (c.still) {
    const k = STILL[c.name];
    scale *= k.scale * (1.0 + 0.05 * (local / len)); dx += k.x; dy += k.y; blur = Math.max(blur, k.blur); bright = k.bright;
  }
  if (c.name === 'lighthouse' && local < 0.35) { const a = 18 * (1 - local / 0.35); dx = a * Math.sin(local * 90); dy = a * Math.cos(local * 70); }
  if (c.name === 'end') {
    const out = prog(t, 25.7, 0.3);
    scale = 1.06 - 0.06 * easeOut(out); blur = 22 * (1 - easeOut(out)); bright = 0.75 + 0.25 * out;
    $('veil').style.opacity = 0.55 * (1 - easeOut(out));
  } else {
    $('veil').style.opacity = 0;
  }
  const bg = $('bg');
  bg.style.transform = 'translate(' + dx + 'px,' + dy + 'px) scale(' + scale + ')';
  bg.style.filter = (blur > 0.05 ? 'blur(' + blur + 'px) ' : '') + 'brightness(' + bright + ')';

  // Flashes on the big beats.
  let flash = 0;
  for (const b of [2.0, 5.0, 16.0, 22.5]) { const d = t - b; if (d >= 0 && d < 0.12) flash = Math.max(flash, 0.35 * (1 - d / 0.12)); }
  $('flash').style.opacity = flash;

  // Shades behind the text.
  const topShade = (t >= 2.0 && t < 3.05) || (t >= 16.0 && t < 22.5) ? 1 : (t < 2.0 || t >= 25.85 ? 0.55 : (t >= 5.0 && t < 16.0 ? 0.6 : 0));
  shade('shadeTop', topShade);
  shade('shadeBottom', (t >= 3.0 && t < 16.0) || (t >= 16.0 && t < 22.5) ? 1 : 0);

  // 0-2: the hook (already on screen in the first frame), and again at the very end so the loop is seamless.
  const hook = $('hook');
  const hookOn = t < 1.97 || t >= 25.84;
  hook.style.opacity = hookOn ? 1 : 0;
  const ht = t >= 25.84 ? t - 25.84 : t;
  const words = [['w1', -1], ['w2', -1], ['w3', 0.5], ['w4', 1.0]];
  for (const [id, at] of words) {
    const w = $(id);
    if (t >= 25.84) { const i = prog(ht, 0, 0.16); w.style.opacity = id === 'w1' || id === 'w2' ? i : 0; w.style.transform = 'scale(' + (0.6 + 0.4 * back(i)) + ')'; continue; }
    if (at < 0) { w.style.opacity = 1; w.style.transform = 'scale(' + (1 + 0.04 * Math.sin(t * 6)) + ')'; continue; }
    const i = prog(t, at, 0.2);
    w.style.opacity = t < at ? 0 : 1;
    w.style.transform = 'scale(' + (0.3 + 0.7 * back(i)) + ') rotate(' + (id === 'w4' ? -4 * back(i) : 0) + 'deg)';
  }
  if (t >= 1.85 && t < 1.97) hook.style.transform = 'scale(' + (1 + 0.6 * easeIn(prog(t, 1.85, 0.12))) + ')';
  else hook.style.transform = 'none';
  if (t >= 1.85 && t < 1.97) hook.style.opacity = 1 - prog(t, 1.85, 0.12);

  // 2-3: the turn.
  pop($('turn'), t, 2.0, 3.0, { d: 0.25, from: 2.2, rot: -6, outD: 0.12 });

  // 3-5: the title.
  pop($('title'), t, 3.0, 5.0, { d: 0.01, from: 1, outD: 0.15 });
  if (t >= 3.0 && t < 5.0) {
    pop($('titleIcon'), t, 3.0, 5.0, { d: 0.3, from: 0, rot: -12, outD: 0.01 });
    rise($('titleKicker'), t, 3.12, 5.0, { outD: 0.01 });
    rise($('titleName'), t, 3.2, 5.0, { dy: 80, outD: 0.01 });
    pop($('titleTag'), t, 3.5, 5.0, { from: 0.6, outD: 0.01 });
  }

  // 5-16: the seven places.
  rise($('chip'), t, 5.0, 16.0, { dy: -80, outD: 0.15 });
  const place = T.clips.find((k) => k.place && t >= k.start && t < k.end);
  const label = $('label');
  if (place) {
    $('count').textContent = place.place + '/7';
    const ci = prog(t, place.start, 0.15);
    $('count').style.transform = 'scale(' + (0.6 + 0.4 * back(ci)) + ')';
    $('count').style.display = 'inline-block';
    const name = $('labelName');
    if (name.dataset.v !== place.title) {
      name.textContent = place.title; name.dataset.v = place.title;
      // Long names shrink to stay clear of the side of the screen (Instagram's buttons sit on the right).
      name.style.fontSize = '116px';
      if (name.scrollWidth > 900) name.style.fontSize = (116 * 900 / name.scrollWidth) + 'px';
      $('labelWhere').textContent = place.where;
      $('labelDot').style.background = C[place.color];
    }
    const i = easeOut(prog(t, place.start + 0.04, 0.22));
    const o = prog(t, place.end - 0.1, 0.1);
    label.style.opacity = 1 - o;
    label.style.clipPath = 'inset(0 ' + (100 * (1 - i)) + '% 0 0)';
    label.style.transform = 'translateX(' + (-40 * (1 - i)) + 'px)';
  } else {
    label.style.opacity = 0;
  }

  // 16-18: Crab Pots.
  pop($('pots'), t, 16.0, 18.0, { d: 0.28, from: 0.5, dy: -40 });
  rise($('potsFoot'), t, 16.5, 18.0);
  // 18-19.5: bait.
  pop($('bait'), t, 18.0, 19.5, { d: 0.25, from: 0.5 });
  $('baitTiles').style.opacity = t >= 18.0 && t < 19.5 ? 1 - prog(t, 19.38, 0.12) : 0;
  pop($('t1'), t, 18.15, 19.6, { from: 0, dy: 80, outD: 0.01 });
  pop($('t2'), t, 18.4, 19.6, { from: 0, dy: 80, outD: 0.01 });
  pop($('t3'), t, 18.65, 19.6, { from: 0, dy: 80, outD: 0.01 });
  // 19.5-21: trades.
  pop($('trades'), t, 19.5, 21.0, { d: 0.25, from: 0.5 });
  rise($('tradesFoot'), t, 19.8, 21.0);
  // 21-22.5: the bottle.
  pop($('bottle'), t, 21.0, 22.5, { d: 0.25, from: 0.5 });

  // 22.5-26: the end card.
  const endOn = t >= 22.5 && t < 25.85;
  $('end').style.opacity = endOn ? 1 - prog(t, 25.6, 0.25) : 0;
  $('end').style.transform = 'scale(' + (1 - 0.06 * easeIn(prog(t, 25.6, 0.25))) + ')';
  if (endOn) {
    pop($('endIcon'), t, 22.5, 26, { d: 0.35, from: 0, rot: -14, outD: 0.01 });
    rise($('endKicker'), t, 22.65, 26, { outD: 0.01 });
    rise($('endName'), t, 22.75, 26, { dy: 90, outD: 0.01 });
    const r = easeOut(prog(t, 22.9, 0.3)); $('endRope').style.opacity = r; $('endRope').style.transform = 'scaleX(' + r + ')';
    pop($('endLoaders'), t, 23.0, 26, { from: 0.4, outD: 0.01 });
    rise($('endVersions'), t, 23.2, 26, { outD: 0.01 });
    pop($('endCta'), t, 23.5, 26, { d: 0.3, from: 0.2, outD: 0.01 });
    const wob = t > 23.8 ? 1 + 0.035 * Math.max(0, Math.sin((t - 23.8) * Math.PI * 2)) : null;
    if (wob) $('endCta').style.transform = 'scale(' + wob + ')';
    rise($('endWhere'), t, 23.8, 26, { outD: 0.01 });
  }
};
</script></body></html>`;

(async () => {
  // `edit.cjs 0.5,2.1,9` renders only those moments (to build/test/), to check a design change quickly.
  const times = process.argv[2] && process.argv[2].includes(',') ? process.argv[2].split(',').map(Number) : null;
  const from = times ? 0 : Number(process.argv[2] || 0);
  const to = times ? 0 : Number(process.argv[3] || timeline.duration);
  fs.mkdirSync(out, { recursive: true });
  const file = path.join(build, 'edit.html');
  fs.writeFileSync(file, html);
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto(url(file));
  await page.evaluate(() => document.fonts.ready);
  if (times) {
    const dir = path.join(build, 'test');
    fs.mkdirSync(dir, { recursive: true });
    for (const t of times) {
      await page.evaluate((x) => window.renderFrame(x), t);
      await page.screenshot({ path: path.join(dir, t.toFixed(2) + '.jpg'), type: 'jpeg', quality: 90 });
    }
    await browser.close();
    return;
  }
  const first = Math.round(from * timeline.fps);
  const last = Math.round(to * timeline.fps);
  for (let f = first; f < last; f++) {
    await page.evaluate((t) => window.renderFrame(t), f / timeline.fps);
    await page.screenshot({ path: path.join(out, String(f).padStart(5, '0') + '.jpg'), type: 'jpeg', quality: 94 });
    if (f % 60 === 0) console.log('frame', f, '/', last);
  }
  await browser.close();
})();
