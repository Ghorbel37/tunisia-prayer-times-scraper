import argparse
import csv
import os
import sys
import time
from datetime import date, timedelta

import requests

# Base URLs for the two different endpoints
PRAYER_URL = "https://www.meteo.tn/horaire_gouvernorat/{date}/{gov}/{deleg}"
SUNRISE_URL = "https://www.meteo.tn/lever_coucher_gouvernorat/{date}/{gov}/{deleg}"

# Known zones: name -> (governorate id, delegation id) on meteo.tn
ZONES = {
    "sfax": (359, 632),
}

COLUMNS = ["DATE", "FAJR", "SUNRISE", "DHUHR", "ASR", "MAGHRIB", "ISHA"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scrape a full year of prayer times from meteo.tn into a CSV file."
    )
    parser.add_argument("--year", type=int, default=date.today().year,
                        help="year to scrape (default: current year)")
    parser.add_argument("--zone", default="sfax", choices=sorted(ZONES),
                        help="known zone to scrape (default: sfax)")
    parser.add_argument("--governorate", type=int,
                        help="meteo.tn governorate id (overrides --zone)")
    parser.add_argument("--delegation", type=int,
                        help="meteo.tn delegation id (overrides --zone)")
    parser.add_argument("--name",
                        help="zone name used in the output file name (default: the zone name)")
    parser.add_argument("--output-dir", default="data",
                        help="folder the CSV is written to (default: data)")
    args = parser.parse_args()

    if (args.governorate is None) != (args.delegation is None):
        parser.error("--governorate and --delegation must be given together")
    if args.governorate is None:
        args.governorate, args.delegation = ZONES[args.zone]
        args.name = args.name or args.zone
    else:
        args.name = args.name or f"{args.governorate}_{args.delegation}"
    return args


def fetch_day(day, gov, deleg):
    date_str = day.strftime("%Y-%m-%d")
    row = {"DATE": date_str}

    # Get Prayer Times
    p_resp = requests.get(PRAYER_URL.format(date=date_str, gov=gov, deleg=deleg), timeout=10)
    p_resp.raise_for_status()
    p_data = p_resp.json().get("data") or {}
    row["FAJR"] = p_data.get("sobh", "")
    row["DHUHR"] = p_data.get("dhohr", "")
    row["ASR"] = p_data.get("aser", "")
    row["MAGHRIB"] = p_data.get("magreb", "")
    row["ISHA"] = p_data.get("isha", "")

    # Get Sunrise
    s_resp = requests.get(SUNRISE_URL.format(date=date_str, gov=gov, deleg=deleg), timeout=10)
    s_resp.raise_for_status()
    s_data = s_resp.json().get("data") or {}
    row["SUNRISE"] = s_data.get("lever", "")

    return row


def scrape_full_timetable(year, gov, deleg, name, output_dir):
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"prayer_times_{name}_{year}.csv")

    print(f"Starting scrape for {name} {year} ({gov}/{deleg})... output file: {filename}")

    rows = []
    missing = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        try:
            row = fetch_day(current_date, gov, deleg)
            if all(row.get(col) for col in COLUMNS):
                print(f"Saved: {date_str}")
            else:
                missing.append(date_str)
                print(f"Incomplete: {date_str}")
            rows.append(row)
        except Exception as e:
            missing.append(date_str)
            rows.append({"DATE": date_str})
            print(f"Failed to fetch {date_str}: {e}")

        # Sleep briefly to be respectful to the server
        time.sleep(0.2)
        current_date += timedelta(days=1)

    if len(missing) == len(rows):
        print(f"No data found for {name} {year}; nothing written.")
        return False

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    if missing:
        print(f"Done with {len(missing)} incomplete day(s): {', '.join(missing)}")
        return False
    print("Done!")
    return True


if __name__ == "__main__":
    args = parse_args()
    ok = scrape_full_timetable(args.year, args.governorate, args.delegation,
                               args.name, args.output_dir)
    sys.exit(0 if ok else 1)
