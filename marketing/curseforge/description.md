![Fisherman's Coast](https://raw.githubusercontent.com/MeherBenSalem/the-fisherman-house/main/marketing/images/banner.png)

**A whole coastline worth visiting.** Seven fishing places, each built for its own kind of shore and placed only where
the land suits it: a harbour pier on the beach, a lighthouse on the rocks, a stilt shack in the swamp, an ice fishing
camp on a frozen sea, a boathouse on the river and a sunken trawler on the ocean floor, plus the original Fisherman's
House, repaired. Each one has a named fisherman with his own trades. Set **Crab Pots** that fish while you are away,
bait them, hang **Fishing Nets**, and open **Messages in a Bottle** that lead to the treasure in a wreck.

Fabric and NeoForge (Forge on 1.20.1) · Minecraft 1.20.1, 1.21.1, 26.1.2, 26.2 and 26.3 · install on the server and
clients · Fabric needs Fabric API, nothing else is needed

Formerly **The Fisherman House**: same mod id, and your worlds keep loading.

![What's new in 2.0](https://raw.githubusercontent.com/MeherBenSalem/the-fisherman-house/main/marketing/images/header-whats-new.png)

Version 2.0 "The Living Coast" rebuilds the mod. Here's what changed from 1.1:

- **Six new structures** next to the old house, one for every kind of shore
- **Shore-aware placement**: nothing floats, nothing is buried, no dock ends on sand
- **Named residents** with exclusive trades who never lose their job
- **Crab Pots** with five catch tables by biome, three **baits**, hopper and comparator support
- **Messages in a Bottle** from rods, pots, chests and traders: a note, and a treasure or a map to a wreck
- **Fishing Nets** to climb and build with
- **The original house, repaired**: its barrels have real loot (they were empty on 1.20.1), Saylor has his own trades,
  the stilts reach the sea floor, and it is far less rare
- An advancement tab, a commented config, an `inspect` command for operators
- Now for **Minecraft 26.3**; on 1.21.1 the Forge jar is replaced by NeoForge

![Seven Places on the Coast](https://raw.githubusercontent.com/MeherBenSalem/the-fisherman-house/main/marketing/images/header-coast.png)

![A whole coast, alive](https://raw.githubusercontent.com/MeherBenSalem/the-fisherman-house/main/marketing/images/card-coast.png)

| Structure | Where | Resident | What is there |
|-----------|-------|----------|---------------|
| Fisherman's Cottage | sandy and snowy beaches | Saylor | the original stilt house over the shallows with its boardwalk, repaired |
| Harbour Pier | sandy beaches | Harbourmaster Wren | a bait shop and a long pier with a T-head, lamp posts, net racks, a crane and a bell |
| Lighthouse | stony shores and beaches | Keeper Morrow | a red and white tower with a lit lantern room, and the keeper's cottage |
| Stilt Shack | swamps and mangrove swamps | Old Bayou Tam | a mangrove hut on stilts with a porch and a little dock |
| Ice Fishing Camp | frozen oceans and rivers | Frost-Beard Ole | a hut on an ice shelf over a hole with a pot already set, a tent, a campfire and a sled |
| River Boathouse | the banks of rivers | Ferryman Hale | a cottage and a roofed slip with a boat in it |
| Sunken Trawler | the floor of the oceans | two drowned deckhands | a broken fishing boat: the hold's barrels and the captain's chest |

Every container has its own loot table, and the Sunken Trawler's captain's chest can hold a Heart of the Sea. Find
them all for the **Coastal Wanderer** advancement.

![Shore-Aware Placement](https://raw.githubusercontent.com/MeherBenSalem/the-fisherman-house/main/marketing/images/header-shore.png)

![Nothing floats, nothing sinks](https://raw.githubusercontent.com/MeherBenSalem/the-fisherman-house/main/marketing/images/card-shore.png)

Before a structure is placed, the mod samples the land where it would stand, in every rotation (and, for the
shore buildings, at a few spots nearby), and picks one that fits:

- Docks and piers point **into water at least three blocks deep**.
- Land parts need **dry, level ground**; a shack or boathouse is not wedged against a cliff.
- The ice camp sits on open water (which then freezes around it), the stilt shack on swamp water or swamp land, the
  wreck on the sea floor under at least twelve blocks of water.
- A spot that does not fit is skipped.

![The Crab Pot](https://raw.githubusercontent.com/MeherBenSalem/the-fisherman-house/main/marketing/images/header-crabpot.png)

![The Crab Pot](https://raw.githubusercontent.com/MeherBenSalem/the-fisherman-house/main/marketing/images/card-crabpot.png)

- Set it in water with open water around it (20 water blocks in the 5×3×5 box around it). Every **60 to 120 seconds**
  it catches something and keeps it in its 5 slots.
- The catch depends on where it is: **frozen water, swamps, rivers, the sea and beaches**, or anywhere else. Fish come
  from vanilla's fishing table, so fish from other mods are caught too.
- **Twice as fast in the rain.** When it is full it waits; nothing is ever lost.
- Hoppers and pipes put bait in from any side and take the catch out (never the bait); comparators read how full it
  is. Sneak-right-click with an empty hand for its status.
- The model shows the bait and the catch; a baited pot leaks bubbles and a catch makes a splash.
- Recipe: a Fishing Net on each side, sticks around them and a string on top. Also sold by every resident.

![Bait and Nets](https://raw.githubusercontent.com/MeherBenSalem/the-fisherman-house/main/marketing/images/header-bait.png)

![Bait makes the catch](https://raw.githubusercontent.com/MeherBenSalem/the-fisherman-house/main/marketing/images/card-bait.png)

| Item | Recipe (shapeless) | In a Crab Pot |
|------|--------------------|---------------|
| Fish Bait ×4 | wheat seeds + rotten flesh | waits half as long |
| Chum ×4 | cod or salmon + rotten flesh + bone meal | waits about a third as long, luck +1 |
| Glow Bait ×4 | glow berries + glow ink sac | luck +3: more treasure, more bottles |

Put bait in by right-clicking the pot or with a hopper; each catch uses one. The **Fishing Net** hangs on a wall like
a ladder, can be climbed, is see-through and can be waterlogged. Recipe: five string in an X make four.

![The Residents](https://raw.githubusercontent.com/MeherBenSalem/the-fisherman-house/main/marketing/images/header-residents.png)

![Fishermen who stay](https://raw.githubusercontent.com/MeherBenSalem/the-fisherman-house/main/marketing/images/card-residents.png)

Saylor, Harbourmaster Wren, Keeper Morrow, Old Bayou Tam, Frost-Beard Ole and Ferryman Hale are journeyman fishermen
who never lose their job. Each sells five to eight exclusive trades: bait, Crab Pots, Fishing Nets, Messages in a
Bottle, Glow Bait, a spyglass at the lighthouse, a boat at the boathouse. Once those are used they level up like any
fisherman.

![Messages in a Bottle](https://raw.githubusercontent.com/MeherBenSalem/the-fisherman-house/main/marketing/images/header-bottle.png)

![Messages in a Bottle](https://raw.githubusercontent.com/MeherBenSalem/the-fisherman-house/main/marketing/images/card-bottle.png)

Fished up by rods (1.5 % of catches, on top of the normal catch), caught by Crab Pots (more often with Glow Bait),
found in the structures and sold by residents. Right-click to break one open: one of twelve notes from the sea is read
out, and the bottle holds either a small treasure or a **map to the nearest Sunken Trawler**.

![For Servers and Modpacks](https://raw.githubusercontent.com/MeherBenSalem/the-fisherman-house/main/marketing/images/header-config.png)

![Your coast, your rules](https://raw.githubusercontent.com/MeherBenSalem/the-fisherman-house/main/marketing/images/card-config.png)

- `config/fisherman_house.json` is written on first start, with comments: Crab Pot timing, the water it needs, the
  rain bonus, and an on/off switch for each structure.
- Biomes, spacing, loot, Crab Pot catches, bottle contents and the shore rules are datapack data.
- `/locate structure #fisherman_house:coastal` finds the nearest of any of them; operators can run
  `/fishermanscoast inspect` to list what a structure holds.
- Worlds from 1.x keep loading: the mod id and the house's structure id are unchanged.

![Downloads](https://raw.githubusercontent.com/MeherBenSalem/the-fisherman-house/main/marketing/images/header-downloads.png)

Pick the file that matches **both** your Minecraft version and your loader:

| Minecraft | Fabric (needs Fabric API) | NeoForge / Forge |
|-----------|---------------------------|------------------|
| 1.20.1 | `fisherman_house-fabric-1.20.1-2.0.0.jar` | `fisherman_house-forge-1.20.1-2.0.0.jar` (Forge 47.4.0+) |
| 1.21.1 | `fisherman_house-fabric-1.21.1-2.0.0.jar` | `fisherman_house-neoforge-1.21.1-2.0.0.jar` (NeoForge 21.1.219+) |
| 26.1.2 | `fisherman_house-fabric-26.1.2-2.0.0.jar` | `fisherman_house-neoforge-26.1.2-2.0.0.jar` (NeoForge 26.1.2.7-beta+) |
| 26.2 | `fisherman_house-fabric-26.2-2.0.0.jar` | `fisherman_house-neoforge-26.2-2.0.0.jar` (NeoForge 26.2.0.93+) |
| 26.3 | `fisherman_house-fabric-26.3-2.0.0.jar` | `fisherman_house-neoforge-26.3-2.0.0.jar` (NeoForge 26.3.0.97+) |

Java 17 for 1.20.1, 21 for 1.21.1, 25 for 26.x.

![FAQ](https://raw.githubusercontent.com/MeherBenSalem/the-fisherman-house/main/marketing/images/header-faq.png)

**Do I need it on the server and the client?** Yes, on both.

**Will my 1.x world break?** No. Houses that already generated stay, and new chunks get the new structures.

**Can I use it in my modpack?** Yes.

**How do I find a structure?** `/locate structure fisherman_house:harbour_pier` (or any other id), or open a Message
in a Bottle and follow the map to a Sunken Trawler.

**A structure is too common or too rare.** Change its spacing in `worldgen/structure_set/<id>.json` with a
datapack, or switch it off in the config.

**Forge on 1.21.1?** There is no Forge build for 1.21.1 any more; use the NeoForge or Fabric jar.

![divider](https://raw.githubusercontent.com/MeherBenSalem/the-fisherman-house/main/marketing/images/divider.png)

[Discord](https://discord.gg/SAmd9fhNhr) · [Source and issues](https://github.com/MeherBenSalem/the-fisherman-house) · [Support us](https://nightbeam.dev/support) · Made by NightBeam Studio
