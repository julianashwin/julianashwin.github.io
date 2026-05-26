# julianashwin.github.io — Website update guide

This is the source for [julianashwin.com](https://julianashwin.com), built with [Quarto](https://quarto.org) and deployed automatically to GitHub Pages on every push to `main`.

---

## How the site works

All content is driven by **YAML data files** in the `data/` folder. You edit a YAML file, commit and push, and the site rebuilds automatically (usually within 1–2 minutes via GitHub Actions).

You never need to touch the `.qmd` page files or `scripts/helpers.py` unless you want to change layout or add a new section type.

---

## File map

```
data/
  profile.yaml          ← bio, contact links, research interests
  news.yaml             ← home-page news items (keep ~5–6 most recent)
  publications.yaml     ← peer-reviewed publications
  working_papers.yaml   ← working papers and preprints
  grants.yaml           ← grants and scholarships
  teaching.yaml         ← courses taught
  presentations.yaml    ← conference and seminar presentations
  editorial.yaml        ← editorial roles and refereeing
  service.yaml          ← departmental/institutional service
  conference_org.yaml   ← conferences and workshops organised
  dissemination.yaml    ← podcasts, blogs, policy pieces
  appointments.yaml     ← employment history (used in CV page)
  education.yaml        ← degrees (used in CV page)

assets/
  photo.jpg             ← profile photo (replace to update)
  cv.pdf                ← compiled CV PDF (see below)

scripts/helpers.py      ← rendering logic (rarely needs editing)
_quarto.yml             ← site config: navigation, theme, metadata
```

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

## Updating the CV PDF

The LaTeX source lives in the companion content repository:

```
website_etc/CV/cv_julian_ashwin.tex
```

To update and publish:

```bash
# 1. Edit the .tex file, then compile:
cd ~/Documents/GitHub/website_etc/CV
pdflatex cv_julian_ashwin.tex
pdflatex cv_julian_ashwin.tex   # second pass for correct hyperlinks

# 2. Copy the PDF into the website assets folder:
cp cv_julian_ashwin.pdf ~/Documents/GitHub/julianashwin.github.io/assets/cv.pdf

# 3. Commit and push:
cd ~/Documents/GitHub/julianashwin.github.io
git add assets/cv.pdf
git commit -m "Update CV PDF"
git push
```

The "CV (PDF)" link on the home page will point to the new file immediately after deployment.

---

## Adding a profile photo

Replace `assets/photo.jpg` with your preferred image (any JPEG, ideally square or portrait, at least 400 × 400 px). The site resizes it automatically.

---

## Changing the navigation

Edit `_quarto.yml` — the `website.navbar.left` list controls which pages appear in the menu.
