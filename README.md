# overwatch-hero-stats

Scrape hero pick/win rates from [overwatch.blizzard.com/en-us/rates](https://overwatch.blizzard.com/en-us/rates) and plot them over time. The site only shows current numbers — this tool builds the history.

## How it works

The rates page server-renders its data: every row is embedded as a JSON string in the `allrows` attribute of the `<div class="herostats-data-table">` element. The scraper fetches the HTML, pulls that JSON out, and stores a snapshot in SQLite tagged with the timestamp and the filter combo (role / input / rq / tier / map / region). Run it on a schedule and you get a time series; the plot CLI queries the DB and draws it.

## Install

Requires Python 3.10+.

```bash
cd overwatch-hero-stats
python3 -m venv .venv
.venv/bin/pip install -e .
```

This installs two CLI scripts: `ow-scrape` and `ow-plot`.

## Scrape

`ow-scrape` takes one snapshot per filter combo and writes it to `data/rates.db`.

```bash
# single combo
.venv/bin/ow-scrape --rq 2 --tier Diamond --region Europe

# fan out across all regions and both queue types in one run (6 combos)
.venv/bin/ow-scrape --all-regions --all-rqs --tier All
```

Filter flags (defaults match the website's defaults):

| Flag | Values | Default |
| --- | --- | --- |
| `--role` | `All`, `Tank`, `Damage`, `Support` | `All` |
| `--input` | `PC`, `Console` | `PC` |
| `--rq` | `0` (Quick Play), `2` (Competitive) | `2` |
| `--tier` | `All`, `Bronze`, `Silver`, `Gold`, `Platinum`, `Diamond`, `Master`, `Grandmaster` | `All` |
| `--map` | `all-maps` or any map slug (e.g. `kings-row`, `busan`) | `all-maps` |
| `--region` | `Americas`, `Asia`, `Europe` | `Europe` |
| `--all-regions` | scrape Americas + Asia + Europe (overrides `--region`) | off |
| `--all-rqs` | scrape both Quick Play and Competitive (overrides `--rq`) | off |
| `--db` | path to SQLite file | `data/rates.db` |

Snapshots are keyed by `(timestamp, hero, filter combo)`. Running the same combo at the same timestamp is idempotent; running it later appends a new point to the time series.

## Plot

`ow-plot` queries the DB for snapshots matching a filter combo and draws pick/win rate over time.

```bash
# show interactively
.venv/bin/ow-plot --rq 2 --tier Diamond --region Europe --hero kiriko --hero ana

# save to file
.venv/bin/ow-plot --rq 2 --region Europe --out plots/comp_eu.png

# only one metric
.venv/bin/ow-plot --rq 2 --region Europe --metric winrate
```

Plot flags:

| Flag | Notes |
| --- | --- |
| `--role` / `--input` / `--rq` / `--tier` / `--map` / `--region` | same values as `ow-scrape`; must match the combo you scraped |
| `--hero` | hero id (e.g. `sierra`, `kings-row`-style slug). Repeatable. Omit to plot every hero present. |
| `--metric` | `pickrate`, `winrate`, or `both` (default) |
| `--out` | save PNG to this path instead of showing interactively |
| `--db` | path to SQLite file |

If you ask for a filter combo you haven't scraped, you'll get `No data for this filter combo`.

## Building history

To build a time series, just run `ow-scrape` periodically. Two options:

**cron** (every 6 hours):

```cron
0 */6 * * * cd /absolute/path/to/overwatch-hero-stats && .venv/bin/ow-scrape --all-regions --all-rqs --quiet
```

**launchd** (macOS) or any other scheduler — same idea, point it at `.venv/bin/ow-scrape`.

## Project layout

```
overwatch-hero-stats/
├── pyproject.toml
├── overwatch_stats/
│   ├── filters.py       # filter enums (role, input, rq, tier, map, region)
│   ├── scraper.py       # fetch + parse the embedded JSON
│   ├── storage.py       # SQLite schema + insert/query helpers
│   ├── cli_scrape.py    # ow-scrape entrypoint
│   └── cli_plot.py      # ow-plot entrypoint
├── data/                # SQLite DB lives here (gitignored)
└── plots/               # default place for saved plots (gitignored)
```
