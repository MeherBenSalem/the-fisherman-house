#!/usr/bin/env python3
"""A small builder for structure templates (the .nbt files vanilla's structure blocks save).

Templates are written in the 1.20.1 format (DataVersion 3465): every newer version upgrades them through its own data
fixers when it loads them, so one file serves all builds. Coordinates may be negative while building; `save` shifts
everything so the smallest corner is (0, 0, 0) and `local` converts a building coordinate to the saved one.
"""
from __future__ import annotations

import gzip
import math
from pathlib import Path

from nbtlib import Byte, Compound, Double, File, Float, Int, List, Long, Short, String

DATA_VERSION = 3465  # 1.20.1
NS = 'fisherman_house'
AIR = 'minecraft:air'


def parse(state: str):
    """'minecraft:oak_stairs[facing=east,half=top]' -> ('minecraft:oak_stairs', {'facing': 'east', 'half': 'top'})."""
    if '[' in state:
        name, props = state[:-1].split('[', 1)
        return name, dict(p.split('=') for p in props.split(',') if p)
    return state, {}


def mc(name: str) -> str:
    return name if ':' in name else 'minecraft:' + name


class Template:
    def __init__(self, name: str):
        self.name = name
        self.blocks: dict[tuple[int, int, int], tuple[str, Compound | None]] = {}
        self.entities: list[tuple[tuple[float, float, float], Compound]] = []
        self.offset = (0, 0, 0)

    # Blocks -------------------------------------------------------------------------------------------------------
    def set(self, x, y, z, state, nbt=None):
        self.blocks[(x, y, z)] = (mc(state), nbt)

    def get(self, x, y, z):
        entry = self.blocks.get((x, y, z))
        return entry[0] if entry else None

    def has(self, x, y, z):
        return (x, y, z) in self.blocks

    def remove(self, x, y, z):
        self.blocks.pop((x, y, z), None)

    def fill(self, x1, y1, z1, x2, y2, z2, state, keep=False, nbt=None):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for z in range(min(z1, z2), max(z1, z2) + 1):
                    if keep and (x, y, z) in self.blocks and self.blocks[(x, y, z)][0] != AIR:
                        continue
                    self.set(x, y, z, state, nbt)

    def air(self, x1, y1, z1, x2, y2, z2):
        """Clears a volume (air is saved, so the terrain there is carved out)."""
        self.fill(x1, y1, z1, x2, y2, z2, AIR)

    def walls(self, x1, y1, z1, x2, y2, z2, state):
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                self.set(x, y, z1, state)
                self.set(x, y, z2, state)
            for z in range(z1, z2 + 1):
                self.set(x1, y, z, state)
                self.set(x2, y, z, state)

    def column(self, x, z, y1, y2, state):
        self.fill(x, y1, z, x, y2, z, state)

    def disc(self, cx, cz, y, radius, state, ring=False):
        for x in range(cx - radius - 1, cx + radius + 2):
            for z in range(cz - radius - 1, cz + radius + 2):
                d = math.hypot(x - cx, z - cz)
                if d <= radius + 0.5 and (not ring or d > radius - 0.5):
                    self.set(x, y, z, state)

    # Block entities ---------------------------------------------------------------------------------------------
    def container(self, x, y, z, state, table):
        block = parse(mc(state))[0].split(':')[1]
        kind = {'barrel': 'barrel', 'chest': 'chest', 'trapped_chest': 'trapped_chest'}.get(block, block)
        self.set(x, y, z, state, Compound({'id': String('minecraft:' + kind), 'LootTable': String(f'{NS}:{table}')}))

    def sign(self, x, y, z, state, lines, color='black', glowing=False):
        """A sign with up to four lines (1.20.1 sign text format)."""
        lines = (list(lines) + ['', '', '', ''])[:4]

        def side(texts):
            return Compound({'messages': List[String]([String('{"text":%s}' % json_str(t)) for t in texts]),
                             'color': String(color), 'has_glowing_text': Byte(1 if glowing else 0)})
        self.set(x, y, z, state, Compound({'id': String('minecraft:sign'), 'is_waxed': Byte(1),
                                           'front_text': side(lines), 'back_text': side(['', '', '', ''])}))

    # Entities ---------------------------------------------------------------------------------------------------
    def entity(self, x, y, z, nbt: Compound):
        self.entities.append(((float(x), float(y), float(z)), nbt))

    def villager(self, x, y, z, name, biome_type, offers, level=3, xp=70, yaw=0.0):
        """A named fisherman who keeps his job: level 3 with experience never loses the profession."""
        nbt = Compound({
            'id': String('minecraft:villager'),
            'CustomName': String('{"text":%s}' % json_str(name)),
            'PersistenceRequired': Byte(1),
            'VillagerData': Compound({'profession': String('minecraft:fisherman'), 'type': String('minecraft:' + biome_type),
                                      'level': Int(level)}),
            'Xp': Int(xp),
            'Offers': Compound({'Recipes': List[Compound]([offer(*o) for o in offers])}),
            'Rotation': List[Float]([Float(yaw), Float(0.0)]),
            'Health': Float(20.0),
        })
        self.entity(x + 0.5, y, z + 0.5, nbt)

    def boat(self, x, y, z, wood='spruce', yaw=0.0):
        self.entity(x + 0.5, y, z + 0.5, Compound({'id': String('minecraft:boat'), 'Type': String(wood),
                                                    'Rotation': List[Float]([Float(yaw), Float(0.0)])}))

    def item_frame(self, x, y, z, facing, item, glow=False):
        """An item frame in the block at (x, y, z), hanging on the face pointing `facing` (its back to the wall)."""
        code = {'down': 0, 'up': 1, 'north': 2, 'south': 3, 'west': 4, 'east': 5}[facing]
        nbt = Compound({'id': String('minecraft:glow_item_frame' if glow else 'minecraft:item_frame'),
                        'Facing': Byte(code), 'Fixed': Byte(1), 'Invulnerable': Byte(1),
                        'TileX': Int(x), 'TileY': Int(y), 'TileZ': Int(z),
                        'Item': Compound({'id': String(mc(item)), 'Count': Byte(1)})})
        self.entity(x + 0.5, y + 0.5, z + 0.5, nbt)

    def mob(self, x, y, z, kind, extra=None):
        nbt = Compound({'id': String(mc(kind)), 'PersistenceRequired': Byte(1)})
        for k, v in (extra or {}).items():
            nbt[k] = v
        self.entity(x + 0.5, y, z + 0.5, nbt)

    # Saving -----------------------------------------------------------------------------------------------------
    def bounds(self):
        xs = [p[0] for p in self.blocks]
        ys = [p[1] for p in self.blocks]
        zs = [p[2] for p in self.blocks]
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    def local(self, x, y, z):
        lo = self.bounds()[0]
        return x - lo[0], y - lo[1], z - lo[2]

    def save(self, path: Path):
        lo, hi = self.bounds()
        size = [hi[i] - lo[i] + 1 for i in range(3)]
        palette: list[tuple[str, tuple]] = []
        index: dict[tuple, int] = {}
        blocks = []
        # Plain blocks first, then blocks with block entities, as vanilla saves them.
        for (x, y, z), (state, nbt) in sorted(self.blocks.items(), key=lambda kv: (kv[1][1] is not None, kv[0][1], kv[0][2], kv[0][0])):
            name, props = parse(state)
            key = (name, tuple(sorted(props.items())))
            if key not in index:
                index[key] = len(palette)
                palette.append(key)
            entry = Compound({'pos': List[Int]([Int(x - lo[0]), Int(y - lo[1]), Int(z - lo[2])]), 'state': Int(index[key])})
            if nbt is not None:
                entry['nbt'] = nbt
            blocks.append(entry)
        pal = []
        for name, props in palette:
            c = Compound({'Name': String(name)})
            if props:
                c['Properties'] = Compound({k: String(v) for k, v in props})
            pal.append(c)
        ents = []
        for (x, y, z), nbt in self.entities:
            lx, ly, lz = x - lo[0], y - lo[1], z - lo[2]
            nbt = Compound(nbt)
            nbt['Pos'] = List[Double]([Double(lx), Double(ly), Double(lz)])
            block = [math.floor(lx), math.floor(ly), math.floor(lz)]
            if 'TileX' in nbt:
                # A hanging entity's block is the one it hangs on (for a 2x2 painting, not the one at its centre), as
                # vanilla saves it: the game places the entity by it.
                block = [int(nbt['TileX']) - lo[0], int(nbt['TileY']) - lo[1], int(nbt['TileZ']) - lo[2]]
                nbt['TileX'], nbt['TileY'], nbt['TileZ'] = (Int(v) for v in block)
            ents.append(Compound({'pos': List[Double]([Double(lx), Double(ly), Double(lz)]),
                                  'blockPos': List[Int]([Int(v) for v in block]),
                                  'nbt': nbt}))
        root = Compound({'size': List[Int]([Int(s) for s in size]), 'palette': List[Compound](pal),
                         'blocks': List[Compound](blocks), 'entities': List[Compound](ents), 'DataVersion': Int(DATA_VERSION)})
        path.parent.mkdir(parents=True, exist_ok=True)
        # A fixed gzip timestamp keeps the file identical when nothing changed.
        with gzip.GzipFile(path, 'wb', mtime=0) as out:
            File(root).write(out, byteorder='big')
        return size


def json_str(text):
    import json
    return json.dumps(text, ensure_ascii=False)


def stack(item, count=1):
    return Compound({'id': String(mc(item)), 'Count': Byte(count)})


def offer(buy, sell, max_uses=12, xp=5, buy_b=None):
    """A trade: buy and sell are (item, count); buy_b is an optional second price."""
    out = Compound({'buy': stack(*buy), 'sell': stack(*sell), 'maxUses': Int(max_uses), 'uses': Int(0), 'xp': Int(xp),
                    'priceMultiplier': Float(0.05), 'rewardExp': Byte(1), 'demand': Int(0), 'specialPrice': Int(0)})
    if buy_b:
        out['buyB'] = stack(*buy_b)
    return out


# Shorthand for block states ------------------------------------------------------------------------------------------

def stairs(material, facing, half='bottom', shape='straight'):
    return f'minecraft:{material}_stairs[facing={facing},half={half},shape={shape}]'


def slab(material, kind='bottom'):
    return f'minecraft:{material}_slab[type={kind}]'


def log(material, axis='y'):
    return f'minecraft:{material}[axis={axis}]'


def fence(material):
    return f'minecraft:{material}_fence'


def trapdoor(material, facing, half='bottom', open_=False):
    return f'minecraft:{material}_trapdoor[facing={facing},half={half},open={str(open_).lower()}]'


def door(t: Template, x, y, z, material, facing, hinge='left'):
    t.set(x, y, z, f'minecraft:{material}_door[facing={facing},half=lower,hinge={hinge},open=false]')
    t.set(x, y + 1, z, f'minecraft:{material}_door[facing={facing},half=upper,hinge={hinge},open=false]')


def lantern(hanging=False):
    return f'minecraft:lantern[hanging={str(hanging).lower()}]'


OPPOSITE = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}
