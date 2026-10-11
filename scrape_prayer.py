import argparse
import csv
import json
import logging
import os
import random
import sys
import time
import unicodedata
from datetime import date, timedelta

import requests
from requests.adapters import HTTPAdapter, Retry

# Base URLs for the two different endpoints
PRAYER_URL = "https://www.meteo.tn/horaire_gouvernorat/{date}/{gov}/{deleg}"
SUNRISE_URL = "https://www.meteo.tn/lever_coucher_gouvernorat/{date}/{gov}/{deleg}"

# One connection reused for every request, instead of a new one each time.
# A failed request is tried again up to 5 times, waiting 0, 10, 20, 40 then 80 seconds.
SESSION = requests.Session()
SESSION.mount("https://", HTTPAdapter(max_retries=Retry(
    total=5, backoff_factor=5, status_forcelist=[429, 500, 502, 503, 504])))

# Every governorate and delegation listed on https://www.meteo.tn/fr/heures-prieres
ZONES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zones.json")
with open(ZONES_FILE, encoding="utf-8") as f:
    GOVERNORATES = json.load(f)["governorates"]


def slug(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return "-".join(text.lower().split())


# Known zones: name -> (governorate id, delegation id) on meteo.tn.
# A governorate name ("tunis") means its main city; "tunis/carthage" picks a delegation.
# ZONE_TITLES keeps the real names for display ("tunis/carthage" -> "Tunis/Carthage").
ZONES = {}
ZONE_TITLES = {}
for gov in GOVERNORATES:
    ZONES[slug(gov["name"])] = (gov["id"], gov["main_delegation"])
    ZONE_TITLES[slug(gov["name"])] = gov["name"]
    for deleg in gov["delegations"]:
        if deleg["id"] == gov["main_delegation"]:
            continue
        ZONES[f"{slug(gov['name'])}/{slug(deleg['name'])}"] = (gov["id"], deleg["id"])
        ZONE_TITLES[f"{slug(gov['name'])}/{slug(deleg['name'])}"] = f"{gov['name']}/{deleg['name']}"


def describe_zones(text):
    """Turn a zone list like "tunis, tunis/carthage" into "Tunis, Tunis/Carthage" for commit messages."""
    zones = list(dict.fromkeys(text.lower().replace(",", " ").split()))
    names = [ZONE_TITLES.get(z, z) for z in zones]
    if "all" in zones:
        # "all" already covers every governorate; only extra delegations are worth naming
        names = ["all governorates"] + [ZONE_TITLES.get(z, z) for z in zones if "/" in z]
    return ", ".join(names)

COLUMNS = ["DATE", "FAJR", "SUNRISE", "DHUHR", "ASR", "MAGHRIB", "ISHA"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scrape a full year of prayer times from meteo.tn into a CSV file."
    )
    parser.add_argument("--year", type=int,
                        help="year to scrape (default: current year, or asked in the menus)")
    parser.add_argument("--zone", nargs="+", action="extend",
                        help="governorate (e.g. tunis) or governorate/delegation "
                             "(e.g. tunis/carthage) to scrape; see --list-zones. "
                             "Give several zones, separated by spaces or commas, "
                             "to scrape each of them, or all for the main city "
                             "of every governorate. "
                             "Without a zone, the script asks for one in menus")
    parser.add_argument("--list-zones", action="store_true",
                        help="print every zone name and exit")
    parser.add_argument("--governorate", type=int,
                        help="meteo.tn governorate id (overrides --zone)")
    parser.add_argument("--delegation", type=int,
                        help="meteo.tn delegation id (overrides --zone)")
    parser.add_argument("--name",
                        help="zone name used in the output file name (default: the zone name)")
    parser.add_argument("--delay", type=float, default=0.2,
                        help="average seconds to wait between days; each wait varies "
                             "randomly between half and one and a half times this "
                             "(default: 0.2)")
    parser.add_argument("--output-dir", default="data",
                        help="folder the CSVs are written to, in one subfolder per zone "
                             "(default: data)")
    args = parser.parse_args()

    if args.list_zones:
        for name in ZONES:
            print(name)
        sys.exit(0)
    if args.zone is None and args.governorate is None and args.delegation is None:
        if not sys.stdin.isatty():
            parser.error("no zone given; pass --zone or --governorate/--delegation")
        ask_interactive(args)
        return args

    if (args.governorate is None) != (args.delegation is None):
        parser.error("--governorate and --delegation must be given together")
    if args.governorate is None:
        zones = [z.lower() for value in args.zone for z in value.replace(",", " ").split()]
        if "all" in zones:
            zones = [slug(gov["name"]) for gov in GOVERNORATES] + [z for z in zones if z != "all"]
        if not zones:
            parser.error("no zone given; pass --zone or --governorate/--delegation")
        for zone in zones:
            if zone not in ZONES:
                parser.error(f"unknown zone '{zone}'; see --list-zones")
        if args.name and len(zones) > 1:
            parser.error("--name only works with a single zone")
        args.targets = [(*ZONES[zone], args.name or zone.replace("/", "_"))
                        for zone in dict.fromkeys(zones)]
    else:
        args.targets = [(args.governorate, args.delegation,
                         args.name or f"{args.governorate}_{args.delegation}")]
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
    print("Governorates:")
    gov = GOVERNORATES[ask_choice("Choose a governorate", [gov["name"] for gov in GOVERNORATES])]
    delegs = gov["delegations"]
    print(f"Delegations of {gov['name']}:")
    labels = [d["name"] + (" (main city)" if d["id"] == gov["main_delegation"] else "")
              for d in delegs]
    d = delegs[ask_choice("Choose a delegation", labels)]
    governorate, delegation = gov["id"], d["id"]
    name = slug(gov["name"])
    if d["id"] != gov["main_delegation"]:
        name += "_" + slug(d["name"])
    args.targets = [(governorate, delegation, name)]

    if args.year is None:
        args.year = ask_int("Year", date.today().year)


def get_data(url):
    resp = SESSION.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json().get("data") or {}


def fetch_day(day, gov, deleg):
    date_str = day.strftime("%Y-%m-%d")
    row = {"DATE": date_str}

    # Get Prayer Times
    p_data = get_data(PRAYER_URL.format(date=date_str, gov=gov, deleg=deleg))
    row["FAJR"] = p_data.get("sobh", "")
    row["DHUHR"] = p_data.get("dhohr", "")
    row["ASR"] = p_data.get("aser", "")
    row["MAGHRIB"] = p_data.get("magreb", "")
    row["ISHA"] = p_data.get("isha", "")

    # Get Sunrise
    s_data = get_data(SUNRISE_URL.format(date=date_str, gov=gov, deleg=deleg))
    row["SUNRISE"] = s_data.get("lever", "")

    return row


def scrape_full_timetable(year, gov, deleg, name, output_dir, delay=0.2):
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    # One folder per zone, so every year of a zone sits together (e.g. Tunis, Tunis_Carthage)
    zone_dir = os.path.join(output_dir, name.title())
    os.makedirs(zone_dir, exist_ok=True)
    filename = os.path.join(zone_dir, f"prayer_times_tunisia_{name}_{year}.csv")

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
        time.sleep(random.uniform(delay * 0.5, delay * 1.5))
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
    # Show the "Retrying ..." lines that requests logs when a request fails
    logging.basicConfig(format="  %(message)s")
    try:
        args = parse_args()
        failed = [name for gov, deleg, name in args.targets
                  if not scrape_full_timetable(args.year, gov, deleg, name, args.output_dir,
                                               args.delay)]
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C (or closing the input in the menus) stops quietly instead of printing a traceback
        print("\nCancelled.")
        sys.exit(1)
    if failed and len(args.targets) > 1:
        print(f"Incomplete zones: {', '.join(failed)}")
    sys.exit(1 if failed else 0)
