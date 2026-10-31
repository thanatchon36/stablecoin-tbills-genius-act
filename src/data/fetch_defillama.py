"""Fetch daily stablecoin circulating supply from DefiLlama (cached under data/raw/)."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from src.utils import cached_json, fetch_timestamp, http_get

log = logging.getLogger(__name__)


def resolve_ids(assets: list[dict[str, Any]], symbols: list[str]) -> dict[str, str]:
    """Map each symbol to a DefiLlama id: peggedUSD + fiat-backed, largest current supply wins."""
    out: dict[str, str] = {}
    for sym in symbols:
        cands = [
            a for a in assets
            if a.get("symbol") == sym and a.get("pegType") == "peggedUSD" and a.get("pegMechanism") == "fiat-backed"
        ]
        if not cands:
            raise ValueError(f"no fiat-backed peggedUSD DefiLlama asset with symbol {sym}")
        best = max(cands, key=lambda a: (a.get("circulating") or {}).get("peggedUSD") or 0)
        if len(cands) > 1:
            log.info("symbol %s matched %d assets; chose id %s (%s)", sym, len(cands), best["id"], best["name"])
        out[sym] = str(best["id"])
    return out


def chart_to_series(rows: list[dict[str, Any]], fetched_at: pd.Timestamp, name: str) -> pd.Series:
    """Convert a stablecoincharts payload to a USD-bn series indexed by snapshot date (UTC).

    The row dated on the fetch day is an intraday snapshot and is dropped as incomplete.
    """
    dates = pd.to_datetime([int(r["date"]) for r in rows], unit="s").normalize()
    vals = [((r.get("totalCirculating") or {}).get("peggedUSD")) for r in rows]
    s = pd.Series(vals, index=dates, name=name, dtype="float64") / 1e9
    s = s[~s.index.duplicated(keep="last")].sort_index()
    today = fetched_at.tz_convert(None).normalize()
    if len(s) and s.index[-1] >= today:
        log.info("%s: dropping incomplete snapshot dated %s", name, s.index[-1].date())
        s = s[s.index < today]
    return s


def fetch_supply(cfg: dict[str, Any], refresh: bool = False) -> tuple[pd.DataFrame, pd.Series, dict[str, str]]:
    """Return (per-coin supply DataFrame, all-USD-pegged aggregate Series, symbol->id map).

    Index = DefiLlama snapshot date d (00:00 UTC), i.e. the value at end of US day d-1.
    """
    dl = cfg["defillama"]
    lst, _ = cached_json(cfg, "defillama_list", lambda: http_get(dl["list_url"]).json(), refresh)
    ids = resolve_ids(lst["peggedAssets"], dl["primary_symbols"])
    log.info("resolved DefiLlama ids: %s", ids)
    coins = {}
    for sym, cid in ids.items():
        url = dl["chart_url"].format(id=cid)
        rows, path = cached_json(cfg, f"defillama_{sym}", lambda u=url: http_get(u).json(), refresh)
        coins[sym] = chart_to_series(rows, pd.Timestamp(fetch_timestamp(path)), sym)
    rows, path = cached_json(cfg, "defillama_allusd", lambda: http_get(dl["aggregate_url"]).json(), refresh)
    allusd = chart_to_series(rows, pd.Timestamp(fetch_timestamp(path)), "ALLUSD")
    return pd.DataFrame(coins).sort_index(), allusd, ids
