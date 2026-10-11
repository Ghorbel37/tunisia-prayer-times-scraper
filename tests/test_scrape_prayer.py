import argparse
import csv
import io
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import scrape_prayer  # noqa: E402


def parse(*argv):
    with mock.patch.object(sys, "argv", ["scrape_prayer.py", *argv]):
        return scrape_prayer.parse_args()


def parse_error(*argv):
    err = io.StringIO()
    with redirect_stderr(err):
        try:
            parse(*argv)
        except SystemExit:
            return err.getvalue()
    raise AssertionError("expected the script to exit")


def full_day(day, gov, deleg):
    return {col: "05:00" for col in scrape_prayer.COLUMNS} | {"DATE": day.isoformat()}


class ZonesTest(unittest.TestCase):
    def test_every_governorate_is_a_zone(self):
        self.assertEqual(len(scrape_prayer.GOVERNORATES), 24)
        for gov in scrape_prayer.GOVERNORATES:
            self.assertIn(scrape_prayer.slug(gov["name"]), scrape_prayer.ZONES)

    def test_governorate_means_its_main_city(self):
        self.assertEqual(scrape_prayer.ZONES["tunis"], (342, 615))

    def test_delegation_zone(self):
        self.assertEqual(scrape_prayer.ZONES["tunis/carthage"], (342, 387))

    def test_main_city_has_no_delegation_zone(self):
        self.assertNotIn("sfax/sfax", scrape_prayer.ZONES)

    def test_names_have_no_accents_or_spaces(self):
        self.assertIn("beja", scrape_prayer.ZONES)
        self.assertIn("le-kef", scrape_prayer.ZONES)


class ParseArgsTest(unittest.TestCase):
    def test_single_zone(self):
        args = parse("--zone", "tunis", "--year", "2026")
        self.assertEqual(args.targets, [(342, 615, "tunis")])
        self.assertEqual(args.year, 2026)

    def test_zone_is_case_insensitive(self):
        self.assertEqual(parse("--zone", "Le-Kef").targets, parse("--zone", "le-kef").targets)

    def test_several_zones_with_spaces_and_commas(self):
        args = parse("--zone", "tunis,ariana", "tunis/carthage")
        self.assertEqual([t[2] for t in args.targets], ["tunis", "ariana", "tunis_carthage"])

    def test_repeated_zones_are_scraped_once(self):
        args = parse("--zone", "tunis", "tunis", "--zone", "tunis")
        self.assertEqual(len(args.targets), 1)

    def test_all_means_every_governorate(self):
        args = parse("--zone", "all", "tunis/carthage")
        self.assertEqual(len(args.targets), 25)
        self.assertEqual(args.targets[-1][2], "tunis_carthage")

    def test_ids_instead_of_zone(self):
        args = parse("--governorate", "342", "--delegation", "615")
        self.assertEqual(args.targets, [(342, 615, "342_615")])

    def test_default_year_is_current_year(self):
        self.assertEqual(parse("--zone", "tunis").year, date.today().year)

    def test_unknown_zone(self):
        self.assertIn("unknown zone 'sfax/sfax'", parse_error("--zone", "sfax/sfax"))

    def test_accents_are_not_accepted(self):
        self.assertIn("unknown zone", parse_error("--zone", "béja"))

    def test_name_needs_a_single_zone(self):
        self.assertIn("--name only works with a single zone",
                      parse_error("--zone", "tunis", "ariana", "--name", "x"))

    def test_governorate_needs_delegation(self):
        self.assertIn("must be given together", parse_error("--governorate", "342"))

    def test_no_zone_without_a_terminal(self):
        with mock.patch.object(sys.stdin, "isatty", return_value=False):
            self.assertIn("no zone given", parse_error())


class InteractiveTest(unittest.TestCase):
    def run_menus(self, *answers):
        args = argparse.Namespace(year=None)
        with mock.patch("builtins.input", side_effect=answers), redirect_stdout(io.StringIO()):
            scrape_prayer.ask_interactive(args)
        return args

    def test_main_city(self):
        tunis = [g["name"] for g in scrape_prayer.GOVERNORATES].index("Tunis") + 1
        gov = scrape_prayer.GOVERNORATES[tunis - 1]
        main = [d["id"] for d in gov["delegations"]].index(gov["main_delegation"]) + 1
        args = self.run_menus(str(tunis), str(main), "2026")
        self.assertEqual(args.targets, [(342, 615, "tunis")])
        self.assertEqual(args.year, 2026)

    def test_year_defaults_to_current_year(self):
        args = self.run_menus("1", "1", "")
        self.assertEqual(args.year, date.today().year)

    def test_no_other_choice(self):
        with self.assertRaises(StopIteration):  # 25 is refused, so it asks again
            self.run_menus("25")


class DescribeZonesTest(unittest.TestCase):
    def test_real_names(self):
        self.assertEqual(scrape_prayer.describe_zones("tunis, le-kef"), "Tunis, Le Kef")

    def test_delegation(self):
        self.assertEqual(scrape_prayer.describe_zones("tunis/carthage"), "Tunis/Carthage")

    def test_all(self):
        self.assertEqual(scrape_prayer.describe_zones("all"), "all governorates")
        self.assertEqual(scrape_prayer.describe_zones("all tunis tunis/carthage"),
                         "all governorates, Tunis/Carthage")


class ScrapeTest(unittest.TestCase):
    def setUp(self):
        self.out = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.out)
        self.sleeps = []
        patches = [
            mock.patch.object(scrape_prayer.time, "sleep", self.sleeps.append),
            mock.patch("sys.stdout", io.StringIO()),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def scrape(self, fetch, name="tunis_carthage", delay=0.2):
        with mock.patch.object(scrape_prayer, "fetch_day", fetch):
            return scrape_prayer.scrape_full_timetable(2026, 342, 387, name, self.out, delay)

    def read_csv(self, name="tunis_carthage", folder="Tunis_Carthage"):
        path = os.path.join(self.out, folder, f"prayer_times_tunisia_{name}_2026.csv")
        with open(path, encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def test_full_year_in_a_capitalized_zone_folder(self):
        self.assertTrue(self.scrape(full_day))
        self.assertEqual(os.listdir(self.out), ["Tunis_Carthage"])
        rows = self.read_csv()
        self.assertEqual(len(rows), 365)
        self.assertEqual(list(rows[0]), scrape_prayer.COLUMNS)
        self.assertEqual(rows[0]["DATE"], "2026-01-01")
        self.assertEqual(rows[-1]["DATE"], "2026-12-31")

    def test_delay_varies_around_the_average(self):
        self.scrape(full_day, delay=2)
        self.assertTrue(all(1 <= s <= 3 for s in self.sleeps))
        self.assertGreater(len(set(self.sleeps)), 1)

    def test_failed_day_is_left_empty(self):
        def fetch(day, gov, deleg):
            if day == date(2026, 3, 1):
                raise ConnectionError("dropped")
            return full_day(day, gov, deleg)

        self.assertFalse(self.scrape(fetch))
        rows = self.read_csv()
        self.assertEqual(len(rows), 365)
        march_first = next(r for r in rows if r["DATE"] == "2026-03-01")
        self.assertEqual(march_first["FAJR"], "")

    def test_failed_first_day_writes_nothing(self):
        def fetch(day, gov, deleg):
            raise ConnectionError("wrong ids")

        self.assertFalse(self.scrape(fetch))
        self.assertEqual(os.listdir(os.path.join(self.out, "Tunis_Carthage")), [])


class YearFilesTest(unittest.TestCase):
    def setUp(self):
        self.out = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.out)

    def add(self, names, year=2027):
        for name in names:
            folder = os.path.join(self.out, name.title())
            os.makedirs(folder, exist_ok=True)
            open(os.path.join(folder, f"prayer_times_tunisia_{name}_{year}.csv"), "w").close()

    def test_every_governorate(self):
        self.add([z for z in scrape_prayer.ZONES if "/" not in z])
        files = scrape_prayer.year_files(2027, self.out)
        self.assertEqual(len(files), 24)
        self.assertIn(os.path.join(self.out, "Le-Kef", "prayer_times_tunisia_le-kef_2027.csv"), files)

    def test_none_if_one_is_missing(self):
        self.add([z for z in scrape_prayer.ZONES if "/" not in z and z != "tunis"])
        self.assertIsNone(scrape_prayer.year_files(2027, self.out))


class FetchDayTest(unittest.TestCase):
    def test_maps_the_meteo_tn_fields(self):
        answers = {
            "horaire": {"sobh": "05:59", "dhohr": "12:30", "aser": "14:55",
                        "magreb": "17:16", "isha": "18:47"},
            "lever": {"lever": "07:31"},
        }
        with mock.patch.object(scrape_prayer, "get_data",
                               lambda url: answers["lever" if "lever" in url else "horaire"]):
            row = scrape_prayer.fetch_day(date(2026, 1, 1), 342, 615)
        self.assertEqual(row, {"DATE": "2026-01-01", "FAJR": "05:59", "SUNRISE": "07:31",
                               "DHUHR": "12:30", "ASR": "14:55", "MAGHRIB": "17:16",
                               "ISHA": "18:47"})


if __name__ == "__main__":
    unittest.main()
