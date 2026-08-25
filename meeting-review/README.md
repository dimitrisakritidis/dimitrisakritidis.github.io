# Meeting-Review — Protokollant (Version 1)

Vier-Ebenen-Auswertung eines Meeting-Transkripts als eigenständige HTML-Seite
(`index.html`, keine Abhängigkeiten, läuft auch offline).

## Ebenen

| Ebene | Inhalt |
|-------|--------|
| **E0** | Rohtranskript mit Timestamps und Sprechern; vermutete Transkriptionsfehler rot (wichtig) / gelb (unwichtig) unterstrichen, Hover zeigt die vermutete Korrektur |
| **E1** | Paraphrasiertes Transkript (bereinigtes Hochdeutsch), gruppiert in Sinn-Einheiten mit Timestamps |
| **E2** | Chronologische Kapitel mit Zeitspannen (wie YouTube-Kapitel) |
| **E3** | Ableitungen: To-dos, Kalender-Vorschläge, Brainstorming, Info-Updates, E-Mail-Entwurf — jeweils mit Belegstellen |

## Bedienung

- **Hover** über eine Textstelle hebt die verknüpften Stellen in allen vier Spalten hervor.
- **Klick** pinnt die Hervorhebung für 7 Sekunden und scrollt die anderen Spalten zur Stelle.
- **Audio**: Die Seite lädt die Aufnahme automatisch von `meta.audioUrl`
  (Standard: `audio/<meeting-id>.m4a` neben der Seite — Datei dort ablegen, fertig).
  Fehlt sie, erscheint der Fallback „Audio laden“ (lokale Datei, verlässt den Rechner
  nicht). Klick auf eine Zeile springt an den *Beginn der Aussage*
  (Schalter „Klick → Audio-Sprung“).
- **E3-Prüfung**: ✓ = absegnen, ✕ = abändern (öffnet ein Textfeld). Der Stand wird pro
  Browser in `localStorage` gehalten.
- **Auswertung**: Gegenüberstellung Claude-Vorschlag ↔ menschliche Fassung mit Wort-Diff,
  Export als „Lektionen-JSON“ (Format unten) für die Protokollant-Datenbank.

## Hinweis zu den Timestamps

Das Quelltranskript hatte **keine** Timestamps. Die Zeiten in dieser Version sind
**simuliert**: aus Sprechtempo (~2,5 Wörter/s) und plausiblen Pausen (Bildschirmfreigabe,
Login-Versuche, Dokument-Lesen) auf die bekannte Aufnahmelänge von 7224 s skaliert.
Sobald WhisperX-Timestamps mitgeliefert werden, ersetzen sie 1:1 die Felder
`start`/`end` in den Segmenten — am Format ändert sich nichts.

## Datenformat (`data/*.json`)

```jsonc
{
  "meta":     { "id", "title", "date", "metaBits": [] },
  "segments": [ { "id": "s001", "speaker": "SPEAKER_02", "start": 3.0, "end": 3.9, "text": "…" } ],
  "units":    [ { "segIds": ["s001","s002"], "speaker": "SPEAKER_02", "text": "…", "minor": true } ],
  "chapters": [ { "title", "summary", "firstSeg": "s001", "lastSeg": "s073" } ],
  "errors":   [ { "segId", "quote", "meant", "severity": "rot|gelb", "reason" } ],
  "e3": {
    "todos":         [ { "text", "owner", "prio", "segIds": [] } ],
    "calendar":      [ { "title", "when", "details", "segIds": [] } ],
    "brainstorming": [ { "text", "segIds": [] } ],
    "infoUpdates":   [ { "text", "segIds": [] } ],
    "emails":        [ { "to", "subject", "body", "segIds": [] } ]
  }
}
```

Alle Querverweise laufen über Segment-IDs — Hover/Pin/Audio brauchen keine weitere Logik.

## Review-Export (Lektionen-JSON)

```jsonc
{
  "meeting":    { "id", "title", "date" },
  "exportedAt": "ISO-Zeit",
  "reviews": [ {
    "id", "type", "segIds": [],
    "claudeProposal": "ursprünglicher Vorschlag",
    "decision": "ok | changed | open",
    "humanVersion": "nur bei changed",
    "reviewedAt": "ISO-Zeit"
  } ]
}
```

Damit lässt sich pro Meeting auswerten, wo Mensch und Protokollant auseinanderlagen —
die Basis für das Lern-Gedächtnis des Agents.

## Nächste Ausbaustufen (nicht Teil von V1)

- Echte WhisperX-Timestamps statt Simulation
- Review-Stand serverseitig statt `localStorage` (Team-Sync), Anbindung Notion-Datenbank
- Automatischer Lektionen-Abgleich über mehrere Meetings
- E-Mail-Nachbereitung nach Schema X bei externen Meetings
