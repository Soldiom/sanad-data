#!/usr/bin/env python3
"""عناوين عربية كصور PNG شفافة — لا تستعمل drawtext مع العربية أبدًا.
الاستخدام: python3 captions.py caps.json /tmp/caps
caps.json = [{"a":0.2,"b":5.0,"t1":"العنوان","t2":"السطر الداعم"}, ...]"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont, features

W       = int(os.environ.get("CAP_W", 1080))
BOLD    = os.environ.get("FONT_BOLD",  "/tmp/IBMPlexSansArabic-Bold.ttf")
LIGHT   = os.environ.get("FONT_LIGHT", "/tmp/IBMPlexSansArabic-Light.ttf")
GOLD    = (228,199,102,255); WHITE=(225,230,238,255)
INK     = (8,11,18,225);     EDGE =(201,162,39,150)

if not features.check("raqm"):
    print("⚠️ RAQM غير متاح — قد ينكسر تشكيل العربية", file=sys.stderr)

def build(caps, out):
    os.makedirs(out, exist_ok=True)
    for i,c in enumerate(caps):
        im = Image.new("RGBA",(W,300),(0,0,0,0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([50,40,W-50,250],20,fill=INK,outline=EDGE,width=2)
        rows=[(c["t1"], ImageFont.truetype(BOLD,56), 78, GOLD)]
        if c.get("t2"): rows.append((c["t2"], ImageFont.truetype(LIGHT,38), 168, WHITE))
        for txt,f,y,col in rows:
            bb=d.textbbox((0,0),txt,font=f,direction="rtl",language="ar")
            d.text(((W-(bb[2]-bb[0]))//2-bb[0], y), txt, font=f, fill=col,
                   direction="rtl", language="ar")
        im.save(f"{out}/c{i}.png")
    json.dump([[c["a"],c["b"]] for c in caps], open(f"{out}/t.json","w"))
    print(f"✅ {len(caps)} عنوانًا → {out}")

if __name__=="__main__":
    build(json.load(open(sys.argv[1])), sys.argv[2] if len(sys.argv)>2 else "/tmp/caps")
