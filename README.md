# julianashwin.github.io — Website update guide

This is the source for [julianashwin.com](https://julianashwin.com), built with [Quarto](https://quarto.org) and deployed automatically to GitHub Pages on every push to `main`.

---

## How the site works

All content is driven by **YAML data files** in the `data/` folder. You edit a YAML file, commit and push, and the site **and the CV PDF** rebuild automatically (usually within 1–2 minutes via GitHub Actions). The YAML files are the single source of truth — there is no separate CV to maintain.

You never need to touch the `.qmd` page files, `scripts/helpers.py`, or `scripts/build_cv.py` unless you want to change layout or add a new section type.

---

## File map

```
data/
  profile.yaml            ← bio, contact links, address, skills
  news.yaml               ← home-page news items (keep ~5–6 most recent)
  publications.yaml       ← peer-reviewed publications
  working_papers.yaml     ← working papers and preprints
  policy_publications.yaml ← policy pieces (CV only)
  grants.yaml             ← grants and scholarships
  prizes.yaml             ← prizes and awards
  teaching.yaml           ← courses taught
  presentations.yaml      ← conference and seminar presentations
  editorial.yaml          ← editorial roles and refereeing
  service.yaml            ← departmental/institutional service
  conference_org.yaml     ← conferences and workshops organised
  dissemination.yaml      ← podcasts, blogs, policy pieces
  appointments.yaml       ← employment history
  education.yaml          ← degrees
  cv.yaml                 ← CV-only prose (supervision summary, evaluation averages)

assets/
  photo.jpg               ← profile photo (replace to update)
  cv.pdf                  ← GENERATED — never edit; built by scripts/build_cv.py

scripts/helpers.py        ← website rendering logic (rarely needs editing)
scripts/build_cv.py       ← generates assets/cv.pdf from data/*.yaml
_quarto.yml               ← site config: navigation, theme, metadata
```

Several data files support optional `cv_*` fields (`cv_section`, `cv_label`, `cv_note`,
`cv_role`, `cv_with`) that control how an entry appears on the CV PDF — each file's
header comment documents the ones it uses.

---

## Updating content

### Add a publication
Open `data/publications.yaml` and add a new block at the top (the site sorts by `year` automatically):

```yaml
- title: "Your Paper Title"
  authors:
    - "Julian Ashwin"
    - "Co-Author Name"
  year: 2026
  journal: "Journal Name"
  doi: "10.xxxx/xxxxxx"        # DOI only, not the full URL
  media:                        # optional: related blog posts / podcasts
    - label: "VoxDev"
      url: "https://..."
```

### Add a news item
Open `data/news.yaml`. Keep the list to ~5–6 items and remove old ones. Markdown links and *italic* are supported:

```yaml
- date: "2026-06"
  text: >
    New paper "[Paper Title](https://doi.org/...)" accepted at *Journal Name*.
```

### Update your bio or contact details
Edit `data/profile.yaml`. The `bio` field supports Markdown links (`[text](url)`) and *italic*.

### Add a grant
Open `data/grants.yaml` and add a block. Entries are sorted by `period_start` (newest first):

```yaml
- title: "Grant Name"
  funder: "Funder Full Name"
  funder_short: "NWO"
  amount: "320,000"
  currency: "EUR"
  role: "PI"          # PI | Co-PI | Co-I | Researcher
  period_start: 2026
  period_end: null    # null = present
  description: ""
  url: ""
```

### Add a presentation
Open `data/presentations.yaml`. Use `YYYY-MM` for the date (or `YYYY-MM-DD` if known):

```yaml
- title: "Paper or Talk Title"
  type: "conference"   # seminar | conference | invited | workshop | keynote
  venue: "Conference Name"
  location: "City, Country"
  date: "2026-06"
```

---

## Previewing locally

Make sure you have run `make install` once to set up the Python virtual environment.

```bash
make preview
```

This starts a live-reload preview at `http://localhost:4848`. Changes to YAML files appear after a page refresh (Quarto re-executes the Python cells on every save).

---

## Deploying

Simply commit and push to `main`:

```bash
git add data/publications.yaml   # or whichever files you changed
git commit -m "Add 2026 paper to publications"
git push
```

GitHub Actions rebuilds and deploys the site automatically. Check the **Actions** tab on GitHub to monitor the build (takes ~1–2 minutes).

---

## The CV PDF

`assets/cv.pdf` is **generated automatically** from the same `data/*.yaml` files that
drive the website — there is nothing separate to update. Every push to `main` rebuilds
it in CI (via Typst, which ships inside Quarto; no LaTeX needed), so adding a paper to
`publications.yaml` updates the website *and* the CV in one edit.

To preview the PDF locally:

```bash
make cv        # writes assets/cv.pdf (and the Typst source to _cv/cv.typ)
```

The CV's header date is set automatically to the month it is built. The old LaTeX
source (`website_etc/CV/cv_julian_ashwin.tex`) is retired and kept only as an archive.

---

## Adding a profile photo

Replace `assets/photo.jpg` with your preferred image (any JPEG, ideally square or portrait, at least 400 × 400 px). The site resizes it automatically.

---

## Changing the navigation

Edit `_quarto.yml` — the `website.navbar.left` list controls which pages appear in the menu.
