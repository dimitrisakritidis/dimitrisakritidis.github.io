# Arbitrage Bot (Krypto Cross-Exchange)

Ein ehrlicher, gebühren-bewusster Arbitrage-Scanner und -Bot für Krypto-Börsen.
Vergleicht in Echtzeit Kurse über mehrere Börsen (via [CCXT](https://github.com/ccxt/ccxt))
und erkennt Preislücken, die **nach Abzug aller Gebühren** noch profitabel sind.

> **Standardmäßig im PAPER-Modus.** Es wird kein echtes Geld bewegt, bis Du Live-Trading
> bewusst in der Config einschaltest **und** API-Keys hinterlegst.

---

## Bitte zuerst lesen: Was geht realistisch — und was nicht

- **Aktien-HFT in Millisekunden?** Für Privatpersonen praktisch unmöglich. Profis sitzen
  mit Co-Location-Servern direkt im Rechenzentrum der Börse, mit Direkt-Feeds für
  fünfstellige Beträge pro Monat und FPGA-Hardware. Über eine normale Internetleitung
  bist Du immer zu langsam. Dieser Bot zielt deshalb auf **Krypto-Cross-Exchange-Arbitrage**,
  weil das über öffentliche APIs tatsächlich erreichbar ist.
- **Gebühren fressen den Profit.** Eine Preislücke von 0,3 % ist *kein* Gewinn, wenn
  beide Börsen je 0,1 % Taker-Fee nehmen plus Withdrawal-Kosten. Der Bot rechnet das
  ehrlich gegen und ignoriert Lücken, die unter Deiner Mindest-Profitschwelle liegen.
- **Latenz & Transfer.** "Klassische" Arbitrage erfordert, Coins zwischen Börsen zu
  bewegen — das dauert Minuten, nicht Millisekunden, und das Fenster kann sich schließen.
  Realistischer ist **bestandsbasierte Arbitrage**: Du hältst auf beiden Börsen Guthaben
  und gleichst nur periodisch ab. Der Bot unterstützt diesen Modus.
- **Risiko.** Kursrisiko, ausgesetzte Withdrawals, API-Ausfälle, Slippage. Setze nie
  Geld ein, dessen Verlust Du nicht verkraftest. Das ist kein Finanzrat.

---

## Installation

```bash
cd trading-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml
```

## Nutzung

**1. Nur scannen (kein Trading, keine Keys nötig) — empfohlener Start:**

```bash
python run.py --scan
```

Zeigt live alle Preislücken über die konfigurierten Börsen und ob sie nach Gebühren
profitabel wären.

**2. Paper-Trading (simuliert Trades mit virtuellem Guthaben):**

```bash
python run.py --paper
```

**3. Live-Trading (echtes Geld — bewusst freischalten):**

In `config.yaml` `mode: live` setzen, API-Keys eintragen, dann:

```bash
python run.py --live
```

Der Bot fragt zur Sicherheit eine Bestätigung ab, bevor er live startet.

---

## Konfiguration

Siehe `config.example.yaml` — kommentiert. Wichtigste Stellschrauben:

| Feld | Bedeutung |
|---|---|
| `exchanges` | Welche Börsen verglichen werden |
| `symbols` | Welche Handelspaare gescannt werden (z. B. `BTC/USDT`) |
| `min_profit_pct` | Mindest-Nettoprofit nach Gebühren, sonst kein Trade |
| `max_trade_quote` | Maximaler Einsatz pro Trade (in Quote-Währung, z. B. USDT) |
| `poll_interval_ms` | Wie oft Kurse abgefragt werden |
| `mode` | `scan` \| `paper` \| `live` |

---

## Haftungsausschluss

Dieses Projekt dient Bildungs- und Experimentierzwecken. Es ist **keine Anlageberatung**.
Handel mit Kryptowährungen ist hochriskant. Der Autor/Betreiber haftet nicht für Verluste.
Prüfe lokale rechtliche und steuerliche Pflichten.
