#!/usr/bin/env python3
"""
Generate assets/cv.pdf from the data/*.yaml files.

The YAML files under data/ are the single source of truth for both the website
and the CV PDF. This script composes a Typst document (Typst ships inside
Quarto, so no LaTeX install is needed) and compiles it:

    python scripts/build_cv.py            # writes _cv/cv.typ, then assets/cv.pdf

Layout mirrors the previous LaTeX CV: A4, 1in margins, 11pt serif, two-column
entries with the date in a narrow left column.

CV-specific fields recognised in the data files (all optional):
  cv_section  where an entry appears on the CV (see comments in each file)
  cv_label    full override of an entry's CV line
  cv_note     short suffix appended to an entry's CV line
  cv_role     teaching role label on the CV (e.g. "coordinator")
  cv_with     co-organiser names for conference organisation
Prose that exists only on the CV (supervision summary, evaluation averages)
lives in data/cv.yaml.
"""

import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def load(name, default=list):
    path = DATA / name
    if not path.exists():
        return default()
    with open(path) as f:
        return yaml.safe_load(f) or default()


# ── Typst helpers ─────────────────────────────────────────────────────────────

def esc(s) -> str:
    """Escape Typst markup characters in plain text."""
    s = str(s)
    s = s.replace("\\", "\\\\")
    for ch in '#$*_[]<>@`~':
        s = s.replace(ch, "\\" + ch)
    return s


def emph(s) -> str:
    return f"#emph[{s}]"


def strong(s) -> str:
    return f"#strong[{s}]"


def typlink(url, label) -> str:
    return f'#link("{url}")[{label}]'


def entry(datecol, body) -> str:
    return f"#entry[{datecol}][{body}]"


# A ";" directly after a #link(...)[...] call is parsed as a Typst code
# terminator and swallowed; wrap separators in a content block instead.
SEMI = "#[;] "


def with_period(s: str) -> str:
    """Append a period unless the text already ends in sentence punctuation."""
    return s if s.rstrip().endswith((".", "!", "?")) else s + "."


def section(title) -> str:
    return f"#sec[{esc(title)}]"


# ── Formatting helpers ────────────────────────────────────────────────────────

def period(start, end) -> str:
    """'Since 2023' when open-ended; '2022–2024' when closed; '2021' when equal."""
    if not start:
        return ""
    if end is None:
        return f"Since {start}"
    if str(end) == str(start):
        return str(start)
    return f"{start}–{end}"


def short_name(full: str) -> str:
    """'Julian Ashwin' → 'Ashwin, J.'; 'Jan-Peter Calliess' → 'Calliess, J.-P.';
    'Katrin Forster van Aerssen' → 'Forster van Aerssen, K.' (first token = given names)."""
    parts = full.split()
    if len(parts) == 1:
        return full
    given, surname = parts[0], " ".join(parts[1:])
    initials = "-".join(p[0] + "." for p in given.split("-"))
    return f"{surname}, {initials}"


def author_line(authors, me="Julian Ashwin") -> str:
    """'Ashwin, J., Bloom, D., and Scott, A.' with the CV owner in bold."""
    names = []
    for a in authors:
        s = esc(short_name(a))
        names.append(strong(s) if a.strip().lower() == me.lower() else s)
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + f", and {names[-1]}"


def join_parts(*parts) -> str:
    return ", ".join(p for p in (str(x).strip() for x in parts if x) if p)


def year_span(years) -> str:
    """['2023–24','2024–25','2025–26'] → '2023–26'; ['2022'] → '2022'."""
    if not years:
        return ""
    firsts = [str(y).split("–")[0] for y in years]
    lasts = [str(y).split("–")[-1] for y in years]
    start, end = min(firsts), max(lasts, key=lambda s: (len(s), s))
    return start if start == end else f"{start}–{end}"


# ── Section builders ──────────────────────────────────────────────────────────

def build_contact(profile):
    dept = esc(join_parts(profile.get("department_full"), ""))
    inst_line = f"{dept}; {esc(profile.get('department', ''))}, {esc(profile.get('institution', ''))}"
    email = profile.get("email", "")
    website = profile.get("website", "")
    scholar = profile.get("google_scholar", "")
    contact_bits = []
    if email:
        contact_bits.append(f'Email: {typlink("mailto:" + email, esc(email))}')
    if website:
        label = esc(website.replace("https://", "").replace("http://", "").rstrip("/"))
        contact_bits.append(f'Website: {typlink(website, label)}')
    if scholar:
        contact_bits.append(f'Google Scholar: {typlink(scholar, "link")}')
    lines = [section("Contact"), inst_line + r" \ "]
    if profile.get("address"):
        lines.append(esc(profile["address"]) + r" \ ")
    lines.append(SEMI.join(contact_bits))
    return lines


def appointment_line(a):
    if a.get("cv_label"):
        return esc(a["cv_label"])
    return esc(join_parts(a.get("title"), a.get("department"), a.get("institution"), a.get("cv_note")))


def build_employment(appointments):
    lines = [section("Employment")]
    by_start = lambda xs: sorted(xs, key=lambda a: a.get("period_start") or 0, reverse=True)
    main = [a for a in appointments if a.get("cv_section") == "employment"]
    affil = [a for a in appointments if a.get("cv_section") == "affiliation"]
    for a in by_start(main):
        lines.append(entry(period(a.get("period_start"), a.get("period_end")), appointment_line(a)))
    if affil:
        lines.append("#subhead[Other appointments and affiliations]")
        for a in by_start(affil):
            lines.append(entry(period(a.get("period_start"), a.get("period_end")), appointment_line(a)))
    return lines


def build_other_employment(appointments):
    other = [a for a in appointments if a.get("cv_section") == "other"]
    if not other:
        return []
    lines = [section("Other Employment")]
    for a in sorted(other, key=lambda a: a.get("period_start") or 0, reverse=True):
        lines.append(entry(period(a.get("period_start"), a.get("period_end")), appointment_line(a)))
    return lines


def build_education(education):
    lines = [section("Education")]
    for e in education:
        degree = esc(e["degree"])
        if e.get("notes"):
            degree += f" ({esc(e['notes'])})"
        body = f"{degree}, {esc(e.get('institution', ''))}"
        if e.get("cv_note"):
            body += r" \ " + esc(e["cv_note"])
        start, end = e.get("year_start"), e.get("year")
        datecol = f"{start}–{end}" if start else str(end or "")
        lines.append(entry(datecol, body))
    return lines


def publication_body(p):
    body = with_period(author_line(p.get("authors", []))) + " "
    body += emph(with_period(esc(p["title"]))) + " "
    if p.get("journal"):
        j = esc(p["journal"])
        if p.get("pages"):
            j += f", pp. {esc(p['pages'])}"
        body += emph(j + ".")
    if p.get("doi"):
        body += " " + typlink(f"https://doi.org/{p['doi']}", esc(f"doi:{p['doi']}"))
    return body


def build_publications(pubs):
    lines = [section("Publications")]
    pubs = sorted(pubs, key=lambda x: x.get("year") or 0, reverse=True)
    prev_year = None
    for p in pubs:
        year = p.get("year")
        datecol = str(year) if year and year != prev_year else ""
        prev_year = year
        lines.append(entry(datecol, publication_body(p)))
    return lines


def build_working_papers(wps):
    lines = [section("Working Papers")]
    wps = sorted(wps, key=lambda x: x.get("year") or 9999, reverse=True)
    for p in wps:
        body = with_period(author_line(p.get("authors", []))) + " "
        body += emph(with_period(esc(p["title"])))
        if p.get("cv_note"):
            body += " " + esc(p["cv_note"])
        lines.append(entry(str(p.get("year") or ""), body))
    return lines


def build_policy_pubs(pols):
    if not pols:
        return []
    lines = [section("Policy Publications")]
    for p in sorted(pols, key=lambda x: x.get("year") or 0, reverse=True):
        body = with_period(author_line(p.get("authors", []))) + " "
        body += emph(with_period(esc(p["title"]))) + " "
        outlet = emph(esc(p["outlet"]) + ".")
        body += typlink(p["url"], outlet) if p.get("url") else outlet
        lines.append(entry(str(p.get("year") or ""), body))
    return lines


def grant_line(g):
    label = esc(g["title"])
    short = g.get("funder_short", "")
    if short and not g["title"].startswith(short):
        label = f"{esc(short)} {label}"
    elif not short and g.get("funder"):
        label = f"{label}, {esc(g['funder'])}"
    if g.get("role"):
        label += f" ({esc(g['role'])})"
    amount = ""
    if g.get("amount"):
        amount = f"{esc(g.get('currency', ''))} {esc(g['amount'])}".strip()
        if g.get("amount_note"):
            amount += f" {esc(g['amount_note'])}"
        if g.get("approx"):
            amount = "approx. " + amount
        amount = ", " + amount
    return label + amount


def build_grants(grants):
    lines = [section("Grants & Fellowships")]
    for g in sorted(grants, key=lambda x: x.get("period_start") or 0, reverse=True):
        lines.append(entry(period(g.get("period_start"), g.get("period_end")), grant_line(g)))
    return lines


def build_prizes(prizes):
    if not prizes:
        return []
    lines = [section("Prizes & Awards")]
    for p in sorted(prizes, key=lambda x: x.get("year") or 0, reverse=True):
        lines.append(entry(str(p.get("year") or ""), esc(join_parts(p.get("title"), p.get("awarder")))))
    return lines


def build_teaching(teaching, cv_extra):
    lines = [section("Teaching")]
    maastricht = [c for c in teaching if c.get("institution") == "Maastricht University"]
    prior = [c for c in teaching if c.get("institution") != "Maastricht University"]

    intro = emph("Maastricht University") + " (since 2023)"
    if cv_extra.get("teaching_evaluations"):
        intro += "; " + esc(cv_extra["teaching_evaluations"].strip())
    lines.append(intro)
    lines.append("#v(2pt)")

    def sort_key(c):
        firsts = [str(y).split("–")[0] for y in c.get("years", [])]
        lasts = [str(y).split("–")[-1] for y in c.get("years", [])]
        return (max(lasts) if lasts else "", min(firsts) if firsts else "")

    for c in sorted(maastricht, key=sort_key, reverse=True):
        body = esc(c["course"])
        if c.get("code"):
            body += f" ({esc(c['code'])})"
        role = c.get("cv_role") or c.get("role", "")
        if role:
            body += " — " + esc(role)
        lines.append(entry(year_span(c.get("years")), body))

    if cv_extra.get("supervision"):
        lines.append("#v(3pt)")
        lines.append(emph("Supervision") + ": " + esc(cv_extra["supervision"].strip()))
        lines.append("#v(3pt)")

    # Group prior teaching by (institution, role); Oxford colleges merge into one line.
    groups = {}
    for c in prior:
        inst = c.get("institution", "")
        norm = "University of Oxford" if "University of Oxford" in inst else inst
        groups.setdefault((norm, c.get("role", "")), []).append(c)
    rows = []
    for (inst, role), cs in groups.items():
        years = [y for c in cs for y in c.get("years", [])]
        courses = "; ".join(esc(c["course"]) for c in cs)
        rows.append((year_span(years), f"{esc(role)}, {esc(inst)} ({courses})"))
    for datecol, body in sorted(rows, key=lambda r: r[0], reverse=True):
        lines.append(entry(datecol, body))
    return lines


SKIP_CITIES = {"", "online", "virtual", "usa", "uk"}


def presentation_label(p):
    if p.get("cv_label"):
        return esc(p["cv_label"])
    label = esc(p["title"])
    city = str(p.get("location", "")).split(",")[0].strip()
    if city.lower() not in SKIP_CITIES and city.lower() not in p["title"].lower():
        label += f", {esc(city)}"
    return label


def build_presentations(presentations):
    lines = [section("Selected Presentations")]
    by_year = {}
    for p in presentations:
        year = str(p.get("date", ""))[:4]
        by_year.setdefault(year, []).append(p)
    for year in sorted(by_year, reverse=True):
        items = sorted(by_year[year], key=lambda p: str(p.get("date", "")))
        lines.append(entry(year, "; ".join(presentation_label(p) for p in items)))
    return lines


def build_service(editorial, service, conf_org):
    lines = [section("Academic Service")]

    lines.append("#subhead[Editorial]")
    for r in [e for e in editorial if e.get("type") in ("editor", "associate-editor")]:
        datecol = str(r["since"]) if r.get("since") else ""
        lines.append(entry(datecol, esc(join_parts(r.get("role"), r.get("outlet")))))
    for s in [s for s in service if s.get("cv_section") == "editorial"]:
        lines.append(entry(period(s.get("period_start"), s.get("period_end")),
                           esc(s.get("cv_label") or s["role"])))

    lines.append("#subhead[Conference and seminar organisation]")
    for c in sorted(conf_org, key=lambda x: x.get("year") or 0, reverse=True):
        datecol = f"Since {c['year']}" if c.get("ongoing") else str(c.get("year") or "")
        role = esc(c.get("role", ""))
        if c.get("cv_with"):
            role += f" (with {esc(c['cv_with'])})"
        body = f"{role}, {esc(c['conference'])}"
        venue = str(c.get("location", "")).split(",")[0].strip()
        if venue and venue.lower() not in SKIP_CITIES and venue.lower() not in c["conference"].lower():
            body += f", {esc(venue)}"
        lines.append(entry(datecol, body))

    referee = [e["outlet"] for e in editorial if e.get("type") == "referee"]
    grant_review = [s.get("cv_label") or s["role"] for s in service if s.get("cv_section") == "refereeing"]
    if referee or grant_review:
        lines.append("#subhead[Refereeing]")
        para = "; ".join(esc(o) for o in referee) + "."
        if grant_review:
            para += " Grant review: " + "; ".join(esc(g) for g in grant_review) + "."
        lines.append(para)

    departmental = [s for s in service if s.get("cv_section") == "departmental"]
    if departmental:
        lines.append("#subhead[Departmental]")
        for s in sorted(departmental, key=lambda x: x.get("period_start") or 0, reverse=True):
            lines.append(entry(period(s.get("period_start"), s.get("period_end")),
                               esc(s.get("cv_label") or s["role"])))
    return lines


def dissemination_item(d, link_on_outlet=False):
    if link_on_outlet:
        label = esc(d.get("outlet", "") or d["title"])
        return typlink(d["url"], label) if d.get("url") else label
    title = emph(esc(d["title"]))
    if d.get("url"):
        title = typlink(d["url"], title)
    return f"{esc(d.get('outlet', ''))} ({title})"


def build_outreach(dissemination):
    lines = [section("Outreach & Dissemination")]
    newest_first = sorted(dissemination, key=lambda x: str(x.get("date", "")), reverse=True)
    groups = [
        ("Podcasts", "podcast", False),
        ("Video & software", "media", False),
        ("Blogs", "blog", True),
    ]
    for label, dtype, link_on_outlet in groups:
        items = [d for d in newest_first if d.get("type") == dtype]
        if items:
            lines.append(emph(label) + ": " + SEMI.join(dissemination_item(d, link_on_outlet) for d in items) + "#[.]")
            lines.append("#v(3pt)")
    if lines and lines[-1] == "#v(3pt)":
        lines.pop()
    return lines


def build_skills(profile):
    skills = profile.get("skills") or {}
    if not skills:
        return []
    lines = [section("Skills")]
    bits = []
    if skills.get("programming"):
        bits.append(strong("Programming") + ": " + esc(skills["programming"]) + ".")
    if skills.get("languages"):
        bits.append(strong("Languages") + ": " + esc(skills["languages"]) + ".")
    lines.append(" ".join(bits))
    return lines


# ── Document assembly ─────────────────────────────────────────────────────────

PREAMBLE = """\
// Generated by scripts/build_cv.py — do not edit by hand.
#set page(paper: "a4", margin: 1in)
#set text(font: "New Computer Modern", size: 11pt)
#set par(justify: true, leading: 0.55em)
#show link: set text(fill: blue)

#let datecolw = 1.9cm
#let entry(date, body) = {
  grid(columns: (datecolw, 1fr), column-gutter: 0pt, align(top + left, date), body)
  v(3pt)
}
#let sec(title) = {
  v(7pt)
  text(weight: "bold", title)
  v(4pt)
}
#let subhead(title) = {
  v(3pt)
  emph(title)
  v(3pt)
}
"""


def build_document():
    profile = load("profile.yaml", dict)
    cv_extra = load("cv.yaml", dict)
    appointments = load("appointments.yaml")
    education = load("education.yaml")
    pubs = load("publications.yaml")
    wps = load("working_papers.yaml")
    pols = load("policy_publications.yaml")
    grants = load("grants.yaml")
    prizes = load("prizes.yaml")
    teaching = load("teaching.yaml")
    presentations = load("presentations.yaml")
    editorial = load("editorial.yaml")
    service = load("service.yaml")
    conf_org = load("conference_org.yaml")
    dissemination = load("dissemination.yaml")

    header = (
        "#align(center)[\n"
        "  #strong[Curriculum Vitae] \\\n"
        f"  #strong[{esc(profile.get('name', ''))}] \\\n"
        f"  ({date.today().strftime('%B %Y')})\n"
        "]\n#v(4pt)"
    )

    blocks = [PREAMBLE, header]
    blocks += build_contact(profile)
    blocks += build_employment(appointments)
    blocks += build_education(education)
    blocks += build_publications(pubs)
    blocks += build_working_papers(wps)
    blocks += build_policy_pubs(pols)
    blocks += build_grants(grants)
    blocks += build_prizes(prizes)
    blocks += build_other_employment(appointments)
    blocks += build_teaching(teaching, cv_extra)
    blocks += build_presentations(presentations)
    blocks += build_service(editorial, service, conf_org)
    blocks += build_outreach(dissemination)
    blocks += build_skills(profile)
    return "\n".join(blocks) + "\n"


def main():
    out_dir = ROOT / "_cv"
    out_dir.mkdir(exist_ok=True)
    typ_path = out_dir / "cv.typ"
    typ_path.write_text(build_document())

    pdf_path = ROOT / "assets" / "cv.pdf"
    result = subprocess.run(
        ["quarto", "typst", "compile", str(typ_path), str(pdf_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout + result.stderr)
        sys.exit(f"Typst compilation failed (source kept at {typ_path})")
    print(f"CV written to {pdf_path}")


if __name__ == "__main__":
    main()
