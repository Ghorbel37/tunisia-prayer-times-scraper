import argparse
import csv
import json
import os
import sys
import time
import unicodedata
from datetime import date, timedelta

import requests

# Base URLs for the two different endpoints
PRAYER_URL = "https://www.meteo.tn/horaire_gouvernorat/{date}/{gov}/{deleg}"
SUNRISE_URL = "https://www.meteo.tn/lever_coucher_gouvernorat/{date}/{gov}/{deleg}"

# Every governorate and delegation listed on https://www.meteo.tn/fr/heures-prieres
ZONES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zones.json")
with open(ZONES_FILE, encoding="utf-8") as f:
    GOVERNORATES = json.load(f)["governorates"]


def slug(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return "-".join(text.lower().split())


# Known zones: name -> (governorate id, delegation id) on meteo.tn.
# A governorate name ("sousse") means its main city; "sousse/msaken" picks a delegation.
ZONES = {}
for gov in GOVERNORATES:
    ZONES[slug(gov["name"])] = (gov["id"], gov["main_delegation"])
    for deleg in gov["delegations"]:
        if deleg["id"] == gov["main_delegation"]:
            continue
        ZONES[f"{slug(gov['name'])}/{slug(deleg['name'])}"] = (gov["id"], deleg["id"])

COLUMNS = ["DATE", "FAJR", "SUNRISE", "DHUHR", "ASR", "MAGHRIB", "ISHA"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scrape a full year of prayer times from meteo.tn into a CSV file."
    )
    parser.add_argument("--year", type=int,
                        help="year to scrape (default: current year, or asked in the menus)")
    parser.add_argument("--zone",
                        help="governorate (e.g. sousse) or governorate/delegation "
                             "(e.g. sousse/msaken) to scrape; see --list-zones. "
                             "Without a zone, the script asks for one in menus")
    parser.add_argument("--list-zones", action="store_true",
                        help="print every zone name and exit")
    parser.add_argument("--governorate", type=int,
                        help="meteo.tn governorate id (overrides --zone)")
    parser.add_argument("--delegation", type=int,
                        help="meteo.tn delegation id (overrides --zone)")
    parser.add_argument("--name",
                        help="zone name used in the output file name (default: the zone name)")
    parser.add_argument("--output-dir", default="data",
                        help="folder the CSV is written to (default: data)")
    args = parser.parse_args()

    if args.list_zones:
        for name in ZONES:
            print(name)
        sys.exit(0)
    if args.zone is None and args.governorate is None and args.delegation is None:
        if not sys.stdin.isatty():
            parser.error("no zone given; pass --zone or --governorate/--delegation")
        try:
            ask_interactive(args)
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            sys.exit(1)
        return args

    if (args.governorate is None) != (args.delegation is None):
        parser.error("--governorate and --delegation must be given together")
    if args.governorate is None:
        zone = args.zone.lower()
        if zone not in ZONES:
            parser.error(f"unknown zone '{args.zone}'; see --list-zones")
        args.governorate, args.delegation = ZONES[zone]
        args.name = args.name or zone.replace("/", "_")
    else:
        args.name = args.name or f"{args.governorate}_{args.delegation}"
    if args.year is None:
        args.year = date.today().year
    return args


def ask(prompt, default=None):
    suffix = f" [{default}]" if default is not None else ""
    answer = input(f"{prompt}{suffix}: ").strip()
    return answer or (str(default) if default is not None else "")


def ask_int(prompt, default=None):
    while True:
        answer = ask(prompt, default)
        if answer.isdigit():
            return int(answer)
        print("Please enter a number.")


def ask_choice(prompt, options, default=None):
    for i, option in enumerate(options, 1):
        print(f"  {i:2}. {option}")
    while True:
        choice = ask_int(prompt, default)
        if 1 <= choice <= len(options):
            return choice - 1
        print(f"Please choose between 1 and {len(options)}.")


def ask_interactive(args):
    gov_names = [gov["name"] for gov in GOVERNORATES] + ["Other (enter meteo.tn ids)"]
    print("Governorates:")
    g = ask_choice("Choose a governorate", gov_names)

    if g == len(GOVERNORATES):
        args.governorate = ask_int("Governorate id")
        args.delegation = ask_int("Delegation id")
        args.name = ask("Name for the file", f"{args.governorate}_{args.delegation}")
    else:
        gov = GOVERNORATES[g]
        delegs = gov["delegations"]
        print(f"Delegations of {gov['name']}:")
        labels = [d["name"] + (" (main city)" if d["id"] == gov["main_delegation"] else "")
                  for d in delegs]
        d = delegs[ask_choice("Choose a delegation", labels)]
        args.governorate, args.delegation = gov["id"], d["id"]
        args.name = slug(gov["name"])
        if d["id"] != gov["main_delegation"]:
            args.name += "_" + slug(d["name"])

    if args.year is None:
        args.year = ask_int("Year", date.today().year)


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

        if current_date == start_date and missing:
            print(f"No data for {date_str}; check the zone ids. Nothing written.")
            return False

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
