import io
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import update_readme  # noqa: E402

REAL_README = os.path.join(update_readme.ROOT, "README.md")


class UpdateReadmeTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        shutil.copy(REAL_README, os.path.join(self.root, "README.md"))
        self.links = update_readme.LINK.findall(self.readme())

    def readme(self):
        with open(os.path.join(self.root, "README.md"), encoding="utf-8") as f:
            return f.read()

    def add_files(self, year, skip=0):
        for base, _ in self.links[skip:]:
            path = os.path.join(self.root, f"{base}_{year}.csv")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "w").close()

    def update(self, year):
        with redirect_stdout(io.StringIO()):
            return update_readme.update_readme(year, self.root)

    def test_readme_links_every_governorate(self):
        self.assertEqual(len(self.links), 24)
        self.assertIn(("data/Le-Kef/prayer_times_tunisia_le-kef", "2026"), self.links)

    def test_links_and_heading_move_to_the_new_year(self):
        before = self.readme()
        self.add_files(2027)
        self.assertTrue(self.update(2027))
        after = self.readme()
        self.assertIn("Prayer times for 2027", after)
        self.assertIn("(data/Tunis/prayer_times_tunisia_tunis_2027.csv)", after)
        self.assertNotIn("_2026.csv)", after)
        # Nothing outside the links and the heading changes
        expected = before.replace("_2026.csv)", "_2027.csv)")
        expected = expected.replace("Prayer times for 2026", "Prayer times for 2027")
        self.assertEqual(after, expected)

    def test_readme_is_left_alone_if_a_file_is_missing(self):
        before = self.readme()
        self.add_files(2027, skip=1)
        self.assertFalse(self.update(2027))
        self.assertEqual(self.readme(), before)

    def test_current_links_point_to_real_files(self):
        root = update_readme.ROOT
        missing = [f"{base}_{year}.csv" for base, year in self.links
                   if not os.path.exists(os.path.join(root, f"{base}_{year}.csv"))]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
