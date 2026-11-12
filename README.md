# STEMEd+ Faculty Development

National professional development in teaching and learning for college and university faculty, instructors,
graduate students, and postdocs across STEM+ fields, with application deadlines in one place:
**https://jlib271.github.io/stemed-faculty-development/**

STEMEd+ Faculty Development is part of [STEMEd+ Commons](https://stemedplus.hcommons.org/), with
[STEMEd+ Professional Learning](https://jlib271.github.io/stemed-professional-learning/) (for K-12 teachers and
informal educators), [STEMEd+ Conferences](https://jlib271.github.io/stemed-conferences/),
[STEMEd+ Funding](https://jlib271.github.io/stemed-funding/), [STEMEd+ Jobs](https://jlib271.github.io/stemed-jobs/),
the [STEMEd+ Digest](https://jlib271.github.io/STEMEd-Digest/), the
[Graduate Programs](https://jlib271.github.io/stem-ed-research-programs/) list, and
[Find Collaborators](https://stemedplus.org/stemed-collaborators/).

## What is listed

- **Who it is for.** Faculty and instructors at colleges and universities, including lecturers, adjuncts, and
  two-year college faculty; and graduate students and postdocs preparing to teach. Each listing says which
  career stages it is designed for.
- **Who runs it.** Only programs run by a national scholarly or professional society or association (in the US
  or internationally), by a US federal agency, by a national program a federal agency funds (for example, NSF-supported
  QUBES Faculty Mentoring Networks), or by a national private foundation or nonprofit (for example, The POGIL
  Project or the Kern Family Foundation's KEEN workshops). The program must be open to people from many
  institutions. **If we are not sure, we leave it out.**
- **What kinds.** Fellowships and cohort programs, workshops and institutes, online courses, webinar series,
  mentoring networks, coaching, certificate programs, and workshops brought to your department.
- **What it shows.** Who it is for, career stage, cost and support, credit, format, how often it runs, and when
  applications open and close. Programs open for applications are listed first.

### Not included

- **Programs a single campus runs for its own people**, such as a teaching center's workshops or a university's
  own Mobile Summer Institute. The page says so at the top and points people to their campus teaching center.
- State and regional programs, such as MAA section NExT programs.
- Programs run by companies.
- Teaching conferences (BCCE, USCOTS, SABER, the ASEE Annual Conference, ...), which are on
  [STEMEd+ Conferences](https://jlib271.github.io/stemed-conferences/).

### Considered but not listed

The National Effective Teaching Institute (NETI) for engineering faculty: it began as an ASEE program, but its
current workshops are run by its co-directors at host universities, and we could not confirm a society or
national nonprofit sponsor. MAA OPEN Math online workshops: their NSF grant was planned to run through summer 2025,
and we could not confirm 2026 workshops. The Cottrell Scholars Collaborative New Faculty Workshop: we could not
confirm recent offerings.

Disciplines come from the list shared across STEMEd+ Commons, kept in [HuMeta](https://github.com/JLib271/HuMeta)
(`standard/humeta/stemedplus_disciplines.json`). Computer science is listed under Engineering and statistics under
Mathematics, as on the other sites.

## Feeds and calendars

| | |
|---|---|
| `feeds/deadlines.ics` | When applications open and close, for Google Calendar, Outlook, or Apple Calendar ("add calendar from URL") |
| `feeds/new.xml` | RSS of newly listed programs |
| `programs.json` | Everything on the site, for reuse |

## Add or correct a listing

- [Suggest a program](https://github.com/JLib271/stemed-faculty-development/issues/new?template=suggest_program.yml)
- [Report new dates or a correction](https://github.com/JLib271/stemed-faculty-development/issues/new?template=update_program.yml)
- No GitHub account? Email the maintainer, Julie Libarkin, at libarkin@msu.edu.

To edit directly, see [CONTRIBUTING.md](CONTRIBUTING.md). Each program is one YAML file in `programs/`,
checked against `schema/program.schema.json`.

## How it works

A GitHub Actions workflow (`.github/workflows/update.yml`) runs every day and on every push:

1. refreshes the shared discipline list from HuMeta;
2. runs the tests and checks every file in `programs/`;
3. builds the site into `output/` and publishes it to GitHub Pages. Sessions whose dates have all passed drop
   off, passed deadlines are marked, programs open for applications move to the top, and the date each program
   was first listed is carried over from the published `programs.json` for the RSS feed.

The footer's "For maintainers" box lists files to re-check: any not checked in 180 days, paused programs not
checked in 60 days, and any session with announced (not yet official) dates within 60 days.

Run it locally:

```sh
pip install -r requirements.txt
python -m unittest discover -s tests -t .
python -m stemed_fd --validate
python -m stemed_fd --out output    # then open output/index.html through a local web server
```

To publish: Settings → Pages → Source: **GitHub Actions**.

## License

Code: MIT ([LICENSE](LICENSE)). Listings in `programs/`: CC BY 4.0 ([programs/LICENSE.md](programs/LICENSE.md)).
