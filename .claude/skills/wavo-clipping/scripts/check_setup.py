"""Prüft, ob alles für Wavo Clipping installiert ist, und zeigt sonst die Befehle zum Installieren."""
import sys as _sys; _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import importlib.util
import platform
import shutil
import sys

system = platform.system()
fehlt = []

if sys.version_info < (3, 9):
    print(f"Python {sys.version.split()[0]} ist zu alt, mindestens 3.9 nötig.")
    fehlt.append("python")

for tool in ("ffmpeg", "ffprobe", "yt-dlp"):
    if shutil.which(tool):
        print(f"OK      {tool}")
    else:
        print(f"FEHLT   {tool}")
        fehlt.append(tool)

for modul, paket in (("faster_whisper", "faster-whisper"), ("PIL", "pillow")):
    if importlib.util.find_spec(modul):
        print(f"OK      {paket} (Python)")
    else:
        print(f"FEHLT   {paket} (Python)")
        fehlt.append(paket)

if not fehlt:
    print("\nAlles bereit.")
    sys.exit(0)

print("\nSo installierst du, was fehlt:")
pip = [p for p in fehlt if p in ("faster-whisper", "pillow")]
tools = [t for t in fehlt if t in ("ffmpeg", "ffprobe", "yt-dlp")]
if tools:
    if system == "Windows":
        if "ffmpeg" in tools or "ffprobe" in tools:
            print("  winget install --id Gyan.FFmpeg -e")
        if "yt-dlp" in tools:
            print("  winget install --id yt-dlp.yt-dlp -e")
        print("  (Danach Claude Code bzw. das Terminal neu starten, damit die Befehle gefunden werden.)")
    elif system == "Darwin":
        print("  brew install " + " ".join(sorted({"ffmpeg" if t != "yt-dlp" else "yt-dlp" for t in tools})))
        print("  (Homebrew fehlt? Anleitung: https://brew.sh)")
    else:
        print("  sudo apt install ffmpeg && python3 -m pip install -U yt-dlp")
if pip:
    print(f"  {sys.executable} -m pip install -U " + " ".join(pip))
sys.exit(1)
