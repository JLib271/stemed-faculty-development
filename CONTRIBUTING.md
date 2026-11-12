# Adding or updating a program

Each program is one YAML file in `programs/`, named for the program (for example `maa-project-next.yml`).
The full list of fields, with descriptions, is in `schema/program.schema.json`.

## Before you add a program

1. **Check it is open to people from many institutions.** A program a single campus runs for its own faculty,
   graduate students, or postdocs is not listed, and neither are state or regional programs (such as MAA section
   NExT programs).
2. **Check who runs it.** A national society or association, a US federal agency, a national program with federal
   agency funds, or a national private foundation or nonprofit must be named on its own website as running or
   funding the program. For a "Federally funded program", say which agency in `funding_note`.
3. **Check who it is for.** College and university faculty and instructors, or graduate students and postdocs
   preparing to teach, in a STEM+ field. The program should be about teaching, learning, mentoring, or the
   academic career, not only research methods in the discipline.
4. **Leave out anything run by a company, and anything you are unsure about.** Teaching conferences belong on
   STEMEd+ Conferences instead.

## Example

```yaml
name: Workshop for Early Career Geoscience Faculty
providers: [National Association of Geoscience Teachers]
sponsor_type: US society               # US society | International society | US federal agency | Federally funded program | Private foundation or nonprofit
funding_note: Supported by NAGT and the National Science Foundation.
type: institute                        # fellowship | institute | course | webinars | network | coaching | credential | departmental | postdoc
audiences: [Faculty and instructors]   # and/or Graduate students and postdocs
career: [New or early-career]          # leave out if open to any stage; also Mid-career and beyond | Leaders and chairs
disciplines: [Earth Science]           # leave out for programs open to all STEM+ fields
format: in person                      # in person | online | hybrid | varies
cost: fee                              # free | stipend | members | fee | varies
cost_note: Includes lodging and some meals; stipends are available by application.
institutions: US institutions only.    # only if limited
url: https://serc.carleton.edu/NAGTWorkshops/earlycareer2027/index.html
frequency: annual                      # annual | twice a year | several times a year | ongoing | irregular
schedule: Five days each June; applications are due in March.
summary: For geoscience faculty in their first three years, on teaching, research, and managing an academic career.
checked: 2026-11-12                    # the day you checked the provider's pages
offerings:                             # optional: sessions, cohorts, or application rounds with dates
  - name: 2027 workshop
    start: 2027-06-20
    end: 2027-06-24
    location: Macalester College, Saint Paul, Minnesota
    url: https://serc.carleton.edu/NAGTWorkshops/earlycareer2027/index.html
    dates_source: official             # official | announced
    deadlines:
      - {label: Applications due, date: 2027-03-15, kind: application}   # application | registration | opens | other
```

A program that is not running this year gets `status: paused` and a `status_note` saying what the provider said.

Write the summary in your own words. Check the file with `python -m stemed_fd --validate`.
