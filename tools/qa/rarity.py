#!/usr/bin/env python3
"""Measures how far the nearest of each structure is from a grid of points (a feel for how common they are).

  python3 tools/qa/rarity.py [--step 2000] [--n 3]
"""
import argparse
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rcon import wait_for  # noqa: E402

STRUCTURES = ('fisherman_house', 'harbour_pier', 'lighthouse', 'stilt_shack', 'ice_fishing_camp', 'river_boathouse',
              'sunken_trawler')

ap = argparse.ArgumentParser()
ap.add_argument('--step', type=int, default=2000)
ap.add_argument('--n', type=int, default=3)
args = ap.parse_args()
r = wait_for()
for s in STRUCTURES:
    dists = []
    for i in range(args.n):
        for j in range(args.n):
            x, z = (i - args.n // 2) * args.step, (j - args.n // 2) * args.step
            out = r.command(f'execute positioned {x} 64 {z} run locate structure fisherman_house:{s}')
            m = re.search(r'\((\d+) blocks away\)', out)
            dists.append(int(m.group(1)) if m else 99999)
    print(f'{s:17s} median {statistics.median(dists):6.0f}  max {max(dists):6d}  {dists}', flush=True)
