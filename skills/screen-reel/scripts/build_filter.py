#!/usr/bin/env python3
"""يبني سلسلة مرشّحات ffmpeg من توقيتات العناوين.
الاستخدام: python3 build_filter.py /tmp/caps/t.json [مدة_التلاشي] > filt.txt
تذكير: مؤشّر الصوت في ffmpeg = عدد صور العناوين + 1."""
import json, sys
t   = json.load(open(sys.argv[1]))
end = float(sys.argv[2]) if len(sys.argv)>2 else 21.3
Y   = int(sys.argv[3]) if len(sys.argv)>3 else 470       # ارتفاع العنوان من الأسفل
pre = ";".join(f"[{i+1}:v]format=rgba[c{i}]" for i in range(len(t)))
ch, prev = "[0:v]setsar=1[v0]", "v0"
for i,(a,b) in enumerate(t):
    o=f"v{i+1}"
    ch += f";[{prev}][c{i}]overlay=0:H-{Y}:enable='between(t,{a},{b})'[{o}]"
    prev=o
print(f"{pre};{ch};[{prev}]fade=t=in:st=0:d=0.4,fade=t=out:st={end}:d=0.6[vout]")
