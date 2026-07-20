#!/usr/bin/env python3
"""صوت عربي عبر Chatterbox مع بذور متعدّدة وتحقّق تلقائي.
الاستخدام: python3 tts.py "النصّ المشكَّل" /tmp/ref.wav /tmp/vo.wav
يجرّب عدّة بذور ويحتفظ بأوّل ناتجٍ يجتاز التفريغ."""
import os, ssl, sys, shutil, subprocess
ssl._create_default_https_context = ssl._create_unverified_context
from gradio_client import Client, handle_file

TEXT = sys.argv[1]
REF  = sys.argv[2] if len(sys.argv)>2 else None
OUT  = sys.argv[3] if len(sys.argv)>3 else "/tmp/vo.wav"
SEEDS= [int(s) for s in os.environ.get("SEEDS","5,11,19").split(",")]
HERE = os.path.dirname(os.path.abspath(__file__))

if any(0x064B <= ord(c) <= 0x0652 for c in TEXT) is False:
    print("⚠️ النصّ بلا تشكيل — النطق سيكون تخمينيًّا. شكّله تشكيلًا كاملًا.", file=sys.stderr)

c = Client("ResembleAI/Chatterbox-Multilingual-TTS",
           token=os.environ.get("HF_TOKEN"), verbose=False)
for seed in SEEDS:
    try:
        kw = dict(text_input=TEXT, language_id="ar",
                  exaggeration_input=float(os.environ.get("EXAG",0.65)),
                  temperature_input=float(os.environ.get("TEMP",0.85)),
                  seed_num_input=seed,
                  cfgw_input=float(os.environ.get("CFG",0.45)),
                  api_name="/generate_tts_audio")
        if REF: kw["audio_prompt_path_input"] = handle_file(REF)
        r = c.predict(**kw)
        cand = f"/tmp/_tts_{seed}.wav"; shutil.copy(r, cand)
        ok = subprocess.run([sys.executable, f"{HERE}/verify_voice.py", cand, TEXT]).returncode==0
        print(f"seed={seed}: {'✅' if ok else '❌'}")
        if ok:
            shutil.copy(cand, OUT); print(f"✅ {OUT}"); sys.exit(0)
    except Exception as e:
        print(f"seed={seed}: ❌ {str(e)[:80]}")
print("⚠️ لم تجتز أيّ بذرة — أعد صياغة الكلمات المتعثّرة", file=sys.stderr)
sys.exit(1)
