<p align="center">
  <a href="https://play.google.com/store/apps/details?id=com.reworewo.prayertimes">
    <img src="https://play-lh.googleusercontent.com/imB-yjAp8qNYa2-Efuk5zR2S7FEvc5vanzOzoXynWLR91DZ-piSjUzWW4nu13Cl3KVNrB-tnYmnGsMHbEndjmJw=w240-h480" alt="Prayer Times app logo" width="96">
  </a>
</p>

# Prayer Times Scraper for Tunisia

A Python script that scrapes Islamic prayer times from Tunisia's official meteorological authority (meteo.tn) and exports them to a CSV file.

## Why this exists

This dataset was made for the [Prayer Times](https://play.google.com/store/apps/details?id=com.reworewo.prayertimes) Android app (`com.reworewo.prayertimes`), because the prayer times set in that app were incorrect for Tunisia. The data itself comes from meteo.tn, not from the app.

## Overview

This script fetches daily prayer times and sunrise information for a full year from the **meteo.tn** API (Tunisia's National Institute of Meteorology). It combines data from two separate endpoints to retrieve the five daily Islamic prayer times plus sunrise information.

## Features

- **Official Source**: Data directly from Tunisia's official weather/meteorological authority
- **Complete Year Coverage**: Scrapes every day of the chosen year
- **Choose the Zone**: All 24 governorates and their delegations, by name or from a menu
- **Yearly Dataset**: A GitHub Action saves each new year's CSV in `data/`
- **Comprehensive Prayer Data**: Captures all five daily prayers:
  - Fajr (pre-dawn)
  - Dhuhr (noon)
  - Asr (afternoon)
  - Maghrib (sunset)
  - Isha (night)
- **Sunrise Times**: Includes sunrise times
- **Respectful Scraping**: A configurable, slightly random delay between requests to avoid server strain
- **CSV Export**: Easy-to-read CSV format for import into other applications

## Usage

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Linux and macOS
source .venv/bin/activate
```

Install the dependency:

```bash
pip install -r requirements.txt
```

### Interactive mode

Run the script without options:

```bash
python scrape_prayer.py
```

It asks you to pick a governorate, then a delegation, then the year (press Enter for the current year).

### Command line

Alternatively, you can directly specify the zone and year:

```bash
python scrape_prayer.py --zone tunis --year 2027
```

To scrape several zones in one run, list them after `--zone`. Each zone gets its own CSV:

```bash
python scrape_prayer.py --zone tunis tunis/carthage ariana
```

Options:

| Option | Meaning |
|--------|---------|
| `--year 2027` | Year to scrape (default: current year) |
| `--zone tunis` | Governorate to scrape, using its main city |
| `--zone tunis/carthage` | A specific delegation of a governorate |
| `--zone tunis ariana` | Several zones, separated by spaces or commas |
| `--zone all` | The main city of every governorate |
| `--list-zones` | Print every zone name |
| `--governorate 342 --delegation 615` | Any meteo.tn zone by its ids (overrides `--zone`) |
| `--name tunis` | Zone name used in the file name (one zone only) |
| `--delay 1` | Average seconds between days, varied randomly by ±50% (default: `0.2`) |
| `--output-dir data` | Folder the CSVs are written to, in one subfolder per zone (default: `data`) |

The script will:
1. Connect to meteo.tn's API
2. Fetch prayer times for each day of the year
3. Save results to `data/<Zone>/prayer_times_tunisia_<zone>_<year>.csv`, so all the years of a zone sit in the same folder
4. Display progress in the console

It exits with an error if any day could not be fetched completely, so a broken year is never mistaken for a good one.

## Yearly dataset

The [Yearly prayer times](.github/workflows/yearly-scrape.yml) workflow runs every year on 1 January, scrapes that year for the main city of every governorate and commits the CSVs to `data/`, so the repository builds up a dataset over the years. It can also be started by hand from the Actions tab, with a year and one or more zones of your choice (for example `tunis, ariana`).

## Output

The script generates a CSV file with the following columns (real values for Tunis):

| DATE       | FAJR  | SUNRISE | DHUHR | ASR   | MAGHRIB | ISHA  |
|------------|-------|---------|-------|-------|---------|-------|
| 2026-01-01 | 05:59 | 07:31   | 12:30 | 14:55 | 17:16   | 18:47 |
| 2026-01-02 | 05:59 | 07:32   | 12:30 | 14:56 | 17:17   | 18:48 |
| ...        | ...   | ...     | ...   | ...   | ...     | ...   |

Each row represents one day with times in HH:MM format.

## Zones

`zones.json` lists all 24 governorates and their delegations with their meteo.tn ids, taken from the [meteo.tn prayer times page](https://www.meteo.tn/fr/heures-prieres). The main city of each governorate was checked against the API. If meteo.tn adds a place, you can still scrape it with `--governorate` and `--delegation`, or add it to `zones.json`.
