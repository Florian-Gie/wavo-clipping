"""Transkribiert ein Video mit Wort-Zeitstempeln und legt einen Kontaktbogen an.

Aufruf: python transkribieren.py clipping/input/video.mp4 [--sprache de]
Ergebnis: clipping/work/<name>.txt, <name>.json, <name>_sheet.jpg
"""
import sys as _sys; _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import json
import os
import subprocess
import sys

from faster_whisper import WhisperModel

if len(sys.argv) < 2:
    sys.exit("Aufruf: python transkribieren.py <video> [--sprache de]")
src = sys.argv[1]
sprache = sys.argv[sys.argv.index("--sprache") + 1] if "--sprache" in sys.argv else None
name = os.path.splitext(os.path.basename(src))[0]
work = os.path.join("clipping", "work")
os.makedirs(work, exist_ok=True)

print("Lade Spracherkennung (beim ersten Mal wird das Modell heruntergeladen) ...", flush=True)
model = WhisperModel("small", device="cpu", compute_type="int8")
segs, info = model.transcribe(src, word_timestamps=True, language=sprache, vad_filter=True)
print(f"Sprache: {info.language}, Länge: {info.duration / 60:.1f} min", flush=True)

out, zeilen = [], []
for s in segs:
    out.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(),
                "words": [{"w": w.word, "s": round(w.start, 2), "e": round(w.end, 2)} for w in (s.words or [])]})
    zeilen.append(f"[{s.start:8.2f}-{s.end:8.2f}] {s.text.strip()}")
    if len(out) % 50 == 0:
        print(f"  ... {s.end / 60:.1f} min transkribiert", flush=True)

with open(os.path.join(work, f"{name}.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
with open(os.path.join(work, f"{name}.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(zeilen))

dauer = info.duration or 60
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf",
                f"fps=24/{dauer:.2f},scale=320:-2,tile=6x4:padding=3:color=white", "-frames:v", "1",
                os.path.join(work, f"{name}_sheet.jpg")], check=False)
print(f"Fertig: {work}/{name}.txt ({len(out)} Abschnitte)")
