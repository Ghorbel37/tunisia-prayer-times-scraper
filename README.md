<p align="center">
  <img src="assets/icon.svg" alt="Crescent and clock icon" width="96">
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
- **Respectful Scraping**: Built-in delays between requests to avoid server strain
- **CSV Export**: Easy-to-read CSV format for import into other applications

## Usage

Install the dependency:

```bash
pip install -r requirements.txt
```

Run the script with:

```bash
python scrape_prayer.py
```

By default it scrapes Sfax for the current year. To be asked for the governorate, delegation and year instead, run:

```bash
python scrape_prayer.py -i
```

Options:

| Option | Meaning |
|--------|---------|
| `-i`, `--interactive` | Ask for the zone and year |
| `--year 2027` | Year to scrape (default: current year) |
| `--zone sousse` | Governorate to scrape, using its main city (default: `sfax`) |
| `--zone sousse/msaken` | A specific delegation of a governorate |
| `--list-zones` | Print every zone name |
| `--governorate 359 --delegation 632` | Any meteo.tn zone by its ids (overrides `--zone`) |
| `--name sfax` | Zone name used in the file name |
| `--output-dir data` | Folder the CSV is written to (default: `data`) |

The script will:
1. Connect to meteo.tn's API
2. Fetch prayer times for each day of the year
3. Save results to `data/prayer_times_<zone>_<year>.csv`
4. Display progress in the console

It exits with an error if any day could not be fetched completely, so a broken year is never mistaken for a good one.

## Yearly dataset

The [Yearly prayer times](.github/workflows/yearly-scrape.yml) workflow runs every year on 1 January, scrapes that year for Sfax and commits the CSV to `data/`, so the repository builds up a dataset over the years. It can also be started by hand from the Actions tab, with a year and zone of your choice.

## Output

The script generates a CSV file with the following columns (real values for Sfax):

| DATE       | FAJR  | SUNRISE | DHUHR | ASR   | MAGHRIB | ISHA  |
|------------|-------|---------|-------|-------|---------|-------|
| 2026-01-01 | 05:53 | 07:23   | 12:27 | 14:58 | 17:20   | 18:48 |
| 2026-01-02 | 05:54 | 07:24   | 12:28 | 14:59 | 17:21   | 18:49 |
| ...        | ...   | ...     | ...   | ...   | ...     | ...   |

Each row represents one day with times in HH:MM format.

## Zones

`zones.json` lists all 24 governorates and their delegations with their meteo.tn ids, taken from the [meteo.tn prayer times page](https://www.meteo.tn/fr/heures-prieres). The main city of each governorate was checked against the API. If meteo.tn adds a place, you can still scrape it with `--governorate` and `--delegation`, or add it to `zones.json`.
