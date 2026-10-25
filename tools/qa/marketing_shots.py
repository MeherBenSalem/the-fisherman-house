#!/usr/bin/env python3
"""Captures the listing screenshots (marketing/images/screenshots/) from a running 26.3 Fabric dev server and client
(see marketing/README.md for the server setup). Every picture is a real, unedited frame of the game: the structures
are where the world generated them, and everything the mod does in them (pots, bait, trades, the bottle) is the mod
running.

  python3 tools/qa/marketing_shots.py [scene ...]          # all scenes, or a few: lighthouse pier
  python3 tools/qa/marketing_shots.py --explore lighthouse # four views of a structure, to choose the camera
"""
from __future__ import annotations

import argparse
import math
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from client import PLAYER, Session  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'marketing' / 'images' / 'screenshots'
NS = 'fisherman_house'

# Camera per structure: yaw around the structure's middle (0 = from the south), distance as a multiple of its size,
# height above its top, the time of day, and an optional nudge of the point looked at.
VIEWS = {
    'fisherman_house': dict(yaw=90, dist=0.75, up=4, time=1000),
    'harbour_pier': dict(yaw=90, dist=0.85, up=5, time=1500),
    'lighthouse': dict(yaw=270, dist=1.25, up=-6, time=12800),
    'stilt_shack': dict(yaw=90, dist=1.1, up=2, time=6000),
    'ice_fishing_camp': dict(yaw=270, dist=1.3, up=3, time=5000),
    'river_boathouse': dict(yaw=90, dist=1.2, up=3, time=2000),
    'sunken_trawler': dict(yaw=180, dist=0.9, up=2, time=6000),
}


def to_jpg(png: Path, name: str):
    OUT.mkdir(parents=True, exist_ok=True)
    jpg = OUT / f'{name}.jpg'
    subprocess.run(['convert', str(png), '-quality', '92', str(jpg)], check=True)
    png.unlink()
    print('saved', jpg.relative_to(ROOT), flush=True)
    return jpg


def box_of(s: Session, sid):
    out = s.cmd(f'locate structure {NS}:{sid}')
    m = re.search(r'\[(-?\d+), ~, (-?\d+)\]', out)
    if not m:
        raise SystemExit(f'{sid}: not located: {out}')
    x, z = int(m.group(1)) // 16 * 16 + 8, int(m.group(2)) // 16 * 16 + 8
    s.cmd(f'forceload add {x - 64} {z - 64} {x + 64} {z + 64}')
    s.cmd(f'tp {PLAYER} {x} 150 {z}')
    for _ in range(40):
        time.sleep(3)
        r = s.cmd(f'fishermanscoast inspect {x} 64 {z}')
        m = re.search(rf'id={sid} box=(-?\d+),(-?\d+),(-?\d+),(-?\d+),(-?\d+),(-?\d+)', r)
        if m:
            return [int(v) for v in m.groups()]
    raise SystemExit(f'{sid}: not inspected')


def view(s: Session, box, yaw, dist, up, look_up=0.0, wait=10):
    x1, y1, z1, x2, y2, z2 = box
    cx, cy, cz = (x1 + x2) / 2 + 0.5, (y1 + y2) / 2, (z1 + z2) / 2 + 0.5
    span = max(x2 - x1, z2 - z1)
    d = span * dist + 6
    px = cx - d * math.sin(math.radians(yaw))
    pz = cz + d * math.cos(math.radians(yaw))
    s.tp(round(px, 2), round(y2 + up, 2), round(pz, 2), facing=(cx, cy + look_up, cz))
    time.sleep(wait)


def structure(s: Session, sid, explore=False):
    box = box_of(s, sid)
    v = VIEWS[sid]
    s.cmd(f'time set {v["time"]}', 'weather clear', f'gamemode spectator {PLAYER}')
    if sid == 'sunken_trawler':
        # Under water the view is fogged until the eyes adapt; night vision and a long wait give a clear picture.
        s.cmd(f'effect give {PLAYER} minecraft:night_vision 600 0 true', f'effect give {PLAYER} minecraft:conduit_power 600 0 true')
    s.hud(False)
    if explore:
        for yaw in (0, 90, 180, 270):
            view(s, box, yaw, v['dist'], v['up'], wait=8)
            s.shot(OUT.parent / 'explore' / f'{sid}_{yaw}.png')
    else:
        view(s, box, v['yaw'], v['dist'], v['up'], wait=40 if sid == 'sunken_trawler' else 12)
        to_jpg(s.shot(OUT / f'{sid}.png'), sid.replace('fisherman_house', 'cottage'))
    s.hud(True)
    s.cmd(f'effect clear {PLAYER}', 'forceload remove all')


def sea_spots(s: Session, box, sea=63):
    """Water at least three deep just outside a structure's box, nearest first."""
    x1, _, z1, x2, _, z2 = box
    spots = []
    for d in range(5, 13, 2):
        for x in range(x1 - d, x2 + d + 1, 2):
            for z in range(z1 - d, z2 + d + 1, 2):
                if x1 - d < x < x2 + d and z1 - d < z < z2 + d:
                    continue
                if all('passed' in s.cmd(f'execute if block {x} {y} {z} minecraft:water').lower() for y in (sea - 1, sea - 3)):
                    spots.append((x, z))
        if len(spots) >= 3:
            break
    return spots


def pots(s: Session):
    """Three pots in the sea beside the Harbour Pier: one baited, one that has caught something, one just set."""
    box = box_of(s, 'harbour_pier')
    s.cmd('time set 5000', 'weather clear', f'gamemode spectator {PLAYER}')
    x1, _, z1, x2, _, z2 = box
    s.cmd(f'fill {x1 - 14} 55 {z1 - 14} {x2 + 14} 63 {z2 + 14} minecraft:water replace {NS}:crab_pot')
    spots = sea_spots(s, box)
    if not spots:
        raise SystemExit('no sea beside the pier')
    x, z = spots[0]
    near = sorted(spots, key=lambda p: abs(p[0] - x) + abs(p[1] - z))[:3]

    def stack(item, count, slot):
        return f'{{Slot:{slot}b,id:"{item}",count:{count}}}'
    contents = [f'{{Items:[{stack(NS + ":fish_bait", 12, 0)}]}}',
                f'{{Items:[{stack("minecraft:salmon", 2, 0)},{stack("minecraft:cod", 3, 1)},{stack(NS + ":chum", 6, 2)}]}}', '']
    for (px, pz), items in zip(near, contents):
        s.cmd(f'setblock {px} 61 {pz} {NS}:crab_pot[waterlogged=true,facing=south]{items}')
    cx = sum(p[0] for p in near) / len(near) + 0.5
    cz = sum(p[1] for p in near) / len(near) + 0.5
    # Under water, with clear eyes: night vision and conduit power, and time for the eyes to adapt.
    s.cmd(f'effect give {PLAYER} minecraft:night_vision 600 0 true', f'effect give {PLAYER} minecraft:conduit_power 600 0 true')
    s.tp(round(cx + 2.6, 2), 60.2, round(cz + 2.6, 2), facing=(cx, 61.3, cz))
    time.sleep(35)
    s.hud(False)
    to_jpg(s.shot(OUT / 'pots.png'), 'pots')
    s.hud(True)
    s.cmd(f'effect clear {PLAYER}', 'forceload remove all')
    # The pot screen, opened with a real right-click: the player looks straight down at a pot in a glass tank.
    x, y, z = 0, 200, 0
    s.cmd(f'forceload add {x - 8} {z - 8} {x + 8} {z + 8}')
    s.cmd(f'fill {x - 3} {y - 2} {z - 3} {x + 3} {y + 2} {z + 3} minecraft:glass')
    s.cmd(f'fill {x - 2} {y - 1} {z - 2} {x + 2} {y + 1} {z + 2} minecraft:water')
    s.cmd(f'setblock {x} {y} {z} {NS}:crab_pot[waterlogged=true,facing=south]{contents[1]}')
    s.cmd(f'setblock {x} {y + 1} {z} minecraft:air', f'setblock {x} {y + 2} {z} minecraft:air', f'gamemode survival {PLAYER}')
    s.tp(x + 0.5, y + 3, z + 0.5, yaw=0, pitch=90)
    time.sleep(4)
    s.hold(3, 0.15)
    time.sleep(2)
    to_jpg(s.shot(OUT / 'pot_screen.png'), 'pot_screen')
    s.key('Escape')
    s.cmd(f'gamemode spectator {PLAYER}')
    s.cmd(f'fill {x - 3} {y - 2} {z - 3} {x + 3} {y + 3} {z + 3} minecraft:air', 'forceload remove all')


def trades(s: Session):
    """The Harbourmaster's trades, opened with a real right-click on him."""
    box = box_of(s, 'harbour_pier')
    s.cmd('time set 6000', f'gamemode survival {PLAYER}', f'effect give {PLAYER} minecraft:resistance 600 4 true')
    x1, y1, z1, x2, y2, z2 = box
    villager = f'@e[type=minecraft:villager,x={x1},y={y1},z={z1},dx={x2 - x1},dy={y2 - y1},dz={z2 - z1},limit=1]'
    pos = s.cmd(f'data get entity {villager} Pos')
    m = re.findall(r'(-?[\d.]+)d', pos)
    if len(m) < 3:
        raise SystemExit(f'no resident: {pos}')
    vx, vy, vz = (float(v) for v in m[:3])
    s.cmd(f'data merge entity {villager} {{NoAI:1b}}')
    # Stand two blocks away, inside, facing him.
    for dx, dz in ((1.6, 0), (-1.6, 0), (0, 1.6), (0, -1.6)):
        if 'passed' in s.cmd(f'execute if block {math.floor(vx + dx)} {math.floor(vy)} {math.floor(vz + dz)} minecraft:air').lower():
            yaw = math.degrees(math.atan2(dx, -dz))
            s.tp(round(vx + dx, 2), vy, round(vz + dz, 2), yaw=yaw, pitch=10)
            break
    time.sleep(4)
    s.hold(3, 0.15)
    time.sleep(2.5)
    to_jpg(s.shot(OUT / 'trades.png'), 'trades')
    s.key('Escape')
    s.cmd(f'data merge entity {villager} {{NoAI:0b}}', 'forceload remove all')


def bottle(s: Session):
    """Opening Messages in a Bottle on the pier until one holds a map, then holding the map; the note is in chat."""
    box = box_of(s, 'harbour_pier')
    x1, y1, z1, x2, y2, z2 = box
    s.cmd('time set 6000', f'gamemode survival {PLAYER}', f'effect give {PLAYER} minecraft:resistance 600 4 true')
    s.tp((x1 + x2) / 2 + 0.5, y1 + 13, (z1 + z2) / 2 + 0.5, yaw=200, pitch=20)
    time.sleep(3)
    for _ in range(25):
        s.cmd(f'clear {PLAYER}', f'item replace entity {PLAYER} hotbar.0 with {NS}:message_in_a_bottle')
        s.key('1')
        time.sleep(0.8)
        s.hold(3, 0.15)
        time.sleep(1)
        if re.search(r'[1-9]', s.cmd(f'clear {PLAYER} minecraft:filled_map 0')):
            break
    # The bottle is used up and the map lands in the next hotbar slot: hold it while the note is still in chat.
    s.key('2')
    s.cmd(f'execute at {PLAYER} run kill @e[type=minecraft:item,distance=..16]')
    time.sleep(0.8)
    to_jpg(s.shot(OUT / 'bottle.png'), 'bottle')


SCENES = {sid: (lambda s, sid=sid: structure(s, sid)) for sid in VIEWS}
SCENES.update({'pots': pots, 'trades': trades, 'bottle': bottle})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--explore', action='store_true')
    ap.add_argument('scenes', nargs='*')
    args = ap.parse_args()
    s = Session()
    s.cmd(f'op {PLAYER}', 'gamerule doDaylightCycle false', 'gamerule advance_time false', 'weather clear')
    for name in args.scenes or list(SCENES):
        if args.explore:
            structure(s, name, explore=True)
        else:
            SCENES[name](s)


if __name__ == '__main__':
    main()
