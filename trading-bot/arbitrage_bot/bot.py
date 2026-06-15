"""Hauptschleife: scannen, melden, (optional) ausfuehren."""

from __future__ import annotations

import time

from .config import Config
from .exchanges import build_clients
from .executor import Executor
from .scanner import scan_symbol


class ArbitrageBot:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        enable_trading = cfg.mode == "live"
        self.clients = build_clients(cfg.exchanges, enable_trading)
        self.executor = Executor(cfg, self.clients) if cfg.mode != "scan" else None

    def run(self) -> None:
        mode = self.cfg.mode.upper()
        print(
            f"== Arbitrage Bot [{mode}] == Boersen: "
            f"{', '.join(self.clients)} | Symbole: {', '.join(self.cfg.symbols)}"
        )
        print(
            f"   Mindest-Nettoprofit: {self.cfg.min_profit_pct*100:.3f}% | "
            f"Einsatz/Trade: {self.cfg.max_trade_quote} | "
            f"Intervall: {self.cfg.poll_interval_ms} ms"
        )
        print("   Strg+C zum Beenden.\n")

        try:
            while True:
                self._tick()
                time.sleep(self.cfg.poll_interval_s)
        except KeyboardInterrupt:
            print("\nBeendet.")

    def _tick(self) -> None:
        stamp = time.strftime("%H:%M:%S")
        found_any = False
        for symbol in self.cfg.symbols:
            opps = scan_symbol(
                symbol, self.clients, self.cfg.risk.slippage_buffer_pct
            )
            for opp in opps:
                found_any = True
                marker = "***" if opp.net_profit_pct >= self.cfg.min_profit_pct else "   "
                print(f"[{stamp}] {marker} {opp}")
                if self.executor is not None:
                    self.executor.execute(opp)

        if not found_any:
            print(f"[{stamp}] keine profitable Lücke (nach Gebuehren).")
