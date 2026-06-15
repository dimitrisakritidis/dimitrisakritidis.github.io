"""Trade-Ausfuehrung mit Risiko-Guards. Paper- und Live-Modus."""

from __future__ import annotations

import time
from collections import deque

from .config import Config
from .exchanges import ExchangeClient
from .scanner import Opportunity


class RiskManager:
    """Notbremsen: Trades/Stunde und Tagesverlust begrenzen."""

    def __init__(self, max_trades_per_hour: int, max_daily_loss_quote: float):
        self.max_trades_per_hour = max_trades_per_hour
        self.max_daily_loss_quote = max_daily_loss_quote
        self._trade_times: deque[float] = deque()
        self._daily_pnl = 0.0
        self._day_start = time.time()

    def _prune(self, now: float) -> None:
        while self._trade_times and now - self._trade_times[0] > 3600:
            self._trade_times.popleft()
        if now - self._day_start > 86400:
            self._day_start = now
            self._daily_pnl = 0.0

    def can_trade(self, now: float | None = None) -> tuple[bool, str]:
        now = now or time.time()
        self._prune(now)
        if len(self._trade_times) >= self.max_trades_per_hour:
            return False, "Trade-Limit pro Stunde erreicht"
        if self._daily_pnl <= -abs(self.max_daily_loss_quote):
            return False, "Tagesverlust-Limit erreicht — Stopp"
        return True, ""

    def record(self, pnl_quote: float, now: float | None = None) -> None:
        now = now or time.time()
        self._trade_times.append(now)
        self._daily_pnl += pnl_quote

    @property
    def daily_pnl(self) -> float:
        return self._daily_pnl


class Executor:
    def __init__(self, cfg: Config, clients: dict[str, ExchangeClient]):
        self.cfg = cfg
        self.clients = clients
        self.risk = RiskManager(
            cfg.risk.max_trades_per_hour, cfg.risk.max_daily_loss_quote
        )
        # Paper-Buchhaltung: virtuelles Quote-Guthaben je Boerse.
        self.paper_balance = {
            cid: cfg.paper_start_balance for cid in clients
        }

    def _trade_size_base(self, opp: Opportunity) -> float:
        """Einsatz (Quote) in Basis-Menge umrechnen, gedeckelt durch max_trade_quote."""
        return self.cfg.max_trade_quote / opp.buy_price

    def execute(self, opp: Opportunity) -> None:
        ok, reason = self.risk.can_trade()
        if not ok:
            print(f"  [risk] uebersprungen: {reason}")
            return

        if opp.net_profit_pct < self.cfg.min_profit_pct:
            return  # unter Schwelle — nicht handeln

        if self.cfg.mode == "paper":
            self._execute_paper(opp)
        elif self.cfg.mode == "live":
            self._execute_live(opp)

    def _execute_paper(self, opp: Opportunity) -> None:
        amount = self._trade_size_base(opp)
        cost = amount * opp.buy_price
        proceeds = amount * opp.sell_price
        buy_fee = cost * self.clients[opp.buy_exchange].taker_fee
        sell_fee = proceeds * self.clients[opp.sell_exchange].taker_fee
        pnl = proceeds - cost - buy_fee - sell_fee

        self.paper_balance[opp.buy_exchange] -= cost + buy_fee
        self.paper_balance[opp.sell_exchange] += proceeds - sell_fee
        self.risk.record(pnl)

        print(
            f"  [PAPER] {opp.symbol} {opp.buy_exchange}->{opp.sell_exchange} "
            f"menge {amount:.6f} | PnL {pnl:+.4f} | "
            f"Tages-PnL {self.risk.daily_pnl:+.4f}"
        )

    def _execute_live(self, opp: Opportunity) -> None:
        buy_client = self.clients[opp.buy_exchange]
        sell_client = self.clients[opp.sell_exchange]

        if not (buy_client.can_trade and sell_client.can_trade):
            print("  [live] Abbruch: API-Keys fuer beide Boersen noetig.")
            return

        amount = self._trade_size_base(opp)
        print(
            f"  [LIVE] {opp.symbol} kaufe {amount:.6f} auf {opp.buy_exchange}, "
            f"verkaufe auf {opp.sell_exchange}"
        )
        try:
            buy_client.create_market_order(opp.symbol, "buy", amount)
            sell_client.create_market_order(opp.symbol, "sell", amount)
        except Exception as exc:  # noqa: BLE001
            # Teil-Ausfuehrung ist hier das reale Risiko: eine Seite gefuellt,
            # die andere nicht. Live-Betrieb braucht zusaetzliche Absicherung.
            print(f"  [LIVE][FEHLER] {exc} — Position pruefen!")
            return

        # Realisierten PnL konservativ aus erwarteten Preisen schaetzen.
        est_pnl = amount * (opp.sell_price - opp.buy_price)
        self.risk.record(est_pnl)
