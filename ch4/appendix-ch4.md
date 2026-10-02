## The company-profile Skill (Chapter 4)

Chapter 4 provides an overview of the company-profile Skill and walks through a few of its steps. This section holds the complete SKILL.md. The Skill also ships two reference files, two scripts and a mock company database. The SKILL.md points to each one by path.

````markdown
---
name: company-profile
description: Generate a polished one-page company profile PDF (investment-bank style tear sheet) for any private or public company, researched from high-quality free sources and optionally enriched from a private SQL financials database the user provides. Use this skill whenever the user asks for a company profile, tear sheet, one-pager, target profile, company snapshot, due-diligence brief, "perfil de empresa", or wants company data (NIF, shareholders, directors, financials, business description) compiled into a document — even if they don't say "PDF" or "profile" explicitly. Especially strong for Portuguese companies (Racius, publicacoes.mj.pt, eInforma), but works for any country.
---

# Company Profile One-Pager

Generate a confidential-memo-style company tear sheet: header with company name, website and logo; left column with business areas & location, photos, and shareholders; right column with a multi-year financial data table; branded footer.

## Workflow overview

1. **Identify and verify the company** — make sure you have the right entity before researching.
2. **Check the private database** — if the user has a financials database (SQL dump or SQLite), pull the financial table from it first.
3. **Research** — gather registry data, business description, people, and remaining financials from free sources.
4. **Fill the JSON spec** — write a `profile.json` following `references/profile-schema.md`.
5. **Generate the PDF** — run `scripts/generate_profile.py`.
6. **Verify and report** — visually check the PDF, then tell the user what came from where and what's missing.

## Step 1 — Identify and verify

Companies share names constantly (there are dozens of "Transportes Silva Lda"). Before researching, establish the exact legal entity:

- If the user gave a website, fetch it and extract the legal name, NIF/VAT number, and address (usually in the footer, "Contactos", privacy policy, or terms page).
- If only a name was given, search for `"<name>" site:racius.com` or `"<name>" NIF` (Portugal) or `"<name>" company registration <country>` and cross-check the industry/location against any context the user gave.
- If two or more plausible matches exist and you can ask the user, present the candidates (name, location, activity) and let them pick. If you cannot ask, choose the best match and state your identification reasoning prominently in your final report.

## Step 2 — Check the private database

Private-company financials are rarely free online, so teams usually keep them in an internal database. If the user pointed you at one (a `.sql` dump or a SQLite file), or their message/context implies an internal data source exists, query it before doing any web research on financials:

```bash
python3 <skill_path>/scripts/query_financials.py <database> "<company name or NIF>"
```

The helper loads `.sql` dumps into in-memory SQLite, matches by NIF (exact) or name (substring), and prints a ready-to-paste `financials` block for `profile.json` — including the standard row order (Revenue → EBITDA → operational metrics → balance-sheet items) with bold flags and spacers. When the database also carries `description`/`portfolio` columns or `shareholders`/`management` tables, those come back too, ready for the corresponding profile.json sections. Use `--list` to browse entries, `--raw` for plain rows. If the user's database has a different schema than the bundled one (see `assets/mock_company_db.sql`), inspect it with `sqlite3` and adapt the query; still produce the same row structure.

Precedence when sources conflict: **user's database > official filings > company statements > press**. Cite the database as the source in your report and in `units_note` (e.g. "€ thousands (company database)"). Database figures are still subject to the honesty rule — never pad missing years or columns.

### Demo entities — don't mix fictional and real data

If the company is found in the database but has no verifiable web presence (or the user says it's a demo), treat it as a **demo entity**: build the entire profile from the database — description, portfolio bullets, shareholders, management, financials — skip web research entirely, and state in your report that the profile is built from demo/fictional data. Mixing invented database figures with real web-researched facts about a real company produces a document that is wrong in both directions; keep each profile purely one or the other.

`assets/mock_company_db.sql` is a 100-company fictional database bundled exactly for this: ids 4–100 (e.g. "Nortec Automation, Lda") are self-contained demo entities with full cap tables and descriptions. It also contains a few real company names carrying mock financials for pipeline testing — those deliberately have no shareholders/management rows, and their figures must never be presented as real.

## Step 3 — Research

Read `references/sources.md` for the per-field source guide (it has a detailed Portugal section — Racius, publicacoes.mj.pt, Portal da Empresa, eInforma — plus international equivalents). Collect:

- **Registry**: legal name, NIF/registration number, legal form, HQ address, incorporation date
- **Business**: what the company does, service/product portfolio, sectors served (from company website, LinkedIn)
- **People**: management/directors; shareholders with percentages when discoverable
- **Size**: employee count (LinkedIn range, registry bands)
- **Financials**: revenue, EBITDA, employees, debt, equity — whatever free sources actually publish

Run searches in parallel where possible. Prefer primary/official sources (official gazettes, registries, the company's own site) over aggregators; when aggregators disagree, note the discrepancy.

### The honesty rule for financials

This document looks authoritative — a fabricated number in it is worse than a blank. Never invent, extrapolate, or "estimate" financial figures. Every number in the table must trace to a source or to the user.

- Free sources often publish only fragments (one year of revenue, an employee band). Use what exists; put `n/a` in cells you can't source.
- If a figure is a stated estimate from a source, append `E` (e.g., `~4,850E`) and say so in your report.
- If financial coverage is too thin to make a useful table and no private database was provided (Step 2), ask the user for one — a `.sql`/SQLite file, pasted figures, or an export from SABI, Informa D&B, or Orbis — offering the exact row/year structure you need. If you cannot ask, generate the profile with `n/a` cells and clearly list what's missing.
- Percentages and ratios (growth, margins, NFD/EBITDA) may be *computed* from sourced figures — that's arithmetic, not invention.

## Step 4 — Fill the JSON spec

Write `profile.json` following `references/profile-schema.md` (read it — the schema doc includes a complete worked example). Notes:

- Keep business bullets to 3–4, each 1–3 lines, written in crisp banker prose ("Company specialized in…", "Comprehensive service portfolio, including (i)…, (ii)…").
- Financial values: pass numbers as numbers (the script formats thousands separators and renders negatives in parentheses); pass percentages/ratios as strings (`"15%"`, `"2.3x"`).
- Order the table like the reference layout: Revenue → COGS → Gross Margin → opex lines → EBITDA, then spacer, then operational metrics (Exports, Employees), then spacer, then balance-sheet items (Fixed Assets, Net Financial Debt, Equity). Bold the key rows. Omit rows you have no data for rather than filling a column of n/a — a shorter honest table beats a long empty one.
- Logo: if you found a clean logo image, download it and set `logo.path`. Otherwise leave it null — the script draws a placeholder monogram logo (or pick a pre-made one from `assets/logos/`). Same for photos: labeled gradient placeholder boxes are the default and are perfectly presentable. Many environments block binary image downloads — in that case don't burn time retrying; instead make the placeholders company-specific: derive the three photo labels from what the company actually does (e.g. a fruit-prep group gets "PHOTO: FRUIT PROCESSING LINE" / "PHOTO: R&D LAB" / "PHOTO: MAIA HQ", not generic labels), and pick the monogram shape that best matches the sector.

## Step 5 — Generate

```bash
python3 <skill_path>/scripts/generate_profile.py profile.json output.pdf
```

Requires `reportlab` (and `Pillow` only if embedding images). The script warns on stderr if content overflows the page — if it does, trim bullets or table rows and rerun.

## Step 6 — Verify and report

Convert the first page to an image (`pdftoppm -png -r 80 output.pdf check`) and look at it, or Read the PDF. Check: no overlapping text, table aligned, footer correct.

Then give the user a short sourcing report: which source each major data point came from (with links), what's `n/a` and why, any identity-verification caveats, and — if financials are thin — the offer to regenerate with user-provided numbers. Remind them that photos/logos scraped from the web are fine for internal mockups but need licensing review before external publication.
````
