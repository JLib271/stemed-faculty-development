import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from stemed_fd import build, feeds, listings

TODAY = dt.date(2026, 11, 12)

PROGRAM = {
    "name": "Example Society Summer Institute",
    "providers": ["Example Society"],
    "sponsor_type": "US society",
    "type": "institute",
    "audiences": ["Faculty and instructors", "Graduate students and postdocs"],
    "career": ["New or early-career"],
    "disciplines": ["Physics"],
    "format": "in person",
    "cost": "stipend",
    "url": "https://example.org/institute",
    "frequency": "annual",
    "schedule": "Every July; apply by March.",
    "summary": "A week of hands-on physics teaching practice for new faculty and postdocs.",
    "checked": "2026-11-01",
    "offerings": [
        {"name": "Summer 2026", "start": "2026-07-01", "end": "2026-07-05", "url": "https://example.org/2026",
         "dates_source": "official", "deadlines": [{"label": "Applications due", "date": "2026-03-01", "kind": "application"}]},
        {"name": "Summer 2027", "start": "2027-07-01", "end": "2027-07-05", "location": "Denver, Colorado",
         "url": "https://example.org/2027", "dates_source": "official",
         "deadlines": [{"label": "Applications open", "date": "2026-11-01", "kind": "opens"},
                       {"label": "Applications due", "date": "2027-03-01", "kind": "application"}]},
    ],
}


def write(folder: Path, name: str, data: dict) -> None:
    (folder / f"{name}.yml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


class ListingTests(unittest.TestCase):
    def test_every_listing_is_valid(self):
        entries, problems = listings.load()
        self.assertEqual(problems, [])
        self.assertGreaterEqual(len(entries), 12)

    def test_listings_cover_both_audiences(self):
        entries = listings.load()[0]
        for audience in listings.AUDIENCES:
            self.assertTrue(any(audience in p["audiences"] for _, p in entries), audience)

    def test_listings_use_https(self):
        for slug, p in listings.load()[0]:
            self.assertTrue(p["url"].startswith("https://"), slug)
            for o in p.get("offerings", []):
                self.assertTrue(o["url"].startswith("https://"), slug)

    def test_no_campus_only_programs(self):
        """The site promises programs open to people from many institutions; catch obvious campus-only listings."""
        for slug, p in listings.load()[0]:
            text = " ".join([p["name"]] + p["providers"] + [p.get("institutions", "")]).lower()
            self.assertNotIn("center for teaching", text, slug)
            self.assertNotIn("only for our", text, slug)

    def test_bad_files_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            bad = dict(PROGRAM, disciplines=["Underwater Basket Weaving"])
            write(folder, "bad-discipline", bad)
            bad = dict(PROGRAM, audiences=["K-12 teachers"])
            write(folder, "bad-audience", bad)
            bad = dict(PROGRAM, status="paused")
            write(folder, "paused-no-note", bad)
            bad = json.loads(json.dumps(PROGRAM))
            bad["offerings"][1]["deadlines"][0]["date"] = "2027-04-01"
            write(folder, "opens-after-close", bad)
            bad = json.loads(json.dumps(PROGRAM))
            bad["offerings"][1]["end"] = "2027-06-01"
            write(folder, "ends-early", bad)
            bad = json.loads(json.dumps(PROGRAM))
            bad["offerings"].append({"name": "Someday", "url": "https://example.org/x", "dates_source": "announced"})
            write(folder, "no-dates", bad)
            entries, problems = listings.load(folder)
            self.assertEqual(entries, [])
            text = "\n".join(problems)
            for name in ("bad-discipline", "bad-audience", "paused-no-note", "opens-after-close", "ends-early", "no-dates"):
                self.assertIn(name, text)

    def test_record_drops_past_offerings_and_marks_open(self):
        r = listings.to_record("example", PROGRAM, TODAY)
        self.assertEqual([o["name"] for o in r["offerings"]], ["Summer 2027"])
        self.assertTrue(r["open"])
        self.assertEqual(r["next"], "2027-03-01")
        self.assertEqual(r["review"], [])

    def test_not_open_before_applications_open(self):
        r = listings.to_record("example", PROGRAM, dt.date(2026, 10, 1))
        self.assertFalse(r["open"])
        self.assertEqual(r["next"], "2026-11-01")

    def test_review_flags(self):
        old = dict(PROGRAM, checked="2025-01-01", status="paused", status_note="Not this year.")
        why = listings.to_record("example", old, TODAY)["review"]
        self.assertTrue(any("last checked" in w for w in why))
        self.assertTrue(any("paused" in w for w in why))
        soon = json.loads(json.dumps(PROGRAM))
        soon["offerings"][1]["dates_source"] = "announced"
        soon["offerings"][1]["deadlines"][1]["date"] = "2026-12-01"
        self.assertTrue(any("confirm" in w for w in listings.to_record("example", soon, TODAY)["review"]))


class BuildTests(unittest.TestCase):
    def test_build_writes_site_feeds_and_calendar(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder, out = Path(tmp) / "programs", Path(tmp) / "out"
            folder.mkdir()
            write(folder, "example", PROGRAM)
            paused = dict(PROGRAM, name="Paused Program", status="paused", status_note="Back in 2027.", offerings=[])
            write(folder, "paused", paused)
            ongoing = dict(PROGRAM, name="Ongoing Webinars", type="webinars", frequency="ongoing", offerings=[])
            write(folder, "ongoing", ongoing)
            previous = Path(tmp) / "previous.json"
            previous.write_text(json.dumps({"programs": [{"id": "program:example", "first_seen": "2026-01-01"}]}))
            real_load = listings.load
            with mock.patch.object(listings, "load", lambda: real_load(folder)):
                payload = build.run(out, str(previous), TODAY)
            names = [p["name"] for p in payload["programs"]]
            self.assertEqual(names, ["Example Society Summer Institute", "Ongoing Webinars", "Paused Program"])
            self.assertEqual(payload["programs"][0]["first_seen"], "2026-01-01")
            self.assertEqual(payload["programs"][1]["first_seen"], TODAY.isoformat())
            for f in ("index.html", "programs.json", "feeds/new.xml", "feeds/deadlines.ics", "stemedplus-theme.css"):
                self.assertTrue((out / f).exists(), f)
            ics = (out / "feeds" / "deadlines.ics").read_bytes().decode("utf-8")
            self.assertIn("DTSTART;VALUE=DATE:20270301", ics)
            self.assertNotIn("20260301", ics)            # passed deadlines are left out
            self.assertTrue(all(len(line.encode()) <= 75 for line in ics.split("\r\n")))
            rss = (out / "feeds" / "new.xml").read_text(encoding="utf-8")
            self.assertIn("Ongoing Webinars", rss)

    def test_describe_mentions_deadline_and_pause(self):
        r = listings.to_record("example", PROGRAM, TODAY)
        self.assertIn("Applications due: March 1, 2027", feeds.describe(r))
        paused = listings.to_record("p", dict(PROGRAM, status="paused", status_note="Back in 2027.", offerings=[]), TODAY)
        self.assertIn("Paused: Back in 2027", feeds.describe(paused))

    def test_page_states_scope(self):
        html = (build.ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.assertIn("programs a single campus runs for its own people", html)
        self.assertIn("graduate students and postdocs", html)
        tagline = build.load_config("site.json")["tagline"]
        self.assertIn("Campus-only programs are not included", tagline)


if __name__ == "__main__":
    unittest.main()
