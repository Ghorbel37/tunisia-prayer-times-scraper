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
- **Choose the Zone**: Pick a known city or any meteo.tn governorate and delegation
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

By default it scrapes Sfax for the current year. Options:

| Option | Meaning |
|--------|---------|
| `--year 2027` | Year to scrape (default: current year) |
| `--zone sfax` | Known zone to scrape (default: `sfax`) |
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

The script generates a CSV file with the following columns:

| DATE       | FAJR  | SUNRISE | DHUHR | ASR   | MAGHRIB | ISHA  |
|------------|-------|---------|-------|-------|---------|-------|
| 2026-01-01 | 06:45 | 07:42   | 12:35 | 15:28 | 17:38   | 19:05 |
| 2026-01-02 | 06:46 | 07:43   | 12:35 | 15:29 | 17:39   | 19:06 |
| ...        | ...   | ...     | ...   | ...   | ...     | ...   |

Each row represents one day with times in HH:MM format.

## Adding a zone

meteo.tn identifies a place by a governorate id and a delegation id (Sfax is `359/632`). To find another one, open the prayer times on meteo.tn with your browser's developer tools and look for a request to `horaire_gouvernorat/<date>/<governorate>/<delegation>`. Then either pass the ids with `--governorate` and `--delegation`, or add the zone to `ZONES` in `scrape_prayer.py` so it can be used with `--zone`.
