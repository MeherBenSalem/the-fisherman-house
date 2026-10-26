# Instagram reel

A 34-second vertical reel (1080×1920, 30 fps), narrated, for Instagram Reels; also fine for TikTok and YouTube Shorts.

| File | What it is |
|------|------------|
| `vo/script.json` | The narration, one sentence per line. |
| `plan.py` | Times the reel to the narration: checks every take, places them, writes `timeline.json` and the narration track. |
| `timeline.json` | The cut list and every spoken word's timing. The picture, the captions and the audio all read it. |
| `capture.py` | Captures the footage from the game, frame by frame, at the lengths in `timeline.json`. |
| `edit.cjs` | Renders the frames: footage, motion graphics and word-timed captions, in the listing's fonts and colours. |
| `audio.py` | Synthesises the music and the sound effects (no samples) and mixes them under the narration. |
| `make.sh` | Audio, frames, the MP4s and the cover. |
| `cover.jpg` | The cover for the profile grid: the title over the lighthouse at sunset. |

The videos (`fishermans-coast-reel.mp4`, narration with music and effects, and `fishermans-coast-reel-no-music.mp4`,
narration and effects only) and the narration are build outputs: they are delivered directly and never committed.

## The narration

The voice is NightBeam's channel voice, an original voice recorded separately: one take per sentence of
`vo/script.json`, each checked word for word with faster-whisper (`plan.py --check`), never time-stretched (the takes
are only cut at their silent ends and placed with short gaps), with a light polish (`VO_CHAIN` in `plan.py`). Under it,
the music is a bed 9 dB down that ducks 7 dB more while the voice speaks, and the effects step aside for it too.

| Time | Picture | Narration |
|------|---------|-----------|
| 0–2.5 s | an empty vanilla beach | "Minecraft beaches are boring." (each word pops on screen as it is said) |
| 2.5–6.7 s | the Lighthouse at sunset, the beat drops | "Not anymore. Fisherman's Coast adds seven places to explore." |
| 6.7–14.6 s | the Cottage, Pier, Lighthouse, Stilt Shack, Ice Fishing Camp, Boathouse, each on its name | "A fisherman's cottage, a harbour pier, a lighthouse, a stilt shack, an ice fishing camp, a river boathouse." |
| 14.6–17 s | the Sunken Trawler (7/7) | "And a sunken trawler, full of loot." |
| 17–19.9 s | Crab Pots under water | "Crab pots fish for you, even while you're AFK." |
| 19.9–22.4 s | the bait cards | "Bait makes them faster and luckier." |
| 22.4–25.4 s | Harbourmaster Wren's trades | "Six fishermen sell exclusive trades." |
| 25.4–28.4 s | a Message in a Bottle opened into a map | "And messages in a bottle can lead to treasure." |
| 28.4–34.1 s | the end card, looping back to the first frame | "It's free on Fabric, NeoForge and Forge. Send this to your fishing buddy." (the script spells it "Neo-Forge" so the voice says both syllables) |

Every cut lands on a spoken word, and every word is captioned: 2–4 words at a time on highlight boxes, the spoken word
in yellow, lifted over the first-person bottle shot so the hotbar and the note
stay visible. The hook and "Not anymore." are already big words on screen, so they are not captioned twice. Every
picture is the game itself: the structures are where the world generated them, and the screens are real right-clicks
(the scenes in `tools/qa/marketing_shots.py`). Only the camera is staged.

## Why it is built this way

From research on how Reels are ranked and watched (October 2026; mostly secondhand marketing sources, so treat the
numbers loosely):

- **Watch time, replays and sends rank first.** Reports of what Instagram's head confirmed put total watch time
  (replays included) first, then sends per reach (DM shares), then likes. Hence a seamless loop and a "send this to your
  fishing buddy" prompt. ([Dataslayer](https://www.dataslayer.ai/blog/instagram-algorithm-2025-complete-guide-for-marketers),
  [SocialPilot](https://www.socialpilot.co/blog/instagram-reels-algorithm), [Hootsuite](https://blog.hootsuite.com/instagram-algorithm/))
- **The first 1.5–3 seconds decide.** Open mid-motion with a pattern interrupt, and make it work on mute, since many
  people watch without sound: the hook is on screen from frame 0, and the twist lands on the beat drop.
  ([Dataslayer](https://www.dataslayer.ai/blog/instagram-algorithm-2025-complete-guide-for-marketers),
  [Quso](https://quso.ai/blog/instagram-reels-best-practices))
- **Something new every 1–2 seconds** through the montage, cut on the spoken names. Short beats under 30 s suit people
  who do not follow you yet; longer explainers can do well too, so this showcase sits between.
- **Safe zones.** Instagram covers the top, the bottom (caption and buttons) and the right (like, comment, share). All
  text sits between y≈300 and y≈1480 and clear of the right edge.
  ([ClipSpeed](https://www.clipspeed.ai/blog/instagram-reels-captions.html), [Argil](https://argil.ai/blog/instagram-reel-size-e350f))
- **Original content and audio**: original footage, an original voice, original music. Whether trending audio beats
  original audio is disputed, so there is also a version without music for adding a track in Instagram.
  ([Dataslayer](https://www.dataslayer.ai/blog/instagram-algorithm-2025-complete-guide-for-marketers),
  [Kontentino](https://www.kontentino.com/q-and-a/trending-audio-instagram-reach/))

## Posting it

A short caption (40 characters or less) with three hashtags, and the links in a pinned comment.

```
Minecraft beaches, finally worth it 🎣 #minecraft #minecraftmods #moddedminecraft
```

Pinned comment:

```
Free on CurseForge and Modrinth (Fabric, NeoForge, Forge · 1.20.1 to 26.3):
https://modrinth.com/mod/fisherman-coast
https://www.curseforge.com/minecraft/mc-mods/the-fisherman-house
```

- Set `cover.jpg` as the cover; everything in it sits inside the middle 3:4, so the grid crop keeps it.
- Post the version with music first. To try a trending sound, post the no-music version and add the track in
  Instagram at about 20–30 %, under the voice.
- Reply to the first comments quickly, share the reel to the Story, and post the same file (without watermarks) to
  TikTok and YouTube Shorts.

## Rebuilding it

1. **Narration:** record one take per sentence of `vo/script.json` as `build/vo/s01_t1.wav`, `s02_t1.wav`, ... (any
   sample rate; one sentence per file), then:

   ```bash
   python3 marketing/reel/plan.py --check   # every take says its line (needs faster-whisper)
   python3 marketing/reel/plan.py           # timeline.json and build/vo.wav
   ```

   Replace any take that fails the check.

2. **Footage** from a 26.3 Fabric dev server and a client in a portrait window on its own X display:

   ```bash
   Xvfb :2 -screen 0 1080x1920x24 &
   sed -i 's/^level-name=.*/level-name=showcase/; s/^view-distance=.*/view-distance=12/' 26.3/fabric/runs/server/server.properties
   rm -f 26.3/fabric/runs/server/config/fisherman_house.json        # the default config
   tools/qa/devrun.sh start-server 26.3 fabric
   DISPLAY=:2 QA_WIDTH=1080 QA_HEIGHT=1920 tools/qa/devrun.sh start-client 26.3 fabric
   python3 tools/qa/rcon.py "op Builder"
   python3 marketing/reel/capture.py --preview pier   # frame a shot: first, middle and last frame
   python3 marketing/reel/capture.py                  # every clip into marketing/reel/build/frames/
   ```

   The world is `showcase` with the QA seed (`1928374655`); the client uses `fov:0.5` and `renderDistance:12` in
   `26.3/fabric/runs/client/options.txt`. The client renders in software, far too slowly to record in real time, so
   `capture.py` moves the camera along an eased path with `/tp`, steps the frozen world one tick, captures the display
   and retakes any frame the game had not redrawn yet: the camera moves are smooth whatever the frame rate.

3. **Edit:** `marketing/reel/make.sh` (Playwright with Chromium, numpy and scipy, ffmpeg).
