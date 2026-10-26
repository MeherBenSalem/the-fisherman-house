#!/usr/bin/env bash
# Builds the reel from the narration and the captured footage (see README.md): audio, frames, then the two MP4s.
#   marketing/reel/make.sh            # everything
#   marketing/reel/make.sh encode     # only re-encode (after audio.py or edit.cjs ran)
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"
if [ "${1:-}" != encode ]; then
  python3 audio.py
  rm -rf build/out
  NODE_PATH="${NODE_PATH:-$(npm root -g)}" node edit.cjs
fi

# H.264 High, 1080x1920, 30 fps, BT.709, AAC 48 kHz, loudness -14 LUFS (the level Instagram plays at) with peaks under
# -1.5 dBFS after AAC encoding (the limiter sits lower, as AAC overshoots a little), fast start.
encode() {  # audio wav, output mp4
  ffmpeg -hide_banner -loglevel error -y -framerate 30 -i build/out/%05d.jpg -i "$1" -map 0:v -map 1:a \
    -c:v libx264 -preset slow -crf 21 -maxrate 10M -bufsize 20M -pix_fmt yuv420p -profile:v high -level 4.2 -g 30 \
    -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
    -af loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.75:level=false \
    -c:a aac -b:a 192k -ar 48000 -movflags +faststart -shortest "$2"
  echo "wrote $2 ($(du -h "$2" | cut -f1))"
}
encode build/mix.wav fishermans-coast-reel.mp4                 # narration, music bed, effects
encode build/voice_sfx.wav fishermans-coast-reel-no-music.mp4  # narration and effects, to add a track in Instagram
# The cover (the frame shown on the profile grid): the title over the lighthouse at sunset, once it is fully in.
frame=$(python3 -c "import json; t = json.load(open('timeline.json')); print(round((t['sentences']['s03'] + 0.8) * 30))")
cp "build/out/$(printf '%05d' "$frame").jpg" cover.jpg
echo "wrote cover.jpg (frame $frame)"
