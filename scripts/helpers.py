"""
Rendering helpers for the Quarto academic website.

Each .qmd page imports this module and calls the relevant render_*() function,
which returns an HTML string that Quarto inserts into the page.

To add a new entry type, add a YAML file under data/ and write a new
render_*() function here following the same pattern as the existing ones.
"""

import yaml
from pathlib import Path
from datetime import datetime


# ── Data loading ─────────────────────────────────────────────────────────────

def load(filename: str) -> list:
    """Load a YAML data file from the data/ directory."""
    path = Path("data") / filename
    with open(path) as f:
        return yaml.safe_load(f) or []


def load_one(filename: str) -> dict:
    """Load a YAML file that contains a single mapping (not a list)."""
    path = Path("data") / filename
    with open(path) as f:
        return yaml.safe_load(f) or {}


# ── Formatting utilities ──────────────────────────────────────────────────────

def _esc(text: str) -> str:
    """Minimal HTML escaping."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _md(text: str) -> str:
    """
    Convert a small subset of Markdown to HTML for free-text fields
    (bio, news items): bold, italic, and [label](url) links.
    Full HTML is passed through unchanged.
    """
    import re
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    return text


def _authors(authors: list, highlight: str = "Julian Ashwin") -> str:
    """Format an author list; bold the entry that matches `highlight` exactly."""
    parts = []
    for a in authors:
        escaped = _esc(a)
        parts.append(f"<strong>{escaped}</strong>" if highlight.lower() == a.lower() else escaped)
    return ", ".join(parts)


def _links(**kwargs) -> str:
    """
    Render a row of pill-style links.
    Pass keyword arguments as label=url; entries with empty/None url are skipped.
    Example: _links(PDF="path/to/file.pdf", DOI="https://doi.org/...")
    """
    parts = []
    for label, url in kwargs.items():
        if url:
            parts.append(f'<a href="{url}" class="pub-link">{label}</a>')
    return f'<span class="pub-links">{"".join(parts)}</span>' if parts else ""


def _period(start, end) -> str:
    """Format a year range; end=None becomes 'present'."""
    end_str = "present" if end is None else str(end)
    return f"{start}–{end_str}" if start else ""


def _fmt_date(date_str: str) -> str:
    """Parse YYYY-MM-DD or YYYY-MM and return a readable string."""
    if not date_str:
        return ""
    s = str(date_str)
    try:
        if len(s) == 10:
            return datetime.strptime(s, "%Y-%m-%d").strftime("%B %Y")
        if len(s) == 7:
            return datetime.strptime(s, "%Y-%m").strftime("%B %Y")
    except ValueError:
        pass
    return s


# ── Page-level renderers ──────────────────────────────────────────────────────

def render_publications(pubs: list) -> str:
    if not pubs:
        return "<p><em>No publications listed yet.</em></p>"
    pubs = sorted(pubs, key=lambda x: x.get("year") or 0, reverse=True)
    rows = []
    for p in pubs:
        journal_line = ""
        if p.get("journal"):
            j = f"<em>{_esc(p['journal'])}</em>"
            if p.get("volume"):
                j += f", {p['volume']}"
            if p.get("issue"):
                j += f"({p['issue']})"
            if p.get("pages"):
                j += f", pp.&nbsp;{_esc(p['pages'])}"
            journal_line = f"<div>{j}</div>"

        doi_url = f"https://doi.org/{p['doi']}" if p.get("doi") else ""
        links = _links(PDF=p.get("pdf"), DOI=doi_url, Link=p.get("url"))

        abstract = ""
        if p.get("abstract"):
            abstract = (
                "<details><summary>Abstract</summary>"
                f'<div class="abstract-text">{_esc(p["abstract"])}</div>'
                "</details>"
            )

        year_str = f" ({p['year']})" if p.get("year") else ""
        rows.append(
            f'<div class="pub-entry">'
            f'<div><strong>{_esc(p["title"])}</strong>{year_str}</div>'
            f'<div>{_authors(p.get("authors", []))}</div>'
            f"{journal_line}"
            f"{links}{abstract}"
            f"</div>"
        )
    return "\n".join(rows)


def render_working_papers(wps: list) -> str:
    if not wps:
        return "<p><em>No working papers listed yet.</em></p>"
    wps = sorted(wps, key=lambda x: x.get("year") or 0, reverse=True)
    status_labels = {
        "working-paper": "Working paper",
        "under-review": "Under review",
        "revise-resubmit": "Revise & resubmit",
    }
    rows = []
    for p in wps:
        status = status_labels.get(p.get("status", ""), p.get("status", ""))
        ssrn_url = (
            p["ssrn"] if p.get("ssrn", "").startswith("http")
            else (f"https://ssrn.com/abstract={p['ssrn']}" if p.get("ssrn") else "")
        )
        links = _links(PDF=p.get("pdf"), SSRN=ssrn_url, Link=p.get("url"))
        abstract = ""
        if p.get("abstract"):
            abstract = (
                "<details><summary>Abstract</summary>"
                f'<div class="abstract-text">{_esc(p["abstract"])}</div>'
                "</details>"
            )
        year_str = f" ({p['year']})" if p.get("year") else ""
        rows.append(
            f'<div class="pub-entry">'
            f'<div><strong>{_esc(p["title"])}</strong>{year_str}</div>'
            f'<div>{_authors(p.get("authors", []))}</div>'
            f'<div><em>{status}</em></div>'
            f"{links}{abstract}"
            f"</div>"
        )
    return "\n".join(rows)


def render_grants(grants: list) -> str:
    if not grants:
        return "<p><em>No grants listed yet.</em></p>"
    grants = sorted(grants, key=lambda x: x.get("period_start", 0), reverse=True)
    rows = []
    for g in grants:
        period = _period(g.get("period_start"), g.get("period_end"))
        funder = g.get("funder_short") or g.get("funder", "")
        amount = ""
        if g.get("amount"):
            currency = g.get("currency", "")
            amount = f" · {currency}&nbsp;{_esc(str(g['amount']))}"
        role = g.get("role", "")
        meta = " · ".join(filter(None, [funder, role, period])) + amount
        link = f'<a href="{g["url"]}">[link]</a>' if g.get("url") else ""
        desc = f'<div style="font-size:0.9em">{_esc(g["description"])}</div>' if g.get("description") else ""
        rows.append(
            f'<div class="pub-entry">'
            f'<div><strong>{_esc(g["title"])}</strong> {link}</div>'
            f'<div style="color:var(--text-muted);font-size:0.9em">{meta}</div>'
            f"{desc}</div>"
        )
    return "\n".join(rows)


def render_teaching(courses: list) -> str:
    if not courses:
        return "<p><em>No courses listed yet.</em></p>"
    level_order = {"phd": 0, "masters": 1, "undergraduate": 2}
    level_labels = {"phd": "PhD", "masters": "Masters", "undergraduate": "Undergraduate"}
    courses = sorted(courses, key=lambda x: level_order.get(x.get("level", ""), 9))
    current_level = None
    rows = []
    for c in courses:
        level = c.get("level", "")
        if level != current_level:
            label = level_labels.get(level, level.title())
            rows.append(f'<h3 class="mt-4">{label}</h3>')
            current_level = level
        code = f" <span style='color:var(--text-muted)'>({_esc(c['code'])})</span>" if c.get("code") else ""
        years = ", ".join(c.get("years", []))
        desc = f'<div style="font-size:0.9em">{_esc(c["description"])}</div>' if c.get("description") else ""
        rows.append(
            f'<div class="pub-entry">'
            f'<div><strong>{_esc(c["course"])}</strong>{code} &nbsp;·&nbsp; {_esc(c.get("role",""))}</div>'
            f'<div style="color:var(--text-muted);font-size:0.9em">{years}</div>'
            f"{desc}</div>"
        )
    return "\n".join(rows)


def render_presentations(presentations: list) -> str:
    if not presentations:
        return "<p><em>No presentations listed yet.</em></p>"
    presentations = sorted(presentations, key=lambda x: str(x.get("date", "")), reverse=True)
    type_labels = {
        "seminar": "Seminar", "conference": "Conference", "keynote": "Keynote",
        "invited": "Invited talk", "workshop": "Workshop",
    }
    rows = []
    for p in presentations:
        date_str = _fmt_date(str(p.get("date", "")))
        ptype = type_labels.get(p.get("type", ""), p.get("type", "").title())
        venue = _esc(p.get("venue", ""))
        location = _esc(p.get("location", ""))
        links = _links(Slides=p.get("slides"), Link=p.get("url"))
        rows.append(
            f'<div class="pub-entry">'
            f'<div><strong>{_esc(p["title"])}</strong></div>'
            f'<div style="color:var(--text-muted);font-size:0.9em">'
            f'{ptype} &nbsp;·&nbsp; {venue} &nbsp;·&nbsp; {location} &nbsp;·&nbsp; {date_str}'
            f"</div>{links}</div>"
        )
    return "\n".join(rows)


def render_editorial(roles: list) -> str:
    if not roles:
        return "<p><em>No editorial roles listed yet.</em></p>"
    type_order = {"editor": 0, "associate-editor": 1, "referee": 2}
    roles = sorted(roles, key=lambda x: type_order.get(x.get("type", ""), 9))
    current_type = None
    type_labels = {"editor": "Editor", "associate-editor": "Associate Editor", "referee": "Referee"}
    rows = []
    for r in roles:
        rtype = r.get("type", "")
        if rtype != current_type:
            label = type_labels.get(rtype, rtype.title())
            rows.append(f'<h3 class="mt-4">{label}</h3>')
            current_type = rtype
        since = f" (since {r['since']})" if r.get("since") else ""
        rows.append(
            f'<div class="pub-entry">'
            f'<div>{_esc(r["outlet"])}{since}</div>'
            f"</div>"
        )
    return "\n".join(rows)


def render_service(items: list) -> str:
    if not items:
        return "<p><em>No service items listed yet.</em></p>"
    items = sorted(items, key=lambda x: x.get("period_start", 0), reverse=True)
    rows = []
    for s in items:
        period = _period(s.get("period_start"), s.get("period_end"))
        dept = _esc(s.get("department") or s.get("institution", ""))
        rows.append(
            f'<div class="pub-entry">'
            f'<div><strong>{_esc(s["role"])}</strong></div>'
            f'<div style="color:var(--text-muted);font-size:0.9em">{dept} &nbsp;·&nbsp; {period}</div>'
            f"</div>"
        )
    return "\n".join(rows)


def render_conference_org(items: list) -> str:
    if not items:
        return "<p><em>No conference organisation listed yet.</em></p>"
    items = sorted(items, key=lambda x: x.get("year", 0), reverse=True)
    rows = []
    for c in items:
        conf = _esc(c["conference"])
        link = f'<a href="{c["url"]}">{conf}</a>' if c.get("url") else conf
        location = _esc(c.get("location", ""))
        year = c.get("year", "")
        rows.append(
            f'<div class="pub-entry">'
            f'<div><strong>{_esc(c["role"])}</strong> &nbsp;·&nbsp; {link}</div>'
            f'<div style="color:var(--text-muted);font-size:0.9em">{location} &nbsp;·&nbsp; {year}</div>'
            f"</div>"
        )
    return "\n".join(rows)


def render_dissemination(items: list) -> str:
    if not items:
        return "<p><em>No outreach items listed yet.</em></p>"
    type_order = {"podcast": 0, "media": 1, "blog": 2, "policy": 3, "public-lecture": 4}
    type_labels = {
        "podcast": "Podcasts", "media": "Software & Media", "blog": "Blogs & Written Pieces",
        "policy": "Policy", "public-lecture": "Public Lectures",
    }
    # Sort by date descending first (stable), then by type order (stable) — gives type groups newest-first within each group.
    items = sorted(items, key=lambda x: str(x.get("date", "")), reverse=True)
    items = sorted(items, key=lambda x: type_order.get(x.get("type", ""), 9))
    current_type = None
    rows = []
    for item in items:
        itype = item.get("type", "")
        if itype != current_type:
            rows.append(f'<h3 class="mt-4">{type_labels.get(itype, itype.title())}</h3>')
            current_type = itype
        date_str = _fmt_date(str(item.get("date", "")))
        outlet = _esc(item.get("outlet", ""))
        title = _esc(item["title"])
        url = item.get("url", "")
        title_html = f'<a href="{url}">{title}</a>' if url else title
        desc = f'<div style="font-size:0.9em">{_esc(item["description"])}</div>' if item.get("description") else ""
        rows.append(
            f'<div class="pub-entry">'
            f"<div><strong>{title_html}</strong></div>"
            f'<div style="color:var(--text-muted);font-size:0.9em">{outlet} &nbsp;·&nbsp; {date_str}</div>'
            f"{desc}</div>"
        )
    return "\n".join(rows)


def render_news(items: list) -> str:
    if not items:
        return ""
    items = sorted(items, key=lambda x: str(x.get("date", "")), reverse=True)
    rows = []
    for n in items:
        date_str = _fmt_date(str(n.get("date", "")))
        rows.append(
            f'<div class="news-item">'
            f'<span class="news-date">{date_str}</span> {_md(n["text"])}'
            f"</div>"
        )
    return "\n".join(rows)
