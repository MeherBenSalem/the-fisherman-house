// Renders the listing artwork in marketing/images/ from real in-game captures (marketing/images/screenshots/), the
// mod's own textures and the bundled OFL fonts. Usage (from the repository root): node marketing/source/render.cjs [name...]
// Requires the `playwright` package with a Chromium build available (NODE_PATH="$(npm root -g)" if installed globally).
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');

// The release and the supported Minecraft versions. Adding a version is one line here
// (plus one row in the download table of curseforge/description.md).
const RELEASE = { version: '2.0', name: 'The Living Coast' };
const VERSIONS = [
  { minecraft: '1.20.1', loaders: ['Fabric', 'Forge'] },
  { minecraft: '1.21.1', loaders: ['Fabric', 'NeoForge'] },
  { minecraft: '26.1.2', loaders: ['Fabric', 'NeoForge'] },
  { minecraft: '26.2', loaders: ['Fabric', 'NeoForge'] },
  { minecraft: '26.3', loaders: ['Fabric', 'NeoForge'] },
];
const LOADERS = ['Fabric', 'Forge', 'NeoForge'].filter((loader) => VERSIONS.some((v) => v.loaders.includes(loader)));

// The palette of a weathered harbour: deep sea, sand, rope, lantern light and buoy red. Each feature has its colour.
const C = {
  deep: '#0b2233', sea: '#123a55', foam: '#f4efe2', sand: '#ead8b0', rope: '#c9a66b', lantern: '#f5b544',
  buoy: '#e04a3a', kelp: '#6fbf73', ice: '#9fd8f0', swamp: '#7fae5a',
};

const root = path.resolve(__dirname, '..', '..');
const out = path.join(root, 'marketing', 'images');
const shots = path.join(out, 'screenshots');
const fonts = path.join(__dirname, 'fonts');
const textures = path.join(root, 'tools', 'assets', 'textures');
const url = (file) => 'file://' + file;
const shot = (name) => url(path.join(shots, name));
const tex = (name) => url(path.join(textures, name + '.png'));

const css = `
@font-face { font-family: Display; font-weight: 700; src: url('${url(path.join(fonts, 'playfair-700.woff2'))}'); }
@font-face { font-family: Display; font-weight: 900; src: url('${url(path.join(fonts, 'playfair-900.woff2'))}'); }
@font-face { font-family: Display; font-weight: 900; font-style: italic; src: url('${url(path.join(fonts, 'playfair-900-italic.woff2'))}'); }
@font-face { font-family: Body; font-weight: 500; src: url('${url(path.join(fonts, 'barlow-500.woff2'))}'); }
@font-face { font-family: Body; font-weight: 700; src: url('${url(path.join(fonts, 'barlow-700.woff2'))}'); }
@font-face { font-family: Body; font-weight: 800; src: url('${url(path.join(fonts, 'barlow-800.woff2'))}'); }
@font-face { font-family: Cond; font-weight: 700; src: url('${url(path.join(fonts, 'barlow-condensed-700.woff2'))}'); }
* { box-sizing: border-box; }
html, body { margin: 0; background: ${C.deep}; color: ${C.foam}; font-family: Body, sans-serif; font-weight: 700; }
.stage { position: relative; overflow: hidden;
         background: radial-gradient(ellipse at 80% -20%, rgba(245,181,68,.22) 0%, rgba(245,181,68,0) 45%),
                     linear-gradient(170deg, ${C.sea} 0%, ${C.deep} 72%); }
.display { font-family: Display, serif; font-weight: 900; letter-spacing: -.005em; }
.title { background: linear-gradient(180deg, #fffaf0 0%, ${C.sand} 55%, #c9a66b 100%);
         -webkit-background-clip: text; background-clip: text; color: transparent; }
.shadow { filter: drop-shadow(0 4px 0 rgba(5,16,26,.9)) drop-shadow(0 0 28px rgba(245,181,68,.22)); }
.kicker { font-family: Cond, sans-serif; color: ${C.lantern}; letter-spacing: .24em; font-size: 24px; text-transform: uppercase; }
.waves { position: absolute; inset: 0; opacity: .08;
         background: radial-gradient(circle at 50% 100%, transparent 18px, #fff 19px, #fff 21px, transparent 22px) 0 0 / 46px 24px; }
.glow { position: absolute; width: 560px; height: 560px; right: -180px; top: -260px; border-radius: 50%;
        background: radial-gradient(circle, rgba(245,181,68,.45) 0%, rgba(245,181,68,.06) 55%, rgba(245,181,68,0) 70%); }
.backdrop { position: absolute; inset: -40px; background-size: cover; background-position: center;
            filter: blur(14px) brightness(.3) saturate(1.15); }
.frame { position: relative; overflow: hidden; background: #000; border-radius: 16px; border: 6px solid ${C.sand};
         box-shadow: 0 0 0 3px rgba(5,16,26,.9), 0 26px 60px rgba(0,0,0,.6); }
.frame img.fill { display: block; width: 100%; height: 100%; object-fit: cover; }
.rope { height: 6px; border-radius: 3px; opacity: .9;
        background: repeating-linear-gradient(135deg, ${C.rope} 0 6px, #8a6a3a 6px 9px); }
.label { position: absolute; display: inline-flex; align-items: center; gap: 10px; padding: 7px 16px 6px; border-radius: 999px;
         font-family: Cond, sans-serif; font-size: 19px; letter-spacing: .1em; text-transform: uppercase; color: ${C.deep};
         background: ${C.foam}; box-shadow: 0 6px 18px rgba(0,0,0,.45); white-space: nowrap; }
.dot { display: inline-block; width: 12px; height: 12px; border-radius: 50%; }
ul.points { list-style: none; padding: 0; margin: 0; }
ul.points li { position: relative; padding-left: 38px; margin: 0 0 15px; font-size: 26px; line-height: 1.3; color: #e9e2d0; font-weight: 500; }
ul.points li::before { content: ''; position: absolute; left: 2px; top: 6px; width: 18px; height: 18px; border-radius: 50%;
                       background: radial-gradient(circle at 50% 50%, ${C.foam} 0 30%, var(--accent, ${C.buoy}) 31% 62%, ${C.foam} 63%);
                       box-shadow: 0 0 0 2px rgba(5,16,26,.6); }
b.hi { color: #fff; font-weight: 800; }
.stats { display: flex; margin-top: 22px; border-radius: 14px; overflow: hidden; background: rgba(11,34,51,.9);
         border: 3px solid rgba(234,216,176,.28); box-shadow: 0 18px 50px rgba(0,0,0,.5); }
.stats > div { flex: 1; padding: 12px 20px 10px; border-left: 3px solid rgba(234,216,176,.14); }
.stats > div:first-child { border-left: 0; }
.stats .t { font-family: Cond, sans-serif; font-size: 16px; letter-spacing: .16em; color: #b9c8d2; text-transform: uppercase; }
.stats .v { font-family: Display, serif; font-weight: 900; font-size: 32px; color: ${C.foam}; margin-top: 2px; white-space: nowrap; }
.pill { display: inline-block; border-radius: 999px; padding: 6px 20px 5px; margin-right: 10px; font-family: Cond, sans-serif;
        font-size: 23px; letter-spacing: .08em; color: ${C.deep}; background: ${C.lantern}; }
.item { image-rendering: pixelated; display: block; }
.tile { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 18px 10px 14px; border-radius: 16px;
        background: rgba(11,34,51,.88); border: 3px solid var(--c); box-shadow: 0 14px 34px rgba(0,0,0,.45); }
.tile .n { font-family: Display, serif; font-weight: 900; font-size: 26px; color: ${C.foam}; text-align: center; line-height: 1.05; }
.tile .s { font-size: 18px; color: #c9d4db; text-align: center; line-height: 1.25; font-weight: 500; }
`;

const page = (width, height, body, transparent = false) => `<!doctype html><html><head><meta charset="utf-8"><style>${css}
body { width: ${width}px; height: ${height}px; } .stage { width: ${width}px; height: ${height}px; }
${transparent ? 'html, body, .stage { background: transparent; }' : ''}</style></head>
<body><div class="stage">${body}</div></body></html>`;

// A capture shown in a frame of the given size; `pos` is the CSS object-position (which part stays in view).
const framed = (file, w, h, pos = 'center', style = '') =>
  `<div class="frame" style="width:${w}px;height:${h}px;${style}"><img class="fill" src="${shot(file)}" style="object-position:${pos}"></div>`;
const label = (text, color, pos) => `<span class="label" style="${pos}"><span class="dot" style="background:${color}"></span>${text}</span>`;
const stats = (items) => `<div class="stats">${items.map(([t, v, flex]) =>
  `<div${flex ? ` style="flex:${flex}"` : ''}><div class="t">${t}</div><div class="v">${v}</div></div>`).join('')}</div>`;
const item = (name, size) => `<img class="item" src="${tex(name)}" style="width:${size}px;height:${size}px">`;

// A feature card: copy on the left, artwork on the right.
const card = ({ kicker, title, points, art, width = 1600, height = 900, artWidth = 940, backdrop, color = C.buoy }) => page(width, height, `
  <div class="backdrop" style="background-image:url('${shot(backdrop)}')"></div><div class="waves"></div><div class="glow"></div>
  <div style="position:absolute;left:74px;top:0;bottom:0;width:${width - artWidth - 146}px;display:flex;flex-direction:column;justify-content:center;--accent:${color}">
    <div class="kicker" style="color:${color}">${kicker}</div>
    <div class="display title shadow" style="font-size:66px;line-height:1.04;margin:12px 0 22px">${title}</div>
    <div class="rope" style="width:220px;margin-bottom:30px"></div>
    <ul class="points">${points.map((point) => `<li>${point.replace(/ (\S+)$/, '&nbsp;$1')}</li>`).join('')}</ul>
  </div>
  <div style="position:absolute;right:62px;top:50%;transform:translateY(-50%);width:${artWidth}px">${art}</div>`);

const versionText = VERSIONS.map((v) => v.minecraft).join(' · ');

// The first lines of the config file the mod writes on first start (copied from a generated file).
const configPanel = () => {
  const file = path.join(__dirname, 'config-excerpt.json');
  const esc = (t) => t.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const text = fs.readFileSync(file, 'utf8').split('\n').slice(0, 30).map((line) => {
    if (/^\s*\/\//.test(line)) return `<span style="color:#8fa3b1">${esc(line)}</span>`;
    return esc(line).replace(/("[^"]+")(:)/g, `<span style="color:${C.lantern}">$1</span>$2`)
      .replace(/: (true|false|-?[\d.]+|"[^"]*")/g, `: <span style="color:${C.kelp}">$1</span>`);
  }).join('\n');
  return `<pre style="margin:0;padding:20px 22px;font-size:14px;line-height:1.5;color:#e6e0d2;white-space:pre;font-family:'DejaVu Sans Mono',monospace">${text}</pre>`;
};

// The seven places, each as a small framed capture with its name.
const PLACES = [
  ['cottage.jpg', "Fisherman's Cottage", 'Beaches', C.sand], ['harbour_pier.jpg', 'Harbour Pier', 'Sandy beaches', C.lantern],
  ['lighthouse.jpg', 'Lighthouse', 'Stony shores', C.buoy], ['stilt_shack.jpg', 'Stilt Shack', 'Swamps', C.swamp],
  ['ice_fishing_camp.jpg', 'Ice Fishing Camp', 'Frozen seas', C.ice], ['river_boathouse.jpg', 'River Boathouse', 'Rivers', C.kelp],
  ['sunken_trawler.jpg', 'Sunken Trawler', 'The sea floor', '#5aa9e6'],
];

const header = (title, color = C.lantern) => page(1400, 120, `
  <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;gap:24px">
    <div class="rope" style="width:240px"></div>
    <span class="dot" style="width:18px;height:18px;background:radial-gradient(circle,${C.foam} 0 30%,${color} 31% 62%,${C.foam} 63%)"></span>
    <div class="display title shadow" style="font-size:58px;white-space:nowrap">${title}</div>
    <span class="dot" style="width:18px;height:18px;background:radial-gradient(circle,${C.foam} 0 30%,${color} 31% 62%,${C.foam} 63%)"></span>
    <div class="rope" style="width:240px"></div>
  </div>`, true);

const divider = () => page(1400, 44, `
  <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;gap:16px">
    <div class="rope" style="width:420px;opacity:.75"></div>
    ${[C.sand, C.lantern, C.buoy, C.kelp, C.ice].map((c) => `<span class="dot" style="width:16px;height:16px;background:radial-gradient(circle,${C.foam} 0 30%,${c} 31% 62%,${C.foam} 63%)"></span>`).join('')}
    <div class="rope" style="width:420px;opacity:.75"></div>
  </div>`, true);

const assets = {
  banner: () => page(1800, 600, `
    <img src="${shot('lighthouse.jpg')}" style="position:absolute;right:-60px;top:-150px;width:1380px;-webkit-mask-image:linear-gradient(90deg,transparent 0%,#000 32%);mask-image:linear-gradient(90deg,transparent 0%,#000 32%)">
    <div style="position:absolute;inset:0;background:linear-gradient(90deg,rgba(11,34,51,.98) 0%,rgba(11,34,51,.93) 33%,rgba(11,34,51,.3) 60%,rgba(11,34,51,0) 80%)"></div>
    <div style="position:absolute;inset:0;background:linear-gradient(0deg,rgba(11,34,51,.8) 0%,rgba(11,34,51,0) 30%)"></div>
    <div class="waves" style="-webkit-mask-image:linear-gradient(90deg,#000 0%,#000 36%,transparent 58%);mask-image:linear-gradient(90deg,#000 0%,#000 36%,transparent 58%)"></div>
    <div style="position:absolute;left:84px;top:62px;width:1100px">
      <div class="kicker">${RELEASE.version} · ${RELEASE.name}</div>
      <div class="display title shadow" style="display:inline-block;font-size:112px;line-height:1.02;margin:12px 0 18px;padding-right:12px;white-space:nowrap">Fisherman’s Coast</div>
      <div class="rope" style="width:560px;margin-bottom:24px"></div>
      <div style="font-size:33px;color:${C.foam};line-height:1.3;font-weight:800">Seven fishing places on every kind of shore,<br>Crab Pots, bait, and bottles that lead to sunken treasure.</div>
      <div style="margin-top:28px">${LOADERS.map((l) => `<span class="pill">${l}</span>`).join('')}
        <span style="font-family:Cond,sans-serif;font-size:24px;color:#c3d1db;margin-left:6px;letter-spacing:.05em">${versionText}</span></div>
    </div>`),

  icon: () => page(512, 512, `
    <div style="position:absolute;inset:0;border-radius:96px;overflow:hidden;background:${C.deep}">
      <img src="${shot('lighthouse.jpg')}" style="position:absolute;width:1320px;left:-420px;top:-150px;filter:saturate(1.15) contrast(1.05)">
      <div style="position:absolute;inset:0;background:radial-gradient(ellipse at 50% 42%,rgba(11,34,51,0) 0%,rgba(11,34,51,.25) 55%,rgba(11,34,51,.9) 100%)"></div>
      <img class="item" src="${tex('item/message_in_a_bottle')}" style="position:absolute;width:176px;height:176px;right:28px;bottom:26px;filter:drop-shadow(0 8px 0 rgba(5,16,26,.85))">
    </div>
    <div style="position:absolute;inset:0;border-radius:96px;border:12px solid transparent;
                background:repeating-linear-gradient(135deg, ${C.rope} 0 12px, #8a6a3a 12px 18px) border-box;
                -webkit-mask:linear-gradient(#000 0 0) padding-box, linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude"></div>`, true),

  'card-coast': () => card({
    kicker: 'The headline', title: 'A whole coast,<br>alive', color: C.lantern, backdrop: 'harbour_pier.jpg',
    points: ['<b class="hi">Seven places</b>, one for every kind of shore', 'Each with its own <b class="hi">resident</b>, trades and loot',
      'Placed only where the land suits them', 'The original house is back, repaired'],
    art: `<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px">
      ${PLACES.slice(0, 6).map(([file, name, where, c]) => `<div style="position:relative">${framed(file, 300, 200, 'center', `border-color:${c};border-width:5px`)}
        <div style="margin-top:6px;font-family:Display,serif;font-weight:900;font-size:22px;color:${C.foam}">${name}</div>
        <div style="font-family:Cond,sans-serif;font-size:16px;letter-spacing:.12em;text-transform:uppercase;color:${c}">${where}</div></div>`).join('')}
      </div>` }),

  'card-shore': () => card({
    kicker: 'Shore-aware placement', title: 'Nothing floats,<br>nothing sinks', color: C.kelp, backdrop: 'river_boathouse.jpg',
    points: ['The land is sampled before anything is placed', 'Docks and piers are turned to point <b class="hi">into deep water</b>',
      'Land parts need dry, level ground', 'Shacks and boathouses stay out of ravines', 'The wreck lies on the sea floor'],
    art: `<div style="position:relative">${framed('harbour_pier.jpg', 940, 529)}${label('Pier into the sea', C.lantern, 'left:18px;top:18px')}
      <div style="position:absolute;right:-24px;bottom:-60px">${framed('river_boathouse.jpg', 420, 236, 'center', `border-color:${C.kelp}`)}</div>
      ${label('Boat slip into the river', C.kelp, 'right:0px;bottom:192px;font-size:15px')}</div>
      <div style="margin-top:80px;width:520px">${stats([['Places', '7'], ['Shore types', '6'], ['Floating', '0']])}</div>` }),

  'card-crabpot': () => card({
    kicker: 'New block', title: 'The<br>Crab Pot', color: C.buoy, backdrop: 'pots.jpg',
    points: ['Set it in open water: it <b class="hi">fishes on its own</b>', 'Catches depend on the biome: sea, river, swamp, frozen water',
      'Bait it for faster, luckier catches; <b class="hi">twice as fast in the rain</b>', 'Hoppers feed bait in and carry the catch out',
      'Full? It waits. Nothing is ever lost'],
    art: `<div style="position:relative">${framed('pots.jpg', 940, 529, 'center 40%', `border-color:${C.buoy}`)}
      <div style="position:absolute;right:-26px;bottom:-70px">${framed('pot_screen.jpg', 420, 236, '50% 38%', `border-color:${C.buoy}`)}</div></div>
      <div style="margin-top:84px;width:500px">${stats([['Slots', '5'], ['Catch every', '60–120 s'], ['Lost', '0']])}</div>` }),

  'card-bait': () => card({
    kicker: 'Three baits', title: 'Bait makes<br>the catch', color: C.lantern, backdrop: 'pots.jpg',
    points: ['<b class="hi">Fish Bait</b>: half the wait', '<b class="hi">Chum</b>: about a third of the wait, and luckier',
      '<b class="hi">Glow Bait</b>: much luckier, more treasure and bottles', 'Crafted from seeds, scraps and glow berries, or bought from residents'],
    art: `<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:22px">
      ${[['item/fish_bait', 'Fish Bait', 'seeds + rotten flesh', 'wait ×0.5', C.sand], ['item/chum', 'Chum', 'fish + flesh + bone meal', 'wait ×0.35 · luck +1', C.buoy],
        ['item/glow_bait', 'Glow Bait', 'glow berries + glow ink', 'luck +3', C.ice]].map(([t, n, r, e, c]) =>
        `<div class="tile" style="--c:${c}">${item(t, 192)}<div class="n">${n}</div><div class="s">${r}</div><div class="s" style="color:${c};font-weight:700">${e}</div></div>`).join('')}
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:22px">
        <div class="tile" style="--c:${C.rope};flex-direction:row;justify-content:center">${item('block/fishing_net', 96)}<div><div class="n" style="text-align:left">Fishing Net</div><div class="s" style="text-align:left">climbable, see-through, waterloggable</div></div></div>
        <div class="tile" style="--c:${C.kelp};flex-direction:row;justify-content:center">${item('item/message_in_a_bottle', 96)}<div><div class="n" style="text-align:left">Message in a Bottle</div><div class="s" style="text-align:left">from rods, pots, loot and residents</div></div></div>
      </div>` }),

  'card-residents': () => card({
    kicker: 'Named residents', title: 'Fishermen<br>who stay', color: C.kelp, backdrop: 'trades.jpg',
    points: ['Saylor, Harbourmaster Wren, Keeper Morrow, Old Bayou Tam, Frost-Beard Ole, Ferryman Hale',
      'Journeymen who <b class="hi">never lose their job</b>', 'Exclusive trades: bait, Crab Pots, nets, bottles, a spyglass, a boat',
      'Then they level up like any fisherman'],
    art: `<div style="position:relative">${framed('trades.jpg', 940, 529, '20% 50%', `border-color:${C.kelp}`)}${label('Harbourmaster Wren', C.kelp, 'left:18px;top:18px')}</div>
      ${stats([['Residents', '6'], ['Exclusive trades', '5–8 each', 2]])}` }),

  'card-bottle': () => card({
    kicker: 'Treasure hunting', title: 'Messages<br>in a Bottle', color: C.ice, backdrop: 'bottle.jpg',
    points: ['Fished up by rods, caught by pots, found in chests', 'Break one open: a note from the sea is read out',
      'Inside: a small treasure, or a <b class="hi">map to a Sunken Trawler</b>', 'The captain’s chest can hold a <b class="hi">Heart of the Sea</b>'],
    art: `<div style="position:relative">${framed('bottle.jpg', 940, 529, 'center 70%', `border-color:${C.ice}`)}
      <div style="position:absolute;right:-26px;bottom:-70px">${framed('sunken_trawler.jpg', 420, 236, 'center', `border-color:#5aa9e6`)}</div>
      ${label('The wreck the map leads to', '#5aa9e6', 'right:4px;bottom:180px;font-size:15px')}</div>
      <div style="margin-top:84px;width:500px">${stats([['Notes', '12'], ['Rod catches', '1.5 %']])}</div>` }),

  'card-config': () => card({
    kicker: 'For servers and modpacks', title: 'Your coast,<br>your rules', color: C.lantern, backdrop: 'lighthouse.jpg',
    points: ['<b class="hi">config/fisherman_house.json</b> with comments: pot timing, water, rain, each structure on or off',
      'Biomes, spacing, loot and pot catches are datapack data', '<b class="hi">/fishermanscoast inspect</b> shows what a structure holds',
      'Worlds from 1.x keep loading', 'No extra library to install'],
    art: `<div style="display:flex;flex-direction:column;gap:18px">
      <div class="frame" style="background:#081a27;border-color:${C.lantern}">${configPanel()}</div>
      ${stats([['Loaders', 'Fabric · NeoForge · Forge', 2], ['Versions', '5']])}</div>` }),
};

const HEADERS = {
  'header-whats-new': ['What’s New in 2.0', C.lantern], 'header-coast': ['Seven Places on the Coast', C.sand],
  'header-shore': ['Shore-Aware Placement', C.kelp], 'header-crabpot': ['The Crab Pot', C.buoy],
  'header-bait': ['Bait and Nets', C.lantern], 'header-residents': ['The Residents', C.kelp],
  'header-bottle': ['Messages in a Bottle', C.ice], 'header-config': ['For Servers and Modpacks', C.lantern],
  'header-downloads': ['Downloads', C.sand], 'header-faq': ['FAQ', C.sand], 'header-gallery': ['Gallery', C.sand],
};
for (const [name, [title, color]] of Object.entries(HEADERS)) {
  assets[name] = () => header(title, color);
}
assets.divider = divider;

(async () => {
  const wanted = process.argv.slice(2);
  const names = wanted.length ? wanted : Object.keys(assets);
  const browser = await chromium.launch();
  const context = await browser.newContext({ deviceScaleFactor: 1 });
  for (const name of names) {
    if (!assets[name]) {
      console.error('unknown asset', name);
      continue;
    }
    const html = assets[name]();
    const file = path.join(__dirname, `.render-${name}.html`);
    fs.writeFileSync(file, html);
    const p = await context.newPage();
    await p.goto(url(file));
    await p.evaluate(() => document.fonts.ready);
    await p.waitForTimeout(250);
    const { width, height } = await p.evaluate(() => ({ width: document.body.scrollWidth, height: document.body.scrollHeight }));
    await p.setViewportSize({ width, height });
    const transparent = name.startsWith('header') || name === 'divider' || name === 'icon';
    await p.screenshot({ path: path.join(out, `${name}.png`), omitBackground: transparent });
    await p.close();
    fs.unlinkSync(file);
    console.log('rendered', name);
  }
  await browser.close();
})();
