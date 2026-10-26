# Instagram reel

A 26-second vertical reel (1080×1920, 30 fps) for Instagram Reels, also fine for TikTok and YouTube Shorts.

| File | What it is |
|------|------------|
| `fishermans-coast-reel.mp4` | The reel with its original music and sound effects (H.264, AAC, -14 LUFS). |
| `cover.jpg` | The cover for the profile grid: the title over the lighthouse at sunset (3.8 s into the reel). |
| `timeline.json` | The cut list: every clip on the 120 BPM beat grid. The picture and the audio both read it. |
| `capture.py` | Captures the footage from the game, frame by frame. |
| `edit.cjs` | Renders the frames: footage plus the motion graphics, in the listing's fonts and colours. |
| `audio.py` | Synthesises the music and the sound effects (no samples, nothing licensed). |
| `make.sh` | Audio, frames and both MP4s. A second MP4, `fishermans-coast-reel-sfx-only.mp4`, has only the sound effects, for posting with a track from Instagram's library. |

## What is in it

| Time | Picture | On screen |
|------|---------|-----------|
| 0–2 s | an empty vanilla beach, flying in | "Minecraft beaches are **boring.**" (readable on mute from the first frame) |
| 2–3 s | the Lighthouse at sunset, the beat drops | "*Not anymore.*" |
| 3–5 s | the Lighthouse | the icon and "Fisherman's Coast: 7 places, one for every shore" |
| 5–16 s | the Cottage, Harbour Pier, Lighthouse, Stilt Shack, Ice Fishing Camp, River Boathouse, Sunken Trawler | a 1/7 → 7/7 counter, each name and its shore |
| 16–18 s | Crab Pots under water | "Crab Pots: catch fish while you're AFK" |
| 18–19.5 s | the baited pots | Fish Bait 2× faster, Chum 3× faster, Glow Bait + treasure |
| 19.5–21 s | Harbourmaster Wren's trades | "6 named fishermen: exclusive trades" |
| 21–22.5 s | a Message in a Bottle opened into a map | "Treasure maps to sunken trawlers" |
| 22.5–26 s | the end card | loaders, versions, "Send this to your fishing duo", CurseForge & Modrinth |

The last frame is the first frame again (the beach and "Minecraft beaches"), and the music ends on the chord it starts
on, so the reel loops without a seam. Every picture is the game itself: the structures are where the world generated
them, and the screens are real right-clicks (the scenes in `tools/qa/marketing_shots.py`). Only the camera is staged.

## Why it is built this way

From research on how Reels are ranked and watched (October 2026; mostly secondhand marketing sources, so treat the
numbers loosely):

- **Watch time, replays and sends rank first.** Reports of what Instagram's head confirmed put total watch time
  (replays included) first, then sends per reach (DM shares), then likes. Hence a short reel (26 s), a seamless loop,
  and a "send this to your fishing duo" prompt. ([Dataslayer](https://www.dataslayer.ai/blog/instagram-algorithm-2025-complete-guide-for-marketers),
  [SocialPilot](https://www.socialpilot.co/blog/instagram-reels-algorithm), [Hootsuite](https://blog.hootsuite.com/instagram-algorithm/))
- **The first 1.5–3 seconds decide.** Open mid-motion with a pattern interrupt, and make it work on mute, since many
  people watch without sound: the hook is text on screen from frame 0, flying over a beach, and the twist lands on the
  beat drop at 2 s. ([Dataslayer](https://www.dataslayer.ai/blog/instagram-algorithm-2025-complete-guide-for-marketers),
  [Quso](https://quso.ai/blog/instagram-reels-best-practices))
- **Under 30 s for people who do not follow you yet**; cut every 1.5 s through the montage so there is always
  something new. ([Dataslayer](https://www.dataslayer.ai/blog/instagram-algorithm-2025-complete-guide-for-marketers))
- **Safe zones.** Instagram covers the top, the bottom (caption and buttons, deeper since late 2025) and the right
  (like, comment, share). All text sits between y≈300 and y≈1460 and clear of the right edge, at 44–190 px.
  ([ClipSpeed](https://www.clipspeed.ai/blog/instagram-reels-captions.html), [Argil](https://argil.ai/blog/instagram-reel-size-e350f))
- **Original content and audio.** Reels need sound to be recommended, and reposted or watermarked content is pushed
  down; this reel is original footage with original music. Whether trending audio beats original audio is disputed,
  so there is also a version with only the sound effects, for trying a trending track from Instagram's library.
  ([Dataslayer](https://www.dataslayer.ai/blog/instagram-algorithm-2025-complete-guide-for-marketers),
  [Kontentino](https://www.kontentino.com/q-and-a/trending-audio-instagram-reach/),
  [ReelForge](https://reelforgeai.io/blog/instagram-reels-reach-collapse-q1-2026))
- **Minecraft short-form** that works shows builds with dramatic camera moves, reveals and fast cuts synced to the
  music. ([CapCut](https://www.capcut.com/resource/minecraft-youtube-shorts))

## Posting it

**Caption** (the first line is what shows; keywords help Instagram file the reel; one question invites comments):

```
Minecraft beaches were boring, so we filled them 🎣 Fisherman's Coast adds 7 places built for every kind of shore, Crab Pots that fish while you're AFK, and bottles with treasure maps. Which one are you building next to?

Free on CurseForge & Modrinth (link in bio). Fabric, NeoForge and Forge, Minecraft 1.20.1 to 26.3.

#minecraft #minecraftmods #moddedminecraft #minecraftbuilds #fabricmc
```

- Five hashtags at most; niche ones over generic ones.
- Set `cover.jpg` as the cover, so the grid shows the mod's name.
- Post the original-audio version first. To try a trending sound, post `fishermans-coast-reel-sfx-only.mp4` and add the
  track in Instagram at about 70 %, with the original sound at about 40 %: the cuts are on a 120 BPM grid.
- Optional: "Comment COAST and I'll DM you the link" works well if the account has an automatic DM reply set up.
- Reply to the first comments quickly, share the reel to the Story, and post the same file (without watermarks) to
  TikTok and YouTube Shorts.

## Rebuilding it

The footage comes from a 26.3 Fabric dev server and a client in a portrait window on its own X display:

```bash
Xvfb :2 -screen 0 1080x1920x24 &
sed -i 's/^level-name=.*/level-name=showcase/; s/^view-distance=.*/view-distance=12/' 26.3/fabric/runs/server/server.properties
rm -f 26.3/fabric/runs/server/config/fisherman_house.json        # the default config
tools/qa/devrun.sh start-server 26.3 fabric
DISPLAY=:2 QA_WIDTH=1080 QA_HEIGHT=1920 tools/qa/devrun.sh start-client 26.3 fabric
python3 tools/qa/rcon.py "op Builder"
python3 marketing/reel/capture.py --preview pier   # frame a shot: first, middle and last frame
python3 marketing/reel/capture.py                  # every clip into marketing/reel/build/frames/
marketing/reel/make.sh                             # audio, frames, MP4s
```

The world is `showcase` with the QA seed (`1928374655`), the client uses `fov:0.5` and `renderDistance:12` in
`26.3/fabric/runs/client/options.txt`. The client renders in software, far too slowly to record in real time, so
`capture.py` moves the camera along an eased path with `/tp`, steps the frozen world one tick and captures the display
for every frame: the camera moves are smooth whatever the frame rate. `edit.cjs` needs Playwright with Chromium,
`audio.py` needs numpy and scipy, `make.sh` needs ffmpeg.
