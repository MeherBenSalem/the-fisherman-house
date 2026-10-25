#!/usr/bin/env python3
"""Builds the coastal structure templates and their placement metadata.

  python3 tools/structures.py        (needs nbtlib; writes tools/assets/structures/*.nbt and structures.json)

tools/datagen.py copies the templates into every workspace and writes each structure's JSON from the metadata here
(anchor, dry and wet sample points, site rules), so the template and its placement never drift apart.

Every template's ground floor sits on layer G; the site's y_offset puts layer G one block below the first free block
above the ground (it replaces the top block of the terrain). Templates are written in the 1.20.1 format.
"""
from __future__ import annotations

import gzip
import json
import math
import random
from pathlib import Path

from nbtlib import Byte, Compound, File, Int, List, String, load

from nbtbuild import (AIR, NS, OPPOSITE, Template, door, fence, lantern, log, offer, slab, stairs, trapdoor)

TOOLS = Path(__file__).resolve().parent
OUT = TOOLS / 'assets' / 'structures'
LEGACY_HOUSE = TOOLS / 'assets' / 'legacy' / 'fisherman_house_1.1.nbt'

# Trades -------------------------------------------------------------------------------------------------------------
E = 'emerald'
B = f'{NS}:fish_bait'
CH = f'{NS}:chum'
GB = f'{NS}:glow_bait'
POT = f'{NS}:crab_pot'
NET = f'{NS}:fishing_net'
BOT = f'{NS}:message_in_a_bottle'
COMMON = [((('cod', 10)), (E, 1), 16, 2), ((('salmon', 8)), (E, 1), 16, 2), (((E, 1)), (B, 6), 16, 2),
          (((E, 2)), (CH, 4), 12, 5), (((E, 1)), (NET, 3), 12, 2)]
TRADES = {
    'fisherman_house': COMMON + [(((E, 4)), (POT, 1), 6, 10), (((E, 6)), (BOT, 1), 3, 15)],
    'harbour_pier': COMMON + [(((E, 3)), (POT, 1), 8, 10), (((E, 3)), (GB, 3), 8, 10), (((E, 6)), (BOT, 1), 3, 15)],
    'lighthouse': [((('cod', 10)), (E, 1), 16, 2), (((E, 3)), (GB, 3), 8, 10), (((E, 5)), (BOT, 1), 4, 15),
                   (((E, 6), ('copper_ingot', 2)), ('spyglass', 1), 3, 15), (((E, 4)), (POT, 1), 6, 10)],
    'stilt_shack': [((('salmon', 8)), (E, 1), 16, 2), ((('slime_ball', 4)), (E, 1), 12, 5), (((E, 1)), (CH, 4), 16, 2),
                    (((E, 1)), (B, 8), 16, 2), (((E, 4)), (POT, 1), 6, 10), (((E, 1)), ('lily_pad', 4), 12, 2)],
    'ice_fishing_camp': [((('cod', 8)), (E, 1), 16, 2), ((('salmon', 6)), (E, 1), 16, 2), (((E, 2)), (CH, 5), 12, 5),
                         (((E, 4)), (POT, 1), 6, 10), (((E, 3)), (GB, 3), 6, 10)],
    'river_boathouse': COMMON + [(((E, 4)), (POT, 1), 6, 10), (((E, 3)), ('oak_boat', 1), 6, 5)],
}


def trades(key):
    out = []
    for prices, sell, uses, xp in TRADES[key]:
        if isinstance(prices[0], str):
            prices = (prices,)
        out.append((prices[0], sell, uses, xp, prices[1] if len(prices) > 1 else None))
    return [(buy, sell, uses, xp, buy_b) for buy, sell, uses, xp, buy_b in out]


def resident(t: Template, x, y, z, key, name, biome, yaw=0.0):
    t.villager(x, y, z, name, biome, [(buy, sell, uses, xp, b) for buy, sell, uses, xp, b in trades(key)], yaw=yaw)


# The metadata datagen turns into each structure's JSON -------------------------------------------------------------
SITES: dict[str, dict] = {}


def ring(cx, cz, radius, n=8):
    return [(cx + round(radius * math.cos(a)), cz + round(radius * math.sin(a))) for a in [i * 2 * math.pi / n for i in range(n)]]


def site(t: Template, key, mode, anchor, dry=(), wet=(), around=(), ground=0, **rules):
    """Records where a template samples the land. Points are in building coordinates; they are saved as template
    coordinates. `ground` is the building y of the layer that replaces the top block of the terrain."""
    def loc(p):
        x, _, z = t.local(p[0], ground, p[1])
        return [x, z]
    g = t.local(0, ground, 0)[1]
    SITES[key] = {'mode': mode, 'anchor': loc(anchor), 'dry': [loc(p) for p in dry], 'wet': [loc(p) for p in wet],
                  'around': [loc(p) for p in around], 'y_offset': -(g + 1), **rules}


# 1. Fisherman's Cottage (the 1.x house, repaired) -------------------------------------------------------------------

def cottage():
    """The original stilt house over the shallows. Its baked-in sea is removed (the real sea is under it now), its
    stilts reach eight blocks deeper, its barrels draw from a loot table, and Saylor is a journeyman who keeps his job."""
    src = load(LEGACY_HOUSE)
    pal = src['palette']
    t = Template('cottage')
    deck = 3  # layer of the walkway planks in the 1.x template
    posts = set()
    barrels = 0
    for b in src['blocks']:
        x, y, z = (int(v) for v in b['pos'])
        entry = pal[int(b['state'])]
        name = str(entry['Name'])
        props = {k: str(v) for k, v in entry.get('Properties', {}).items()}
        if name == 'minecraft:water' or (name == 'minecraft:air' and y <= deck):
            continue
        if name == 'minecraft:spruce_log' and y == 0:
            posts.add((x, z))
        state = name + ('[' + ','.join(f'{k}={v}' for k, v in sorted(props.items())) + ']' if props else '')
        if 'waterlogged' in props:
            state = state.replace('waterlogged=true', 'waterlogged=false')
        nbt = None
        if 'nbt' in b:
            nbt = Compound(b['nbt'])
            if name == 'minecraft:barrel':
                barrels += 1
                nbt = Compound({'id': String('minecraft:barrel'),
                                'LootTable': String(f'{NS}:chests/fisherman_house' + ('_storage' if barrels % 3 else ''))})
            elif name == 'minecraft:decorated_pot':
                nbt = Compound({'id': String('minecraft:decorated_pot')})
        t.set(x, y, z, state, nbt)
    for x, z in posts:
        t.column(x, z, -8, -1, log('spruce_log'))
    for e in src['entities']:
        nbt = e['nbt']
        kind = str(nbt['id'])
        x, y, z = (float(v) for v in e['pos'])
        if kind == 'minecraft:villager':
            resident(t, int(x), y, int(z), 'fisherman_house', 'Saylor', 'plains', yaw=90.0)
        elif kind == 'minecraft:boat':
            t.boat(int(x), y, int(z), 'spruce', float(nbt['Rotation'][0]))
        elif kind == 'minecraft:item_frame':
            facing = {0: 'down', 1: 'up', 2: 'north', 3: 'south', 4: 'west', 5: 'east'}[int(nbt['Facing'])]
            item = str(nbt['Item']['id'])
            t.item_frame(int(e['blockPos'][0]), int(e['blockPos'][1]), int(e['blockPos'][2]), facing, item)
        elif kind == 'minecraft:painting':
            p = Compound({k: v for k, v in nbt.items() if k in ('id', 'facing', 'variant', 'Rotation')})
            # Hanging entities need their block; the game moves it with the entity when it places the template.
            bx, by, bz = (int(v) for v in e['blockPos'])
            p.update({'TileX': Int(bx), 'TileY': Int(by), 'TileZ': Int(bz)})
            t.entities.append(((x, y, z), p))
    # A crab pot already set in the water by the dock, so the first thing players see is what the mod adds.
    t.set(15, deck - 2, 1, f'{NS}:crab_pot[facing=north,waterlogged=false,baited=true,caught=false]')
    t.set(15, deck - 1, 1, 'minecraft:chain[axis=y]')
    site(t, 'fisherman_house', 'land', anchor=(4, 13), ground=deck,
         dry=[(2, 11), (6, 11), (2, 15), (6, 15)],
         wet=[(20, 13), (32, 13), (30, 22), (15, 4)],
         max_slope=2, min_depth=2, max_above_sea=3, search=2)
    return t


POT = f'{NS}:crab_pot'


def pot(facing='north', baited=False):
    return f'{POT}[facing={facing},waterlogged=false,baited={str(baited).lower()},caught=false]'


def net(facing):
    """A Fishing Net hanging on the block behind it; `facing` points away from that block."""
    return f'{NS}:fishing_net[facing={facing},waterlogged=false]'


def gable_roof(t: Template, x1, x2, z1, z2, y, material, ridge_slab=True, gable=None, ends=True):
    """A roof over x1..x2 (inclusive) whose ridge runs along x, rising one block per row from z1 and z2 to the
    middle. The gable ends at x1 and x2 are filled with `gable` under the roof line."""
    half = (z2 - z1) // 2
    for i in range(half + 1):
        yy = y + i
        for x in range(x1 - 1, x2 + 2):
            if z1 + i < z2 - i:
                t.set(x, yy, z1 + i, stairs(material, 'south'))
                t.set(x, yy, z2 - i, stairs(material, 'north'))
            elif z1 + i == z2 - i:
                t.set(x, yy, z1 + i, slab(material) if ridge_slab else f'minecraft:{material}s')
        if gable and ends:
            for x in (x1, x2):
                for z in range(z1 + i + 1, z2 - i):
                    t.set(x, yy, z, gable)
    return y + half


def cone(t: Template, cx, cz, y, radius, material):
    """A round roof of stairs rising one ring per layer, capped with a full block."""
    for r in range(radius, 0, -1):
        yy = y + (radius - r)
        for x in range(cx - r - 1, cx + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                d = math.hypot(x - cx, z - cz)
                if r - 0.5 < d <= r + 0.5:
                    dx, dz = x - cx, z - cz
                    facing = ('west' if dx > 0 else 'east') if abs(dx) >= abs(dz) else ('north' if dz > 0 else 'south')
                    t.set(x, yy, z, stairs(material, facing))
                elif d <= r - 0.5:
                    t.set(x, yy, z, f'minecraft:{material}')
    t.set(cx, y + radius, cz, f'minecraft:{material}')
    return y + radius


def frame_walls(t: Template, x1, z1, x2, z2, y1, y2, post, infill, every=4):
    """Timber-framed walls: posts at the corners and every few blocks, infill between, a beam on top."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x not in (x1, x2) and z not in (z1, z2):
                continue
            corner = x in (x1, x2) and z in (z1, z2)
            along_x = z in (z1, z2)
            idx = (x - x1) if along_x else (z - z1)
            length = (x2 - x1) if along_x else (z2 - z1)
            is_post = corner or (idx % every == 0) or idx == length
            for y in range(y1, y2 + 1):
                if y == y2 and not corner:
                    t.set(x, y, z, log(post.replace('[axis=y]', ''), 'x' if along_x else 'z'))
                else:
                    t.set(x, y, z, log(post) if is_post else f'minecraft:{infill}')


# 2. Harbour Pier ---------------------------------------------------------------------------------------------------

def harbour_pier():
    """A bait shop on the beach and a long pier with a T-head, lamp posts, net racks, a crane and a bell."""
    t = Template('harbour_pier')
    G = 0
    # Shop: x 0..10, z 0..8, on a stone plinth that reaches into the sand.
    t.fill(0, G - 4, 0, 10, G - 2, 8, 'minecraft:cobblestone')
    t.fill(0, G - 1, 0, 10, G - 1, 8, 'minecraft:stone_bricks')
    t.fill(0, G, 0, 10, G, 8, 'minecraft:spruce_planks')
    t.air(-1, G + 1, -2, 11, G + 13, 9)
    frame_walls(t, 0, 0, 10, 8, G + 1, G + 4, 'stripped_spruce_log', 'birch_planks', every=5)
    for x in (2, 3, 7, 8):
        t.fill(x, G + 2, 0, x, G + 3, 0, 'minecraft:glass_pane')
        t.fill(x, G + 2, 8, x, G + 3, 8, 'minecraft:glass_pane')
    for z in (2, 6):
        t.fill(0, G + 2, z, 0, G + 3, z, 'minecraft:glass_pane')
        t.fill(10, G + 2, z, 10, G + 3, z, 'minecraft:glass_pane')
    # Shutters beside the front windows.
    for x, side in ((1, 'west'), (4, 'east'), (6, 'west'), (9, 'east')):
        t.set(x, G + 2, -1, trapdoor('spruce', side, open_=True))
        t.set(x, G + 3, -1, trapdoor('spruce', side, open_=True))
    for x in (1, 4, 6, 9):
        t.set(x, G + 1, -1, 'minecraft:potted_blue_orchid' if x in (1, 9) else AIR)
    door(t, 5, G + 1, 0, 'spruce', 'north')
    door(t, 5, G + 1, 8, 'spruce', 'south')
    t.set(5, G, -1, stairs('spruce', 'south'))
    top = gable_roof(t, 0, 10, -1, 9, G + 5, 'deepslate_tile', gable='minecraft:spruce_planks')
    t.set(0, G + 7, 4, 'minecraft:glass_pane')
    t.set(10, G + 7, 4, 'minecraft:glass_pane')
    # Brick chimney with a campfire on top for smoke.
    t.fill(2, G + 1, 7, 2, top + 1, 7, 'minecraft:bricks')
    t.set(2, top + 2, 7, 'minecraft:campfire[lit=true,signal_fire=false,facing=north,waterlogged=false]')
    t.set(3, G + 1, 7, 'minecraft:furnace[facing=north,lit=false]')
    # Inside: a counter, barrels, pots, nets, carpet and lanterns.
    t.fill(6, G + 1, 3, 9, G + 1, 3, slab('spruce', 'top'))
    t.set(6, G + 1, 2, 'minecraft:barrel[facing=up,open=false]')
    t.container(9, G + 1, 1, 'minecraft:barrel[facing=up,open=false]', 'chests/harbour_pier')
    t.container(9, G + 2, 1, 'minecraft:barrel[facing=west,open=false]', 'chests/harbour_pier_storage')
    t.container(8, G + 1, 1, 'minecraft:barrel[facing=up,open=false]', 'chests/harbour_pier_storage')
    t.set(1, G + 1, 1, pot('east'))
    t.set(1, G + 2, 1, pot('south'))
    t.set(2, G + 1, 1, pot('south', baited=True))
    for x in (4, 5, 6, 7, 8):
        t.set(x, G + 3, 7, net('north'))
    for z in (5, 6):
        t.set(9, G + 3, z, net('west'))
    t.fill(3, G + 1, 4, 4, G + 1, 5, 'minecraft:light_blue_carpet')
    t.set(3, G + 4, 4, lantern(hanging=True))
    t.set(7, G + 4, 4, lantern(hanging=True))
    t.item_frame(9, G + 3, 2, 'west', 'cod')
    t.item_frame(1, G + 3, 3, 'east', 'salmon')
    t.item_frame(1, G + 3, 4, 'east', 'tropical_fish')
    resident(t, 7, G + 1, 2, 'harbour_pier', 'Harbourmaster Wren', 'plains', yaw=180.0)
    t.sign(5, G + 3, -1, 'minecraft:spruce_wall_sign[facing=north]', ['', 'BAIT & TACKLE', '~ harbour ~', ''])
    # The pier: x 3..7 to z 30, then a T-head x 0..10, z 30..36. Posts reach twelve blocks down.
    t.fill(3, G, 9, 7, G, 36, 'minecraft:spruce_planks')
    t.fill(0, G, 30, 10, G, 36, 'minecraft:spruce_planks')
    t.air(0, G + 1, 9, 10, G + 6, 36)
    for z in range(9, 30):
        for x in (3, 7):
            t.set(x, G + 1, z, fence('spruce'))
    for z in range(10, 31, 4):
        for x in (3, 7):
            t.column(x, z, G - 12, G - 1, log('spruce_log'))
            t.set(x, G + 1, z, log('spruce_log'))
    for x, z in ((0, 30), (10, 30), (0, 36), (10, 36), (5, 36), (0, 33), (10, 33)):
        t.column(x, z, G - 12, G - 1, log('spruce_log'))
    for x in range(0, 11):
        t.set(x, G + 1, 36, fence('spruce'))
        if not 3 <= x <= 7:
            t.set(x, G + 1, 30, fence('spruce'))
    for z in range(31, 36):
        t.set(0, G + 1, z, fence('spruce'))
        t.set(10, G + 1, z, fence('spruce'))
    t.set(0, G + 1, 32, AIR)  # gaps for stepping into a boat
    t.set(10, G + 1, 32, AIR)
    for x, z in ((3, 18), (7, 26), (0, 30), (10, 30)):
        t.fill(x, G + 1, z, x, G + 3, z, fence('spruce'))
        t.set(x, G + 4, z, lantern())
    # Net racks on the T-head: plank frames with nets on their inner faces.
    for x, face in ((1, 'east'), (9, 'west')):
        t.fill(x, G + 1, 33, x, G + 3, 35, 'minecraft:stripped_spruce_wood')
        for z in (33, 34, 35):
            for y in (G + 1, G + 2, G + 3):
                t.set(x + (1 if face == 'east' else -1), y, z, net(face))
    # Crane with a hanging barrel over the water.
    t.fill(8, G + 1, 31, 8, G + 6, 31, log('spruce_log'))
    t.fill(9, G + 6, 31, 12, G + 6, 31, log('spruce_log', 'x'))
    t.fill(12, G + 2, 31, 12, G + 5, 31, 'minecraft:chain[axis=y]')
    t.set(12, G + 1, 31, 'minecraft:barrel[facing=up,open=false]')
    t.set(5, G + 1, 35, 'minecraft:bell[attachment=floor,facing=north,powered=false]')
    t.set(4, G + 1, 31, pot('north'))
    t.set(4, G + 2, 31, pot('east'))
    t.set(6, G + 1, 31, 'minecraft:barrel[facing=up,open=false]')
    t.container(2, G + 1, 31, 'minecraft:chest[facing=east,type=single,waterlogged=false]', 'chests/harbour_pier')
    t.boat(-2, G - 0.4, 32, 'spruce', 0.0)
    t.boat(12, G - 0.4, 34, 'oak', 180.0)
    site(t, 'harbour_pier', 'land', anchor=(5, 4), ground=G,
         dry=[(0, 0), (10, 0), (0, 8), (10, 8), (5, 4)],
         wet=[(5, 34), (1, 35), (9, 35), (5, 22)],
         max_slope=2, min_depth=3, max_above_sea=3, search=2)
    return t


# 3. Lighthouse -----------------------------------------------------------------------------------------------------

def lighthouse():
    """A red and white tower on a rock with a gallery, a lit lantern room under a copper cap, and the keeper's cottage."""
    t = Template('lighthouse')
    G = 0
    R = 4
    top = G + 21
    # Rock: a stone plinth under tower and cottage.
    for y in range(G - 5, G):
        t.disc(0, 0, y, 6, 'minecraft:cobblestone')
    t.disc(0, 0, G, 6, 'minecraft:stone_bricks')
    for x, z in ((-6, 0), (0, -6), (6, -2), (-4, 4), (-5, -4)):
        t.set(x, G, z, 'minecraft:mossy_stone_bricks')
    t.fill(5, G - 4, -4, 13, G, 4, 'minecraft:cobblestone')
    t.fill(5, G, -4, 13, G, 4, 'minecraft:stone_bricks')
    for y in range(G + 1, top + 12):
        t.disc(0, 0, y, 6, AIR)
    t.air(5, G + 1, -5, 14, G + 10, 5)
    # Tower: bands of white and red, hollow, with a ladder on the south wall.
    for y in range(G + 1, top):
        band = ((y - G - 1) // 4) % 2
        t.disc(0, 0, y, R, 'minecraft:red_concrete' if band else 'minecraft:white_concrete', ring=True)
    t.column(0, 3, G + 1, top, 'minecraft:ladder[facing=north,waterlogged=false]')
    for y, (x, z) in ((G + 6, (-4, 0)), (G + 11, (0, -4)), (G + 16, (4, 0)), (G + 11, (-4, 0))):
        t.fill(x, y, z, x, y + 1, z, 'minecraft:glass_pane')
    t.disc(0, 0, G + 10, R - 1, 'minecraft:spruce_planks')
    t.set(0, G + 10, 3, 'minecraft:ladder[facing=north,waterlogged=false]')
    t.set(1, G + 11, 0, 'minecraft:barrel[facing=up,open=false]')
    t.set(-1, G + 11, 1, lantern())
    door(t, 0, G + 1, -4, 'spruce', 'north')
    t.set(0, G, -5, stairs('stone_brick', 'south'))
    t.set(-1, G + 3, -5, 'minecraft:wall_torch[facing=north]')
    t.set(1, G + 3, -5, 'minecraft:wall_torch[facing=north]')
    # Gallery with an iron railing.
    t.disc(0, 0, top, R + 1, 'minecraft:polished_andesite')
    t.set(0, top, 3, 'minecraft:ladder[facing=north,waterlogged=false]')
    t.disc(0, 0, top + 1, R + 1, 'minecraft:iron_bars', ring=True)
    # Lantern room: glass on posts around a bright core.
    for y in range(top + 1, top + 5):
        t.disc(0, 0, y, 2, 'minecraft:glass', ring=True)
    for x, z in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        t.column(x, z, top + 1, top + 4, 'minecraft:polished_andesite')
    t.set(0, top + 1, 0, 'minecraft:sea_lantern')
    t.set(0, top + 2, 0, 'minecraft:glowstone')
    t.set(0, top + 3, 0, 'minecraft:sea_lantern')
    for x, z in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
        t.set(x, top + 2, z, lantern())
    t.set(0, top + 1, 1, AIR)
    # Copper cap and a lightning rod.
    t.disc(0, 0, top + 5, 3, 'minecraft:waxed_oxidized_cut_copper_slab[type=bottom,waterlogged=false]')
    cap = cone(t, 0, 0, top + 6, 2, 'waxed_oxidized_cut_copper')
    t.set(0, cap + 1, 0, 'minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]')
    # Keeper's cottage, east of the tower: x 6..12, z -3..3.
    t.fill(6, G + 1, -3, 12, G + 1, 3, 'minecraft:stone_bricks')
    frame_walls(t, 6, -3, 12, 3, G + 1, G + 4, 'stripped_spruce_log', 'spruce_planks', every=3)
    for x in range(7, 12):
        for z in (-3, 3):
            t.set(x, G + 1, z, 'minecraft:stone_bricks')
    t.fill(7, G + 1, -2, 11, G + 1, 2, AIR)
    t.fill(7, G, -2, 11, G, 2, 'minecraft:spruce_planks')
    gable_roof(t, 6, 12, -4, 4, G + 5, 'deepslate_tile', gable='minecraft:spruce_planks')
    door(t, 6, G + 1, 0, 'spruce', 'west')
    for x in (8, 10):
        t.fill(x, G + 2, -3, x, G + 3, -3, 'minecraft:glass_pane')
        t.fill(x, G + 2, 3, x, G + 3, 3, 'minecraft:glass_pane')
    t.fill(12, G + 2, 0, 12, G + 3, 0, 'minecraft:glass_pane')
    t.set(11, G + 1, -2, 'minecraft:red_bed[facing=west,part=head,occupied=false]')
    t.set(10, G + 1, -2, 'minecraft:red_bed[facing=west,part=foot,occupied=false]')
    t.container(11, G + 1, 2, 'minecraft:chest[facing=west,type=single,waterlogged=false]', 'chests/lighthouse')
    t.set(11, G + 1, 1, 'minecraft:barrel[facing=up,open=false]')
    t.set(7, G + 1, 2, 'minecraft:bookshelf')
    t.set(8, G + 1, 2, 'minecraft:cartography_table')
    t.set(9, G + 4, 0, lantern(hanging=True))
    t.set(7, G + 1, -2, 'minecraft:crafting_table')
    t.item_frame(11, G + 3, -1, 'west', 'compass')
    t.set(9, G + 1, 0, 'minecraft:brown_carpet')
    resident(t, 9, G + 1, 1, 'lighthouse', 'Keeper Morrow', 'plains', yaw=270.0)
    site(t, 'lighthouse', 'land', anchor=(0, 0), ground=G,
         dry=[(0, 0), (-3, -3), (3, 3), (-3, 3), (3, -3), (10, 0)],
         wet=ring(0, 0, 13), max_slope=3, min_depth=2, max_above_sea=10, any_wet=True, search=2)
    return t


# 4. Stilt Shack ----------------------------------------------------------------------------------------------------

def stilt_shack():
    """A mangrove hut on stilts over swamp water: porch, ladder to a little dock, cauldron and brewing stand."""
    t = Template('stilt_shack')
    G = 0           # the water's (or the mud's) top block
    D = G + 4       # the deck
    for x in (0, 4, 8):
        for z in (0, 4, 8):
            if (x, z) != (4, 4):
                t.column(x, z, G - 4, D - 1, log('mangrove_log'))
    t.fill(0, D, 0, 8, D, 8, 'minecraft:mangrove_planks')
    t.fill(2, D, 9, 6, D, 11, 'minecraft:mangrove_planks')
    t.column(2, 11, G - 3, D - 1, log('mangrove_log'))
    t.column(6, 11, G - 3, D - 1, log('mangrove_log'))
    t.air(-1, D + 1, -1, 9, D + 9, 12)
    frame_walls(t, 1, 1, 7, 7, D + 1, D + 3, 'mangrove_log', 'mangrove_planks', every=3)
    for x in (3, 5):
        t.set(x, D + 2, 1, 'minecraft:glass_pane')
        t.set(x, D + 2, 7, 'minecraft:glass_pane')
    t.set(1, D + 2, 4, 'minecraft:glass_pane')
    t.set(7, D + 2, 4, 'minecraft:glass_pane')
    door(t, 4, D + 1, 7, 'mangrove', 'south')
    roof = gable_roof(t, 1, 7, 0, 8, D + 4, 'mangrove', gable='minecraft:mangrove_planks')
    t.fill(6, D + 1, 2, 6, roof + 1, 2, 'minecraft:mud_bricks')
    t.set(6, roof + 2, 2, 'minecraft:campfire[lit=true,signal_fire=false,facing=north,waterlogged=false]')
    # Moss and vines on the roof edges.
    for x in range(0, 9, 2):
        t.set(x, D + 3, -1, 'minecraft:vine[north=false,south=true,east=false,west=false,up=false]')
        t.set(x + 1, D + 3, 9, 'minecraft:vine[north=true,south=false,east=false,west=false,up=false]')
    # Inside.
    t.set(2, D + 1, 2, 'minecraft:water_cauldron[level=3]')
    t.set(3, D + 1, 2, 'minecraft:brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]')
    t.set(5, D + 1, 2, 'minecraft:furnace[facing=south,lit=false]')
    t.set(2, D + 1, 5, 'minecraft:green_bed[facing=north,part=head,occupied=false]')
    t.set(2, D + 1, 6, 'minecraft:green_bed[facing=north,part=foot,occupied=false]')
    t.container(6, D + 1, 6, 'minecraft:barrel[facing=up,open=false]', 'chests/stilt_shack')
    t.set(6, D + 1, 5, 'minecraft:barrel[facing=up,open=false]')
    t.set(6, D + 2, 6, pot('west', baited=True))
    t.set(4, D + 3, 4, lantern(hanging=True))
    t.set(4, D + 3, 2, net('south'))
    t.set(3, D + 3, 6, net('north'))
    t.set(5, D + 3, 6, net('north'))
    t.item_frame(2, D + 2, 3, 'east', 'fishing_rod')
    resident(t, 4, D + 1, 4, 'stilt_shack', 'Old Bayou Tam', 'swamp', yaw=180.0)
    # Porch with a rail, a lamp post and a ladder down to a dock on the water.
    for x in range(0, 9):
        if x != 4:
            t.set(x, D + 1, 8, AIR) if 1 <= x <= 7 else t.set(x, D + 1, 8, fence('mangrove'))
    for z in range(9, 12):
        t.set(2, D + 1, z, fence('mangrove'))
        t.set(6, D + 1, z, fence('mangrove'))
    t.set(3, D + 1, 11, fence('mangrove'))
    t.set(5, D + 1, 11, fence('mangrove'))
    t.fill(6, D + 2, 11, 6, D + 3, 11, fence('mangrove'))
    t.set(6, D + 4, 11, lantern())
    t.set(4, D, 11, AIR)
    t.column(4, 12, G + 1, D - 1, log('mangrove_log'))
    t.column(4, 11, G + 1, D, 'minecraft:ladder[facing=north,waterlogged=false]')
    t.fill(3, G + 1, 12, 5, G + 1, 15, 'minecraft:mangrove_planks')
    t.set(4, G + 1, 12, log('mangrove_log'))
    t.fill(3, G - 3, 15, 3, G, 15, log('mangrove_log'))
    t.fill(5, G - 3, 15, 5, G, 15, log('mangrove_log'))
    t.set(3, G + 2, 15, fence('mangrove'))
    t.set(5, G + 2, 15, fence('mangrove'))
    t.set(6, G, 14, pot('east'))
    t.boat(7, G + 1, 13, 'spruce', 90.0)
    site(t, 'stilt_shack', 'swamp', anchor=(4, 4), ground=G,
         dry=[(0, 0), (8, 0), (0, 8), (8, 8), (4, 4), (4, 14)], around=ring(4, 6, 12),
         max_slope=2, max_depth=4, max_rise=4)
    return t


# 5. Ice Fishing Camp -----------------------------------------------------------------------------------------------

def ice_fishing_camp():
    """A spruce hut on an ice shelf over a hole in the ice, with a pot already set, a campfire, a tent and a sled."""
    t = Template('ice_fishing_camp')
    G = 0           # the top water block, frozen by the shelf
    for x in range(-7, 8):
        for z in range(-7, 8):
            d = math.hypot(x, z * 1.15)
            if d <= 7.2:
                t.set(x, G, z, 'minecraft:packed_ice' if (x * 7 + z * 3) % 5 else 'minecraft:ice')
                if d <= 5.5:
                    t.set(x, G - 1, z, 'minecraft:ice')
                if d > 6.2 and (x + z) % 3 == 0:
                    t.set(x, G, z, 'minecraft:ice')
                t.set(x, G + 1, z, AIR)
                if d > 3.5 and (x * 5 + z) % 4 == 0:
                    t.set(x, G + 1, z, 'minecraft:snow[layers=1]')
    # Icebergs are placed before structures and never seen by the shore sampling: clear a tall column over the shelf so
    # the camp always stands in open air, in a bay of the iceberg if there is one.
    for x in range(-7, 8):
        for z in range(-7, 8):
            if math.hypot(x, z * 1.15) <= 7.2:
                t.air(x, G + 2, z, x, G + 30, z)
    # Hut: x -2..2, z -2..2.
    t.fill(-2, G, -2, 2, G, 2, 'minecraft:spruce_planks')
    frame_walls(t, -2, -2, 2, 2, G + 1, G + 3, 'stripped_spruce_log', 'spruce_planks', every=4)
    t.fill(-1, G + 1, -1, 1, G + 2, 1, AIR)
    door(t, 0, G + 1, 2, 'spruce', 'south')
    t.set(-2, G + 2, 0, 'minecraft:glass_pane')
    t.set(2, G + 2, 0, 'minecraft:glass_pane')
    roof = gable_roof(t, -2, 2, -3, 3, G + 4, 'spruce', gable='minecraft:spruce_planks')
    for x in range(-3, 4):
        for z in range(-3, 4):
            if t.get(x, roof, z) and 'slab' in t.get(x, roof, z):
                t.set(x, roof + 1, z, 'minecraft:snow[layers=2]')
    # The hole: open water inside the hut, a pot hanging in it on a chain.
    t.column(0, -1, G - 1, G + 3, 'minecraft:chain[axis=y,waterlogged=false]')
    t.set(0, G - 2, -1, pot('south', baited=True))
    t.container(-1, G + 1, -1, 'minecraft:barrel[facing=up,open=false]', 'chests/ice_fishing_camp')
    t.set(1, G + 1, -1, 'minecraft:barrel[facing=up,open=false]')
    t.set(1, G + 1, 1, 'minecraft:furnace[facing=west,lit=false]')
    t.set(-1, G + 3, 0, lantern(hanging=True))
    t.item_frame(1, G + 2, -1, 'south', 'cod')
    resident(t, 0, G + 1, 0, 'ice_fishing_camp', 'Frost-Beard Ole', 'snow', yaw=180.0)
    # Outside: campfire with logs to sit on, a wool tent, a sled with barrels.
    t.set(0, G + 1, 5, 'minecraft:campfire[lit=true,signal_fire=false,facing=north,waterlogged=false]')
    t.set(-1, G + 1, 6, log('spruce_log', 'x'))
    t.set(2, G + 1, 5, log('spruce_log', 'z'))
    for z in (-2, -1, 0, 1):
        t.set(5, G + 1, z, 'minecraft:white_wool')
        t.set(4, G + 2, z, 'minecraft:white_wool')
        t.set(6, G + 2, z, 'minecraft:white_wool')
        t.set(5, G + 3, z, 'minecraft:white_wool')
        t.set(5, G + 1, z, AIR)
        t.set(5, G + 2, z, AIR)
        t.set(4, G + 1, z, 'minecraft:white_wool')
        t.set(6, G + 1, z, 'minecraft:white_wool')
    t.set(5, G + 1, -2, 'minecraft:white_wool')
    t.set(5, G + 2, -2, 'minecraft:white_wool')
    t.set(5, G + 1, 1, 'minecraft:light_gray_carpet')
    t.set(5, G + 1, 0, 'minecraft:cyan_bed[facing=north,part=head,occupied=false]')
    t.set(5, G + 1, 1, 'minecraft:cyan_bed[facing=north,part=foot,occupied=false]')
    t.fill(-5, G + 1, -2, -4, G + 1, 1, 'minecraft:spruce_slab[type=bottom,waterlogged=false]')
    t.set(-5, G + 2, -1, 'minecraft:barrel[facing=up,open=false]')
    t.set(-4, G + 2, 0, pot('east'))
    t.set(-5, G + 1, -3, fence('spruce'))
    t.set(-4, G + 1, -3, fence('spruce'))
    t.fill(-3, G + 1, 4, -3, G + 2, 4, fence('spruce'))
    t.set(-3, G + 3, 4, lantern())
    site(t, 'ice_fishing_camp', 'water', anchor=(0, 0), ground=G,
         wet=[(0, 0), (-6, 0), (6, 0), (0, -6), (0, 6), (-4, -4), (4, 4)], max_slope=0, min_depth=3)
    return t


# 6. River Boathouse ------------------------------------------------------------------------------------------------

def river_boathouse():
    """An oak cottage on the bank and a roofed slip over the water with a boat in it."""
    t = Template('river_boathouse')
    G = 0
    # Cottage: x 0..6, z 0..6.
    t.fill(0, G - 3, 0, 6, G - 1, 6, 'minecraft:cobblestone')
    t.fill(0, G, 0, 6, G, 6, 'minecraft:oak_planks')
    t.air(-1, G + 1, -1, 7, G + 10, 7)
    frame_walls(t, 0, 0, 6, 6, G + 1, G + 3, 'oak_log', 'white_terracotta', every=3)
    for x in (0, 6):
        t.set(x, G + 2, 2, 'minecraft:glass_pane')
        t.set(x, G + 2, 4, 'minecraft:glass_pane')
    t.set(2, G + 2, 0, 'minecraft:glass_pane')
    t.set(4, G + 2, 0, 'minecraft:glass_pane')
    door(t, 3, G + 1, 0, 'oak', 'north')
    door(t, 3, G + 1, 6, 'oak', 'south')
    gable_roof(t, 0, 6, -1, 7, G + 4, 'dark_oak', gable='minecraft:oak_planks')
    t.set(1, G + 1, 1, 'minecraft:crafting_table')
    t.container(5, G + 1, 1, 'minecraft:chest[facing=west,type=single,waterlogged=false]', 'chests/river_boathouse')
    t.set(5, G + 1, 2, 'minecraft:barrel[facing=up,open=false]')
    t.set(1, G + 1, 4, 'minecraft:yellow_bed[facing=north,part=head,occupied=false]')
    t.set(1, G + 1, 5, 'minecraft:yellow_bed[facing=north,part=foot,occupied=false]')
    t.set(3, G + 3, 3, lantern(hanging=True))
    t.set(5, G + 1, 5, 'minecraft:potted_poppy')
    t.item_frame(5, G + 2, 3, 'west', 'salmon')
    resident(t, 3, G + 1, 3, 'river_boathouse', 'Ferryman Hale', 'plains', yaw=0.0)
    # Boathouse: a slip x 1..5, z 7..16 with walkways on both sides over the water.
    for x in (1, 5):
        t.fill(x, G, 7, x, G, 16, 'minecraft:oak_planks')
        for z in (7, 10, 13, 16):
            t.column(x, z, G - 6, G + 3, log('oak_log'))
    for x in (0, 6):
        for z in range(7, 17):
            t.set(x, G + 1, z, fence('oak'))
    t.air(1, G + 1, 7, 5, G + 7, 17)
    for x in (1, 5):
        for z in (7, 10, 13, 16):
            t.column(x, z, G + 1, G + 3, log('oak_log'))
    t.fill(1, G + 4, 7, 5, G + 4, 16, AIR)
    for z in range(6, 18):
        t.set(0, G + 4, z, stairs('dark_oak', 'east'))
        t.set(6, G + 4, z, stairs('dark_oak', 'west'))
        t.set(1, G + 5, z, stairs('dark_oak', 'east'))
        t.set(5, G + 5, z, stairs('dark_oak', 'west'))
        t.set(2, G + 6, z, stairs('dark_oak', 'east'))
        t.set(4, G + 6, z, stairs('dark_oak', 'west'))
        t.set(3, G + 7, z, slab('dark_oak'))
    for x in (1, 5):
        t.fill(x, G + 4, 7, x, G + 4, 16, log('oak_log', 'z'))
    t.fill(2, G + 4, 16, 4, G + 4, 16, log('oak_log', 'x'))
    t.set(3, G + 3, 16, lantern(hanging=True))
    t.set(3, G + 3, 10, lantern(hanging=True))
    t.fill(2, G, 7, 4, G, 7, 'minecraft:oak_planks')
    for z in (10, 13):
        t.set(2, G + 2, z, net('east'))
        t.set(4, G + 2, z, net('west'))
    t.set(1, G + 1, 8, 'minecraft:barrel[facing=up,open=false]')
    t.set(5, G + 1, 8, pot('west'))
    t.boat(3, G - 0.4, 12, 'oak', 0.0)
    site(t, 'river_boathouse', 'land', anchor=(3, 3), ground=G,
         dry=[(0, 0), (6, 0), (0, 6), (6, 6), (3, 3)],
         wet=[(3, 11), (3, 15), (2, 17), (4, 17)], around=ring(3, 3, 10), max_slope=2, min_depth=2, max_above_sea=3,
         max_rise=6, search=2)
    return t


# 7. Sunken Trawler -------------------------------------------------------------------------------------------------

def sunken_trawler():
    """A fishing trawler on the sea floor: a broken hull, a fallen mast, nets, the hold's barrels and the captain's chest."""
    t = Template('sunken_trawler')
    G = 0           # the sea floor's top block
    rnd = random.Random(7)
    W = 'minecraft:water[level=0]'
    hull, deck = 'dark_oak_planks', 'spruce_planks'
    length = 22

    def half_width(z):
        if z >= length - 4:
            return max(0, 3 - (z - (length - 4)))
        return 3

    # Water everywhere around and inside, so no air pockets are left under the sea.
    for x in range(-6, 7):
        for z in range(-3, length + 3):
            for y in range(G + 1, G + 10):
                t.set(x, y, z, W)
    for z in range(0, length):
        w = half_width(z)
        t.set(0, G, z, log('stripped_dark_oak_log', 'z'))
        for x in range(-w, w + 1):
            if abs(x) == w:
                for y in range(G + 1, G + 5):
                    if rnd.random() > (0.25 if 6 < z < 15 and x > 0 else 0.06):
                        t.set(x, y, z, f'minecraft:{hull}')
                t.set(x, G + 5, z, slab('dark_oak', 'bottom'))
            elif abs(x) == w - 1:
                t.set(x, G + 1, z, f'minecraft:{hull}')
        for x in range(-w + 1, w):
            if rnd.random() > 0.15:
                t.set(x, G + 4, z, f'minecraft:{deck}')
    t.fill(-3, G, 0, 3, G + 4, 0, f'minecraft:{hull}')
    t.fill(-1, G + 2, 0, 1, G + 2, 0, 'minecraft:glass_pane')
    # A torn hole in the deck over the hold.
    for x, z in ((0, 8), (1, 8), (0, 9), (-1, 9), (0, 10), (1, 10), (1, 11)):
        t.set(x, G + 4, z, W)
    # Hold: sand drifted in, barrels and the hold's loot.
    for z in range(6, 14):
        for x in range(-2, 3):
            if rnd.random() < 0.4:
                t.set(x, G + 1, z, 'minecraft:sand')
    t.container(-2, G + 2, 7, 'minecraft:barrel[facing=up,open=false]', 'chests/sunken_trawler')
    t.container(2, G + 2, 12, 'minecraft:barrel[facing=up,open=false]', 'chests/sunken_trawler')
    t.set(-2, G + 2, 12, 'minecraft:barrel[facing=up,open=false]')
    t.set(2, G + 2, 7, pot('north'))
    t.set(-1, G + 2, 14, pot('west'))
    # Wheelhouse at the stern with the captain's chest.
    t.fill(-2, G + 5, 1, 2, G + 7, 4, f'minecraft:{deck}')
    t.fill(-1, G + 5, 2, 1, G + 7, 3, W)
    t.fill(-2, G + 6, 2, -2, G + 6, 3, 'minecraft:glass_pane')
    t.fill(2, G + 6, 2, 2, G + 6, 3, W)
    t.set(0, G + 6, 4, W)
    t.set(0, G + 5, 4, W)
    t.fill(-2, G + 8, 1, 2, G + 8, 4, slab('dark_oak', 'bottom'))
    t.set(1, G + 8, 3, W)
    t.container(-1, G + 5, 2, 'minecraft:chest[facing=east,type=single,waterlogged=true]', 'chests/sunken_trawler_captain')
    t.set(1, G + 7, 2, 'minecraft:lantern[hanging=true,waterlogged=true]')
    t.set(0, G + 5, 3, 'minecraft:barrel[facing=up,open=false]')
    # Broken mast and the fallen top lying on the sea floor beside the hull.
    t.column(0, 12, G + 5, G + 8, log('spruce_log'))
    for z in range(8, 18):
        t.set(5, G + 1, z, log('spruce_log', 'z'))
    t.set(5, G + 2, 15, log('spruce_log', 'x'))
    t.set(6, G + 2, 15, log('spruce_log', 'x'))
    # Nets hanging on the hull, kelp and sea pickles around.
    for z in range(3, 15, 2):
        side = 3 if half_width(z) == 3 else None
        if side and t.get(-4, G + 3, z) is None or t.get(-4, G + 3, z) == W:
            if t.get(-3, G + 3, z) == f'minecraft:{hull}':
                t.set(-4, G + 3, z, f'{NS}:fishing_net[facing=west,waterlogged=true]')
                t.set(-4, G + 2, z, f'{NS}:fishing_net[facing=west,waterlogged=true]')
    for x, z in ((-5, 2), (4, 20), (-4, 17), (6, 4), (-6, 10)):
        h = rnd.randint(2, 5)
        for y in range(G + 1, G + 1 + h):
            t.set(x, y, z, 'minecraft:kelp_plant')
        t.set(x, G + 1 + h, z, 'minecraft:kelp[age=20]')
    for x, z in ((3, -1), (-3, 19), (4, 8)):
        t.set(x, G + 1, z, 'minecraft:sea_pickle[pickles=3,waterlogged=true]')
    t.mob(1, G + 5, 9, 'drowned', {'CustomName': String('{"text":"Drowned Deckhand"}')})
    t.mob(-1, G + 2, 10, 'drowned')
    wet = [(0, 0), (0, 11), (0, 21), (-3, 6), (3, 15), (-5, 18), (5, 3)]
    site(t, 'sunken_trawler', 'seafloor', anchor=(0, 10), ground=G, wet=wet, max_slope=4, min_depth=12)
    return t



def legacy_house():
    """The 1.x template, kept at its id so houses 1.x left half-generated finish the way they started. Only one thing
    changes: its paintings and item frames recorded their block 8 below where they hang, so the game logged an error
    and dropped the position; the block is now the one they hang on."""
    src = load(LEGACY_HOUSE)
    for e in src['entities']:
        if 'TileX' in e['nbt']:
            for axis, v in zip('XYZ', e['blockPos']):
                e['nbt'][f'Tile{axis}'] = Int(int(v))
    with gzip.GzipFile(OUT / 'fisherman_house.nbt', 'wb', mtime=0) as out:
        File(src).write(out, byteorder='big')


BUILDERS = [cottage, harbour_pier, lighthouse, stilt_shack, ice_fishing_camp, river_boathouse, sunken_trawler]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for build in BUILDERS:
        t = build()
        size = t.save(OUT / f'{t.name}.nbt')
        print(f'{t.name}: {size[0]}x{size[1]}x{size[2]}, {len(t.blocks)} blocks, {len(t.entities)} entities')
    legacy_house()
    (OUT / 'sites.json').write_text(json.dumps(SITES, indent=2) + '\n')


if __name__ == '__main__':
    main()
