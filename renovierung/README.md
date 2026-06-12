# Projekt: Zimmer-Renovierung — 3D-Modell aus Video

**Für die KI-Session, die das hier liest (Claude / Fable 5):** Dieses Dokument ist deine vollständige Arbeitsanweisung. Arbeite so autonom wie möglich und frag nur nach, wenn du wirklich blockiert bist. Es existiert außerdem eine **`LOG.md`** im selben Drive-Ordner mit dem kompletten bisherigen Chatverlauf — bei Unklarheiten zuerst dort nachlesen, bevor du den User fragst.

---

## 1. Ziel

Aus einem Handyvideo des Zimmers (mit gesprochenen Anmerkungen) eine digitale 3D-Kopie bauen und für die Renovierungsplanung nutzen (Möbel umstellen, Varianten durchspielen). Genauigkeit: Proportionen und Layout zählen, Farben/Details von Kleidung etc. sind egal. Reale Maße hat der User geliefert (siehe `renovierung/masse.md` im Repo — das ist die **Quelle der Wahrheit** für alle Maße).

## 2. Wo liegt was

| Was | Wo |
|---|---|
| Code & Modell | GitHub-Repo `dimitrisakritidis/dimitrisakritidis.github.io`, Branch **`claude/3d-room-video-model-tdxrqq`** |
| 3D-Modell (Three.js, interaktiv) | `renovierung/index.html` |
| Alle Maße + offene Punkte | `renovierung/masse.md` |
| 2D-Grundriss (generiert) | `renovierung/grundriss.py` → `grundriss.png` |
| Video | `IMG_6971.MOV` (1,4 GB) im Drive-Ordner „Claude Renovierung" — **per Drive-MCP NICHT herunterladbar** (Base64-Limit). Transferweg: GitHub-Release (siehe §5) |
| Chatverlauf bisher | `LOG.md` im selben Drive-Ordner |

## 3. Raum-Konvention (wichtig, überall einheitlich)

Wände im Uhrzeigersinn: **A** (lang, 414 cm, Bett/Kleiderstangen) → **B** (kurz, 300 cm, Schrank/Regal) → **C** (lang, mit Tür) → **D** (kurz, mit Fenster). Schacht 15×48 cm in Ecke A/B. Deckenhöhe **292 cm** (gemessen). Koordinaten: x entlang Wand A (0 = Ecke D/A), y/z von Wand A Richtung Wand C, Höhe nach oben. Details in `masse.md`.

## 4. Umgebung einrichten (Cloud-Session)

Die Netzwerk-Policy lässt nur bestimmte Hosts zu. **Getestet am 12.06.2026:**

- ✅ erlaubt: `pypi.org` (pip), `github.com`, `raw.githubusercontent.com`, GitHub-Release-Downloads
- ❌ blockiert: `huggingface.co`, `openaipublic.azureedge.net`, `cdn.jsdelivr.net`, `drive.google.com` (Direktdownload), `api.github.com` (stattdessen GitHub-MCP-Tools nutzen!)

Setup-Befehle (funktionieren nachweislich):

```bash
pip install imageio-ffmpeg opencv-python-headless sherpa-onnx
mkdir -p /home/user/asr && cd /home/user/asr
curl -sL -O https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.tar.bz2
tar xjf sherpa-onnx-whisper-small.tar.bz2 && rm sherpa-onnx-whisper-small.tar.bz2
curl -sL -O https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx
```

ffmpeg-Binary danach: `python3 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"`

## 5. Video beschaffen

1,4 GB sind durch den Drive-MCP nicht übertragbar. Stattdessen lädt der User das Video als **GitHub-Release-Asset** hoch (Repo → Releases → Draft a new release → Tag z.B. `video` → Datei anhängen → Publish). Prüfen, ob schon vorhanden: Release-Seite `https://github.com/dimitrisakritidis/dimitrisakritidis.github.io/releases` per curl abrufen (HTML), `expanded_assets`-Fragmente auflösen, nach `releases/download/...MOV|mp4` greppen — oder GitHub-MCP `list_releases`. Download des Assets per curl funktioniert.

Falls noch kein Release existiert: User erinnern (Schritte oben nennen), währenddessen mit allem weiterarbeiten, was ohne Video geht, und einen Monitor (Polling ~90 s auf die Release-Seite) bewaffnen, der dich weckt.

## 6. Pipeline (sobald Video da ist)

1. **Audio extrahieren:** `ffmpeg -i video.MOV -ac 1 -ar 16000 audio.wav`
2. **Segmentieren + transkribieren:** Silero-VAD (Sprech-Segmente mit Start/Ende in Sekunden) → jedes Segment einzeln durch sherpa-onnx-Whisper (`language="de"`, `task="transcribe"`, int8-Modelle). Ergebnis: Transkript mit Zeitstempeln. **Wichtig:** Whisper hier liefert keine Wort-Zeitstempel — die Zeiten kommen aus den VAD-Segmenten.
3. **Frames ziehen:** (a) an jedem Transkript-Zeitstempel gezielt 2–3 Frames, (b) zusätzlich grobes Raster alle 1–2 s über das ganze Video. Frames mit dem Read-Tool als Bilder ansehen.
4. **Abgleichen:** Offene Punkte aus `masse.md` (Fensterhöhe, Kommoden-Anzahl/-Positionen, Bett-Grundfläche/-Position, IKEA-Regal B/H, Klimmzugstange, Heizkörper/Steckdosen) aus den Frames klären; gesprochene Anweisungen aus dem Transkript umsetzen.
5. **Modell updaten:** `renovierung/index.html` (Three.js) und `grundriss.py` korrigieren, `masse.md` fortschreiben, Annahmen-Markierungen (orange) entfernen, sobald bestätigt.
6. **Committen & pushen** auf den Branch (Maße-Quelle immer mit aktualisieren).

## 7. Arbeitsregeln

- Sprache mit dem User: **Deutsch**, locker, ehrlich bei Einschätzungen.
- Autonom arbeiten, erst handeln, dann berichten. Nur bei echten Richtungsentscheidungen fragen.
- **Keinen Pull Request** erstellen, außer der User verlangt es explizit. Nur auf den o.g. Branch pushen.
- Annahmen immer sichtbar kennzeichnen (im 3D-Modell orange, in `masse.md` als „Annahme").
- Maße: ±10–20 % Toleranz bei reiner Video-Schätzung; alles Wichtige am realen Maß des Users kalibrieren.
- Toleranz-Check der Planung bisher: Kleiderstangen auf 270 cm, Decke 292 cm, Bett 160 cm + 100 cm Luft = 260 ✓.

## 8. Renovierungswünsche des Users (Stand 12.06.2026)

1. Großer weißer Schrank (100×65×237) an Wand B verschieben, rechts daneben 10–20 cm Spalt für Besen/Handfeger + 2 kleine Regale für Werkzeugkoffer.
2. **2 Kleiderstangen nebeneinander** (nicht untereinander) auf **270 cm** Höhe übers Bett, direkt links neben der Klimmzugstange.
3. Klimmzugstange von diagonal auf **parallel zur Wand** versetzen.
4. User erreicht ohne Hilfe 240 cm; ein kleiner Hocker kommt ins Zimmer (auch fürs Training).
