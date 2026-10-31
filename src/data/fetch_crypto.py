"""Fetch the daily BTCUSDT close from Binance (paginated klines, cached under data/raw/)."""

from __future__ import annotations

import logging
import time
from typing import Any

import pandas as pd

from src.utils import cached_json, fetch_timestamp, http_get

log = logging.getLogger(__name__)
DAY_MS = 86_400_000


def _fetch_all_klines(url_tmpl: str, start: str) -> list[list[Any]]:
    """Page through 1000-day kline batches until the API returns fewer rows."""
    start_ms = int(pd.Timestamp(start, tz="UTC").timestamp() * 1000)
    rows: list[list[Any]] = []
    while True:
        batch = http_get(url_tmpl.format(start_ms=start_ms)).json()
        rows.extend(batch)
        if len(batch) < 1000:
            return rows
        start_ms = int(batch[-1][0]) + DAY_MS
        time.sleep(0.5)


def fetch_btc(cfg: dict[str, Any], refresh: bool = False) -> pd.Series:
    """BTC close in USD, indexed by UTC calendar day of the candle.

    The candle for day d closes at 23:59:59 UTC on d (~19:59 New York), so it is assigned to US day d.
    The candle still open on the fetch day is dropped.
    """
    c = cfg["crypto"]
    rows, path = cached_json(cfg, "binance_btcusdt", lambda: _fetch_all_klines(c["binance_url"], c["binance_start"]), refresh)
    idx = pd.to_datetime([int(r[0]) for r in rows], unit="ms").normalize()
    s = pd.Series([float(r[4]) for r in rows], index=idx, name="BTC").sort_index()
    s = s[~s.index.duplicated(keep="last")]
    today = pd.Timestamp(fetch_timestamp(path)).tz_convert(None).normalize()
    s = s[s.index < today]
    log.info("BTC: %s to %s, %d obs", s.index[0].date(), s.index[-1].date(), len(s))
    return s
