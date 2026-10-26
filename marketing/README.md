# Marketing

Listing copy and artwork for CurseForge and Modrinth.

| Path | What it is |
|------|------------|
| `curseforge/description.md` | The project description (Markdown; also works on Modrinth). Images load from this repo's `main` branch. |
| `curseforge/summary.txt` | The one-line summary (under 250 characters). |
| `images/banner.png` | 1800×600 header banner. |
| `images/icon.png` | 512×512 project icon (also the mod's in-jar `logo.png`). |
| `images/card-*.png` | 1600×900 feature cards used in the description and as gallery images. |
| `images/header-*.png`, `images/divider.png` | Transparent section headers and a divider for the description. |
| `images/screenshots/*.jpg` | Real in-game captures (Minecraft 26.3, Fabric) used by the cards and the gallery. |
| `source/render.cjs` | Renders every PNG above from the screenshots, the mod's textures and the bundled fonts. |
| `source/config-excerpt.json` | The config file as the mod writes it on first start, shown on the config card. |
| `source/fonts/` | Playfair Display, Barlow and Barlow Condensed, all under the SIL Open Font License (licence files included). |
| `reel/` | A 26-second Instagram reel (1080×1920) made from in-game footage, with its own music; see `reel/README.md`. |

The look: a weathered harbour at dusk. Deep sea blue behind everything with a faint fish-scale wave pattern, a warm
lantern glow, sand-gold serif titles in Playfair Display over clean Barlow text, rope-textured rules and borders, and
one colour per feature (lantern amber for the coast, the bait and the config, buoy red for the Crab Pot, kelp green for shore
placement and the residents, ice blue for the bottle). The icon is the Lighthouse at sunset in a rope frame, with the
Message in a Bottle texture.

## Regenerating the images

Needs Node.js and Playwright with Chromium:

```bash
NODE_PATH="$(npm root -g)" node marketing/source/render.cjs               # everything
NODE_PATH="$(npm root -g)" node marketing/source/render.cjs card-crabpot  # one asset
```

The release name and the supported Minecraft versions and loaders are at the top of `render.cjs`. Supporting a new
Minecraft version means adding one line there, plus one row to the download table in `description.md`. After
changing the icon, copy `images/icon.png` to every workspace's `common/src/main/resources/logo.png`.

## Retaking the screenshots

`tools/qa/marketing_shots.py` captures every screenshot from a dev client (see `tools/qa/` and `CONTRIBUTING.md`): a
1920×1080 window under Xvfb, on a 26.3 Fabric dev server with a world named `showcase` (normal world type, the QA
seed `1928374655`), `view-distance=12` and the default config:

```bash
tools/qa/devrun.sh prepare-server 26.3 fabric showcase
sed -i 's/view-distance=8/view-distance=12/' 26.3/fabric/runs/server/server.properties
rm 26.3/fabric/runs/server/config/fisherman_house.json   # the default config instead of the fast QA pots
tools/qa/devrun.sh start-server 26.3 fabric && tools/qa/devrun.sh start-client 26.3 fabric
python3 tools/qa/rcon.py "op Builder"
python3 tools/qa/marketing_shots.py              # or a few: lighthouse pots bottle
python3 tools/qa/marketing_shots.py --explore lighthouse   # four views, to choose a camera
```

Every structure is where the world generated it, found with `/locate` and untouched; the camera for each is set in
`VIEWS` at the top of the script. Every screenshot is a single unedited frame.

| Screenshot | Scene |
|------------|-------|
| `cottage.jpg` | The Fisherman's Cottage on a snowy beach, from the sea. |
| `harbour_pier.jpg` | The Harbour Pier, from above the sea. |
| `lighthouse.jpg` | The Lighthouse on a stony shore at sunset, its lantern lit. |
| `stilt_shack.jpg` | The Stilt Shack in a swamp. |
| `ice_fishing_camp.jpg` | The Ice Fishing Camp on a frozen ocean among icebergs. |
| `river_boathouse.jpg` | The River Boathouse on a river bank. |
| `sunken_trawler.jpg` | The Sunken Trawler on the ocean floor (the camera has night vision and conduit power, so the water is clear). |
| `pots.jpg` | Three Crab Pots set by command in the sea beside the Harbour Pier: one holding bait, one holding a catch and bait, one empty. The bait and catch inside, the bubbles and the buoys are the mod's model and particles. |
| `pot_screen.jpg` | A Crab Pot in a glass tank, opened with a real right-click. |
| `trades.jpg` | Harbourmaster Wren's trades, opened with a real right-click (he is frozen with `NoAI` so he stands still). |
| `bottle.jpg` | Messages in a Bottle opened with real right-clicks on the pier until one holds a map; the map is held and the note is in chat. |
