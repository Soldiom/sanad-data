#!/usr/bin/env bash
# الأنبوب كاملًا. الاستخدام:
#   ./pipeline.sh <url> <beats.json> <caps.json> "<النصّ المشكَّل>" [ref.wav]
set -euo pipefail
URL="$1"; BEATS="$2"; CAPS="$3"; TEXT="${4:-}"; REF="${5:-}"
HERE="$(cd "$(dirname "$0")" && pwd)"
W=/tmp/reel-work; rm -rf "$W"; mkdir -p "$W"
export PATH="/tmp/npm-global/bin:$PATH"

echo "① تسجيل…"
node "$HERE/record.js" "$URL" "$W/vid" "$BEATS"
SRC=$(ls "$W"/vid/*.webm | head -1)

echo "② اقتطاع…"
i=0; : > "$W/cl.txt"
for seg in "${SEGMENTS:-3:5.5 11:6 28:5 48:5.5}"; do :; done
for seg in ${SEGMENTS:-3:5.5 11:6 28:5 48:5.5}; do
  ss="${seg%%:*}"; t="${seg##*:}"; i=$((i+1))
  ffmpeg -v error -y -i "$SRC" -ss "$ss" -t "$t" \
    -vf "scale=1080:1920:flags=lanczos,eq=saturation=1.06:contrast=1.03" \
    -c:v libx264 -crf 18 -pix_fmt yuv420p -r 30 "$W/q$i.mp4"
  echo "file '$W/q$i.mp4'" >> "$W/cl.txt"
done
ffmpeg -v error -y -f concat -safe 0 -i "$W/cl.txt" -c copy "$W/cut.mp4"

echo "③ عناوين…"
python3 "$HERE/captions.py" "$CAPS" "$W/caps"
N=$(python3 -c "import json;print(len(json.load(open('$W/caps/t.json'))))")
python3 "$HERE/build_filter.py" "$W/caps/t.json" "${FADE_AT:-21.3}" "${CAP_Y:-470}" > "$W/filt.txt"
CAP_ARGS=(); for ((k=0;k<N;k++)); do CAP_ARGS+=(-i "$W/caps/c$k.png"); done

if [ -n "$TEXT" ]; then
  echo "④ صوت + ⑤ تحقّق…"
  python3 "$HERE/tts.py" "$TEXT" "$REF" "$W/vo.wav"
  ffmpeg -v error -y -i "$W/vo.wav" \
    -af "adelay=680|680,apad=pad_dur=10,volume=1.2,highpass=f=85,lowpass=f=11000,acompressor=threshold=-18dB:ratio=3.2:attack=6:release=200,aresample=48000" \
    -t "${DUR:-22}" "$W/vo_p.wav"
  echo "⑥ تركيب…"
  ffmpeg -v error -y -i "$W/cut.mp4" "${CAP_ARGS[@]}" -i "$W/vo_p.wav" \
    -filter_complex "$(cat "$W/filt.txt")" -map "[vout]" -map "$((N+1)):a" -t "${DUR_V:-21.9}" \
    -c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p -r 30 \
    -c:a aac -b:a 192k -ar 48000 -movflags +faststart "${OUT:-/tmp/reel.mp4}"
  echo "⑦ تفريغ الناتج…"
  ffmpeg -v error -y -i "${OUT:-/tmp/reel.mp4}" -vn -ar 16000 -ac 1 "$W/final.wav"
  python3 "$HERE/verify_voice.py" "$W/final.wav" "$TEXT" || echo "⚠️ راجع النطق"
else
  echo "⑥ تركيب صامت…"
  ffmpeg -v error -y -i "$W/cut.mp4" "${CAP_ARGS[@]}" \
    -filter_complex "$(cat "$W/filt.txt")" -map "[vout]" -an -t "${DUR_V:-21.9}" \
    -c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p -r 30 -movflags +faststart "${OUT:-/tmp/reel.mp4}"
fi
echo "✅ ${OUT:-/tmp/reel.mp4}"
