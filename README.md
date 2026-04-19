# Prayer Times Scraper for Tunisia

A Python script that scrapes Islamic prayer times from Tunisia's official meteorological authority (meteo.tn) and exports them to a CSV file.

## Overview

This script fetches daily prayer times and sunrise information for the entire year 2026 from the **meteo.tn** API (Tunisia's National Institute of Meteorology). It combines data from two separate endpoints to retrieve the five daily Islamic prayer times plus sunrise information.

## Features

- **Official Source**: Data directly from Tunisia's official weather/meteorological authority
- **Complete Year Coverage**: Scrapes all 365 days of 2026
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

Run the script with:

```bash
python scrape_prayer.py
```

The script will:
1. Connect to meteo.tn's API
2. Fetch prayer times for each day of 2026
3. Save results to `prayer_times_sfax_2026.csv`
4. Display progress in the console

## Output

The script generates a CSV file with the following columns:

| DATE       | FAJR  | SUNRISE | DHUHR | ASR   | MAGHRIB | ISHA  |
|------------|-------|---------|-------|-------|---------|-------|
| 2026-01-01 | 06:45 | 07:42   | 12:35 | 15:28 | 17:38   | 19:05 |
| 2026-01-02 | 06:46 | 07:43   | 12:35 | 15:29 | 17:39   | 19:06 |
| ...        | ...   | ...     | ...   | ...   | ...     | ...   |

Each row represents one day with times in HH:MM format.

## Customization

To modify the script for different regions or years:

1. **Change the year**: Modify `start_date` and `end_date` in the `scrape_full_timetable()` function
2. **Change the region**: The coordinates `359/632` refer to a specific regions. Different governorates use different codes. Check meteo.tn for your code.