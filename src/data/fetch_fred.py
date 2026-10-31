"""Fetch daily FRED series via the public fredgraph CSV endpoint (no API key).

fred.stlouisfed.org refuses connections from GitHub-hosted runners (probed 2026-10-31), so when it
is unreachable and FRED_API_KEY is set, the same series is taken from the official FRED API and
written in the fredgraph CSV layout. CI uses this for the S&P 500 and VIX, which are not committed.
"""

from __future__ import annotations

import io
import logging
import os
from typing import Any

import pandas as pd
import requests

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


API_URL = "https://api.stlouisfed.org/fred/series/observations"


def api_to_csv(observations: list[dict[str, str]], series: str) -> str:
    """FRED API observations -> fredgraph CSV text ('.' = missing becomes an empty field)."""
    rows = [f"{o['date']},{'' if o['value'] == '.' else o['value']}" for o in observations]
    return "\n".join([f"observation_date,{series}", *rows]) + "\n"


def download(url: str, series: str) -> str:
    """fredgraph CSV; falls back to the FRED API (key from FRED_API_KEY) if the site is unreachable."""
    try:
        return http_get(url).text
    except requests.RequestException:
        key = os.environ.get("FRED_API_KEY")
        if not key:
            raise
        log.warning("fredgraph unreachable; fetching %s from the FRED API", series)
        params = {"series_id": series, "api_key": key, "file_type": "json"}
        return api_to_csv(http_get(API_URL, params=params).json()["observations"], series)


def fetch_fred(cfg: dict[str, Any], refresh: bool = False) -> pd.DataFrame:
    """Download (or load cached) every series in config: outcomes, CMT alternatives and controls."""
    f = cfg["fred"]
    out = {}
    for sid in f["outcomes"] + f["outcomes_cmt_alt"] + f["controls"]:
        url = f["url"].format(series=sid)
        text, _ = cached_text(cfg, f"fred_{sid}", lambda u=url, s=sid: download(u, s), refresh)
        out[sid] = parse_fred_csv(text, sid)
        log.info("FRED %s: %s to %s, %d obs", sid, out[sid].first_valid_index().date(),
                 out[sid].last_valid_index().date(), out[sid].notna().sum())
    return pd.DataFrame(out).sort_index()
