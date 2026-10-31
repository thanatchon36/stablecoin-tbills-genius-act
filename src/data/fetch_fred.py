"""Fetch daily FRED series via the public fredgraph CSV endpoint (no API key)."""

from __future__ import annotations

import io
import logging
from typing import Any

import pandas as pd

from src.utils import cached_text, http_get

log = logging.getLogger(__name__)


def parse_fred_csv(text: str, series: str) -> pd.Series:
    """Parse a fredgraph CSV; '.' and blanks become NaN."""
    df = pd.read_csv(io.StringIO(text), na_values=["."])
    date_col = df.columns[0]
    s = pd.to_numeric(df[series], errors="coerce")
    s.index = pd.to_datetime(df[date_col])
    s.name = series
    return s.sort_index()


def fetch_fred(cfg: dict[str, Any], refresh: bool = False) -> pd.DataFrame:
    """Download (or load cached) every series in config: outcomes, CMT alternatives and controls."""
    f = cfg["fred"]
    out = {}
    for sid in f["outcomes"] + f["outcomes_cmt_alt"] + f["controls"]:
        url = f["url"].format(series=sid)
        text, _ = cached_text(cfg, f"fred_{sid}", lambda u=url: http_get(u).text, refresh)
        out[sid] = parse_fred_csv(text, sid)
        log.info("FRED %s: %s to %s, %d obs", sid, out[sid].first_valid_index().date(),
                 out[sid].last_valid_index().date(), out[sid].notna().sum())
    return pd.DataFrame(out).sort_index()
