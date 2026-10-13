"""Copy a new year's files to data/_latest and show that year in the README,
once every governorate has a file for it.

data/_latest/prayer_times_tunisia_<zone>.csv always holds the newest complete year,
so links to it never change.

Used by the yearly workflow: python .github/scripts/update_readme.py 2027
"""
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import scrape_prayer  # noqa: E402

SECTION = "## Ready-made data"
LATEST_DIR = os.path.join("data", "_latest")
HEADING = re.compile(r"Prayer times for \d{4}")


def latest_file(year_file, year):
    """data/Tunis/prayer_times_tunisia_tunis_2027.csv -> prayer_times_tunisia_tunis.csv"""
    return os.path.basename(year_file).replace(f"_{year}.csv", ".csv")


def update_readme(year, root=ROOT):
    files = scrape_prayer.year_files(year, os.path.join(root, "data"))
    if not files:
        print(f"Nothing updated: not every governorate has a file for {year}")
        return False

    latest_dir = os.path.join(root, LATEST_DIR)
    os.makedirs(latest_dir, exist_ok=True)
    for f in files:
        shutil.copyfile(f, os.path.join(latest_dir, latest_file(f, year)))

    # Only the "Ready-made data" section of the README is touched
    path = os.path.join(root, "README.md")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    start = text.index(SECTION)
    end = text.find("\n## ", start + len(SECTION))
    end = len(text) if end == -1 else end
    section = HEADING.sub(f"Prayer times for {year}", text[start:end])
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text[:start] + section + text[end:])
    print(f"data/_latest and the README now show {year}")
    return True


if __name__ == "__main__":
    update_readme(int(sys.argv[1]))
