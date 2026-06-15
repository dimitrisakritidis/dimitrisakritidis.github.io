"""Duenne Abstraktion ueber CCXT zum Abruf von Orderbuch-Tops."""

from __future__ import annotations

from dataclasses import dataclass

try:
    import ccxt
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "ccxt ist nicht installiert. Fuehre 'pip install -r requirements.txt' aus."
    ) from exc

from .config import ExchangeConfig


@dataclass
class Quote:
    """Bestes Gebot/Angebot fuer ein Symbol auf einer Boerse."""

    exchange_id: str
    symbol: str
    bid: float  # bester Verkaufspreis fuer uns (wir verkaufen zum Bid)
    ask: float  # bester Kaufpreis fuer uns (wir kaufen zum Ask)
    timestamp: float


class ExchangeClient:
    """Kapselt eine CCXT-Boerseninstanz inkl. Gebuehr."""

    def __init__(self, cfg: ExchangeConfig, enable_trading: bool):
        if not hasattr(ccxt, cfg.id):
            raise ValueError(f"Unbekannte CCXT-Boersen-ID: '{cfg.id}'")

        klass = getattr(ccxt, cfg.id)
        params = {"enableRateLimit": True}
        if enable_trading and cfg.api_key:
            params["apiKey"] = cfg.api_key
            params["secret"] = cfg.secret

        self.id = cfg.id
        self.taker_fee = cfg.taker_fee
        self.client = klass(params)
        self._can_trade = enable_trading and bool(cfg.api_key)

    @property
    def can_trade(self) -> bool:
        return self._can_trade

    def fetch_quote(self, symbol: str) -> Quote | None:
        """Top-of-Book holen. Gibt None zurueck, wenn das Symbol fehlt/Fehler."""
        try:
            ob = self.client.fetch_order_book(symbol, limit=5)
            bid = ob["bids"][0][0] if ob.get("bids") else None
            ask = ob["asks"][0][0] if ob.get("asks") else None
            if bid is None or ask is None:
                return None
            return Quote(
                exchange_id=self.id,
                symbol=symbol,
                bid=float(bid),
                ask=float(ask),
                timestamp=ob.get("timestamp") or 0.0,
            )
        except Exception as exc:  # noqa: BLE001 - Boersen werfen viele Fehlertypen
            print(f"  [warn] {self.id} {symbol}: {exc}")
            return None

    def create_market_order(self, symbol: str, side: str, amount: float):
        """Echte Order (nur live). amount ist Menge in Basis-Waehrung."""
        if not self._can_trade:
            raise RuntimeError(f"{self.id}: Trading nicht aktiviert (keine API-Keys).")
        return self.client.create_order(symbol, "market", side, amount)


def build_clients(
    exchanges: list[ExchangeConfig], enable_trading: bool
) -> dict[str, ExchangeClient]:
    return {e.id: ExchangeClient(e, enable_trading) for e in exchanges}
