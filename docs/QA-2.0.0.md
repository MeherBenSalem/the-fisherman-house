# QA record: Fisherman's Coast 2.0.0

Every build was checked in the game: a dev server and a real game client (under Xvfb, driven with the real mouse and
keyboard) for each of the ten builds, then each release jar on a real server with the real loader, and a world from
1.1.0 opened with 2.0. Every failure found was fixed and the affected builds were run again. The tools are in
[`tools/qa/`](../tools/qa) (see [CONTRIBUTING](../CONTRIBUTING.md#testing-in-game)).

## What is checked

`tools/qa/coast_checks.py`, on a fresh normal world (seed `1928374655`, Crab Pots set to 5 seconds by the QA config):

| Area | Checks |
|------|--------|
| Config | the QA config file is completed with the defaults and its comments; QA values are kept |
| Structures, natural | for each of the seven: `/locate` finds it; its chunks generate; `/fishermanscoast inspect` finds it with its containers' loot tables, its named resident with the exclusive trades (and Crab Pots for sale), its Crab Pots and Fishing Nets; loot rolls into the containers; `#fisherman_house:coastal` locates |
| Structures, templates | each template placed on its own with `/place template` holds the same, and the 1.x house template (kept for 1.x worlds) still places |
| Crab Pot | in glass tanks high above the terrain: a catch in open water, bait used one per catch, nothing in a puddle, nothing lost or added when full, a hopper below takes the catch and leaves the bait, a hopper above puts bait in and nothing else, a comparator reads it, it drops itself and its contents when broken, the catch table follows the biome at three structures |
| Loot | every chest and Crab Pot table rolls; a Message in a Bottle can hold a map to a Sunken Trawler; rods fish up bottles (400 catches) |
| Client | a real right-click puts bait in a pot and the model shows it; the pot screen opens; a real right-click opens a Message in a Bottle and grants Message Received; walking into each structure grants its discovery advancement, then Coastal Wanderer; the recipes load; the client log has no model or texture errors |
| Logs | no errors about the mod, its loot or structures, and no errors at all (two exceptions: vanilla's own `/place template` before 26.3 logs "invalid position" for paintings, see below, and NeoForge 26.x logs a netty error with no mods at all) |

On the production servers the same server checks run (no client), plus one more: the Fisherman's Cottage keeps all
six paintings and three item frames hanging after the game's survival check (one that cannot hang drops as an item).
The dev runs gained this check after the full matrix; 1.20.1 Forge and 26.3 Fabric were run again with it.

## Results: dev server and real client (`tools/qa/run_matrix.sh`)

Final results, each on a fresh world with the final code for that version:

| Build | Checks | Failures |
|-------|--------|----------|
| 1.20.1 Fabric | 155 | 0 |
| 1.20.1 Forge | 155 | 0 |
| 1.21.1 Fabric | 155 | 0 |
| 1.21.1 NeoForge | 155 | 0 |
| 26.1.2 Fabric | 155 | 0 |
| 26.1.2 NeoForge | 155 | 0 |
| 26.2 Fabric | 155 | 0 |
| 26.2 NeoForge | 155 | 0 |
| 26.3 Fabric | 155 | 0 |
| 26.3 NeoForge | 155 | 0 |

1.20.1 and 26.1.2 are from a rerun after the fixes for those versions; the other six are from the full run before it,
which already had their fixes. After the Cottage's paintings changed, 1.20.1 Forge and 26.3 Fabric were run once more
with the painting check added: 156 checks, 0 failures each.

## Results: release jars on real servers (`tools/qa/prodserver.sh`)

Each jar from `releases/` on a vanilla server with the loader installed by its own installer (Fabric with Fabric API,
Forge 47.4.0, NeoForge at the versions in the download table), fresh world, server checks plus the hanging check:

| Jar | Loader | Checks | Failures |
|-----|--------|--------|----------|
| `fisherman_house-fabric-1.20.1-2.0.0.jar` | Fabric Loader 0.16.9, Fabric API 0.92.2 | 142 | 0 |
| `fisherman_house-forge-1.20.1-2.0.0.jar` | Forge 47.4.0 | 142 | 0 |
| `fisherman_house-fabric-1.21.1-2.0.0.jar` | Fabric Loader 0.16.9, Fabric API 0.116.0 | 142 | 0 |
| `fisherman_house-neoforge-1.21.1-2.0.0.jar` | NeoForge 21.1.219 | 142 | 0 |
| `fisherman_house-fabric-26.1.2-2.0.0.jar` | Fabric Loader 0.18.6, Fabric API 0.145.4 | 142 | 0 |
| `fisherman_house-neoforge-26.1.2-2.0.0.jar` | NeoForge 26.1.2.7-beta | 142 | 0 * |
| `fisherman_house-fabric-26.2-2.0.0.jar` | Fabric Loader 0.19.3, Fabric API 0.152.1 | 142 | 0 |
| `fisherman_house-neoforge-26.2-2.0.0.jar` | NeoForge 26.2.0.93 | 142 | 0 * |
| `fisherman_house-fabric-26.3-2.0.0.jar` | Fabric Loader 0.19.5, Fabric API 0.165.0 | 142 | 0 |
| `fisherman_house-neoforge-26.3-2.0.0.jar` | NeoForge 26.3.0.97 | 142 | 0 |

\* NeoForge 26.x servers log a `NoClassDefFoundError` for netty's macOS/BSD transport (`io.netty.channel.kqueue`) at
startup on Linux. A NeoForge 26.3 server with no mods at all logs the same lines, so the log check leaves them out; on
these two runs the check was made before that, and the logs were checked again afterwards (no other errors).

## Results: upgrading a 1.1.0 world (`tools/qa/migration.sh`)

A 1.20.1 Fabric world made with 1.1.0 (built from the last 1.x commit): a 1.x house was located and only the chunks
on one side of it generated, then the world was opened with the 2.0 jar and the rest generated.

| Check | Result |
|-------|--------|
| 2.0 loads the 1.1.0 world | pass |
| the half-generated 1.x house is still there and is finished from its 1.x template (barrels and Saylor, as 1.x placed them) | pass |
| no errors in the 2.0 server log | pass |

## Found and fixed

| What QA found | Fix |
|---------------|-----|
| `/locate structure fisherman_house:river_boathouse` blocked a real server for 35 to 46 s, which disconnects every player (bottle maps use the same search) | shore sampling reads a column only when the rules need it, and land structures check their water before their ground: under 6 s, the same structures found at the same positions (timings below) |
| 1.20.1, 1.21.1, 26.1.2, 26.2: paintings and item frames logged "invalid position" when a structure generated, and 2x2 paintings moved by a block | the structure piece places the template's entities itself with their block moved along (26.3's own placement already does), and templates store a hanging entity's real anchor block |
| The 1.x house template stored its paintings' blocks 8 blocks too low (the same error in 1.x) | the kept template's anchors are corrected; nothing else in it changes |
| NeoForge 26.1.2: rods never fished up a Message in a Bottle (0 in 400) | NeoForge 26.1.2 still needs the global loot modifier list, which is now generated for it |
| 1.21.1 and later: three of the Cottage's six paintings dropped as items a few seconds after it generated; the 1.x house's larger paintings overlap a shelf or the wall itself | each is a one-block painting that exists on every version, and the template builder checks every painting has air in front and a wall behind; the check counts them after the game's survival check |
| Production test servers on 26.x stopped ticking 60 s after starting (newer servers pause when empty), so Crab Pots never caught anything | the test servers run with `pause-when-empty-seconds=-1` (a server setting, not the mod) |
| The QA's template check placed the kept 1.x template instead of the new Cottage | it places `cottage`, and checks the 1.x template separately |
| Paintings without a stored block failed to load from the templates on 26.x | the template builder stores it |
| The ice camp was swallowed by icebergs | the template clears the air above its shelf |
| The stilt shack was placed wedged against a hillside | an `around` ring of sample points with a `max_rise` rule (all versions, unit-tested) |
| The drowned deckhands were skipped on a peaceful QA world | the QA world runs on normal difficulty without monster spawning |
| `minecraft:chain` in a loot table broke loading on 26.3 | removed from the loot table |
| Advancements named structures that did not exist yet | generated together with the structures |

`/locate` timings on a real 26.3 Fabric server, fresh world, from (0, 0) and from (3000, -2000):

| Structure | Before | After |
|-----------|--------|-------|
| Fisherman's Cottage | 6.6 s, 1.6 s | 4.7 s, 0.8 s |
| Harbour Pier | 2.7 s, 2.9 s | 1.5 s, 1.5 s |
| Lighthouse | 0.9 s, 1.3 s | 0.4 s, 0.5 s |
| Stilt Shack | 0.7 s, 0.2 s | 0.4 s, 0.2 s |
| Ice Fishing Camp | 0.1 s, 0.0 s | 0.1 s, 0.0 s |
| River Boathouse | 45.7 s, 35.1 s | 5.5 s, 5.9 s |
| Sunken Trawler | 0.4 s, 1.1 s | 0.2 s, 0.2 s |

## Unit tests

`./gradlew build` runs the Minecraft-free tests in every workspace: 22 tests (shore placement rules, Crab Pot timing
and bait, config), all passing on all five versions.

## Screenshots

The listing screenshots in [`marketing/images/screenshots/`](../marketing/images/screenshots) are real frames from a
26.3 Fabric client, captured by `tools/qa/marketing_shots.py` and looked at one by one; the QA run also saves a
screenshot of each structure from every build.
