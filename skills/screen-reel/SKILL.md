---
name: screen-reel
description: Record a real website into a vertical 9:16 social reel with human-like scrolling, correctly-shaped Arabic captions, and an optional Arabic voiceover that is machine-verified before use. Trigger whenever the user asks to record a screen, capture a site, make a reel/short/story/TikTok/Instagram video from a webpage, add an Arabic voiceover to a video, or produce a promo clip for a web app — even if they don't say "reel". Also use when a previously made recording looks robotic, is framed wrong, or has mispronounced Arabic.
---

# Screen Reel

Turn a live website into a publishable vertical video. Every stage has a failure mode that is invisible until you inspect the output — so this skill measures instead of assuming.

## Pipeline

```
① record   Playwright, human-easing scroll  → webm
② cut      pick the strong beats            → mp4 segments
③ caption  Arabic text → PNG overlays       → transparent strips
④ voice    Chatterbox TTS (fully vocalized) → wav
⑤ verify   Whisper transcribes it back      → pass or regenerate
⑥ compose  ffmpeg overlay + audio           → final mp4
```

## Setup

```bash
export NPM_CONFIG_PREFIX=/tmp/npm-global && export PATH="/tmp/npm-global/bin:$PATH"
npm i -g playwright && npx playwright install chromium --with-deps
pip install -q --break-system-packages gradio_client librosa
```
`ffmpeg` is normally preinstalled — confirm with `which ffmpeg`.

## Quick path

```bash
scripts/pipeline.sh https://example.com beats.json caps.json "النصُّ المُشكَّل" ref.wav
```
Runs all six stages and the final transcription check. Omit the text for a silent reel.
Env overrides: `SEGMENTS` `DUR` `CAP_Y` `FADE_AT` `OUT` `SEEDS` `EXAG` `TEMP` `CFG`.

## ① Record

**The framing trap:** if `viewport` and `recordVideo.size` differ, the page renders at viewport size in the corner of a larger canvas and fills only a fraction of the frame. Keep them identical and upscale later.

```js
viewport:    {width:540, height:960},
recordVideo: {dir:'/tmp/vid', size:{width:540, height:960}}   // ← must match
```

Then in ffmpeg: `scale=1080:1920:flags=lanczos`.

Use `scripts/record.js`. It scrolls with `easeInOutCubic` over 24–32 steps, inserts variable pauses, and adds a ~9% chance of a brief hesitation — mechanical `behavior:'smooth'` reads as a bot.

Record generously (60–90s) and cut the good parts. Choreograph beats, don't just scroll: land on an element → let it glow → zoom the detail in stages (1.5 → 2.0 → 2.4), never one jump.

## ② Cut

```bash
enc() { ffmpeg -v error -y -i "$SRC" -ss "$1" -t "$2" \
  -vf "scale=1080:1920:flags=lanczos,eq=saturation=1.06:contrast=1.03" \
  -c:v libx264 -crf 18 -pix_fmt yuv420p -r 30 "/tmp/$3.mp4"; }
enc 3 5.5 q1; enc 11 6 q2; enc 28 5 q3; enc 48 5.5 q4
printf "file '/tmp/q1.mp4'\nfile '/tmp/q2.mp4'\n..." > /tmp/cl.txt
ffmpeg -v error -y -f concat -safe 0 -i /tmp/cl.txt -c copy /tmp/cut.mp4
```

Verify coverage before continuing — see `references/verify.md`.

## ③ Captions

**Never use ffmpeg `drawtext` for Arabic** — it renders letters unjoined and reversed. Render each caption to a transparent PNG with Pillow using `direction="rtl", language="ar"` (Pillow ≥10 with RAQM), then `overlay`.

Do **not** pre-process with `arabic_reshaper` + `python-bidi` when RAQM is present — double-shaping breaks the text. Check with `PIL.features.check('raqm')`.

Use `scripts/captions.py`. Keep captions in the safe zone: `overlay=0:H-470` and nothing below `H-170`, or Instagram's UI covers them.

## ④ Voice

Chatterbox Multilingual (`ResembleAI/Chatterbox-Multilingual-TTS`, `language_id="ar"`) with an 8-second reference clip for timbre.

**Fully vocalize the Arabic.** A bare `خبرٍ` was read as `خِبْرة`; `خَبَرٍ` reads correctly. Partial diacritics are worse than none — they mislead. Full vocalization also *raised* pitch variance ~22% because the model stopped hedging.

Tuning that measured best: `exaggeration 0.65 · temperature 0.85 · cfg 0.45`.

Seeds differ materially — one truncated the script after four words. Generate 2–3 seeds and pick by verification, not by faith.

## ⑤ Verify — do not skip

Transcribe the generated audio with Whisper and diff against the script. Three separate mispronunciations survived listening-by-assumption in one session (`يشتغل→يشترل`, `بَنَيْتُ→بُنيب`, `خَبَر→خِبْرة`).

```bash
python3 scripts/verify_voice.py /tmp/vo.wav "النصّ المتوقَّع"
```

Fails → reword the offending word (a synonym often fixes it: `يشتغل` → `يعمل`), regenerate, verify again.

Also measure pace: **120–150 words/minute** is natural Arabic news delivery. Below ~110 sounds dragged. This metric ruled out an alternative model that scored well on cleanliness but spoke at 58 wpm.

## ⑥ Compose

```bash
ffmpeg -y -i /tmp/cut.mp4 -i c0.png -i c1.png -i c2.png -i c3.png -i /tmp/vo.wav \
  -filter_complex "$(cat /tmp/filt.txt)" -map "[vout]" -map 5:a -t 21.9 \
  -c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p -r 30 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart /tmp/reel.mp4
```

Audio input index = number of PNGs + 1. Miscounting yields `Failed to set value 'N:a' for option 'map'`.

Build the filter graph with `scripts/build_filter.py`.

## Final check

Extract the finished video's own audio and transcribe *that* — it catches errors introduced during composition, not just generation.

```bash
ffmpeg -v error -y -i /tmp/reel.mp4 -vn -ar 16000 -ac 1 /tmp/final.wav
python3 scripts/verify_voice.py /tmp/final.wav "النصّ المتوقَّع"
```

## Targets

| | |
|---|---|
| Resolution | 1080×1920 |
| Duration | 15–25s |
| Page coverage | ≥ 85% of frame width |
| Pace | 120–150 wpm |
| Bottom safe zone | no ink in last 170px |
| Size | < 5 MB |

## When there's no voice

A silent reel is legitimate — most reels are watched muted, and captions carry the message. Prefer silence over a voice that fails verification. The user's own 8-second recording, cloned through Chatterbox, beats any synthetic default.
