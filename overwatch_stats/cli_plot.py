"""CLI: plot pick/win rate over time for a given filter combo."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from . import filters as F
from .storage import DEFAULT_DB_PATH, connect, query_series


def _add_filter_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--role", choices=F.ROLES, default=F.DEFAULTS["role"])
    p.add_argument("--input", choices=F.INPUTS, default=F.DEFAULTS["input"])
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


def _filter_label(f: dict) -> str:
    return (
        f"role={f['role']}  input={f['input']}  rq={F.RQ_LABELS[f['rq']]}  "
        f"tier={f['tier']}  map={f['map']}  region={f['region']}"
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Plot Overwatch hero pick/win rate over time from stored snapshots."
    )
    _add_filter_args(p)
    p.add_argument("--metric", choices=["pickrate", "winrate", "both"], default="both")
    p.add_argument("--hero", action="append", default=None,
                   help="Hero id (e.g. 'sierra'). Repeatable. Omit to plot all.")
    p.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    p.add_argument("--out", type=Path, default=None,
                   help="Save to file instead of showing interactively")
    args = p.parse_args(argv)

    flt = _filters_from_args(args)
    conn = connect(args.db)
    series = query_series(conn, flt, heroes=args.hero)
    if not series:
        print("No data for this filter combo. Run ow-scrape with the same filters first.",
              file=sys.stderr)
        return 1

    metrics = ["pickrate", "winrate"] if args.metric == "both" else [args.metric]
    fig, axes = plt.subplots(len(metrics), 1, figsize=(11, 4 * len(metrics)), sharex=True)
    if len(metrics) == 1:
        axes = [axes]

    for ax, metric in zip(axes, metrics):
        for hero_id, points in sorted(series.items()):
            xs = [datetime.fromisoformat(ts) for ts, _, _ in points]
            ys = [pr if metric == "pickrate" else wr for _, pr, wr in points]
            ax.plot(xs, ys, marker="o", markersize=3, linewidth=1, label=hero_id)
        ax.set_ylabel(f"{metric} (%)")
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
        # Legend can get crowded; only show if <= 15 series
        if len(series) <= 15:
            ax.legend(loc="best", fontsize=8)

    fig.autofmt_xdate()
    fig.suptitle(_filter_label(flt), fontsize=10)
    fig.tight_layout()

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.out, dpi=120)
        print(f"Saved {args.out}")
    else:
        plt.show()
    return 0


if __name__ == "__main__":
    sys.exit(main())
