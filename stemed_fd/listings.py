"""Professional learning programs kept by hand, one YAML file each in programs/."""
import datetime as dt
import json
from pathlib import Path
from typing import List, Optional, Tuple

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from .disciplines import DISCIPLINES

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "programs"
SCHEMA = json.loads((ROOT / "schema" / "program.schema.json").read_text(encoding="utf-8"))
# The allowed disciplines are the shared STEMEd+ list, not a copy in the schema file.
SCHEMA["properties"]["disciplines"]["items"] = {"enum": list(DISCIPLINES)}
REVIEW_AFTER_DAYS = 180
# Paused programs and dates a partner announced are worth a fresh look this often.
PAUSED_REVIEW_DAYS = 60
CONFIRM_WITHIN_DAYS = 60

TYPE_LABELS = {
    "fellowship": "Fellowship or cohort program",
    "institute": "Workshop or institute",
    "course": "Online course",
    "webinars": "Webinar series",
    "network": "Mentoring network or community of practice",
    "coaching": "Coaching or mentoring",
    "credential": "Certificate program",
    "departmental": "Workshop for your department or campus",
    "postdoc": "Teaching postdoc or teaching fellowship",
}
COST_LABELS = {
    "free": "Free",
    "stipend": "Free, with lodging, meals, or travel covered",
    "members": "Free for members",
    "fee": "Fee",
    "varies": "Cost varies",
}
AUDIENCES = ["Faculty and instructors", "Graduate students and postdocs"]
CAREER = ["New or early-career", "Mid-career and beyond", "Leaders and chairs"]
SPONSOR_TYPES = ["US society", "International society", "US federal agency", "Federally funded program",
                 "Private foundation or nonprofit"]
APPLY_KINDS = ("application", "registration")


def _plain(value):
    """YAML reads dates as date objects; the schema and the site want strings."""
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, list):
        return [_plain(v) for v in value]
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    return value


def _last_date(o: dict) -> Optional[str]:
    dates = [o[k] for k in ("start", "end") if o.get(k)] + [d["date"] for d in o.get("deadlines", [])]
    return max(dates) if dates else None


def _date_problems(data: dict) -> List[str]:
    problems = []
    for n, o in enumerate(data.get("offerings", [])):
        if o.get("end") and not o.get("start"):
            problems.append(f"offerings.{n}: has an end date but no start date")
        if o.get("start") and o.get("end") and o["end"] < o["start"]:
            problems.append(f"offerings.{n}: ends ({o['end']}) before it starts ({o['start']})")
        if not _last_date(o):
            problems.append(f"offerings.{n}: needs a start date or at least one deadline")
        deadlines = o.get("deadlines", [])
        opens = [d["date"] for d in deadlines if d.get("kind") == "opens"]
        closes = [d["date"] for d in deadlines if d.get("kind") in APPLY_KINDS]
        if opens and closes and max(opens) > min(closes):
            problems.append(f"offerings.{n}: applications open ({max(opens)}) after they close ({min(closes)})")
    if data.get("status") == "paused" and not data.get("status_note"):
        problems.append("status is paused, so add a status_note")
    return problems


def load(folder: Path = FOLDER) -> Tuple[List[Tuple[str, dict]], List[str]]:
    """(slug, program) for every valid file, and a list of problems."""
    validator = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
    entries, problems = [], []
    for path in sorted(folder.glob("*.yml")):
        try:
            data = _plain(yaml.safe_load(path.read_text(encoding="utf-8")))
        except yaml.YAMLError as exc:
            problems.append(f"{path.name}: not valid YAML ({exc})")
            continue
        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        for e in errors:
            where = ".".join(str(p) for p in e.path) or "(file)"
            problems.append(f"{path.name}: {where}: {e.message}")
        if errors:
            continue
        extra = _date_problems(data)
        problems += [f"{path.name}: {p}" for p in extra]
        if not extra:
            entries.append((path.stem, data))
    return entries, problems


def _offering(slug: str, n: int, o: dict, today_s: str) -> dict:
    deadlines = sorted(
        ({"label": d["label"], "date": d["date"], "kind": d.get("kind", "other"), "note": d.get("note", ""),
          "passed": d["date"] < today_s} for d in o.get("deadlines", [])),
        key=lambda d: d["date"])
    opens = [d["date"] for d in deadlines if d["kind"] == "opens"]
    closes = [d for d in deadlines if d["kind"] in APPLY_KINDS and not d["passed"]]
    is_open = bool(closes) and all(day <= today_s for day in opens)
    return {
        "id": f"offering:{slug}:{o.get('start') or _last_date(o)}:{n}",
        "name": o["name"],
        "start": o.get("start", ""),
        "end": o.get("end", o.get("start", "")),
        "location": o.get("location", ""),
        "format": o.get("format", ""),
        "url": o["url"],
        "dates_source": o["dates_source"],
        "note": o.get("note", ""),
        "deadlines": deadlines,
        "open": is_open,
        "happening": bool(o.get("start")) and o["start"] <= today_s <= (o.get("end") or o["start"]),
    }


def to_record(slug: str, p: dict, today: dt.date) -> dict:
    """The program, with the offerings that still have a date to come."""
    today_s = today.isoformat()
    offerings = [_offering(slug, n, o, today_s) for n, o in enumerate(p.get("offerings", []))
                 if _last_date(o) >= today_s]
    offerings.sort(key=lambda o: (o["start"] or min([d["date"] for d in o["deadlines"]] or ["9999"]), o["name"]))
    upcoming = [d["date"] for o in offerings for d in o["deadlines"] if not d["passed"] and d["kind"] != "other"]
    upcoming += [o["start"] for o in offerings if o["start"] and o["start"] >= today_s]
    status = p.get("status", "active")
    review = []
    if p["checked"] < (today - dt.timedelta(days=REVIEW_AFTER_DAYS)).isoformat():
        review.append(f"last checked {p['checked']}")
    if status == "paused" and p["checked"] < (today - dt.timedelta(days=PAUSED_REVIEW_DAYS)).isoformat():
        review.append("paused: check whether it is running again")
    soon = (today + dt.timedelta(days=CONFIRM_WITHIN_DAYS)).isoformat()
    for o in offerings:
        dates = [d["date"] for d in o["deadlines"] if not d["passed"]] + ([o["start"]] if o["start"] else [])
        if o["dates_source"] == "announced" and dates and min(dates) <= soon:
            review.append(f"confirm {o['name']} on the provider's page")
    return {
        "id": f"program:{slug}",
        "slug": slug,
        "name": p["name"],
        "short": p.get("short", ""),
        "providers": p["providers"],
        "sponsor_type": p["sponsor_type"],
        "funding_note": p.get("funding_note", ""),
        "type": p["type"],
        "audiences": p["audiences"],
        "career": p.get("career", []),
        "institutions": p.get("institutions", ""),
        "disciplines": p.get("disciplines", []),
        "all_fields": not p.get("disciplines"),
        "format": p.get("format", "varies"),
        "cost": p["cost"],
        "cost_note": p.get("cost_note", ""),
        "credit": p.get("credit", ""),
        "url": p["url"],
        "frequency": p["frequency"],
        "status": status,
        "status_note": p.get("status_note", ""),
        "schedule": p["schedule"],
        "summary": p["summary"],
        "checked": p["checked"],
        "offerings": offerings,
        "open": any(o["open"] for o in offerings),
        "next": min(upcoming) if upcoming else "",
        "review": review,
        "file": f"programs/{slug}.yml",
    }
