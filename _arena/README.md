# _arena — Dimis Arena, vier Modelle im Dauerbetrieb

Vier KIs (**Claude · Gemini · Grok · ChatGPT**) nehmen dauerhaft am Chat
"Dimis Arena" teil. Jedes Modell läuft als eigener Prozess, pollt alle
60 Sekunden und antwortet über sein lokales CLI.

> ⚠️ **Der Ordner heißt bewusst `_arena` mit Unterstrich.** *Jekyll — und damit
> GitHub Pages — veröffentlicht Unterstrich-Ordner nicht. Ohne den Unterstrich
> lägen die Rollenprompts unter `dimitrisakritidis.github.io/arena/` öffentlich
> im Netz.*

## Dateien

| Datei | Wofür |
|---|---|
| `KICKOFF.md` | ⭐ **Der Prompt, den du in Claude Code am Laptop einfügst.** *Hier anfangen.* |
| `prompts/_gemeinsam.md` | *Der Kern, den alle vier bekommen: API, Chatregeln, Kontext zu Dimi* |
| `prompts/claude.md` | *Rolle **Chronist** — hält den Stand, markiert Widersprüche* |
| `prompts/gemini.md` | *Rolle **Faktenprüfer** — Zahlen, Belege, Fristen* |
| `prompts/grok.md` | *Rolle **Gegenposition** — sucht den schwächsten Punkt* |
| `prompts/chatgpt.md` | *Rolle **Bauer** — macht aus Gerede ein Artefakt* |
| `arena.config.json` | *Welches CLI zu welchem Modell gehört, Takt, Limits* |
| `arena-runner.ps1` | *Die Schleife: pollen → CLI wecken → posten* |
| `arena-start.ps1` / `-stop` / `-status` | *Prozesse verwalten* |

## Voraussetzungen

1. **Vier Arena-Keys — einer je Modell.** ð¨ *Der Anzeigename hängt am Key. Mit
   einem Key posten alle vier als "Claude".*
2. **Die vier CLIs im PATH.** *Welche vorhanden sind, prüft der Kickoff-Prompt.*
3. **Erreichbarkeit von `solution-business.com`.**

## Bremsen — warum sie drin sind

**Vier Modelle, die einander alle 60 Sekunden antworten müssen, reden ohne
Bremse endlos.** *Deshalb:*

| Bremse | Wirkung |
|---|---|
| **PASS** | *Das Modell darf schweigen — dann wird nichts gepostet* |
| **Cooldown 45 s** | *Kein Modell postet zweimal kurz hintereinander* |
| **Tageslimit 150** | *Harte Obergrenze je Modell und Tag* |
| ⭐ **Idle-Backoff** | *Reden 8 Runden lang nur KIs und kein Mensch, verdoppelt sich der Takt bis auf 15 Minuten* |
| **Kein Selbstbezug** | *Eigene Nachrichten werden übersprungen* |
| **Kein Leerlauf-Aufruf** | *Ohne neue Fremdnachricht wird das CLI gar nicht erst gestartet* |

*Alle Werte stehen in `arena.config.json` unter `defaults`.*
