"""RSS of newly listed programs, and a calendar of application and registration deadlines."""
import datetime as dt
from email.utils import format_datetime
from pathlib import Path
from typing import List
from xml.etree import ElementTree as ET

from .listings import COST_LABELS, TYPE_LABELS


def pretty(iso: str) -> str:
    d = dt.date.fromisoformat(iso)
    return f"{d:%B} {d.day}, {d.year}"


def describe(p: dict) -> str:
    parts = [TYPE_LABELS[p["type"]] + " for " + " and ".join(a.lower() for a in p["audiences"]),
             " and ".join(p["providers"]), COST_LABELS[p["cost"]]]
    upcoming = sorted((d for o in p["offerings"] for d in o["deadlines"] if not d["passed"] and d["kind"] != "other"),
                      key=lambda d: d["date"])
    if upcoming:
        parts.append(f"{upcoming[0]['label']}: {pretty(upcoming[0]['date'])}")
    if p["status"] == "paused":
        parts.append("Paused: " + p["status_note"])
    parts.append(p["summary"])
    return ". ".join(x.rstrip(".") for x in parts if x) + "."


def write_rss(path: Path, programs: List[dict], site: dict, now: dt.datetime) -> None:
    rss = ET.Element("rss", version="2.0")
    ch = ET.SubElement(rss, "channel")
    ET.SubElement(ch, "title").text = f"{site['title']}: newly listed programs"
    ET.SubElement(ch, "link").text = site["site_url"]
    ET.SubElement(ch, "description").text = site["tagline"]
    ET.SubElement(ch, "lastBuildDate").text = format_datetime(now)
    newest = sorted(programs, key=lambda p: (p["first_seen"], p["id"]), reverse=True)[: site.get("feed_size", 100)]
    for p in newest:
        e = ET.SubElement(ch, "item")
        ET.SubElement(e, "title").text = p["name"]
        ET.SubElement(e, "link").text = p["url"]
        ET.SubElement(e, "guid", isPermaLink="false").text = p["id"]
        ET.SubElement(e, "description").text = describe(p)
        day = dt.datetime.fromisoformat(p["first_seen"]).replace(tzinfo=dt.timezone.utc)
        ET.SubElement(e, "pubDate").text = format_datetime(day)
        for c in p["audiences"] + p["disciplines"] + [TYPE_LABELS[p["type"]]]:
            ET.SubElement(e, "category").text = c
    ET.indent(rss)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(rss, encoding="utf-8") + b"\n")


def _ics_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _fold(line: str) -> List[str]:
    """iCalendar lines are at most 75 octets; longer ones continue with a leading space."""
    out, data = [], line.encode("utf-8")
    while len(data) > 75:
        cut = 75 if not out else 74
        while cut and (data[cut] & 0xC0) == 0x80:   # do not split a UTF-8 character
            cut -= 1
        out.append(data[:cut].decode("utf-8"))
        data = data[cut:]
    out.append(data.decode("utf-8"))
    return [out[0]] + [" " + s for s in out[1:]]


def deadline_event(p: dict, o: dict, d: dict, stamp: str) -> List[str]:
    slug = "".join(c if c.isalnum() else "-" for c in d["label"].lower()).strip("-")
    last = (dt.date.fromisoformat(d["date"]) + dt.timedelta(days=1)).strftime("%Y%m%d")
    note = (d["note"] + " ") if d.get("note") else ""
    lines = ["BEGIN:VEVENT", f"UID:{o['id'].replace(':', '-')}-{slug}-{d['date']}@stemed-faculty-development",
             f"DTSTAMP:{stamp}", f"DTSTART;VALUE=DATE:{d['date'].replace('-', '')}", f"DTEND;VALUE=DATE:{last}",
             "SUMMARY:" + _ics_text(f"{d['label']}: {p['name']} ({o['name']})"),
             "DESCRIPTION:" + _ics_text(f"{note}{describe(p)} Always confirm on the provider's page: {o['url']}"),
             "URL:" + o["url"], "END:VEVENT"]
    return [part for line in lines for part in _fold(line)]


def write_ics(folder: Path, programs: List[dict], site: dict, now: dt.datetime) -> None:
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//STEMEd+//Faculty Development//EN", "CALSCALE:GREGORIAN"]
    lines += _fold("X-WR-CALNAME:" + _ics_text(f"{site['title']}: deadlines"))
    lines += _fold("X-WR-CALDESC:" + _ics_text(
        "When applications open and close for national teaching professional development for college faculty, "
        "instructors, graduate students, and postdocs. Always confirm on the provider's page."))
    for p in programs:
        for o in p["offerings"]:
            for d in o["deadlines"]:
                if not d["passed"] and d["kind"] != "other":
                    lines += deadline_event(p, o, d, stamp)
    lines.append("END:VCALENDAR")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "deadlines.ics").write_bytes(("\r\n".join(lines) + "\r\n").encode("utf-8"))
