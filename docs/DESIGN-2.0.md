# Fisherman's Coast 2.0: audit, market gaps and plan

This document records what The Fisherman House 1.1.0 actually did (read from the code and the structure file, not
from the listing), what players expect from a coastal structure or fishing mod today, where 1.1.0 fell short, and what
2.0 changes. Every 2.0 claim below is implemented in all ten builds and checked in game by
`tools/qa/coast_checks.py` (see [CONTRIBUTING](../CONTRIBUTING.md#testing-in-game) and [QA-2.0.0](QA-2.0.0.md)).

## 1. Audit of 1.1.0

| Area | What the code and data did |
|------|----------------------------|
| Content | One structure, `fisherman_house:fisherman_house` (a 42×14×27 template), and nothing else: no blocks, no items, no code beyond a log line. |
| Placement | A vanilla jigsaw structure at a **fixed height** (y 59-60) in `#minecraft:is_beach` (1.21.1+) or only `minecraft:beach` (1.20.1, so snowy beaches never got one). No check of the ground: the house could stand in a dune, hang over a drop or put its dock on dry sand, and its random rotation often pointed the dock inland. The template carried 4,200 water blocks, so it poured a rectangle of sea onto whatever it landed on. |
| Rarity | `spacing` 300 chunks, `separation` 5: one attempt per 4,800×4,800 blocks, and most attempts fail the biome check. In practice almost nobody ever saw one. |
| Loot | The listing promised treasure maps and fishing loot. The barrels held **fixed items** saved in the template (salmon, bread, carrots, seeds): every house in every world gave the same handful of food, six barrels were empty, and there were no maps or loot tables at all. |
| 1.20.1 data | The template was saved by a 1.21.1 game (item `count` instead of `Count`), so on 1.20.1 **every barrel was empty** and every item frame blank. |
| Resident | "Saylor" was a level 1 fisherman with no experience and stale brain memories (home and job site at the coordinates of the world the house was built in). A level 1 villager without experience loses the profession when it has no job site, so Saylor usually became an unemployed villager with vanilla trades at best. |
| Worldgen step | `lakes` on 1.20.1 (the house could be overwritten by later surface features), `surface_structures` elsewhere. |
| Versions | 1.20.1 (Fabric, Forge), 1.21.1 (Fabric, Forge, NeoForge), 26.1.2 and 26.2 (Fabric, NeoForge). No 26.3. |
| Repository | MCreator-era leftovers: a `shared/` copy of the data that had drifted from the workspaces (different step and biomes), local upload scripts (`scripts/upload_platforms.mjs`, `upload_local.ps1`) with a committed upload state file, a stray patch-notes file at the root. No tests, no QA scripts, no release jars, no CI. |

## 2. What players expect

Gathered from the comment sections, issue trackers and reviews of the popular fishing, ocean and coastal-structure
mods, and from long-running community wishes ("fishing is just waiting for a bite", "beaches are empty", "structures
float or get buried", "the loot is rotten flesh", "I want something to do near the sea"):

1. **Coastlines that feel lived in**: more than one building, different for each kind of coast (sandy beach, stony
   shore, swamp, frozen sea, river), and well built, not a box with a roof.
2. **Structures that fit the land**: docks that reach the water, nothing floating, flooded or cut in half.
3. **A reason to visit**: loot worth the walk, a trader with something you can't get elsewhere, a lead to the next
   place to explore.
4. **Fishing with more depth** than right-click and wait: passive traps that make a waterside base useful, bait that
   matters, catches that depend on where you are, and treasure.
5. **Treasure hunting at sea**: maps found by fishing that lead somewhere, not only vanilla's buried chests.
6. **Vanilla feel and compatibility**: vanilla fish tables (so fish from other mods show up), datapack control of
   frequency, biomes and loot, `/locate`, advancements, no hard dependencies.
7. **Stable ids** so updating does not break worlds, and every loader on the versions people play.

What the market offers today (no project is named here): fishing overhauls focus on rods, minigames and dozens of new
fish; trap mods add one block with a GUI; a few datapacks add a floating village or a single lighthouse; ocean mods
add mobs and food. **Nobody ties the coast together**: settlements that sit right on every kind of shore, residents
with their own trades, a passive trap and bait economy that rewards a seaside base, and fished-up bottles that start a
treasure hunt for a wreck. That is the gap 2.0 fills, on every loader and version the studio supports.

## 3. Gap table

| Expectation | 1.1.0 | 2.0 |
|-------------|-------|-----|
| Structures | 1 house | **7 coastal structures**: Fisherman's Cottage (the original, repaired), Harbour Pier, Lighthouse, Stilt Shack, Ice Fishing Camp, River Boathouse and the underwater Sunken Trawler |
| Coast types | sandy beach only | sandy and snowy beaches, stony shores, swamps and mangroves, frozen oceans and rivers, rivers and lakes inland, the ocean floor |
| Fit to the land | fixed y, random rotation, its own sea poured onto the beach | **Shore-aware placement**: the land is sampled before anything is placed; docks and piers are turned to face open water, land parts need dry and level ground, water parts need real water depth, the wreck lies on the sea floor |
| Rarity | 1 attempt per 300×300 chunks | one attempt every 24-40 chunks per structure (most attempts on a suitable shore succeed); kept away from villages |
| Loot | fixed food in 1 of 15 barrels, nothing on 1.20.1 | a loot table per structure (and a captain's chest on the wreck), rolled per container |
| Residents | a level 1 fisherman who lost his job | **Five named residents** who keep their profession, each with exclusive trades (bait, crab pots, nets, bottles) plus vanilla fisherman trades as they level up |
| Fishing gameplay | none | **Crab Pot** (passive trap with biome catches, bait and rain bonus, hopper and comparator support), three baits, **Message in a Bottle** (fished or trapped; opens into a note, a little treasure or a map to a Sunken Trawler), a rare extra catch on vanilla rods |
| Decoration | none | **Fishing Net**: climbable, waterloggable netting used all over the structures |
| Progression | none | an advancement tab: find each structure, set a trap, open a bottle, buy from a resident, visit all seven |
| Datapacks | structure JSON only | biomes per structure (biome tags), spacing (structure sets), loot tables, crab pot catch tables chosen by biome tags, the bottle's contents |
| Config | none | `config/fisherman_house.json`: crab pot timing, water, rain bonus, rod bottles |
| Admin | none | `/fishermanscoast inspect` lists the structures, containers, loot tables, residents and pots around a spot |
| 1.20.1 | empty barrels | identical to every other version (templates are written in the oldest format and upgraded by the game) |
| Versions | 1.20.1, 1.21.1, 26.1.2, 26.2 | 1.20.1 (Fabric, Forge); 1.21.1, 26.1.2, 26.2, 26.3 (Fabric, NeoForge) |
| Tests / QA | none | JUnit for placement, crab pot and config rules; in-game QA on all ten builds and the remapped jars |

## 4. Name and identity

**Fisherman's Coast** (was The Fisherman House). The mod is no longer one house: it is the whole shoreline, its
people and its fishing. The name keeps the word players know, says "coast" for the structures and "fisherman" for the
gameplay, and no other project uses it. The visual identity is a weathered harbour: deep sea blue, sand and rope
tones, lantern amber, a serif display face for the title and a clean sans for text.

The **mod id stays `fisherman_house`** and the structure id `fisherman_house:fisherman_house` is unchanged, so worlds
from 1.x load without any remapping: saved structure starts, the template and the advancements keep their ids. Only
the display name, the jar's display metadata and the marketing change. The GitHub repository keeps its name.

## 5. The feature set as built

### The headline: a living coast

Seven structures, each built for one kind of shore, each with a reason to go in:

| Id | Name | Where | Resident | Why visit |
|----|------|-------|----------|-----------|
| `fisherman_house` (unchanged) | Fisherman's Cottage | sandy and snowy beaches | Saylor, fisherman | the original house, repaired: loot barrels, a dock, Saylor's trades |
| `harbour_pier` | Harbour Pier | sandy beaches | Harbourmaster Wren | a long pier with a bait shop, crab pots in the water, the best bait and pot trades |
| `lighthouse` | Lighthouse | stony shores and beaches | Keeper Morrow | a striped tower with a lit lantern room; the keeper's chest holds maps to wrecks and a spyglass |
| `stilt_shack` | Stilt Shack | swamps, mangrove swamps | Old Bayou Tam | a hut on stilts over the water, swamp loot (slime, potions), cheap bait |
| `ice_fishing_camp` | Ice Fishing Camp | frozen oceans and rivers, snowy beaches | Frost-Beard Ole | a hut over a hole in the ice with a crab pot already set |
| `river_boathouse` | River Boathouse | the banks of rivers and lakes in temperate land | Ferryman Hale | a boathouse with a boat and a slipway |
| `sunken_trawler` | Sunken Trawler | the floor of temperate, lukewarm, cold and deep oceans | none (two drowned crew) | the captain's chest, the target of every bottle map |

Shore-aware placement is the part players notice without knowing it: before a structure is placed, the land around
the chosen chunk is sampled (a few dozen columns, before features, both with and without water). A shore structure
(cottage, pier, boathouse) needs dry, level ground for its land part and water at least three blocks deep where its
dock or pier ends, and is turned to the one rotation that sends the dock into the water. The lighthouse needs dry
ground with water within a few blocks. The stilt shack stands on swamp water or swamp land. The ice camp needs water
(it freezes over), and the hole inside the hut stays open because it is under a roof. The wreck needs ten blocks of
water and lies on the sea floor. A spot that fails is skipped, the next attempt is a few dozen chunks away.

### Crab Pot

A waterlogged trap that fishes on its own. Place it in water with enough open water around it (at least 20 water
blocks in the 5×3×5 box around the pot, so a puddle does not work). Every 60-120 seconds (configurable) it catches
something and stores it in its 5 slots; when it is full it waits instead of losing anything.

* **Where decides what**: the catch table is picked by the biome, through biome tags a datapack can change:
  frozen water, swamps, rivers, oceans and beaches, and a default. All of them draw their fish from vanilla's
  `gameplay/fishing/fish`, so fish added by other mods are caught too. Each place adds its own extras: kelp, sea
  pickles, nautilus shells and prismarine at sea; clay, gold nuggets and lily pads in rivers; slime balls and bones in
  swamps; ice and prismarine crystals in frozen water.
* **Bait**: Fish Bait halves the wait; Chum cuts it to a third and adds luck (fewer junk catches); Glow Bait adds a lot
  of luck (treasure and bottles become likely) without speeding up. One bait is used per catch.
* **Rain**: the pot works twice as fast while it rains on it, like a rod.
* **Automation**: hoppers and pipes can put bait in (only bait) from any side and take catches out (never bait).
  Comparators read how full it is.
* **Visuals**: the model shows the bait inside, and the catch once there is one; a catch splashes (bubbles, splash
  particles and sound) and a baited pot gives off a trail of bubbles.
* Right-click opens its 5 slots. Sneak-right-click with an empty hand shows its status in the action bar (water,
  bait, how long until the next catch, full).

Recipe: two Fishing Nets, five sticks and a string. Residents sell it too.

### Bait

| Item | Recipe | Effect in a Crab Pot |
|------|--------|----------------------|
| Fish Bait | wheat seeds + rotten flesh → 4 | waits ×0.5 |
| Chum | cod or salmon + rotten flesh + bone meal → 4 | waits ×0.35, luck +1 |
| Glow Bait | glow berries + glow ink sac → 4 | luck +3 |

Luck shifts the catch tables' weights the way vanilla's Luck of the Sea does: less junk, more treasure.

### Message in a Bottle

Found by Crab Pots (rare, more with Glow Bait), by rod fishing (a 1.5 % chance per catch, on top of the normal
catch), in structure loot and from residents. Using it breaks the bottle (glass sound and particles) and rolls
`fisherman_house:gameplay/message_in_a_bottle`: one of twelve notes from the sea is read out in chat, and the bottle
gives either a small treasure (emeralds, gold, a name tag, a nautilus shell) or a **treasure map to the nearest
Sunken Trawler**. Everything about it is a loot table, so datapacks can change it.

### Fishing Net

A thin, waterloggable net that hangs on walls like a ladder and can be climbed. It is what makes the structures look
like working harbours, and players can build with it. Recipe: five string in an X make four.

### Residents

Each resident is a vanilla villager placed with the structure: named, already at the journeyman level with
experience (so it never loses its profession), next to a barrel (the fisherman's job site), and with exclusive
trades written into it: bait, Crab Pots, Fishing Nets, Messages in a Bottle, and buying fish and catches. Once the
exclusive trades are used, the resident levels up like any fisherman and adds vanilla trades.

### Advancements

A "Fisherman's Coast" tab: one per structure found, Set the Trap (place a Crab Pot), Message Received (open a bottle),
Tools of the Trade (buy a Crab Pot from a resident), X Marks the Wreck (find a Sunken Trawler) and Coastal Wanderer (all
seven structures).

### Configuration

`config/fisherman_house.json`, written on first start with comments:

| Key | Default | What it does |
|-----|---------|--------------|
| `crab_pot.min_seconds`, `.max_seconds` | `60`, `120` | Time between catches without bait (random in between) |
| `crab_pot.min_water` | `20` | Water blocks needed in the 5×3×5 box around a pot |
| `crab_pot.rain_bonus` | `true` | Twice as fast in the rain |
| `rod_bottles` | `true` | Rods can fish up a Message in a Bottle |

## 6. The plan as built

### Ids and saves

* `fisherman_house:fisherman_house` keeps its structure and structure set ids. Its structure type changes from jigsaw
  to the mod's own shore-aware type. Houses already generated keep loading: a saved structure start names the
  structure (unchanged) and stores its pieces with their own piece type (vanilla's jigsaw piece, which still exists)
  and their template, so old starts load as they are.
* The 1.x template stays in the mod, unchanged, at its id `fisherman_house:fisherman_house`: a house that 1.x started
  but did not finish (its chunks at the edge of the explored world) is completed from the same template it began
  with. The repaired house is a new template, `fisherman_house:cottage`. All other ids are new content.
* New blocks: `crab_pot` (with a block entity of the same id), `fishing_net`. New items: `fish_bait`, `chum`,
  `glow_bait`, `message_in_a_bottle`.

### Code

* `common/` holds everything. `core/` is Minecraft-free (shore placement rules, crab pot timing and bait maths, the
  config) and covered by JUnit. `world/` holds the structure type and piece, `block/` the pot and net, `item/` the
  bottle. Loader modules only register content, the command, the loot injection and the creative tab entries.
* Templates are generated by `tools/structures.py` from a small builder (walls, roofs, stairs, lanterns, nets,
  furniture) and saved in the 1.20.1 format, so every version upgrades them through its own data fixers: one source
  for all ten builds. The 1.x house is repaired by the same script (loot tables, resident, no stale memories).
* Data and assets are generated by `tools/datagen.py` in each Minecraft version's own format (folder names, loot
  function and predicate syntax, recipes, item model definitions and pack formats differ between 1.20.1 and 26.3);
  textures by `tools/gen_textures.py`.
* The rod loot uses each loader's own mechanism: Fabric's loot table event, NeoForge's data-driven `add_table` global
  loot modifier, and a small global loot modifier on Forge 1.20.1.

### Out of scope for 2.0

* A fishing minigame and new fish species: fishing overhauls do that well; Fisherman's Coast stays vanilla-plus and
  uses vanilla's fish tables so it works next to them.
* Custom villager professions and workstations: profession registries differ on every loader and version; the
  residents are fishermen with exclusive trades instead.
* Rendering the catch inside the pot as a 3D item: block entity renderers changed completely between 1.20.1 and 26.x;
  the pot's model states show bait and catch instead.
* Dropping 1.21.1 Forge: the studio's builds are Fabric and NeoForge on 1.21.1 (Forge stays on 1.20.1). See the
  patch notes.
