#!/usr/bin/env python3
"""Captures the footage for the Instagram reel (marketing/reel/) from a running 26.3 Fabric dev server and a portrait
client: the client window is 1080x1920 on its own X display (see marketing/reel/README.md for the setup).

Every clip is captured frame by frame: the camera is moved along an eased path with /tp, the game renders, the display
is captured. Software rendering is far too slow to record in real time, so this is what makes the camera moves smooth.
The world is frozen with /tick freeze and stepped one tick per frame (30 ticks a second of footage, 1.5x real time).
Every structure is where the world generated it; nothing in the pictures is edited.

  python3 marketing/reel/capture.py                      # every clip
  python3 marketing/reel/capture.py pier lighthouse      # a few
  python3 marketing/reel/capture.py --preview pier       # first, middle and last frame only, to frame a shot
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'qa'))
from client import PLAYER, Session  # noqa: E402
from marketing_shots import box_of  # noqa: E402

NS = 'fisherman_house'
FPS = 30
OUT = ROOT / 'marketing' / 'reel' / 'build' / 'frames'
TIMELINE = json.loads((Path(__file__).resolve().parent / 'timeline.json').read_text())


def length(name):
    """How long a clip runs in the edit (timeline.json, timed to the narration by plan.py), plus two spare frames."""
    clip = next(c for c in TIMELINE['clips'] if c['name'] == name)
    return clip['end'] - clip['start'] + 2 / FPS


def same(a, b, threshold=0.05):
    """Whether two captures show the same picture (mean grey-level difference on a small copy)."""
    import numpy as np
    from PIL import Image
    x, y = (np.asarray(Image.open(p).convert('L').resize((135, 240)), dtype=float) for p in (a, b))
    return float(np.abs(x - y).mean()) < threshold


def ease(t):
    """Ease in and out (smootherstep)."""
    return t * t * t * (t * (t * 6 - 15) + 10)


def cruise(t):
    """Mostly constant speed, so the camera is still moving at the cuts (fast montages feel continuous)."""
    return 0.8 * t + 0.2 * ease(t)


def ease_in(t):
    return 0.5 * t + 0.5 * t * t


def ease_out(t):
    return 1 - (1 - t) ** 2


def lerp(a, b, t):
    return a + (b - a) * t


def orbit(centre, yaw0, yaw1, dist0, dist1, up0, up1, look_up=0.0, curve=ease):
    """A camera circling `centre` (yaw 0 = from the south, degrees), moving in or out and up or down."""
    cx, cy, cz = centre

    def at(t):
        u = curve(t)
        yaw, dist, up = math.radians(lerp(yaw0, yaw1, u)), lerp(dist0, dist1, u), lerp(up0, up1, u)
        return (cx - dist * math.sin(yaw), cy + up, cz + dist * math.cos(yaw)), (cx, cy + look_up, cz)
    return at


def dolly(p0, p1, look0, look1, curve=ease):
    """A camera moving in a straight line while its aim moves from one point to another."""
    def at(t):
        u = curve(t)
        return tuple(lerp(a, b, u) for a, b in zip(p0, p1)), tuple(lerp(a, b, u) for a, b in zip(look0, look1))
    return at


class Reel:
    def __init__(self, preview=False):
        self.s = Session(display=':2')
        self.preview = preview
        self.s.cmd(f'gamemode spectator {PLAYER}', 'weather clear', 'gamerule advance_time false',
                   'gamerule advance_weather false')

    def clip(self, name, seconds, path, settle=14, wait=0.55):
        frames = round(seconds * FPS)
        out = OUT / name
        shutil.rmtree(out, ignore_errors=True)
        out.mkdir(parents=True)
        indices = [0, frames // 2, frames - 1] if self.preview else range(frames)
        self.s.cmd('tick freeze')
        for n, i in enumerate(indices):
            pos, look = path(i / (frames - 1))
            self.s.tp(round(pos[0], 3), round(pos[1], 3), round(pos[2], 3), facing=look)
            if n == 0 or self.preview:
                time.sleep(settle if n == 0 else 4)
            else:
                self.s.cmd('tick step 1')
                time.sleep(wait)
            self.s.shot(out / f'{i:04d}.jpg')
            # A frame identical to the one before means the game had not drawn the new camera position yet (a visible
            # stutter): wait and take it again.
            for _ in range(6):
                if n == 0 or self.preview or not same(out / f'{i:04d}.jpg', out / f'{indices[n - 1]:04d}.jpg'):
                    break
                time.sleep(0.4)
                self.s.shot(out / f'{i:04d}.jpg')
        self.s.cmd('tick unfreeze')
        if self.preview:
            sheet = OUT.parent / f'preview-{name}.jpg'
            subprocess.run(['montage', *sorted(str(p) for p in out.glob('*.jpg')), '-tile', '3x1', '-geometry',
                            '360x640+4+4', str(sheet)], check=True)
            print('preview', sheet.relative_to(ROOT), flush=True)
        else:
            print('captured', name, frames, 'frames', flush=True)

    def place(self, sid, time_of_day=6000, underwater=False):
        box = box_of(self.s, sid)
        self.s.cmd(f'time set {time_of_day}', 'effect clear ' + PLAYER)
        if underwater:
            self.s.cmd(f'effect give {PLAYER} minecraft:night_vision 900 0 true',
                       f'effect give {PLAYER} minecraft:conduit_power 900 0 true')
        x1, y1, z1, x2, y2, z2 = box
        return box, ((x1 + x2) / 2 + 0.5, (y1 + y2) / 2, (z1 + z2) / 2 + 0.5), max(x2 - x1, z2 - z1)


# The clips ----------------------------------------------------------------------------------------------------------

def beach(r: Reel):
    """The hook: an empty vanilla beach, low and slow (nothing of the mod in it)."""
    r.s.cmd('forceload remove all', 'time set 3000', 'effect clear ' + PLAYER)
    x, z = BEACH
    r.s.cmd(f'forceload add {x - 64} {z - 64} {x + 64} {z + 64}')
    r.clip('beach', length('beach'), dolly((x - 2, 70, z + 8), (x + 1, 68.2, z - 3), (x - 6, 63, z - 40), (x - 2, 62.5, z - 44),
                                curve=ease_in))


def lighthouse(r: Reel):
    box, c, span = r.place('lighthouse', 12800)
    r.clip('lighthouse', length('lighthouse'), orbit(c, 250, 290, span * 1.7 + 6, span * 1.05 + 6, box[4] - c[1] + 6, box[4] - c[1] - 4,
                                    look_up=2, curve=ease_out))


def lighthouse_day(r: Reel):
    box, c, span = r.place('lighthouse', 6000)
    top = box[4] - c[1]
    r.clip('lighthouse_day', length('lighthouse_day'), orbit(c, 110, 150, span * 1.0 + 6, span * 0.8 + 6, top + 3, top - 1,
                                        look_up=3, curve=cruise))


def cottage(r: Reel):
    box, c, span = r.place('fisherman_house', 1000)
    # The template's middle is out on the boardwalk: circle the house itself, where Saylor lives.
    x1, y1, z1, x2, y2, z2 = box
    pos = r.s.cmd(f'data get entity @e[type=minecraft:villager,x={x1},y={y1},z={z1},dx={x2 - x1},dy={y2 - y1},'
                  f'dz={z2 - z1},limit=1] Pos')
    house = tuple(float(v) for v in re.findall(r'(-?[\d.]+)d', pos)[:3])
    r.clip('cottage', length('cottage'), orbit(house, 60, 100, 26, 20, 12, 8, look_up=-1, curve=cruise))


def pier(r: Reel):
    box, c, span = r.place('harbour_pier', 1500)
    r.clip('pier', length('pier'), orbit(c, 70, 110, span * 0.9 + 6, span * 0.7 + 6, box[4] - c[1] + 5, box[4] - c[1] + 1,
                                  curve=cruise))


def stilt(r: Reel):
    box, c, span = r.place('stilt_shack', 6000)
    r.clip('stilt', length('stilt'), orbit(c, 70, 110, span * 1.2 + 6, span * 0.9 + 6, box[4] - c[1] + 4, box[4] - c[1],
                                   curve=cruise))


def ice(r: Reel):
    box, c, span = r.place('ice_fishing_camp', 5000)
    r.clip('ice', length('ice'), orbit(c, 250, 290, span * 1.3 + 6, span * 1.0 + 6, box[4] - c[1] + 5, box[4] - c[1] + 2,
                                 curve=cruise))


def boathouse(r: Reel):
    box, c, span = r.place('river_boathouse', 2000)
    r.clip('boathouse', length('boathouse'), orbit(c, 70, 110, span * 1.1 + 6, span * 0.85 + 6, box[4] - c[1] + 4, box[4] - c[1] + 1,
                                       curve=cruise))


def trawler(r: Reel):
    box, c, span = r.place('sunken_trawler', 6000, underwater=True)
    r.clip('trawler', length('trawler'), orbit(c, 160, 205, span * 0.75 + 4, span * 0.55 + 4, 9, 6, look_up=-2, curve=cruise),
           settle=40)


def pots(r: Reel):
    """Three Crab Pots in the sea by the Harbour Pier: one baited, one with a catch, one just set. Under water, pushing
    in."""
    from marketing_shots import sea_spots
    box = box_of(r.s, 'harbour_pier')
    r.s.cmd('time set 5000', 'weather clear', f'gamemode spectator {PLAYER}')
    x1, _, z1, x2, _, z2 = box
    r.s.cmd(f'fill {x1 - 14} 55 {z1 - 14} {x2 + 14} 63 {z2 + 14} minecraft:water replace {NS}:crab_pot')
    spots = sea_spots(r.s, box)
    x, z = spots[0]
    near = sorted(spots, key=lambda p: abs(p[0] - x) + abs(p[1] - z))[:3]

    def stack(item, count, slot):
        return f'{{Slot:{slot}b,id:"{item}",count:{count}}}'
    contents = [f'{{Items:[{stack(NS + ":fish_bait", 12, 0)}]}}',
                f'{{Items:[{stack("minecraft:salmon", 2, 0)},{stack("minecraft:cod", 3, 1)},'
                f'{stack(NS + ":chum", 6, 2)}]}}', '']
    for (px, pz), items in zip(near, contents):
        r.s.cmd(f'setblock {px} 61 {pz} {NS}:crab_pot[waterlogged=true,facing=south]{items}')
    cx = sum(p[0] for p in near) / 3 + 0.5
    cz = sum(p[1] for p in near) / 3 + 0.5
    r.s.cmd(f'effect give {PLAYER} minecraft:night_vision 900 0 true',
            f'effect give {PLAYER} minecraft:conduit_power 900 0 true')
    r.clip('pots', length('pots'), dolly((cx + 4.6, 60.4, cz + 4.6), (cx + 2.4, 60.0, cz + 2.4), (cx, 61.4, cz), (cx, 61.2, cz),
                            curve=cruise), settle=40)


def screens(r: Reel):
    """The pot screen, the Harbourmaster's trades and a bottle opened into a map: the listing screenshots' scenes (real
    right-clicks in the real game, see tools/qa/marketing_shots.py), captured again in portrait."""
    import marketing_shots as ms
    out = OUT / 'stills'
    ms.OUT = out
    shutil.rmtree(out, ignore_errors=True)
    r.s.cmd('tick unfreeze')
    r.s.hud(True)
    ms.pots(r.s)       # also the pot screen
    ms.trades(r.s)
    ms.bottle(r.s)
    r.s.hud(False)
    print('captured stills', sorted(p.name for p in out.glob('*.jpg')), flush=True)


# An empty vanilla beach in the showcase world (seed 1928374655), far from any of the mod's structures.
BEACH = (-792, 332)
CLIPS = {'beach': beach, 'lighthouse': lighthouse, 'lighthouse_day': lighthouse_day, 'cottage': cottage, 'pier': pier,
         'stilt': stilt, 'ice': ice, 'boathouse': boathouse, 'trawler': trawler, 'pots': pots, 'screens': screens}


def main():
    global BEACH
    ap = argparse.ArgumentParser()
    ap.add_argument('--preview', action='store_true')
    ap.add_argument('--beach', default='', help='x,z of an empty beach for the hook')
    ap.add_argument('clips', nargs='*')
    args = ap.parse_args()
    if args.beach:
        BEACH = tuple(int(v) for v in args.beach.split(','))
    r = Reel(preview=args.preview)
    r.s.hud(False)
    for name in args.clips or list(CLIPS):
        CLIPS[name](r)
    r.s.hud(True)
    r.s.cmd('tick unfreeze', 'forceload remove all')


if __name__ == '__main__':
    main()
