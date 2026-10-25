#!/usr/bin/env python3
"""In-game checks for Fisherman's Coast against a running dev server (see devrun.sh), optionally with the QA client.
The world is a normal one (seed in devrun.sh); test rigs are built with commands high above the terrain.

Server checks:
  * config: the short QA config was completed with the defaults and comments;
  * structures: every structure is found by /locate (and by the #fisherman_house:coastal tag), its chunks generate,
    and /fishermanscoast inspect finds its containers with the structure's loot tables, its named resident with the
    exclusive trades, its Crab Pots and Fishing Nets; its loot rolls; the template also places on its own;
  * crab_pot: in open water a pot catches; bait is used per catch; a pot in a puddle and a full pot catch nothing;
    hoppers take the catch but not the bait and can only put bait in; a comparator reads it; breaking it drops the pot
    and its contents; pots pick the catch table of their biome;
  * loot: every loot table rolls, a bottle can hold a map to a Sunken Trawler, and rods fish up bottles;
  * log: no errors.
Client checks (--client): the player baits a pot by hand, opens it, opens a Message in a Bottle, and walks into every
structure (discovery advancements); screenshots are taken along the way.

  python3 tools/qa/coast_checks.py --log /tmp/fc-qa/fabric-server.log --ws 26.3 --loader fabric [--client --shots DIR]
"""
from __future__ import annotations

import argparse
import math
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rcon import wait_for  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
NS = 'fisherman_house'
PLAYER = 'Builder'
FAILURES: list[str] = []
COUNT = [0]
# id: (tables in its containers, resident name or None, whether the resident sells pots, least pots, least nets)
STRUCTURES = {
    'fisherman_house': ({'chests/fisherman_house', 'chests/fisherman_house_storage'}, 'Saylor', True, 1, 0),
    'harbour_pier': ({'chests/harbour_pier', 'chests/harbour_pier_storage'}, 'Harbourmaster Wren', True, 4, 10),
    'lighthouse': ({'chests/lighthouse'}, 'Keeper Morrow', True, 0, 0),
    'stilt_shack': ({'chests/stilt_shack'}, 'Old Bayou Tam', True, 1, 3),
    'ice_fishing_camp': ({'chests/ice_fishing_camp'}, 'Frost-Beard Ole', True, 2, 0),
    'river_boathouse': ({'chests/river_boathouse'}, 'Ferryman Hale', True, 1, 4),
    'sunken_trawler': ({'chests/sunken_trawler', 'chests/sunken_trawler_captain'}, None, False, 2, 4),
}
# Structures whose template has another name (the house's 1.x template keeps the house's id).
TEMPLATES = {'fisherman_house': 'cottage'}
VANILLA_PLACE = ('QA: vanilla /place template from here', 'QA: vanilla /place template done')
TABLES = ['chests/' + t for t in ('fisherman_house', 'fisherman_house_storage', 'harbour_pier', 'harbour_pier_storage',
                                  'lighthouse', 'stilt_shack', 'ice_fishing_camp', 'river_boathouse', 'sunken_trawler',
                                  'sunken_trawler_captain')]
TABLES += ['gameplay/crab_pot/' + t for t in ('default', 'ocean', 'river', 'swamp', 'frozen', 'junk', 'treasure')]
RIG_Y = 250


def check(name, ok, detail=''):
    COUNT[0] += 1
    print(('PASS ' if ok else 'FAIL ') + name + (f'  [{str(detail)[:500]}]' if detail and not ok else ''), flush=True)
    if not ok:
        FAILURES.append(name)
    return ok


class Server:
    def __init__(self, port, legacy):
        self.rcon = wait_for(port)
        self.legacy = legacy  # 1.20.1 item NBT

    def cmd(self, command):
        return self.rcon.command(command)

    def gamerule(self, camel, snake, value):
        out = self.cmd(f'gamerule {camel} {value}')
        if 'Unknown' in out or 'Incorrect' in out or 'expected' in out.lower():
            out = self.cmd(f'gamerule {snake} {value}')
        return out

    def test(self, x, y, z, block):
        return 'passed' in self.cmd(f'execute if block {x} {y} {z} {block}').lower()

    def items(self, x, y, z):
        return count_items(self.cmd(f'data get block {x} {y} {z} Items'))

    def entities(self, selector):
        self.cmd('scoreboard objectives add fcqa dummy')
        self.cmd(f'execute store result score #n fcqa if entity {selector}')
        m = re.search(r'has (\d+)', self.cmd('scoreboard players get #n fcqa'))
        return int(m.group(1)) if m else 0

    def stack(self, item, count, slot):
        if self.legacy:
            return f'{{Slot:{slot}b,id:"{item}",Count:{count}b}}'
        return f'{{Slot:{slot}b,id:"{item}",count:{count}}}'

    def pot(self, x, y, z, water=True, items=()):
        state = f'{NS}:crab_pot[waterlogged={str(water).lower()}]'
        nbt = '{Items:[' + ','.join(self.stack(i, c, s) for s, (i, c) in enumerate(items)) + ']}' if items else ''
        self.cmd(f'setblock {x} {y} {z} {state}{nbt}')

    def inspect(self, x, z, fill=False, tries=25, want=None):
        """The inspect line of structure `want` at (x, z), once its chunks and its resident have loaded."""
        out = ''
        needs_resident = want is not None and STRUCTURES[want][1] is not None
        for i in range(tries):
            out = self.cmd(f'fishermanscoast inspect {x} 64 {z}')
            line = pick(out, want)
            if line and (not needs_resident or 'residents=-' not in line or i >= tries // 2):
                if fill:
                    line = pick(self.cmd(f'fishermanscoast inspect {x} 64 {z} fill'), want) or line
                return parse(line)
            time.sleep(3)
        return {'raw': out}


def pick(out, want):
    for line in re.findall(r'FC inspect id=\S+ .*?(?=FC inspect|$)', out, re.S):
        if want is None or line.startswith(f'FC inspect id={want} '):
            return line
    return None


def counts(text):
    if text in ('-', None):
        return {}
    out = {}
    for part in re.findall(r'[^,*]+(?:\[[^\]]*\])?\*\d+', text):
        key, n = part.rsplit('*', 1)
        out[key.lstrip(',')] = int(n)
    return out


def parse(line):
    m = re.search(r'FC inspect id=(\S+) box=(\S+) containers=(\S+) residents=(\S+) pots=(\d+) pot_tables=(\S+) nets=(\d+)'
                  r'(?: stacks=(\d+) maps=(\d+))?', line or '')
    if not m:
        return {'raw': line}
    return {'id': m.group(1), 'box': [int(v) for v in m.group(2).split(',')], 'containers': counts(m.group(3)),
            'residents': counts(m.group(4)), 'pots': int(m.group(5)), 'pot_tables': counts(m.group(6)),
            'nets': int(m.group(7)), 'stacks': int(m.group(8) or 0), 'maps': int(m.group(9) or 0), 'raw': line}


def count_items(text):
    totals: dict[str, int] = {}
    for obj in re.findall(r'\{[^{}]*id: "[^"]+"[^{}]*\}', text):
        item = re.search(r'id: "([^"]+)"', obj).group(1)
        m = re.search(r'\b[cC]ount: (\d+)', obj)
        totals[item] = totals.get(item, 0) + (int(m.group(1)) if m else 1)
    return totals


# Config ----------------------------------------------------------------------------------------------------------------

def check_config():
    cfg = ROOT / ARGS.ws / ARGS.loader / 'runs' / 'server' / 'config' / f'{NS}.json'
    if not ARGS.ws:
        cfg = Path(ARGS.config) if ARGS.config else None
    if cfg is None:
        return
    text = cfg.read_text() if cfg.exists() else ''
    check('config: completed with comments', text.startswith("// Fisherman's Coast."), cfg)
    check('config: QA values kept, defaults added', '"min_seconds": 5' in text and '"rain_bonus": true' in text
          and '"sunken_trawler": true' in text, text[:300])


# Structures --------------------------------------------------------------------------------------------------------------

def locate(s, sid):
    out = s.cmd(f'locate structure {NS}:{sid}')
    m = re.search(r'\[(-?\d+), ~, (-?\d+)\]', out)
    return (int(m.group(1)), int(m.group(2))) if m else None


def check_structure(s, sid, info, label):
    tables, resident, sells_pots, pots, nets = STRUCTURES[sid]
    if not check(f'{label} {sid}: inspect finds it', info.get('id') in (sid, 'area'), info.get('raw')):
        return
    found = {k.split(':', 1)[1] for k in info['containers'] if k.startswith(NS + ':')}
    check(f'{label} {sid}: containers use its loot tables', tables <= found, info['containers'])
    if resident:
        key = resident.replace(' ', '_')
        here = {k: v for k, v in info['residents'].items() if k.startswith(key + '[')}
        check(f'{label} {sid}: {resident} lives there', len(here) >= 1, info['residents'])
        offers = [int(re.search(r'\[(\d+)', k).group(1)) for k in here]
        check(f'{label} {sid}: {resident} has the exclusive trades', any(o >= 5 for o in offers)
              and (not sells_pots or any(',pots' in k for k in here)), here)
    check(f'{label} {sid}: crab pots', info['pots'] >= pots, info['pots'])
    check(f'{label} {sid}: fishing nets', info['nets'] >= nets, info['nets'])


def check_structures(s):
    located = {}
    for sid in STRUCTURES:
        pos = locate(s, sid)
        if not check(f'locate {sid}', pos is not None):
            continue
        x, z = pos[0] // 16 * 16 + 8, pos[1] // 16 * 16 + 8
        s.cmd(f'forceload add {x - 48} {z - 48} {x + 48} {z + 48}')
        info = s.inspect(x, z, fill=True, want=sid)
        check_structure(s, sid, info, 'natural')
        if info.get('id') == sid:
            located[sid] = info
            check(f'natural {sid}: loot rolled into the containers', info['stacks'] >= 2, info.get('raw'))
        s.cmd('forceload remove all')
    tag = s.cmd(f'locate structure #{NS}:coastal')
    check('locate #fisherman_house:coastal', f'{NS}:' in tag, tag)
    # The templates also place on their own (entities, containers, pots), in the sky over spawn. The house's template
    # is the repaired `cottage`; its id `fisherman_house` keeps the 1.x template for houses 1.x left half-generated.
    # /place template is vanilla's own placement, which on 1.20.1 and 1.21.1 logs "invalid position" for every painting
    # and item frame (the mod's structure piece places them itself); the log check allows that between these markers.
    s.cmd(f'say {VANILLA_PLACE[0]}')
    for i, sid in enumerate(STRUCTURES):
        x, z = -400 + i * 60, -300
        s.cmd(f'forceload add {x - 8} {z - 8} {x + 48} {z + 48}')
        out = s.cmd(f'place template {NS}:{TEMPLATES.get(sid, sid)} {x} 200 {z}')
        if not check(f'place template {sid}', 'loaded template' in out.lower() or 'placed' in out.lower(), out):
            continue
        time.sleep(2)
        info = parse(pick(s.cmd(f'fishermanscoast inspect area {x - 2} 195 {z - 2} {x + 46} 245 {z + 46}'), 'area'))
        check_structure(s, sid, info, 'template')
        s.cmd(f'fill {x - 2} 195 {z - 2} {x + 46} 245 {z + 46} minecraft:air')
        s.cmd(f'kill @e[type=!minecraft:player,x={x - 2},y=195,z={z - 2},dx=48,dy=50,dz=48]')
        s.cmd('forceload remove all')
    x, z = -400, -240
    s.cmd(f'forceload add {x - 8} {z - 8} {x + 48} {z + 48}')
    out = s.cmd(f'place template {NS}:fisherman_house {x} 200 {z}')
    check('place template fisherman_house (kept from 1.x)', 'loaded template' in out.lower() or 'placed' in out.lower(), out)
    time.sleep(2)
    s.cmd(f'fill {x - 2} 195 {z - 2} {x + 46} 245 {z + 46} minecraft:air')
    s.cmd(f'kill @e[type=!minecraft:player,x={x - 2},y=195,z={z - 2},dx=48,dy=50,dz=48]')
    s.cmd('forceload remove all')
    s.cmd(f'say {VANILLA_PLACE[1]}')
    return located


# Crab pots ---------------------------------------------------------------------------------------------------------------

def tank(s, x, z, y=RIG_Y, water=True):
    """A glass tank 7x5x7 (inside 5x3x5) filled with water, its middle at (x, y, z)."""
    s.cmd(f'fill {x - 3} {y - 2} {z - 3} {x + 3} {y + 2} {z + 3} minecraft:glass')
    s.cmd(f'fill {x - 2} {y - 1} {z - 2} {x + 2} {y + 1} {z + 2} ' + ('minecraft:water' if water else 'minecraft:air'))


def check_crab_pots(s):
    base = 0
    s.cmd(f'forceload add {base - 32} {-32} {base + 96} {32}')
    time.sleep(2)
    # A: open water, no bait. B: open water with bait. C: a puddle. D: a full pot.
    tank(s, base, 0)
    s.pot(base, RIG_Y, 0)
    tank(s, base + 10, 0)
    s.pot(base + 10, RIG_Y, 0, items=[(f'{NS}:fish_bait', 10)])
    s.cmd(f'fill {base + 17} {RIG_Y - 1} -1 {base + 19} {RIG_Y + 1} 1 minecraft:stone')
    s.cmd(f'setblock {base + 18} {RIG_Y + 1} 0 minecraft:air')
    s.pot(base + 18, RIG_Y, 0)
    tank(s, base + 26, 0)
    s.pot(base + 26, RIG_Y, 0, items=[('minecraft:stone', 64)] * 5)
    time.sleep(14)
    a = s.items(base, RIG_Y, 0)
    check('crab_pot: catches in open water', sum(a.values()) >= 1, a)
    b = s.items(base + 10, RIG_Y, 0)
    caught = sum(v for k, v in b.items() if k != f'{NS}:fish_bait')
    check('crab_pot: bait is used, one per catch', caught >= 1 and b.get(f'{NS}:fish_bait', 0) <= 9, b)
    check('crab_pot: baited pot shows its bait', s.test(base + 10, RIG_Y, 0, f'{NS}:crab_pot[baited=true]'))
    check('crab_pot: a pot with a catch shows it', s.test(base, RIG_Y, 0, f'{NS}:crab_pot[caught=true]'))
    c = s.items(base + 18, RIG_Y, 0)
    check('crab_pot: a puddle catches nothing', not c, c)
    d = s.items(base + 26, RIG_Y, 0)
    check('crab_pot: a full pot loses nothing and adds nothing', d == {'minecraft:stone': 320}, d)
    # E: hoppers. The pot holds bait and a cod; a hopper under it takes the cod only. A hopper above it holds dirt
    # and bait; only the bait goes in.
    x = base + 40
    s.cmd(f'fill {x - 1} {RIG_Y - 2} -1 {x + 1} {RIG_Y + 2} 1 minecraft:stone')
    s.pot(x, RIG_Y, 0, water=False, items=[(f'{NS}:chum', 3), ('minecraft:cod', 1)])
    s.cmd(f'setblock {x} {RIG_Y - 1} 0 minecraft:hopper[facing=down]')
    time.sleep(3)
    below = s.items(x, RIG_Y - 1, 0)
    check('crab_pot: a hopper below takes the catch', below.get('minecraft:cod', 0) == 1, below)
    check('crab_pot: a hopper below leaves the bait', below.get(f'{NS}:chum', 0) == 0
          and s.items(x, RIG_Y, 0).get(f'{NS}:chum', 0) == 3, (below, s.items(x, RIG_Y, 0)))
    s.cmd(f'setblock {x} {RIG_Y - 1} 0 minecraft:stone')
    hopper = '{Items:[' + s.stack('minecraft:dirt', 4, 0) + ',' + s.stack(f'{NS}:glow_bait', 2, 1) + ']}'
    s.cmd(f'setblock {x} {RIG_Y + 1} 0 minecraft:hopper[facing=down]{hopper}')
    time.sleep(3)
    inside = s.items(x, RIG_Y, 0)
    above = s.items(x, RIG_Y + 1, 0)
    check('crab_pot: a hopper above can put bait in', inside.get(f'{NS}:glow_bait', 0) == 2, inside)
    check('crab_pot: a hopper above cannot put anything else in', 'minecraft:dirt' not in inside
          and above.get('minecraft:dirt', 0) == 4, (inside, above))
    # F: a comparator reads the pot.
    s.cmd(f'setblock {x + 2} {RIG_Y} 0 minecraft:comparator[facing=west]')
    s.cmd(f'setblock {x + 1} {RIG_Y} 0 minecraft:air')
    s.cmd(f'setblock {x + 1} {RIG_Y} 0 minecraft:comparator[facing=west]')
    s.cmd(f'setblock {x + 2} {RIG_Y} 0 minecraft:redstone_lamp')
    time.sleep(1)
    check('crab_pot: a comparator reads it', s.test(x + 2, RIG_Y, 0, 'minecraft:redstone_lamp[lit=true]'))
    # G: breaking it drops the pot and what is inside.
    s.cmd(f'kill @e[type=minecraft:item,x={x - 3},y={RIG_Y - 3},z=-3,dx=6,dy=6,dz=6]')
    s.cmd(f'setblock {x} {RIG_Y} 0 minecraft:air destroy')
    time.sleep(1)
    area = f'x={x - 3},y={RIG_Y - 3},z=-3,dx=6,dy=6,dz=6'
    pot = s.entities(f'@e[type=minecraft:item,{area},nbt={{Item:{{id:"{NS}:crab_pot"}}}}]')
    bait = s.entities(f'@e[type=minecraft:item,{area},nbt={{Item:{{id:"{NS}:chum"}}}}]')
    check('crab_pot: breaking it drops the pot and its contents', pot == 1 and bait == 1, (pot, bait))
    s.cmd(f'fill {base - 4} {RIG_Y - 3} -4 {base + 44} {RIG_Y + 3} 4 minecraft:air')
    s.cmd('kill @e[type=minecraft:item]')
    s.cmd('forceload remove all')


def check_pot_tables(s, located):
    """Pots pick the catch table of their biome (frozen, swamp, river, ocean or default)."""
    expected = {'sunken_trawler': 'ocean', 'ice_fishing_camp': 'frozen', 'stilt_shack': 'swamp'}
    for sid, place in expected.items():
        info = located.get(sid)
        if not info:
            check(f'crab_pot: {place} catch table', False, f'{sid} not inspected')
            continue
        check(f'crab_pot: pots at the {sid} use the {place} table', info['pot_tables'].get(place, 0) >= 1, info['pot_tables'])


# Loot -----------------------------------------------------------------------------------------------------------------

def check_loot(s):
    for table in TABLES:
        out = s.cmd(f'loot spawn 0 {RIG_Y} 0 loot {NS}:{table}')
        check(f'loot: {table} rolls', 'Dropped' in out and not out.startswith('Dropped 0'), out)
    s.cmd('kill @e[type=minecraft:item]')
    # Bottles hold a map to the nearest Sunken Trawler (near spawn in the QA world) or a small treasure.
    s.cmd(f'forceload add -16 -16 16 16')
    maps = 0
    for _ in range(40):
        s.cmd(f'loot spawn 0 {RIG_Y} 0 loot {NS}:gameplay/message_in_a_bottle')
        maps = s.entities('@e[type=minecraft:item,nbt={Item:{id:"minecraft:filled_map"}}]')
        if maps:
            break
    check('loot: a Message in a Bottle can hold a map to a Sunken Trawler', maps >= 1, maps)
    s.cmd('kill @e[type=minecraft:item]')
    # Rods: 1.5 % of catches bring a bottle along (400 catches: at least one in all but 0.2 % of runs).
    for _ in range(400):
        s.cmd(f'loot spawn 0 {RIG_Y} 0 fish minecraft:gameplay/fishing 0 {RIG_Y} 0 minecraft:fishing_rod')
    bottles = s.entities(f'@e[type=minecraft:item,nbt={{Item:{{id:"{NS}:message_in_a_bottle"}}}}]')
    total = s.entities('@e[type=minecraft:item]')
    check('loot: rods fish up Messages in a Bottle', 1 <= bottles <= 20, (bottles, total))
    s.cmd('kill @e[type=minecraft:item]')
    s.cmd('forceload remove all')


# Client -------------------------------------------------------------------------------------------------------------------

def check_client(s, located, shots):
    from client import Session
    cs = Session()
    cs.cmd(f'gamemode survival {PLAYER}', 'time set 1000', 'weather clear', f'advancement revoke {PLAYER} everything',
           f'clear {PLAYER}', f'effect give {PLAYER} minecraft:resistance 99999 4 true')
    shots = Path(shots) if shots else None
    # A pot in a tank at eye level: bait it by hand, then open it.
    x = 300
    s.cmd(f'forceload add {x - 16} -16 {x + 16} 16')
    tank(s, x, 0, y=RIG_Y)
    s.pot(x, RIG_Y, 0)
    s.cmd(f'fill {x - 3} {RIG_Y - 3} 4 {x + 3} {RIG_Y - 3} 7 minecraft:glass')
    s.cmd(f'fill {x - 1} {RIG_Y + 2} -1 {x + 1} {RIG_Y + 2} 1 minecraft:air')
    s.cmd(f'fill {x - 2} {RIG_Y + 2} -2 {x + 2} {RIG_Y + 2} 2 minecraft:glass')
    s.cmd(f'setblock {x} {RIG_Y + 2} 0 minecraft:air')
    s.cmd(f'setblock {x} {RIG_Y + 1} 0 minecraft:air')
    cs.cmd(f'item replace entity {PLAYER} weapon.mainhand with {NS}:fish_bait 8')
    cs.tp(x + 0.5, RIG_Y + 3, 0.5, yaw=0, pitch=90)
    time.sleep(3)
    cs.hold(3, 0.15)
    time.sleep(1.5)
    inside = s.items(x, RIG_Y, 0)
    check('client: right-click with bait puts it in the pot', inside.get(f'{NS}:fish_bait', 0) >= 1, inside)
    check('client: the pot shows its bait', s.test(x, RIG_Y, 0, f'{NS}:crab_pot[baited=true]'))
    cs.cmd(f'item replace entity {PLAYER} weapon.mainhand with minecraft:air')
    time.sleep(1)
    cs.hold(3, 0.15)
    time.sleep(1.5)
    if shots:
        cs.shot(shots / 'crab_pot_screen.png')
    cs.key('Escape')
    time.sleep(0.5)
    # A Message in a Bottle: right-click in the air.
    cs.cmd(f'item replace entity {PLAYER} weapon.mainhand with {NS}:message_in_a_bottle 2')
    cs.tp(x + 0.5, RIG_Y + 6, 10.5, yaw=0, pitch=-30)
    s.cmd(f'fill {x - 1} {RIG_Y + 5} 9 {x + 1} {RIG_Y + 5} 11 minecraft:glass')
    time.sleep(2)
    cs.hold(3, 0.15)
    time.sleep(2)
    left = re.search(r'(\d+)', s.cmd(f'clear {PLAYER} {NS}:message_in_a_bottle 0') or '')
    check('client: using a bottle opens it', left is not None and left.group(1) == '1', s.cmd(f'clear {PLAYER} {NS}:message_in_a_bottle 0'))
    adv = s.cmd(f'execute if entity @a[name={PLAYER},advancements={{{NS}:open_bottle=true}}]')
    check('client: Message Received advancement', 'passed' in adv.lower(), adv)
    s.cmd(f'fill {x - 4} {RIG_Y - 4} -4 {x + 4} {RIG_Y + 6} 12 minecraft:air')
    s.cmd('forceload remove all')
    # Walk into every structure.
    cs.cmd(f'gamemode creative {PLAYER}')
    for sid, info in located.items():
        x1, y1, z1, x2, y2, z2 = info['box']
        cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
        s.cmd(f'forceload add {x1} {z1} {x2} {z2}')
        cs.cmd(f'tp {PLAYER} {cx + 0.5} {(y1 + y2) // 2} {cz + 0.5}')
        adv = ''
        for _ in range(20):
            time.sleep(2)
            adv = s.cmd(f'execute if entity @a[name={PLAYER},advancements={{{NS}:discover_{sid}=true}}]')
            if 'passed' in adv.lower():
                break
        check(f'client {sid}: discovery advancement', 'passed' in adv.lower(), adv)
        if shots:
            span = max(x2 - x1, z2 - z1, y2 - y1)
            d = span * 0.9 + 6
            px, pz, py = cx + d * 0.7, cz + d * 0.7, y2 + d * 0.25
            cs.cmd(f'gamemode spectator {PLAYER}')
            cs.tp(round(px, 1), round(py, 1), round(pz, 1), facing=((x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2))
            time.sleep(6)
            cs.hud(False)
            cs.shot(shots / f'{sid}.png')
            cs.hud(True)
            cs.cmd(f'gamemode creative {PLAYER}')
        s.cmd('forceload remove all')
    adv = s.cmd(f'execute if entity @a[name={PLAYER},advancements={{{NS}:all_structures=true}}]')
    check('client: Coastal Wanderer after all seven', 'passed' in adv.lower() or len(located) < len(STRUCTURES), adv)
    recipe = s.cmd(f'recipe give {PLAYER} {NS}:crab_pot')
    check('client: recipes load', 'nlocked' in recipe or 'nlocked' in recipe.lower() or 'already' in recipe.lower(), recipe)
    client_log = ROOT / ARGS.ws / ARGS.loader / 'runs' / 'client' / 'logs' / 'latest.log'
    text = client_log.read_text(errors='replace') if client_log.exists() else ''
    bad = [l for l in text.splitlines() if NS in l and ('ERROR' in l or 'Missing' in l or 'missing' in l)]
    check('client: models and textures load without errors', not bad, bad[:3])


def check_log(path):
    text = Path(path).read_text(errors='replace')
    lines = text.splitlines()
    errors = []
    in_place = False
    for l in lines:
        if VANILLA_PLACE[0] in l or VANILLA_PLACE[1] in l:
            in_place = VANILLA_PLACE[0] in l
        elif in_place and re.search(r'(Hanging|Block-attached) entity at invalid position', l):
            continue
        elif re.search(r'/(ERROR|FATAL)\]|Exception|Couldn\'t parse|Failed to (load|parse)', l) \
                and 'Narrator' not in l and 'realms' not in l.lower():
            errors.append(l)
    ours = [l for l in errors if NS in l or 'fishermanhouse' in l or 'loot' in l.lower() or 'structure' in l.lower()]
    check('log: no errors about the mod, its loot or structures', not ours, ours[:3])
    check('log: no errors at all', not errors, errors[:3])


def main():
    global ARGS
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=25575)
    ap.add_argument('--log', required=True)
    ap.add_argument('--client', action='store_true')
    ap.add_argument('--ws', default='')
    ap.add_argument('--loader', default='')
    ap.add_argument('--config', default='', help='config file to check when there is no --ws (production servers)')
    ap.add_argument('--minecraft', default='', help='Minecraft version for NBT syntax when there is no --ws')
    ap.add_argument('--shots')
    ARGS = ap.parse_args()
    s = Server(ARGS.port, legacy=(ARGS.minecraft or ARGS.ws) == '1.20.1')
    s.cmd('time set noon')
    s.cmd('weather clear')
    s.gamerule('doDaylightCycle', 'advance_time', 'false')
    s.gamerule('doWeatherCycle', 'advance_weather', 'false')
    check_config()
    located = check_structures(s)
    check_crab_pots(s)
    check_pot_tables(s, located)
    check_loot(s)
    if ARGS.client:
        check_client(s, located, ARGS.shots)
    check_log(ARGS.log)
    print(f'{COUNT[0]} checks, {len(FAILURES)} failures' + (': ' + ', '.join(FAILURES) if FAILURES else ''))
    sys.exit(1 if FAILURES else 0)


if __name__ == '__main__':
    main()
