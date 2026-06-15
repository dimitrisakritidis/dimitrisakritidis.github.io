"""Arbitrage-Erkennung: vergleicht Quotes und rechnet Gebuehren ehrlich gegen."""

from __future__ import annotations

from dataclasses import dataclass

from .exchanges import ExchangeClient, Quote


@dataclass
class Opportunity:
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float  # wir kaufen zum Ask auf der guenstigen Boerse
    sell_price: float  # wir verkaufen zum Bid auf der teuren Boerse
    gross_spread_pct: float  # Brutto-Preislücke vor Gebuehren
    net_profit_pct: float  # Netto nach beiden Taker-Fees (und Slippage-Puffer)

    def __str__(self) -> str:
        arrow = f"{self.buy_exchange} -> {self.sell_exchange}"
        return (
            f"{self.symbol:>10} | {arrow:<22} | "
            f"kauf {self.buy_price:.2f} / verk {self.sell_price:.2f} | "
            f"brutto {self.gross_spread_pct*100:+.3f}% | "
            f"netto {self.net_profit_pct*100:+.3f}%"
        )


def find_opportunities(
    symbol: str,
    quotes: list[Quote],
    fees: dict[str, float],
    slippage_buffer_pct: float,
) -> list[Opportunity]:
    """Alle profitablen (boerse_kauf, boerse_verkauf)-Paare fuer ein Symbol.

    Logik: Auf Boerse A zum Ask kaufen, gleichzeitig auf Boerse B zum Bid
    verkaufen. Profit entsteht, wenn B.bid deutlich ueber A.ask liegt — genug,
    um die Taker-Fees beider Seiten plus einen Slippage-Puffer zu decken.
    """
    opps: list[Opportunity] = []

    for buy in quotes:
        for sell in quotes:
            if buy.exchange_id == sell.exchange_id:
                continue
            if buy.ask <= 0 or sell.bid <= 0:
                continue

            gross = (sell.bid - buy.ask) / buy.ask
            fee_cost = fees.get(buy.exchange_id, 0.0) + fees.get(sell.exchange_id, 0.0)
            net = gross - fee_cost - slippage_buffer_pct

            if net > 0:
                opps.append(
                    Opportunity(
                        symbol=symbol,
                        buy_exchange=buy.exchange_id,
                        sell_exchange=sell.exchange_id,
                        buy_price=buy.ask,
                        sell_price=sell.bid,
                        gross_spread_pct=gross,
                        net_profit_pct=net,
                    )
                )

    opps.sort(key=lambda o: o.net_profit_pct, reverse=True)
    return opps


def scan_symbol(
    symbol: str,
    clients: dict[str, ExchangeClient],
    slippage_buffer_pct: float,
) -> list[Opportunity]:
    quotes = []
    for client in clients.values():
        q = client.fetch_quote(symbol)
        if q is not None:
            quotes.append(q)

    if len(quotes) < 2:
        return []

    fees = {cid: c.taker_fee for cid, c in clients.items()}
    return find_opportunities(symbol, quotes, fees, slippage_buffer_pct)
