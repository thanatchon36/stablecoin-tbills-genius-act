"""Shared helpers: config loading, logging setup and the on-disk raw cache."""

from __future__ import annotations

import gzip
import json
import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
TS_FMT = "%Y%m%dT%H%M%SZ"
log = logging.getLogger(__name__)


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Read config.yaml from the repo root."""
    with open(path or ROOT / "config.yaml") as f:
        return yaml.safe_load(f)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logging once."""
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def raw_dir(cfg: dict[str, Any]) -> Path:
    d = ROOT / cfg["paths"]["raw"]
    d.mkdir(parents=True, exist_ok=True)
    return d


def latest_cached(cfg: dict[str, Any], name: str, ext: str) -> Path | None:
    """Most recent cached raw file `{name}_{timestamp}.{ext}`, or None."""
    files = sorted(raw_dir(cfg).glob(f"{name}_*.{ext}"))
    return files[-1] if files else None


def fetch_timestamp(path: Path) -> datetime:
    """Parse the UTC fetch timestamp embedded in a cached raw filename."""
    stamp = path.name.split("_")[-1].split(".")[0]
    return datetime.strptime(stamp, TS_FMT).replace(tzinfo=UTC)


def http_get(url: str, retries: int = 4, sleep: float = 2.0, timeout: float = 60.0) -> requests.Response:
    """GET with simple exponential back-off; raises after the last failure."""
    headers = {"User-Agent": "stablecoin-tbills-genius-act research (python-requests)"}
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            log.warning("GET failed (%s/%s) %s: %s", attempt + 1, retries, url, e)
            if attempt == retries - 1:
                raise
            time.sleep(sleep * 2**attempt)
    raise RuntimeError("unreachable")


def cached_json(cfg: dict[str, Any], name: str, fetch: Callable[[], Any], refresh: bool = False) -> tuple[Any, Path]:
    """Return JSON from the newest cache file, or fetch and store it as gzipped JSON."""
    path = None if refresh else latest_cached(cfg, name, "json.gz")
    if path is None:
        data = fetch()
        stamp = datetime.now(UTC).strftime(TS_FMT)
        path = raw_dir(cfg) / f"{name}_{stamp}.json.gz"
        with gzip.open(path, "wt") as f:
            json.dump(data, f)
        log.info("fetched %s -> %s", name, path.name)
    else:
        log.info("using cached %s", path.name)
    with gzip.open(path, "rt") as f:
        return json.load(f), path


def cached_text(cfg: dict[str, Any], name: str, fetch: Callable[[], str], refresh: bool = False) -> tuple[str, Path]:
    """Return text (CSV) from the newest cache file, or fetch and store it."""
    path = None if refresh else latest_cached(cfg, name, "csv")
    if path is None:
        text = fetch()
        stamp = datetime.now(UTC).strftime(TS_FMT)
        path = raw_dir(cfg) / f"{name}_{stamp}.csv"
        path.write_text(text)
        log.info("fetched %s -> %s", name, path.name)
    else:
        log.info("using cached %s", path.name)
    return path.read_text(), path
