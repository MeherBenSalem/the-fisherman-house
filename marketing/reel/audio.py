#!/usr/bin/env python3
"""Makes the reel's audio from scratch (no samples): an original 120 BPM track and sound effects, both timed from
timeline.json so every cut lands on a beat.

  python3 marketing/reel/audio.py      # build/music.wav, sfx.wav, mix.wav, voice_sfx.wav (48 kHz stereo)

The track is a sea shanty in D minor for a pop beat: a plucked melody (Karplus-Strong strings), a pad, a bass, drums.
It opens on C major with a riser, drops on D minor with the "Not anymore" cut, goes under water for the Sunken Trawler,
and ends on the intro's picking, so the reel loops cleanly. With the narration (build/vo.wav, from plan.py) it also
writes build/mix.wav (voice, music bed, effects) and build/voice_sfx.wav (voice and effects, for a trending track).
Needs numpy and scipy.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

HERE = Path(__file__).resolve().parent
BUILD = HERE / 'build'
TL = json.loads((HERE / 'timeline.json').read_text())
SR = 48000
DUR = TL['duration']
BEAT = 60 / TL['bpm']
BAR = 4 * BEAT
N = int(DUR * SR)
rng = np.random.default_rng(1928374655)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, 'low', fs=SR, output='sos'), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, 'high', fs=SR, output='sos'), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], 'band', fs=SR, output='sos'), x)


def env(n, a, d, s, r, hold):
    """ADSR in samples' worth of seconds: attack, decay, sustain level, release, and the time before release."""
    t = np.arange(n) / SR
    e = np.where(t < a, t / max(a, 1e-4), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-4)))
    rel = np.clip(1 - (t - hold) / max(r, 1e-4), 0, 1)
    return e * np.where(t > hold, rel, 1)


class Bus:
    def __init__(self):
        self.l = np.zeros(N + SR * 3)
        self.r = np.zeros(N + SR * 3)

    def add(self, x, t, gain=1.0, pan=0.0):
        i = int(round(t * SR))
        if i >= N:
            return
        if i < 0:   # starts before the reel: keep only what falls inside it
            x, i = x[-i:], 0
        x = x * gain
        n = min(len(x), len(self.l) - i)
        self.l[i:i + n] += x[:n] * np.sqrt(0.5 * (1 - pan))
        self.r[i:i + n] += x[:n] * np.sqrt(0.5 * (1 + pan))

    def stereo(self):
        return np.stack([self.l[:N], self.r[:N]])


# Instruments ------------------------------------------------------------------------------------------------------

def pluck(m, dur, bright=0.5):
    """Karplus-Strong: a plucked string, like a mandolin. The averaging filter adds half a sample of delay, so the
    delay line is half a sample shorter than the period to keep the note in tune."""
    f = mtof(m)
    p = max(2, int(round(SR / f - 0.5)))
    n = int(SR * (dur + 0.6))
    y = np.zeros(n + p + 1)
    y[:p + 1] = lp(rng.uniform(-1, 1, p + 1), min(SR / 2.2, 2000 + 9000 * bright), 1)
    damp = 0.997 if f < 400 else 0.994
    for s in range(p + 1, len(y), p):
        e = min(s + p, len(y))
        y[s:e] = damp * 0.5 * (y[s - p:e - p] + y[s - p - 1:e - p - 1])
    out = y[:n]
    fade = np.clip(1 - (np.arange(n) / SR - dur) / 0.25, 0, 1)
    return out * fade


def saw(f, n, detune_cents=(0,)):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for c in detune_cents:
        ff = f * 2 ** (c / 1200)
        phase = rng.uniform(0, 1)
        out += 2 * ((t * ff + phase) % 1) - 1
    return out / len(detune_cents)


def pad(notes, dur, cutoff=1700):
    n = int(SR * (dur + 0.5))
    x = sum(saw(mtof(m), n, (-8, 0, 7)) for m in notes) / len(notes)
    x = lp(lp(x, cutoff, 1), cutoff * 1.4, 1)
    return x * env(n, 0.12, 0.6, 0.75, 0.45, dur)


def bass(m, dur):
    n = int(SR * (dur + 0.1))
    t = np.arange(n) / SR
    x = 0.7 * np.sin(2 * np.pi * mtof(m) * t) + 0.45 * lp(saw(mtof(m), n), 420)
    return np.tanh(1.6 * x) * env(n, 0.005, 0.12, 0.55, 0.06, dur)


def kick(muffled=False):
    n = int(SR * 0.45)
    t = np.arange(n) / SR
    f = 46 + 110 * np.exp(-t / 0.035)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)
    x += 0.35 * lp(rng.uniform(-1, 1, n), 4000) * np.exp(-t / 0.004)
    return lp(x, 300) if muffled else x


def clap():
    n = int(SR * 0.35)
    t = np.arange(n) / SR
    noise = bp(rng.uniform(-1, 1, n), 900, 3200)
    e = sum(np.where(t >= o, np.exp(-(t - o) / 0.012), 0) for o in (0, 0.011, 0.022)) * 0.6 + \
        np.where(t >= 0.03, np.exp(-(t - 0.03) / 0.11), 0)
    return noise * e


def hat(open_=False):
    n = int(SR * (0.3 if open_ else 0.06))
    t = np.arange(n) / SR
    return hp(rng.uniform(-1, 1, n), 7500) * np.exp(-t / (0.09 if open_ else 0.014))


def crash():
    n = int(SR * 2.2)
    t = np.arange(n) / SR
    return hp(rng.uniform(-1, 1, n), 5000) * np.exp(-t / 0.7) * 0.6


# Effects ----------------------------------------------------------------------------------------------------------

def swept(n, f0, f1, width=1.6, block=256):
    """Noise through a band-pass filter whose centre slides from f0 to f1 (log), block by block."""
    x = rng.uniform(-1, 1, n)
    out = np.zeros(n)
    for s in range(0, n, block):
        u = s / n
        fc = f0 * (f1 / f0) ** u
        lo, hi = fc / width, min(fc * width, SR / 2.1)
        sos = butter(2, [lo, hi], 'band', fs=SR, output='sos')
        seg = x[max(0, s - 2048):s + block]
        out[s:s + block] = sosfilt(sos, seg)[-len(x[s:s + block]):]
    return out


def whoosh(d=0.3, up=True):
    n = int(SR * d)
    t = np.arange(n) / SR
    x = swept(n, 400, 6000) if up else swept(n, 6000, 400)
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    return x * e


def riser(d):
    n = int(SR * d)
    t = np.arange(n) / SR
    u = t / d
    noise = swept(n, 300, 9000, width=1.4) * u ** 2
    tone = np.sin(2 * np.pi * np.cumsum(150 * 2 ** (u * 3)) / SR) * u ** 3 * 0.35
    return noise + tone


def boom():
    n = int(SR * 1.6)
    t = np.arange(n) / SR
    f = 38 + 60 * np.exp(-t / 0.08)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55)
    x += 0.5 * lp(rng.uniform(-1, 1, n), 1200) * np.exp(-t / 0.18)
    return np.tanh(1.5 * x)


def pop():
    n = int(SR * 0.09)
    t = np.arange(n) / SR
    f = 900 * np.exp(-t / 0.03) + 300
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.025)


def tick():
    n = int(SR * 0.04)
    t = np.arange(n) / SR
    return hp(rng.uniform(-1, 1, n), 3000) * np.exp(-t / 0.006) + 0.5 * np.sin(2 * np.pi * 2400 * t) * np.exp(-t / 0.01)


def bubbles(d, rate=14):
    n = int(SR * d)
    out = np.zeros(n)
    for _ in range(int(d * rate)):
        s = int(rng.uniform(0, n - SR * 0.08))
        m = int(SR * rng.uniform(0.03, 0.07))
        t = np.arange(m) / SR
        f0 = rng.uniform(400, 1100)
        f = f0 * (1 + 2.5 * t / t[-1])
        out[s:s + m] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / t[-1]) * rng.uniform(0.3, 1)
    return out


def clink():
    n = int(SR * 1.2)
    t = np.arange(n) / SR
    return sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / d)
               for f, a, d in ((2350, 0.6, 0.35), (3130, 0.4, 0.25), (4720, 0.25, 0.15), (6090, 0.15, 0.1)))


def chime():
    n = int(SR * 1.4)
    t = np.arange(n) / SR
    return sum(a * np.sin(2 * np.pi * mtof(m) * t) * np.exp(-t / 0.5) for m, a in ((86, 0.5), (93, 0.35), (98, 0.25)))


def reverb(x, seconds=1.4, mix=0.25):
    n = int(SR * seconds)
    t = np.arange(n) / SR
    out = []
    for _ in range(2):
        ir = rng.uniform(-1, 1, n) * np.exp(-t / (seconds / 5))
        ir = lp(ir, 6000)
        ir /= np.sqrt(np.sum(ir ** 2))
        out.append(ir)
    wet = np.stack([fftconvolve(x[0], out[0])[:x.shape[1]], fftconvolve(x[1], out[1])[:x.shape[1]]])
    return x + mix * wet


# The arrangement ----------------------------------------------------------------------------------------------------

CHORDS = {'Dm': [62, 65, 69], 'Bb': [58, 62, 65], 'F': [60, 65, 69], 'C': [60, 64, 67]}
ROOTS = {'Dm': 38, 'Bb': 34, 'F': 41, 'C': 36}
MOTIF = {
    'Dm': [(0, .75, 74), (.75, .25, 74), (1, .5, 72), (1.5, .5, 69), (2, 1, 74), (3, .5, 77), (3.5, .5, 76)],
    'Bb': [(0, .75, 74), (.75, .25, 72), (1, .5, 70), (1.5, .5, 69), (2, 1.5, 70), (3.5, .5, 72)],
    'F': [(0, .75, 72), (.75, .25, 72), (1, .5, 69), (1.5, .5, 65), (2, 1, 69), (3, .5, 72), (3.5, .5, 74)],
    'C': [(0, 1, 76), (1, .5, 74), (1.5, .5, 72), (2, 2, 67)],
}
CLIP = {c['name']: c for c in TL['clips']}
DROP = CLIP['lighthouse']['start']                              # "Not anymore": the beat drops on D minor
UNDER = (CLIP['trawler']['start'], CLIP['trawler']['end'])      # the Sunken Trawler: the track goes under water
END = CLIP['end']['start']                                      # the end card: the beat stops on an impact
# Bar 0 is the intro on C (tension) and ends on the drop; then D minor, B flat, F, C; the end returns to the intro's
# picking, so the reel loops.
FIRST = DROP - BAR
BARS = ['C'] + (['Dm', 'Bb', 'F', 'C'] * 8)[:int((DUR - DROP) / BAR) + 1]


def music():
    drums, keys, low, lead = Bus(), Bus(), Bus(), Bus()
    kicks = []
    for b, chord in enumerate(BARS):
        t0 = FIRST + b * BAR
        full = b >= 1 and t0 < END
        tail = t0 >= END - BAR / 2
        # Pad everywhere; the picked arpeggio in the intro and on the end card; bass, drums and melody in between.
        keys.add(pad(CHORDS[chord], BAR - 0.05, cutoff=1100 if b == 0 or tail else 2400), t0, 0.42)
        if b == 0 or tail:
            for i in range(16):
                m = (CHORDS[chord] + [n + 12 for n in CHORDS[chord]])[i % 6] + 12
                ti = t0 + i * BEAT / 4
                if ti >= DUR:
                    break
                if ti >= 0 and (b == 0 or ti >= END):
                    keys.add(lp(pluck(m, 0.2, 0.3), 2500), ti, 0.18 * (0.6 + 0.4 * (i % 4 == 0)), pan=0.4 * np.sin(i))
        if not full:
            continue
        for beat in range(4):
            tb = t0 + beat * BEAT
            if tb >= END:
                break
            under = UNDER[0] <= tb < UNDER[1]
            if not under or beat % 2 == 0:
                drums.add(kick(muffled=under), tb, 0.7)
                kicks.append(tb)
            if beat % 2 == 1 and not under:
                drums.add(clap(), tb, 0.55)
            if not under:
                drums.add(hat(), tb + BEAT / 2, 0.24, pan=0.3)
                if tb >= UNDER[1]:
                    drums.add(hat(), tb + BEAT / 4, 0.08, pan=-0.3)
                    drums.add(hat(), tb + 3 * BEAT / 4, 0.08, pan=-0.3)
            for half in range(2):
                low.add(bass(ROOTS[chord] + (12 if half else 0), BEAT / 2 - 0.03), tb + half * BEAT / 2, 0.3)
        octave = 12 if t0 >= UNDER[1] else 0
        for at, d, m in MOTIF[chord]:
            tm = t0 + at * BEAT
            if tm >= END or UNDER[0] <= tm < UNDER[1]:
                continue
            lead.add(pluck(m + octave, d * BEAT, 0.7), tm, 0.7, pan=-0.15)
            lead.add(pluck(m + octave - 12, d * BEAT, 0.4), tm + 0.012, 0.3, pan=0.2)
            if octave:
                third = m + octave - (3 if m % 12 in (2, 9) else 4)   # a third below: minor on D and A
                lead.add(pluck(third, d * BEAT, 0.5), tm + 0.006, 0.22, pan=0.35)
    for t in (DROP, UNDER[1]):
        drums.add(crash(), t, 0.5)

    # Sidechain: pad and bass duck under each kick (the "pump").
    duck = np.ones(N)
    tt = np.arange(N) / SR
    for k in kicks:
        i = int(k * SR)
        m = min(N - i, int(0.3 * SR))
        if m > 0:
            duck[i:i + m] = np.minimum(duck[i:i + m], 1 - 0.55 * np.exp(-tt[:m] / 0.09))
    keys_s, low_s = keys.stereo() * duck, low.stereo() * duck
    lead_s = lead.stereo()
    # A dotted-eighth echo on the melody, panned.
    delay = int(0.75 * BEAT * SR)
    echo = np.zeros_like(lead_s)
    echo[0, delay:] = lead_s[1, :-delay] * 0.28
    echo[1, 2 * delay:] = lead_s[0, :-2 * delay] * 0.18
    mix = reverb(keys_s + lead_s + echo, 1.6, 0.35) + low_s + reverb(drums.stereo(), 0.9, 0.12)
    # Under water: everything through a low-pass, faded in and out at the cuts.
    wet = np.stack([lp(mix[0], 650, 4), lp(mix[1], 650, 4)]) * 1.4
    w = np.clip((tt - (UNDER[0] - 0.05)) / 0.1, 0, 1) * np.clip(((UNDER[1] + 0.02) - tt) / 0.06, 0, 1)
    return mix * (1 - w) + wet * w


def word_time(sid, n):
    ws = [w for w in TL.get('words', []) if w['sid'] == sid]
    return ws[n]['s'] if len(ws) > n else None


def sfx():
    s = Bus()
    rise = min(1.5, DROP - 0.1)
    s.add(riser(rise), DROP - rise, 0.35)
    s.add(boom(), DROP, 0.9)
    s.add(boom(), END, 0.8)
    s.add(chime(), END + 0.02, 0.25)
    for n in (2, 3):                      # "are", "boring" pop in on their words
        t = word_time('s01', n)
        if t is not None:
            s.add(pop(), t, 0.35)
    for c in TL['clips']:
        if c['start'] > DROP and c['name'] != 'end':   # the end card comes in on its impact instead
            s.add(whoosh(0.28), c['start'] - 0.22, 0.18, pan=0.2 * np.sin(c['start']))
        if c.get('place'):
            s.add(tick(), c['start'] + 0.04, 0.22)
    s.add(pop(), TL['sentences'].get('s03', DROP + 1.0), 0.3)
    bait = CLIP['bait']['start']
    for d in (0.15, 0.4, 0.65):
        s.add(pop(), bait + d, 0.28)
    s.add(pop(), END + 1.0, 0.28)
    s.add(bubbles(UNDER[1] - UNDER[0]), UNDER[0], 0.06)
    s.add(bubbles(CLIP['pots']['end'] - CLIP['pots']['start'], rate=8), CLIP['pots']['start'], 0.035)
    s.add(clink(), CLIP['bottle']['start'], 0.2)
    return reverb(s.stereo(), 1.0, 0.18)


def master(x, peak=0.89):
    x = np.tanh(1.3 * x / np.max(np.abs(x))) / np.tanh(1.3)
    # Fade the first and last few milliseconds so the loop does not click.
    f = int(0.004 * SR)
    x[:, :f] *= np.linspace(0, 1, f)
    x[:, -f:] *= np.linspace(1, 0, f)
    return x * peak


def rms(x):
    return float(np.sqrt(np.mean(x ** 2)) + 1e-9)


def narrated(vo, music_bed, effects):
    """The voice on top; the music as a bed 9 dB under it, ducked 7 dB more while the voice speaks; the effects well
    under the voice (their peaks 11 dB below its peak), ducked while it speaks."""
    vo = vo / np.max(np.abs(vo))
    win = int(0.25 * SR)
    env = np.convolve(np.abs(vo), np.ones(win) / win, mode='same')
    duck = np.where(env > 0.008, 10 ** (-7 / 20), 1.0)
    duck = np.convolve(duck, np.ones(win) / win, mode='same')
    speaking = env > 0.008
    voice_level = rms(vo[speaking]) if speaking.any() else rms(vo)
    bed = music_bed / rms(music_bed) * voice_level * 10 ** (-9 / 20) if music_bed is not None else 0
    fx = effects / np.max(np.abs(effects)) * 10 ** (-11 / 20)
    # The effects step aside for the voice too (6 dB while it speaks), so no word is masked by a whoosh or an impact.
    fx_duck = np.convolve(np.where(env > 0.008, 10 ** (-6 / 20), 1.0), np.ones(win) / win, mode='same')
    out = np.stack([vo, vo]) + bed * duck + fx * fx_duck
    return out / np.max(np.abs(out)) * 0.89


def write(name, x):
    BUILD.mkdir(exist_ok=True)
    wavfile.write(BUILD / name, SR, (x.T * 32767).astype(np.int16))
    print('wrote', (BUILD / name).relative_to(HERE.parents[1]))


if __name__ == '__main__':
    m = music()
    e = sfx()
    write('music.wav', master(m))
    write('sfx.wav', master(e, 0.7))
    vo_path = BUILD / 'vo.wav'
    if vo_path.exists():
        rate, vo = wavfile.read(vo_path)
        vo = (vo.astype(np.float64) / (32768 if vo.dtype == np.int16 else 1))[:N]
        vo = np.pad(vo, (0, N - len(vo)))
        write('mix.wav', narrated(vo, m, e))
        write('voice_sfx.wav', narrated(vo, None, e))
    else:
        write('mix.wav', master(m / np.max(np.abs(m)) + 0.55 * e / np.max(np.abs(e))))
