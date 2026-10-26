#!/usr/bin/env python3
"""Times the reel to its narration: places the voice takes, finds every word, and writes timeline.json.

  python3 marketing/reel/plan.py [--check]      # needs numpy, scipy and faster-whisper

The narration is recorded separately, one take per sentence of vo/script.json, as build/vo/s01_t1.wav, s02_t1.wav, ...
(see README.md). Takes are only trimmed at their silent ends and placed with short gaps: never time-stretched. Every cut lands on a spoken word: the drop on "Not anymore", each of the seven places on its name, each
feature on its sentence. --check transcribes the takes and lists any that do not say their line.

Writes timeline.json (clips, words for the captions) and build/vo.wav (the narration with a light polish, VO_CHAIN).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.io import wavfile

HERE = Path(__file__).resolve().parent
BUILD = HERE / 'build'
TAKES = BUILD / 'vo'
SR = 48000
FPS = 30
# A light polish for the narration (low cut and gentle compression); the VO_CHAIN environment variable replaces it.
VO_CHAIN = os.environ.get('VO_CHAIN', 'highpass=f=80,acompressor=threshold=-18dB:ratio=2:attack=10:release=150')
LEAD_IN = 0.12            # the first word starts almost at once: the hook is the first thing heard
GAP = {'s02': 0.22, 's03': 0.28, 's09': 0.38, 's10': 0.42}   # before each sentence; the rest get DEFAULT_GAP
# Spelled for the voice, shown as written in the captions (the hyphen makes the voice say both syllables clearly).
DISPLAY = {'Neo-Forge': 'NeoForge'}
DEFAULT_GAP = 0.26
TAIL = 0.8                # the end card after the last word, before the loop
PLACES = [
    ('cottage', "Fisherman's Cottage", 'sandy & snowy beaches', 'sand'),
    ('pier', 'Harbour Pier', 'sandy beaches', 'lantern'),
    ('lighthouse_day', 'Lighthouse', 'stony shores', 'buoy'),
    ('stilt', 'Stilt Shack', 'swamps & mangroves', 'swamp'),
    ('ice', 'Ice Fishing Camp', 'frozen oceans', 'ice'),
    ('boathouse', 'River Boathouse', 'riverbanks', 'kelp'),
]


def load(path):
    rate, x = wavfile.read(path)
    x = x.astype(np.float32)
    if x.ndim > 1:
        x = x.mean(axis=1)
    if np.abs(x).max() > 2:
        x /= 32768
    if rate != SR:
        from math import gcd
        from scipy.signal import resample_poly
        g = gcd(SR, rate)
        x = resample_poly(x, SR // g, rate // g).astype(np.float32)
    return x


def trim(x, threshold=0.008, pad=0.03):
    """Cut the silence before the first and after the last sound (nothing else is changed)."""
    win = int(0.01 * SR)
    env = np.convolve(np.abs(x), np.ones(win) / win, mode='same')
    loud = np.where(env > threshold)[0]
    a = max(0, loud[0] - int(pad * SR))
    b = min(len(x), loud[-1] + int(pad * SR))
    return x[a:b]


def words_of(x):
    """faster-whisper word timings ("small" model, on the CPU)."""
    from faster_whisper import WhisperModel
    global MODEL
    if 'MODEL' not in globals():
        MODEL = WhisperModel('small', device='cpu', compute_type='int8')
    audio = np.interp(np.arange(0, len(x), SR / 16000), np.arange(len(x)), x).astype(np.float32)
    segs, _ = MODEL.transcribe(audio, word_timestamps=True, language='en')
    return [(w.word.strip(), float(w.start), float(w.end)) for s in segs for w in s.words]


def letters(text):
    """Only letters and digits, with British spellings folded (whisper writes "harbor" for "harbour")."""
    return re.sub(r'[^a-z0-9]', '', text.lower().replace('our', 'or'))


def spoken(text):
    """What a line sounds like, for the take check: letters only, digits as words ("6" is "six")."""
    names = 'zero one two three four five six seven eight nine ten'.split()
    return letters(re.sub(r'\b(10|[0-9])\b', lambda m: names[int(m.group(1))], text))


def align(text, heard):
    """The script's own words (its spelling and punctuation, for the captions) timed by what whisper heard: both are
    reduced to letters and matched character by character, so "boat house" still times "boathouse"."""
    import difflib
    tokens = text.split()
    spans, sl = [], ''
    for tok in tokens:
        a = len(sl)
        sl += letters(tok)
        spans.append((a, len(sl)))
    times, wl = [], ''
    for w, a, b in heard:
        part = letters(w)
        for k in range(len(part)):
            times.append(a + (b - a) * k / max(1, len(part)))
        wl += part
    times.append(heard[-1][2] if heard else 0.0)
    match = {}
    for blk in difflib.SequenceMatcher(None, sl, wl, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            match[blk.a + k] = blk.b + k
    out = []
    for tok, (a, b) in zip(tokens, spans):
        idx = [match[k] for k in range(a, b) if k in match]
        if not idx:
            continue
        start = times[idx[0]]
        end = times[min(idx[-1] + 1, len(times) - 1)]
        out.append((DISPLAY.get(tok, tok), start, max(end, start + 0.05)))
    ratio = difflib.SequenceMatcher(None, sl, wl, autojunk=False).ratio()
    return out, ratio


def frame(t):
    return round(t * FPS) / FPS


def main():
    script = json.loads((HERE / 'vo' / 'script.json').read_text())
    check = '--check' in sys.argv
    takes, words, bad = {}, {}, []
    for sid, text in script:
        path = TAKES / f'{sid}_t1.wav'
        x = trim(load(path))
        heard = words_of(x)
        # Cut right after the last word (and just before the first): no trailing breath or silence. Only the ends are
        # cut; the voice itself is never stretched.
        if heard:
            a = max(0, int((heard[0][1] - 0.06) * SR))
            b = min(len(x), int((heard[-1][2] + 0.25) * SR))   # room for a final "s", which whisper ends early
            x = x[a:b]
            heard = [(w, s0 - a / SR, s1 - a / SR) for w, s0, s1 in heard]
        takes[sid] = x
        words[sid], ratio = align(text, heard)
        if spoken(' '.join(w for w, _, _ in heard)) != spoken(text) or len(words[sid]) != len(text.split()):
            bad.append((sid, text, ' '.join(w for w, _, _ in heard)))
    for sid, text, said in bad:
        print(f'MISMATCH {sid}: wanted "{text}" / heard "{said}"')
    if check:
        sys.exit(1 if bad else 0)

    # Place the sentences.
    starts, t = {}, LEAD_IN
    for i, (sid, _) in enumerate(script):
        if i:
            t += GAP.get(sid, DEFAULT_GAP)
        starts[sid] = t
        t += len(takes[sid]) / SR
    total = frame(t + TAIL)
    vo = np.zeros(int(total * SR) + SR)
    for sid, x in takes.items():
        i = int(starts[sid] * SR)
        vo[i:i + len(x)] += x
    vo = vo[:int(total * SR)]
    BUILD.mkdir(exist_ok=True)
    raw = BUILD / 'vo_raw.wav'
    wavfile.write(raw, SR, vo.astype(np.float32))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(raw), '-af', VO_CHAIN, '-ar', str(SR), '-ac', '1',
                    str(BUILD / 'vo.wav')], check=True)

    absw = [dict(w=w, s=round(starts[sid] + a, 3), e=round(starts[sid] + b, 3), sid=sid)
            for sid, _ in script for w, a, b in words[sid]]

    def word_start(sid, n):
        return starts[sid] + words[sid][n][1]

    # The cuts.
    s04 = words[script[3][0]]
    articles = [i for i, (w, _, _) in enumerate(s04) if letters(w) in ('a', 'an')]
    if len(articles) != len(PLACES):
        sys.exit(f'expected {len(PLACES)} places in s04, found {len(articles)} articles: {[w for w, _, _ in s04]}')
    cuts = [('beach', 0.0), ('lighthouse', starts['s02'])]
    cuts += [(name, starts['s04'] if k == 0 else word_start('s04', articles[k]) - 0.04)
             for k, (name, *_rest) in enumerate(PLACES)]
    cuts += [('trawler', starts['s05']), ('pots', starts['s06']), ('bait', starts['s07']), ('trades', starts['s08']),
             ('bottle', starts['s09']), ('end', starts['s10'])]
    clips = []
    for k, (name, t0) in enumerate(cuts):
        t1 = cuts[k + 1][1] if k + 1 < len(cuts) else total
        clip = {'name': name, 'start': frame(t0), 'end': frame(t1)}
        if name in [p[0] for p in PLACES]:
            n = [p[0] for p in PLACES].index(name)
            clip.update(place=n + 1, title=PLACES[n][1], where=PLACES[n][2], color=PLACES[n][3])
        if name == 'trawler':
            clip.update(place=7, title='Sunken Trawler', where='the ocean floor', color='ice')
        if name == 'bait':
            clip.update(file='pots', still=True)
        if name in ('trades', 'bottle'):
            clip.update(still=True)
        clips.append(clip)
    timeline = {'fps': FPS, 'bpm': 120, 'duration': total, 'clips': clips,
                'sentences': {sid: round(starts[sid], 3) for sid in starts}, 'words': absw}
    (HERE / 'timeline.json').write_text(json.dumps(timeline, indent=1) + '\n')
    for c in clips:
        print(f"{c['name']:15s} {c['start']:6.2f} - {c['end']:6.2f}  ({c['end'] - c['start']:.2f} s)")
    print(f'total {total:.2f} s, {len(absw)} words')


if __name__ == '__main__':
    main()
