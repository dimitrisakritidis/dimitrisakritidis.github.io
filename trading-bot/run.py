#!/usr/bin/env python3
"""Einstiegspunkt fuer den Arbitrage Bot.

Beispiele:
    python run.py --scan         # nur Kurse vergleichen (keine Keys noetig)
    python run.py --paper        # Trades simulieren
    python run.py --live         # echtes Geld (Sicherheitsabfrage)
"""

from __future__ import annotations

import argparse
import sys

from arbitrage_bot.bot import ArbitrageBot
from arbitrage_bot.config import load_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Krypto Cross-Exchange Arbitrage Bot")
    parser.add_argument("--config", default="config.yaml", help="Pfad zur Config")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--scan", action="store_true", help="Nur scannen")
    group.add_argument("--paper", action="store_true", help="Paper-Trading")
    group.add_argument("--live", action="store_true", help="Live-Trading (echtes Geld!)")
    args = parser.parse_args()

    try:
        cfg = load_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Konfigurationsfehler: {exc}", file=sys.stderr)
        return 1

    # CLI-Flag ueberschreibt den Modus aus der Config.
    if args.scan:
        cfg.mode = "scan"
    elif args.paper:
        cfg.mode = "paper"
    elif args.live:
        cfg.mode = "live"

    if cfg.mode == "live":
        print("!! LIVE-MODUS: Es wird ECHTES Geld eingesetzt.")
        print("!! Du handelst auf eigenes Risiko. Keine Anlageberatung.")
        confirm = input("Tippe 'ICH VERSTEHE' zum Fortfahren: ").strip()
        if confirm != "ICH VERSTEHE":
            print("Abgebrochen.")
            return 0

    ArbitrageBot(cfg).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
