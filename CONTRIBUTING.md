# Contributing

Thanks for helping improve Fisherman's Coast.

## How to contribute

1. Fork the repository and create a feature branch from `main`.
2. Make focused changes in the relevant Minecraft version workspace (`1.20.1/`, `1.21.1/`, `26.1.2/`, `26.2/` or
   `26.3/`). A gameplay change usually belongs in all five: the `common/` code is nearly identical between them, and
   only version-specific APIs differ.
3. If you changed structures, data, textures or language, regenerate them (below) instead of editing the JSON.
4. Build the workspace you changed (`./gradlew build` from that folder, with Java 17 for 1.20.1, 21 for 1.21.1 and 25
   for 26.x). This also runs the unit tests.
5. Open a pull request describing the change and how you tested it.

## Layout

Each workspace is a MultiLoader Gradle build:

- `common/`: everything that matters.
  - `core/` is Minecraft-free and unit-tested (`common/src/test`): the shore placement rules (`Shore`), the Crab Pot's
    timing and bait maths (`CrabPotRules`) and the config file (`CoastConfig`).
  - `world/` holds the shore-aware structure type (`fisherman_house:coastal`) and its piece, `block/` the Crab Pot and
    the Fishing Net, `item/` the Message in a Bottle, `command/` `/fishermanscoast inspect`, `content/` the
    registrations.
- `fabric/`, `neoforge/` (`forge/` on 1.20.1): entry points that register the content, the creative tab entries and
  the command, and add the rod's extra loot (Fabric's loot table event; a loot modifier on NeoForge and Forge).

Templates, assets and data are generated:

```bash
pip install nbtlib Pillow
python3 tools/gen_textures.py   # block and item textures, into tools/assets/textures/
python3 tools/structures.py     # the seven templates and their sample points, into tools/assets/structures/
python3 tools/datagen.py        # everything under */common/src/main/resources/{assets,data} and the loot modifiers
```

`tools/structures.py` builds each template with a small builder (`tools/nbtbuild.py`) in the 1.20.1 format; every
newer version upgrades it with its own data fixers, so one file serves all builds. Each template records where it
samples the land (`site(...)`: dry points for its land part, wet points for its dock or hull, and the rules) and
`tools/datagen.py` writes those into the structure JSON. The Fisherman's Cottage is the 1.x house, repaired by the same
script from `tools/assets/legacy/fisherman_house_1.1.nbt`; the 1.x template itself is also written, with only its
paintings' and item frames' anchor blocks corrected, and stays at the id `fisherman_house:fisherman_house` for houses
1.x left half-generated.

`tools/datagen.py` knows each version's format (folder names, ingredient and result syntax, loot conditions and
functions, item model definitions, pack formats, loot modifiers); change the tables at its top and run it, then
rebuild. CI fails when the committed files differ from what the tools generate.

## Testing in game

`tools/qa/` drives dev servers over RCON and a real client under Xvfb (software rendering). It needs `xdotool` and
ImageMagick (`import`) and an X server on `:1` (`Xvfb :1 -screen 0 1920x1080x24 &`); 26.x clients also need Mesa EGL
(`libegl1 libegl-mesa0 libgl1-mesa-dri libgles2`).

```bash
tools/qa/devrun.sh prepare-server 26.3 fabric     # eula, RCON on 25575 (password qa), a fresh normal world, fast pots
tools/qa/devrun.sh start-server 26.3 fabric
tools/qa/devrun.sh start-client 26.3 fabric       # joins localhost:25565 as "Builder"
python3 tools/qa/rcon.py "op Builder"
python3 tools/qa/coast_checks.py --log /tmp/fc-qa/fabric-server.log --client --ws 26.3 --loader fabric --shots /tmp/fc-qa/shots
tools/qa/devrun.sh stop-client; tools/qa/devrun.sh stop-server 26.3
```

`coast_checks.py` checks, on a normal world with a fixed seed:

- the config file (the QA config is completed with defaults and comments);
- every structure: `/locate` finds it, its chunks generate, and `/fishermanscoast inspect` finds its containers with
  their loot tables, its named resident with the exclusive trades, its Crab Pots and Fishing Nets, and loot in the
  containers; each template also places on its own (`/place template`);
- the Crab Pot in glass tanks high above the terrain: a catch in open water, bait used per catch, nothing in a puddle,
  nothing lost or added when full, hoppers below (catch out, bait stays) and above (bait in, nothing else), a
  comparator, the drops when broken, and the catch table picked by the biome at three structures;
- every loot table, a bottle that holds a map to a Sunken Trawler, and bottles from 400 rod catches;
- with `--client`: the player baits a pot with a real right-click and opens it, opens a Message in a Bottle (and gets
  the advancement), walks into every structure (discovery advancements), recipes load and the client log has no
  model or texture errors; screenshots are taken along the way;
- the server log has no errors.

`tools/qa/run_matrix.sh` does all of that on a fresh world for every build (ten: five versions, two loaders each):

```bash
tools/qa/run_matrix.sh                       # all builds; results in /tmp/fc-qa/results/
tools/qa/run_matrix.sh 26.3:fabric 1.20.1:forge
```

Release jars are smoke-tested on real servers (vanilla with the real loader from its installer, the jar from
`releases/`, game port 25566 and RCON 25576, so it can run beside a dev server), and a 1.1.0 world is upgraded:

```bash
tools/build_release.sh
tools/qa/prodserver.sh run 1.20.1 forge           # setup, start, server checks, stop
tools/qa/migration.sh <path to a 1.1.0 Fabric 1.20.1 jar>
```

`tools/qa/rarity.py` prints how far the nearest of each structure is from a grid of points on a running server.
Stop dev runs with `devrun.sh stop-client` / `stop-server`, which only look at Java processes.

If you change gameplay or data, run the checks on every workspace you touched, for both loaders.

## Coding expectations

- Prefer small, reviewable PRs over large mixed changes.
- Keep ids stable: block, item, block entity, structure and template ids are what saved worlds refer to.
- Keep logic Minecraft-free where it can be, and test it in `common/src/test`.
- Match existing naming (`mod_id` is `fisherman_house`, packages are `tn.nightbeam.fishermanhouse`), package layout
  and MultiLoader patterns. Keep loader entry points thin.
- Do not commit build output, run directories, IDE metadata, or local secrets.
- When fixing a bug, say which versions and loaders you verified.

## Issues

Use GitHub Issues for bugs and feature requests. Include the Minecraft version, mod loader, mod version, other
worldgen or fishing mods, steps to reproduce and, for a structure, the output of `/fishermanscoast inspect` there.

## Licensing

By contributing, you agree that your contributions are licensed under the Apache License, Version 2.0, unless you
state otherwise in the pull request.
