#!/usr/bin/env python3
"""يفرّغ الصوت بـWhisper ويقارنه بالنصّ المتوقَّع + يقيس الإيقاع.
الاستخدام: python3 verify_voice.py /tmp/vo.wav "النصّ المتوقَّع"
يخرج 0 إذا نجح، 1 إذا فشل — صالح للاستخدام في شرط."""
import os, ssl, sys, re, warnings
warnings.filterwarnings("ignore")
ssl._create_default_https_context = ssl._create_unverified_context

AUDIO = sys.argv[1]
WANT  = sys.argv[2] if len(sys.argv)>2 else ""

AR_EQ = str.maketrans("أإآىة","ااايه")
def strip(s):
    s = re.sub(r"[\u064B-\u0652\u0640]", "", s)          # حركات وتطويل
    s = re.sub(r"[^\w\u0600-\u06FF ]+", " ", s)          # ترقيم عربي ولاتيني
    s = s.translate(AR_EQ)                                 # توحيد الهمزات والتاء
    return re.sub(r"\s+", " ", s).strip()

def pace(path):
    """مدّة الكلام وحده — تستبعد الصمت المضاف عند التركيب،
    وإلا بدا الإيقاع بطيئًا كذبًا في الملفّ النهائيّ الممدود."""
    import librosa, numpy as np
    y,sr = librosa.load(path, sr=22050)
    rms  = librosa.feature.rms(y=y, frame_length=1024, hop_length=256)[0]
    thr  = max(rms.max()*0.06, 0.008)
    speech = (rms > thr).sum() * 256 / sr
    return max(speech, 0.1), len(y)/sr

try:
    from gradio_client import Client, handle_file
    w = Client("openai/whisper", token=os.environ.get("HF_TOKEN"), verbose=False)
    heard = str(w.predict(handle_file(AUDIO), "transcribe", api_name="/predict")).strip()
except Exception as e:
    print(f"⚠️ تعذّر التحقّق: {str(e)[:90]}"); sys.exit(0)

print(f"🎧 المسموع: {heard[:170]}")
speech, total = pace(AUDIO)
nwords = len(strip(WANT).split()) or len(strip(heard).split())
wpm = nwords/speech*60 if speech else 0
tail = f" (من {total:.1f}s بالصمت)" if total-speech > 1.5 else ""
print(f"⏱ كلام {speech:.1f}s{tail} · {wpm:.0f} كلمة/دقيقة  {'✅' if 115<=wpm<=155 else '⚠️ خارج ١١٥–١٥٥'}")

if not WANT: sys.exit(0)
hw, ww = set(strip(heard).split()), strip(WANT).split()
def near(w_, pool):
    if w_ in pool: return True
    for h in pool:
        if abs(len(h)-len(w_))<=2 and sum(a==b for a,b in zip(h,w_))>=len(w_)*0.75:
            return True
    return False
missing = [w_ for w_ in ww if len(w_)>3 and not near(w_,hw)]
if missing:
    print(f"❌ كلمات لم تُنطق كما كُتبت: {', '.join(missing[:8])}")
    print("   الحل: شكّل الكلمة تشكيلًا كاملًا، أو استبدلها بمرادف، ثم أعد التوليد ببذرة أخرى.")
    sys.exit(1)
print("✅ النطق مطابق")
