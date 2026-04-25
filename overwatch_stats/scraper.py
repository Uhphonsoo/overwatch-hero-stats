"""Scrape hero pick/win rates from overwatch.blizzard.com/en-us/rates.

The page server-renders the data: every row of the rates table is embedded as a
JSON-encoded string in the `allrows` attribute of the `<div class="herostats-data-table">`
element. We fetch the HTML, find that attribute, HTML-unescape it, and json.loads it.
"""
from __future__ import annotations

import html as htmlmod
import json
import re
from dataclasses import dataclass
from typing import Iterable

import requests

from .filters import DEFAULTS

URL = "https://overwatch.blizzard.com/en-us/rates/"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)
_ALLROWS_RE = re.compile(r'class="herostats-data-table"\s+allrows="([^"]*)"')


@dataclass(frozen=True)
class HeroRate:
    hero_id: str
    hero_name: str
    role: str  # TANK / DAMAGE / SUPPORT
    pickrate: float
    winrate: float


def build_params(filters: dict) -> dict:
    """Merge user filters over defaults; only include keys the site recognises."""
    out = dict(DEFAULTS)
    for k, v in filters.items():
        if v is not None:
            out[k] = v
    return out


def fetch_html(filters: dict, *, timeout: float = 30.0, session: requests.Session | None = None) -> str:
    sess = session or requests.Session()
    resp = sess.get(
        URL,
        params=build_params(filters),
        headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.text


def parse_rates(html: str) -> list[HeroRate]:
    m = _ALLROWS_RE.search(html)
    if not m:
        raise ValueError("Could not find herostats-data-table allrows attribute in HTML")
    raw = htmlmod.unescape(m.group(1))
    rows = json.loads(raw)
    out: list[HeroRate] = []
    for row in rows:
        cells = row["cells"]
        hero = row["hero"]
        out.append(
            HeroRate(
                hero_id=row["id"],
                hero_name=cells["name"],
                role=hero["role"],
                pickrate=float(cells["pickrate"]),
                winrate=float(cells["winrate"]),
            )
        )
    return out


def scrape(filters: dict, *, session: requests.Session | None = None) -> list[HeroRate]:
    return parse_rates(fetch_html(filters, session=session))


def scrape_many(combos: Iterable[dict]) -> list[tuple[dict, list[HeroRate]]]:
    """Scrape several filter combos with one session for connection reuse."""
    sess = requests.Session()
    results = []
    for f in combos:
        results.append((f, scrape(f, session=sess)))
    return results
