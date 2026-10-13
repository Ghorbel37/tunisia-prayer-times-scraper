import io
import os
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".github", "scripts"))
import update_readme  # noqa: E402
from scrape_prayer import GOVERNORATES, slug  # noqa: E402

REAL_README = os.path.join(update_readme.ROOT, "README.md")
ZONES = [slug(gov["name"]) for gov in GOVERNORATES]


class UpdateReadmeTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        shutil.copy(REAL_README, os.path.join(self.root, "README.md"))

    def readme(self):
        with open(os.path.join(self.root, "README.md"), encoding="utf-8") as f:
            return f.read()

    def latest(self, zone):
        return os.path.join(self.root, update_readme.LATEST_DIR, f"prayer_times_tunisia_{zone}.csv")

    def add_files(self, year, skip=0):
        for zone in ZONES[skip:]:
            path = os.path.join(self.root, "data", zone.title(),
                                f"prayer_times_tunisia_{zone}_{year}.csv")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"{zone} {year}\n")

    def update(self, year):
        with redirect_stdout(io.StringIO()):
            return update_readme.update_readme(year, self.root)

    def test_new_year_is_copied_to_latest(self):
        self.add_files(2027)
        self.assertTrue(self.update(2027))
        self.assertEqual(sorted(os.listdir(os.path.join(self.root, update_readme.LATEST_DIR))),
                         sorted(f"prayer_times_tunisia_{zone}.csv" for zone in ZONES))
        with open(self.latest("le-kef"), encoding="utf-8") as f:
            self.assertEqual(f.read(), "le-kef 2027\n")

    def test_only_the_heading_year_changes_in_the_readme(self):
        before = self.readme()
        self.add_files(2027)
        self.assertTrue(self.update(2027))
        self.assertEqual(self.readme(), before.replace("Prayer times for 2026", "Prayer times for 2027"))

    def test_nothing_changes_if_a_file_is_missing(self):
        before = self.readme()
        self.add_files(2027, skip=1)
        self.assertFalse(self.update(2027))
        self.assertEqual(self.readme(), before)
        self.assertFalse(os.path.exists(os.path.join(self.root, update_readme.LATEST_DIR)))

    def test_readme_links_point_to_the_latest_files(self):
        links = re.findall(r"\((data/_latest/[^)\s]+\.csv)\)", self.readme())
        self.assertEqual(sorted(links), sorted(f"data/_latest/prayer_times_tunisia_{zone}.csv"
                                               for zone in ZONES))
        missing = [link for link in links
                   if not os.path.exists(os.path.join(update_readme.ROOT, link))]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
