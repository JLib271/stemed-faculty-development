"""Read the program listings and write the website, feed, and calendar.

    python -m stemed_fd --out output --previous https://<owner>.github.io/<repo>
    python -m stemed_fd --validate      # only check programs/*.yml

Output (all static, served by GitHub Pages):
    index.html              searchable list of programs
    programs.json           everything listed; also tells the next run when each program was first seen
    feeds/new.xml           RSS of newly listed programs
    feeds/deadlines.ics     calendar of when applications open and close
"""
import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional
from urllib.request import Request, urlopen

from . import feeds, listings
from .disciplines import DISCIPLINES

ROOT = Path(__file__).resolve().parent.parent
USER_AGENT = "STEMEd+ Faculty Development (https://github.com/JLib271/stemed-faculty-development)"
ASSETS = ("stemedplus-commons-logo.png", "stemedplus-commons-logo-white.png", "stemedplus-theme.css", "manrope.woff")


def load_config(name: str) -> dict:
    return json.loads((ROOT / "config" / name).read_text(encoding="utf-8"))


def load_previous(previous: Optional[str]) -> List[dict]:
    """Programs from the last published programs.json (a URL or a local path). A missing
    or unreadable file just means a fresh start, e.g. on the very first run."""
    if not previous:
        return []
    try:
        if previous.startswith(("http://", "https://")):
            url = previous.rstrip("/") + "/programs.json"
            with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=60) as resp:
                data = json.load(resp)
        else:
            data = json.loads(Path(previous).read_text(encoding="utf-8"))
        return data.get("programs", [])
    except Exception as exc:  # noqa: BLE001 - any failure means "start fresh"
        print(f"Note: no previous listings loaded from {previous} ({exc}).")
        return []


def _order(p: dict) -> tuple:
    """Open for applications first (soonest deadline first), then anything with a date coming,
    then ongoing programs, then paused ones."""
    if p["status"] == "paused":
        return (3, "", p["name"].lower())
    if p["open"]:
        return (0, p["next"], p["name"].lower())
    if p["next"]:
        return (1, p["next"], p["name"].lower())
    return (2, "", p["name"].lower())


def run(out: Path, previous: Optional[str], today: dt.date, now: Optional[dt.datetime] = None) -> dict:
    now = now or dt.datetime.combine(today, dt.time(12), tzinfo=dt.timezone.utc)
    site = load_config("site.json")
    first_seen: Dict[str, str] = {p["id"]: p.get("first_seen", today.isoformat()) for p in load_previous(previous)}

    entries, problems = listings.load()
    if problems:
        raise SystemExit("Problems in programs/:\n  " + "\n  ".join(problems))
    programs = [listings.to_record(slug, data, today) for slug, data in entries]
    for p in programs:
        p["first_seen"] = first_seen.get(p["id"], today.isoformat())
    programs.sort(key=_order)

    payload = {
        "generated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "today": today.isoformat(),
        "site": site,
        "disciplines": list(DISCIPLINES),
        "types": listings.TYPE_LABELS,
        "costs": listings.COST_LABELS,
        "audiences": listings.AUDIENCES,
        "career": listings.CAREER,
        "sponsor_types": listings.SPONSOR_TYPES,
        "review": [{"title": p["name"], "file": p["file"], "why": p["review"]} for p in programs if p["review"]],
        "programs": programs,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "programs.json").write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
                                       encoding="utf-8")
    shutil.copyfile(ROOT / "site" / "index.html", out / "index.html")
    for name in ASSETS:
        shutil.copyfile(ROOT / "site" / name, out / name)
    feeds.write_rss(out / "feeds" / "new.xml", programs, site, now)
    feeds.write_ics(out / "feeds", programs, site, now)
    print(f"Wrote {len(programs)} program(s), {sum(p['open'] for p in programs)} open for applications; "
          f"{len(payload['review'])} to re-check.")
    return payload


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path("output"))
    ap.add_argument("--previous", help="URL of the published site (or a local programs.json)")
    ap.add_argument("--validate", action="store_true", help="only check programs/*.yml")
    args = ap.parse_args(argv)
    if args.validate:
        entries, problems = listings.load()
        for p in problems:
            print(p)
        print(f"{len(entries)} valid file(s), {len(problems)} problem(s).")
        return 1 if problems else 0
    run(args.out, args.previous, dt.date.today())
    return 0


if __name__ == "__main__":
    sys.exit(main())
