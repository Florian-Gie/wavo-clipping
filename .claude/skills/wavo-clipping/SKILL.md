---
name: wavo-clipping
description: Macht aus einem langen Video (YouTube, Twitch, Kick, Datei) fertige Kurzclips für TikTok, Reels und Shorts – im Hochformat mit weißer Überschrift-Box im TikTok-Stil und Caption pro Clip. Lädt das Video, transkribiert es, schlägt die besten Stellen vor, wartet auf Freigabe und rendert dann. Hält sich an das Briefing einer Clipping-Kampagne (Pflicht-Caption, Hashtags, Logo, Länge). Auslöser - "mach Clips aus diesem Video", "clippe das", "wavo clipping", "Kampagne clippen", ein Video-Link mit der Bitte um Clips.
---

# Wavo Clipping

Du machst aus einem langen Video fertige Kurzclips. Antworte auf Deutsch, in der du-Form, kurz und verständlich – der Nutzer ist oft Anfänger.

Alle Skripte liegen in `scripts/` neben dieser Datei. Rufe sie mit vollem Pfad auf (`<SKILL_DIR>/scripts/...`). Arbeitsordner ist der Ordner, in dem der Nutzer Claude Code gestartet hat.

## Ablauf

### 1. Einrichtung prüfen (immer zuerst)
```
python <SKILL_DIR>/scripts/check_setup.py
```
Fehlt etwas, zeigt das Skript die Befehle zum Installieren. Erkläre dem Nutzer in einem Satz, was fehlt, und führe die Installation nach seinem Okay aus. Danach erneut prüfen.

### 2. Briefing klären
Frag nach, falls nicht schon genannt:
- Link oder Datei des Videos (nur Material aus der Kampagne!)
- Pflicht-Caption, Pflicht-Hashtags, Pflicht-Text oder Logo auf dem Clip
- Länge (Standard: 20–60 Sekunden), Sprache der Überschriften (Standard: Sprache des Videos)
- Wie viele Clips (Standard: so viele gute Stellen wie es gibt, mindestens 5)

Wenn der Nutzer das Briefing nicht hat, mach mit den Standards weiter und sag ihm, dass er das Briefing der Kampagne prüfen muss.

### 3. Video laden
```
yt-dlp -f "bv*[height<=1080]+ba/b[height<=1080]" --merge-output-format mp4 -o "clipping/input/%(title).60s.%(ext)s" "<LINK>"
```
Bei einer lokalen Datei: nach `clipping/input/` kopieren.

### 4. Transkribieren
```
python <SKILL_DIR>/scripts/transkribieren.py "clipping/input/<datei>.mp4"
```
Erzeugt `clipping/work/<name>.txt` (Zeitstempel + Text) und `.json` (Wort-Zeitstempel). Bei langen Videos dauert das einige Minuten – sag dem Nutzer Bescheid.

### 5. Stellen auswählen
Lies das Transkript und such die stärksten Momente:
- lustige Momente, starke Reaktionen, einprägsame Zitate, krasse Zahlen oder Aussagen
- jeder Clip muss **für sich verständlich** sein (keine Bezüge auf vorher Gesagtes)
- **sauberer Anfang** (mitten im spannenden Satz starten ist okay, nicht mitten im Wort) und **sauberes Ende** (Satzende) – nutze die Wort-Zeitstempel aus der JSON
- Länge laut Briefing, sonst 20–60 s
- Stellen mit Hintergrundmusik weglassen
- lieber mehr Clips als zu wenig

Zu jedem Clip eine **Überschrift** für die weiße Box: clickbaitig, aber korrekt, 1–3 SCHLÜSSELWÖRTER IN CAPS, am Ende ein 😳. Beispiel: „He says he LOST 2 MILLION in ONE day 😳“. Optional eine kurze **Zitatzeile** (das stärkste Zitat in Klammern).

### 6. Übersicht zeigen und WARTEN
Zeig eine Tabelle: Nr · Start–Ende · Länge · Worum es geht · Überschrift.
**Rendere nichts, bevor der Nutzer zugestimmt hat.** Er darf Clips streichen oder Überschriften ändern.

### 7. Rendern
Für jeden freigegebenen Clip eine JSON-Datei in `clipping/clips/<name>_NN.json` schreiben:
```json
{
  "src": "clipping/input/<datei>.mp4",
  "start": 123.40, "end": 158.20,
  "headline": "He says he LOST 2 MILLION in ONE day 😳",
  "quote": "(I didn't sleep for a week)",
  "logo": "clipping/assets/logo.png",
  "logo_pos": "oben-rechts",
  "out": "clipping/output/<projekt>/<name>_NN.mp4"
}
```
`quote`, `logo`, `logo_pos` (oben-links/oben-rechts/unten-links/unten-rechts) und `cx` (Bildmitte der Person, 0–1, Standard 0.5) sind optional. Dann:
```
python <SKILL_DIR>/scripts/render_clip.py clipping/clips/<name>_01.json clipping/clips/<name>_02.json ...
```
Ist die Person nicht mittig im Bild, schau dir das Vorschaubild `clipping/work/<name>_sheet.jpg` an und setz `cx` passend (z. B. 0.3 für links).

### 8. Captions
Pro Clip eine Datei `<name>_NN_caption.txt` neben dem Video: kurze Caption in der Sprache der Zielgruppe, passende Hashtags und **alle Pflicht-Angaben aus dem Briefing** (Pflicht-Caption, @-Erwähnungen, Hashtags, ggf. Werbekennzeichnung).

### 9. Abschluss
Sag dem Nutzer, in welchem Ordner die Clips liegen, und erinnere ihn kurz an:
- Clip aufs Handy schicken und vom **aufgewärmten** Account posten
- Caption aus der `_caption.txt` übernehmen
- Link bei Content Rewards einreichen

## Stil der Clips (fest eingebaut)
1080×1920, Video als großer Ausschnitt in der Mitte, oben und unten dasselbe Video stark unscharf, weiße Überschrift-Boxen im TikTok-Stil (Schrift TikTok Sans, OFL), optional Zitatzeile darüber. Keine Untertitel, keine Musik, keine Zooms, keine Effekte – außer das Briefing verlangt etwas anderes.

## Regeln
- Nur Material clippen, für das es eine Kampagne gibt. Keine fremden Videos ohne Erlaubnis.
- Nie Logos oder Wasserzeichen der Kampagne entfernen, wenn das Briefing sie verlangt.
- Nicht spiegeln oder verfremden, um Erkennung zu umgehen.
- Keine erfundenen Aussagen in Überschriften.
