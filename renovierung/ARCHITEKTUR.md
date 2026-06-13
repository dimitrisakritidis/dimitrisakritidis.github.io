# ARCHITEKTUR — `index.html` (3D-Modell + Möbel-Editor)

_Code-Karte für Bugfixing & Kontrolle. Stand 2026-06-13. Wenn du als frische Session den Code prüfst: lies dies zuerst, dann `index.html` von oben nach unten. Maße-Wahrheit ist `masse.md`._

## Tech-Stack
- **Three.js r0.165.0**, geladen per `<script type="importmap">` von `cdn.jsdelivr.net` (ES-Module). Braucht daher einen HTTP-Server (nicht per `file://` öffnen).
- Addons: `OrbitControls` (Kamera), `TransformControls` (Verschiebe-/Dreh-Gizmo), `CSS2DRenderer`/`CSS2DObject` (HTML-Beschriftungen im 3D-Raum).
- **On-Demand-Rendering**: KEIN `setAnimationLoop`. `renderFrame()` wird nur bei Änderungen aufgerufen (OrbitControls `change`, TransformControls `change`/`objectChange`, UI-Aktionen). `renderer` hat `preserveDrawingBuffer:true`, damit Screenshots/Canvas-Reads den letzten Frame behalten.

## Koordinatensystem (Meter)
- `RX=4.14` (Länge Wand A/C), `RZ=3.00` (Länge Wand B/D), `RH=2.92` (Deckenhöhe).
- **x** läuft entlang Wand A, 0 = Ecke D/A. **z** von Wand A (z=0) Richtung Wand C (z=RZ). **y** = Höhe.
- Die Gruppe `room` ist um `(-RX/2, 0, -RZ/2)` verschoben → **Weltursprung (0,0,0) = Raummitte auf Bodenhöhe**. Alle Bestandsmöbel + Wände + neue Bausteine hängen in `room` (room-lokale Koordinaten).
- Wände im Uhrzeigersinn: **A** (Bett) → **B** (Schrank/Kallax) → **C** (Tür) → **D** (Fenster). Details/Maße in `masse.md`.

## Bau-Helfer (für die statische Szene)
- `box(w,h,d, x,y,z, mat, parent=room)` — Quader; **x/y/z sind die Min-Ecke** (nicht das Zentrum), das Mesh wird intern um `+w/2,+h/2,+d/2` zentriert.
- `rotBox(w,h,d, cx,y,cz, angleDeg, mat)` — Quader, dessen **cx/cz das Zentrum** sind, mit Drehung um die Y-Achse (für den schräggestellten Fenster-Schreibtisch).
- `label(text, x,y,z, assume=false)` — CSS2D-Beschriftung, landet in `labels[]` (vom „Beschriftungen"-Schalter gesteuert). `assume=true` → orange (= Annahme/Entwurf).
- `dim(text, ax,ay,az, bx,by,bz, off)` — Maßlinie + Label, landet in `dims[]` (vom „Maße"-Schalter gesteuert).

## Aufbau-Reihenfolge im `<script>`
1. Konstanten (Raum/Tür/Fenster).
2. Scene/Camera/Renderer/CSS2DRenderer/OrbitControls/Licht.
3. `room`-Gruppe + Materialien + Helfer (`box`/`label`/`dim`).
4. Boden, Decke (`ceiling`, default unsichtbar), Wände A–D, Fenster, Schacht.
5. Bestandsmöbel (Klappbett, Kleiderstangen, Schrank, Klimmzugstange, Massageliege, Kallax, Schreibtisch, Heizkörper, Nische, Spiegel, Elektrik) — Ziel-Layout.
6. Maßketten (`dim`).
7. UI-Verdrahtung der oberen Checkboxen + `renderFrame()`-Definition + initialer Render.
8. **Möbel-Editor** (Abschnitt „===== Möbel-Editor ====="): siehe unten.

## Editor-System (der neue Teil)
Datenstrukturen:
- `editable[]` — Liste der **nutzererzeugten Bausteine** (Meshes). NUR diese sind klick-selektierbar; Bestandsmöbel sind bewusst statisch.
- `selected` — aktuell ausgewähltes Mesh (oder null).
- `tcontrols` — TransformControls. In die Szene gehängt versionsfest: `scene.add(tcontrols.getHelper ? tcontrols.getHelper() : tcontrols)` (r166+ braucht `getHelper()`, r165 nicht).
- `labels[]` — enthält jetzt AUCH die Baustein-Maß-Labels (folgen dem „Beschriftungen"-Schalter).

Funktionen:
- `addBlock(wCm,hCm,dCm,colorHex)` — erzeugt opaken Quader (+ Kanten + Maß-Label als Kind), hängt ihn in `room`, leicht versetzt um Raummitte (`(n%5-2)*0.3` / `floor(n/5)*0.3`), pusht in `editable[]`, selektiert ihn. Maße werden vorher per `clampCm` auf **1..400 cm** begrenzt.
- `selectObject(obj|null)` — setzt/entfernt emissive-Highlight, attach/detach Gizmo.
- `deleteSelected()` — räumt **das CSS2D-Label explizit ab** (`removeFromParent()` + `element.remove()` + aus `labels[]`), entfernt das Mesh aus `room`, disposed Geometrie/Material.
- `setMode('translate'|'rotate')` — Gizmo-Modus + Button-Hervorhebung.
- `applySnap()` — bei aktivem Snap: `setTranslationSnap(0.05)` (5 cm) + `setRotationSnap(degToRad(angleStep))` (90/45/15°); sonst `null`.
- `updateSelInfo()` — zeigt die Drehwinkel X/Y/Z des ausgewählten Bausteins im Panel.

Event-Flow:
- Auswahl: `pointerdown` merkt Startpunkt + `onGizmo` (= `tcontrols.axis!==null`). `pointerup` selektiert per Raycaster **nur**, wenn die Maus < 5 px bewegt wurde UND nicht das Gizmo bedient wurde (Klick ≠ Kamera-Drag ≠ Gizmo-Zug).
- `dragging-changed` → OrbitControls während eines Gizmo-Zugs gesperrt.
- `pointercancel` (Touch) → State-Reset **und** `controls.enabled=true` (sonst bliebe die Kamera auf Mobilgeräten dauerhaft gesperrt).
- `keydown`: `W`=Verschieben, `E`=Drehen, `Entf`=Löschen (kein Backspace), `Esc`=Abwählen — ignoriert, wenn ein INPUT/SELECT/TEXTAREA/BUTTON fokussiert ist.

## Designentscheidungen / Fallstricke (gegen r165-Quellcode geprüft)
- **Bausteine liegen in `room`, nicht in `scene`** — damit das 5-cm-Raster mit den Bestandsmöbeln fluchtet (room ist um nicht-rasterteilige Werte verschoben; ein Welt-Raster wäre ~2 cm versetzt).
- **Bausteine sind opak** (kein `transparent`) → saubere Tiefensortierung vor/hinter den Glaswänden. Kanten-`LineSegments` geben die Kontur.
- **Wände** (`matWall`): `transparent, opacity:0.30, side:DoubleSide, depthWrite:false`; per `room.traverse` zusätzlich `castShadow=false` (sonst würfen Glaswände harte Schatten).
- Das **Gizmo ist absichtlich durch die Wände sichtbar** (TransformControls nutzt intern `depthTest:false`) — kein Bug.
- On-Demand-Rendering: **jede** Zustandsänderung muss ein `renderFrame()` auslösen. Bei Erweiterungen daran denken.

## Lokal starten & prüfen
```powershell
& "D:\Miniforge3\envs\whisperx\python.exe" -m http.server 8765 --directory "D:\Dimi-KI\Zimmer_Renovierung\repo\renovierung"
```
Dann `http://localhost:8765/`. (Jeder andere statische Server tut es auch.) Browser-Konsole sollte fehlerfrei sein.

## Gegenprüfung der Inhalte
- **Maße**: `masse.md` ist die Quelle der Wahrheit (Chat-Maße bestätigt, Video-Schätzungen als solche markiert).
- **Video-Befunde** lassen sich gegen die Rohquellen prüfen: `../../_arbeit/frames/` (366 Frames, alle 2 s) + `../../_arbeit/transkript*/audio.srt` (gesprochene Anmerkungen mit Zeitstempeln). Siehe `INDEX.md` im Projektordner.
