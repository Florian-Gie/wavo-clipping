"""Rendert Clips im Wavo-Stil: 1080x1920, Video mittig, unscharfer Hintergrund, weiße Überschrift-Box.

Aufruf: python render_clip.py clip1.json [clip2.json ...]
JSON: {"src", "start", "end", "headline", "out"} + optional "quote", "cx" (0-1), "logo", "logo_pos"
Pfade sind relativ zum aktuellen Ordner.
"""
import sys as _sys; _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import json
import os
import platform
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(SKILL, "assets", "fonts", "TikTokSans-SemiBold.ttf")
FONT_Q = os.path.join(SKILL, "assets", "fonts", "TikTokSans-Medium.ttf")
W, H = 1080, 1920
FG_H, FG_Y = 1200, 400          # Vordergrund-Ausschnitt
HEAD_SIZE, HEAD_MAXW = 54, 900
QUOTE_SIZE = 36

EMOJI_KANDIDATEN = {
    "Windows": ["C:/Windows/Fonts/seguiemj.ttf"],
    "Darwin": ["/System/Library/Fonts/Apple Color Emoji.ttc"],
    "Linux": ["/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", "/usr/share/fonts/noto/NotoColorEmoji.ttf"],
}


def lade_emoji_font():
    for pfad in EMOJI_KANDIDATEN.get(platform.system(), []):
        if not os.path.exists(pfad):
            continue
        for groesse in (64, 109, 160, 137, 96, 48):
            try:
                f = ImageFont.truetype(pfad, groesse)
                f.getbbox("😳")
                return f
            except OSError:
                continue
    return None


EFONT = lade_emoji_font()


def ist_emoji(ch):
    return ord(ch) >= 0x2190 and ch not in "–—„“”‚‘’…"


def emoji_bild(ch, ziel):
    """Emoji in Originalgröße der Schrift zeichnen und auf Zielhöhe skalieren (nötig für Farb-Emoji-Fonts)."""
    s = EFONT.size
    img = Image.new("RGBA", (int(s * 1.4), int(s * 1.4)), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((0, 0), ch, font=EFONT, embedded_color=True)
    bbox = img.getbbox()
    if not bbox:
        return None
    img = img.crop(bbox)
    f = ziel / img.height
    return img.resize((max(1, int(img.width * f)), ziel), Image.LANCZOS)


def bereinigen(text):
    return text if EFONT else "".join(ch for ch in text if not ist_emoji(ch)).strip()


def breite(font, s):
    return sum(font.size * 1.05 if ist_emoji(ch) else font.getlength(ch) for ch in s)


def umbrechen(font, text, maxw):
    worte = text.split()
    for n in range(1, 6):
        bestes = None

        def teile(i, k):
            if k == 1:
                yield [worte[i:]]
                return
            for j in range(i + 1, len(worte) - k + 2):
                for rest in teile(j, k - 1):
                    yield [worte[i:j]] + rest
        if n > len(worte):
            break
        for parts in teile(0, n):
            zeilen = [" ".join(p) for p in parts]
            ws = [breite(font, z) for z in zeilen]
            if max(ws) > maxw:
                continue
            score = max(ws) - min(ws)
            if bestes is None or score < bestes[0]:
                bestes = (score, zeilen)
        if bestes:
            return bestes[1]
    return [text]


def zeichne(img, d, x, y, s, font, farbe):
    for ch in s:
        if ist_emoji(ch):
            e = emoji_bild(ch, int(font.size * 0.95))
            if e:
                img.alpha_composite(e, (int(x + 3), int(y + font.size * 0.08)))
            x += font.size * 1.05
        else:
            d.text((x, y), ch, font=font, fill=farbe)
            x += font.getlength(ch)


def ueberschrift_png(text, pfad):
    font = ImageFont.truetype(FONT, HEAD_SIZE)
    zeilen = umbrechen(font, bereinigen(text), HEAD_MAXW)
    lh, padx, pady, rad = int(HEAD_SIZE * 1.18), 18, 8, 16
    img = Image.new("RGBA", (W, lh * len(zeilen) + 2 * pady + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ws = [breite(font, z) for z in zeilen]
    for k, w in enumerate(ws):
        x0 = (W - w) / 2 - padx
        d.rounded_rectangle([x0, k * lh, x0 + w + 2 * padx, k * lh + lh + 2 * pady], rad, fill=(255, 255, 255, 255))
    bb = font.getbbox("HxgyÄ")
    cap = bb[3] - bb[1]
    for k, (z, w) in enumerate(zip(zeilen, ws)):
        zeichne(img, d, (W - w) / 2, k * lh + (lh + 2 * pady - cap) / 2 - bb[1], z, font, (0, 0, 0, 255))
    img.save(pfad)
    return img.size[1]


def zitat_png(text, pfad):
    font = ImageFont.truetype(FONT_Q, QUOTE_SIZE)
    zeilen = umbrechen(font, bereinigen(text), 860)
    lh = int(QUOTE_SIZE * 1.25)
    img = Image.new("RGBA", (W, lh * len(zeilen) + 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for k, z in enumerate(zeilen):
        d.text(((W - font.getlength(z)) / 2, k * lh + 4), z, font=font, fill="white", stroke_width=3, stroke_fill="black")
    img.save(pfad)
    return img.size[1]


def groesse(src):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=width,height", "-of", "csv=p=0", src], text=True)
    return tuple(map(int, out.strip().split(",")[:2]))


def hat_ton(src):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                                   "stream=index", "-of", "csv=p=0", src], text=True)
    return bool(out.strip())


def render(cfg):
    src, out = cfg["src"], cfg["out"]
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    work = os.path.join("clipping", "work")
    os.makedirs(work, exist_ok=True)
    s, e = float(cfg["start"]), float(cfg["end"])
    dur = e - s
    sw, sh = groesse(src)
    name = os.path.splitext(os.path.basename(out))[0]

    kopf = os.path.join(work, f"{name}_kopf.png")
    hh = ueberschrift_png(cfg["headline"], kopf)
    inputs = ["-ss", f"{s:.3f}", "-t", f"{dur:.3f}", "-i", src, "-loop", "1", "-i", kopf]
    n = 2
    zitat_idx = logo_idx = None
    if cfg.get("quote"):
        zitat = os.path.join(work, f"{name}_zitat.png")
        qh = zitat_png(cfg["quote"], zitat)
        inputs += ["-loop", "1", "-i", zitat]
        zitat_idx, n = n, n + 1
    if cfg.get("logo"):
        inputs += ["-loop", "1", "-i", cfg["logo"]]
        logo_idx, n = n, n + 1

    # Vordergrund: Ausschnitt mit Seitenverhältnis 1080:1200 um cx herum (bei Hochformat-Quellen ganze Breite)
    crop_w = min(sw, round(sh * W / FG_H))
    crop_h = min(sh, round(crop_w * FG_H / W))
    cx = float(cfg.get("cx", 0.5))
    x0 = int(max(0, min(sw - crop_w, cx * sw - crop_w / 2)))
    y0 = int((sh - crop_h) / 2)
    kopf_y = FG_Y - hh // 2 - 10

    fc = ["[0:v]fps=30,split=2[a][b]",
          f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40:3,eq=brightness=-0.04[bg]",
          f"[b]crop={crop_w}:{crop_h}:{x0}:{y0},scale={W}:{FG_H}[fg]",
          f"[bg][fg]overlay=0:{FG_Y}[v0]",
          f"[v0][1:v]overlay=0:{kopf_y}:shortest=1[v1]"]
    letzte = "v1"
    if zitat_idx is not None:
        fc.append(f"[{letzte}][{zitat_idx}:v]overlay=0:{kopf_y - qh - 4}:shortest=1[v2]")
        letzte = "v2"
    if logo_idx is not None:
        pos = {"oben-links": "40:40", "oben-rechts": "W-w-40:40", "unten-links": f"40:{FG_Y + FG_H - 40}-h",
               "unten-rechts": f"W-w-40:{FG_Y + FG_H - 40}-h"}.get(cfg.get("logo_pos", "oben-rechts"), "W-w-40:40")
        fc.append(f"[{logo_idx}:v]scale=220:-1[lg]")
        fc.append(f"[{letzte}][lg]overlay={pos}:shortest=1[v3]")
        letzte = "v3"
    fc.append(f"[{letzte}]format=yuv420p[vout]")

    karte = ["-map", "[vout]"]
    if hat_ton(src):
        fc.append(f"[0:a]loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=out:st={max(dur - 0.25, 0):.2f}:d=0.25[aout]")
        karte += ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"]

    cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), *karte, "-t", f"{dur:.3f}",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", "30", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print("OK", out, flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Aufruf: python render_clip.py clip1.json [clip2.json ...]")
    if not EFONT:
        print("Hinweis: Keine Emoji-Schrift gefunden, Emojis werden weggelassen.")
    for p in sys.argv[1:]:
        with open(p, encoding="utf-8") as f:
            render(json.load(f))
