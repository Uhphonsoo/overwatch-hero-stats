"""CLI: scrape one or more filter combos and store snapshots in SQLite."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import filters as F
from .scraper import scrape
from .storage import DEFAULT_DB_PATH, connect, insert_snapshot, utcnow_iso


def _add_filter_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--role", choices=F.ROLES, default=F.DEFAULTS["role"])
    p.add_argument("--input", choices=F.INPUTS, default=F.DEFAULTS["input"],
                   help="PC or Console")
    p.add_argument("--rq", choices=F.RQS, default=F.DEFAULTS["rq"],
                   help="0=Quick Play, 2=Competitive")
    p.add_argument("--tier", choices=F.TIERS, default=F.DEFAULTS["tier"])
    p.add_argument("--map", choices=F.MAPS, default=F.DEFAULTS["map"], dest="map_")
    p.add_argument("--region", choices=F.REGIONS, default=F.DEFAULTS["region"])


def _filters_from_args(args: argparse.Namespace) -> dict:
    return {
        "role": args.role,
        "input": args.input,
        "rq": args.rq,
        "tier": args.tier,
        "map": args.map_,
        "region": args.region,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Scrape Overwatch hero rates for a filter combo and store a snapshot."
    )
    _add_filter_args(p)
    p.add_argument("--db", type=Path, default=DEFAULT_DB_PATH,
                   help=f"SQLite DB path (default: {DEFAULT_DB_PATH})")
    p.add_argument("--all-regions", action="store_true",
                   help="Scrape Americas, Asia, and Europe (overrides --region)")
    p.add_argument("--all-rqs", action="store_true",
                   help="Scrape both Quick Play and Competitive (overrides --rq)")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)

    base = _filters_from_args(args)
    regions = F.REGIONS if args.all_regions else [base["region"]]
    rqs = F.RQS if args.all_rqs else [base["rq"]]

    combos = [
        {**base, "region": r, "rq": rq}
        for r in regions
        for rq in rqs
    ]

    conn = connect(args.db)
    ts = utcnow_iso()
    total = 0
    for f in combos:
        rates = scrape(f)
        n = insert_snapshot(conn, rates, f, ts=ts)
        total += n
        if not args.quiet:
            print(
                f"[{ts}] inserted {n} rows  "
                f"role={f['role']} input={f['input']} rq={F.RQ_LABELS[f['rq']]} "
                f"tier={f['tier']} map={f['map']} region={f['region']}"
            )
    if not args.quiet:
        print(f"Done. {total} rows across {len(combos)} combo(s) -> {args.db}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
