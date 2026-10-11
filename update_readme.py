"""Point the README's download links at a new year, once that year's files exist.

Used by the yearly workflow: python update_readme.py 2027
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SECTION = "## Ready-made data"
LINK = re.compile(r"\((data/[^)\s]+?)_(\d{4})\.csv\)")
HEADING = re.compile(r"Prayer times for \d{4}")


def update_readme(year, root=ROOT):
    path = os.path.join(root, "README.md")
    with open(path, encoding="utf-8") as f:
        text = f.read()

    # Only the "Ready-made data" section is touched
    start = text.index(SECTION)
    end = text.find("\n## ", start + len(SECTION))
    end = len(text) if end == -1 else end
    section = text[start:end]

    links = [f"{base}_{year}.csv" for base, _ in LINK.findall(section)]
    missing = [link for link in links if not os.path.exists(os.path.join(root, link))]
    if not links or missing:
        print(f"README not updated: {len(missing)} of {len(links)} files missing for {year}")
        return False

    section = LINK.sub(lambda m: f"({m.group(1)}_{year}.csv)", section)
    section = HEADING.sub(f"Prayer times for {year}", section)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text[:start] + section + text[end:])
    print(f"README links now point to {year}")
    return True


if __name__ == "__main__":
    update_readme(int(sys.argv[1]))
