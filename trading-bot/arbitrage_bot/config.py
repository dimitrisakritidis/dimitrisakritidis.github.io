"""Konfiguration laden und validieren."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import yaml


@dataclass
class ExchangeConfig:
    id: str
    taker_fee: float
    api_key: str = ""
    secret: str = ""


@dataclass
class RiskConfig:
    max_trades_per_hour: int = 20
    max_daily_loss_quote: float = 50.0
    slippage_buffer_pct: float = 0.0005


@dataclass
class Config:
    mode: str
    exchanges: list[ExchangeConfig]
    symbols: list[str]
    min_profit_pct: float
    max_trade_quote: float
    poll_interval_ms: int
    paper_start_balance: float
    risk: RiskConfig = field(default_factory=RiskConfig)

    @property
    def poll_interval_s(self) -> float:
        return self.poll_interval_ms / 1000.0


def load_config(path: str) -> Config:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Config '{path}' nicht gefunden. "
            f"Kopiere config.example.yaml -> config.yaml und passe sie an."
        )

    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    exchanges = [
        ExchangeConfig(
            id=e["id"],
            taker_fee=float(e["taker_fee"]),
            api_key=e.get("api_key", "") or "",
            secret=e.get("secret", "") or "",
        )
        for e in raw.get("exchanges", [])
    ]

    if len(exchanges) < 2:
        raise ValueError("Mindestens zwei Boersen noetig, um Kurse zu vergleichen.")

    risk_raw = raw.get("risk", {}) or {}
    risk = RiskConfig(
        max_trades_per_hour=int(risk_raw.get("max_trades_per_hour", 20)),
        max_daily_loss_quote=float(risk_raw.get("max_daily_loss_quote", 50.0)),
        slippage_buffer_pct=float(risk_raw.get("slippage_buffer_pct", 0.0005)),
    )

    mode = str(raw.get("mode", "scan")).lower()
    if mode not in ("scan", "paper", "live"):
        raise ValueError(f"Ungueltiger Modus '{mode}'. Erlaubt: scan, paper, live.")

    return Config(
        mode=mode,
        exchanges=exchanges,
        symbols=list(raw.get("symbols", [])),
        min_profit_pct=float(raw.get("min_profit_pct", 0.002)),
        max_trade_quote=float(raw.get("max_trade_quote", 100.0)),
        poll_interval_ms=int(raw.get("poll_interval_ms", 1500)),
        paper_start_balance=float(raw.get("paper_start_balance", 1000.0)),
        risk=risk,
    )
