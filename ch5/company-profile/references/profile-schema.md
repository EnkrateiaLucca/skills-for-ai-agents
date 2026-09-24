# profile.json schema

All fields optional unless marked required. The script degrades gracefully: missing sections are simply not drawn.

```jsonc
{
  "company_name": "Nortec Automation",        // required. Header splits first word (heavy) / rest (light)
  "display_bold": "NORTEC",                   // optional override for the heavy part
  "display_light": "AUTOMATION",              // optional override for the light part
  "website": "www.nortec-automation.com",

  "logo": {
    "path": null,                             // path to PNG/JPG → drawn in the header box
    "text": "NORTEC",                         // used by the generated monogram logo if path is null
    "shape": "triangle"                       // triangle | circle | diamond | hexagon | bars
  },

  "branding": {
    "firm_name": "Crest Capital Partners",    // footer, rendered uppercase
    "confidential": true,                     // appends "– STRICTLY CONFIDENTIAL"
    "page_number": 3                          // omit or null for no page number
  },

  "headquarters": "Aveiro, Portugal",         // rendered as the gray "Headquarters:" bar

  "registry_line": "NIF 501 234 567 · Sociedade por Quotas · Incorporated 1998",
                                              // optional small gray line under the HQ bar

  "business_bullets": [                       // 3–4 dash bullets, 1–3 lines each
    "Company specialized in engineering and integration of industrial automation systems, serving the automotive, food and packaging sectors",
    "Comprehensive service portfolio, including (i) design and assembly of automated production lines, (ii) collaborative robotics, (iii) machine vision and quality control systems, and (iv) retrofit of industrial equipment",
    "Complementary offering of preventive maintenance contracts and proprietary MES software for real-time production monitoring (including energy efficiency and OEE reporting modules)"
  ],

  "photos": [                                 // up to 3. path null → gradient placeholder box with label
    {"label": "PHOTO: PRODUCTION LINE", "path": null},
    {"label": "PHOTO: ROBOTIC CELL", "path": null},
    {"label": "PHOTO: ENGINEERING CENTER", "path": null}
  ],

  "shareholders": [                           // section skipped if empty
    {"name": "Rui Barbosa", "pct": "52.00%"},
    {"name": "Inês Correia", "pct": "33.00%"},
    {"name": "Vetta Capital SGPS", "pct": "15.00%"}
  ],
  "shareholders_note": null,                  // optional small gray note, e.g. "SA — share register not public; founders per 2009 incorporation act"

  "management": [                             // optional; rendered as a compact list under shareholders
    {"name": "Rui Barbosa", "role": "Managing Director"}
  ],

  "financials": {
    "title": "FINANCIAL DATA",
    "units_note": "€ thousands",              // small right-aligned gray note above the table
    "years": ["2021", "2022", "2023", "2024"],
    "rows": [
      // numbers → formatted with thousand separators; negatives in (parentheses)
      // strings → passed through verbatim (use for %, ratios, "n/a", "~4,850E")
      {"label": "Revenue",            "values": [4850, 5430, 6240, 7180], "bold": true},
      {"label": "Revenue Growth (%)", "values": ["7%", "12%", "15%", "15%"]},
      {"label": "COGS",               "values": [-2180, -2390, -2750, -3090]},
      {"label": "Gross Margin",       "values": [2670, 3040, 3490, 4090], "bold": true},
      {"label": "Gross Margin (%)",   "values": ["55%", "56%", "56%", "57%"]},
      {"label": "External Services",  "values": [-620, -671, -730, -795]},
      {"label": "Personnel Costs",    "values": [-1480, -1655, -1890, -2160]},
      {"label": "Other Gains & Losses","values": [-24, 31, 18, 22]},
      {"label": "EBITDA",             "values": [546, 745, 888, 1157], "bold": true},
      {"label": "EBITDA Margin (%)",  "values": ["11%", "14%", "14%", "16%"]},
      {"spacer": true},
      {"label": "Exports",            "values": [1940, 2340, 2870, 3590], "bold": true},
      {"label": "Exports (% of revenue)", "values": ["40%", "43%", "46%", "50%"]},
      {"label": "Employees",          "values": [62, 68, 77, 85], "bold": true},
      {"spacer": true},
      {"label": "Fixed Assets",       "values": [780, 842, 915, 1010], "bold": true},
      {"label": "Inventories",        "values": [430, 512, 568, 605]},
      {"label": "Net Financial Debt", "values": [1240, 1050, 790, 420], "bold": true},
      {"label": "NFD/EBITDA",         "values": ["2.3x", "1.4x", "0.9x", "0.4x"]},
      {"label": "Equity",             "values": [1120, 1398, 1745, 2210], "bold": true}
    ]
  },

  "sources_note": null                        // optional tiny footer-adjacent note, e.g. "Sources: Racius, publicacoes.mj.pt, company website"
}
```

Layout rules the script enforces:

- Bold financial rows get a light-gray background band; the year header row is navy with white text.
- 1–5 year columns supported; column widths adapt.
- The left column flows top-down (heading → HQ bar → registry line → bullets → photos → shareholders → management). If it overflows the page, the script prints a warning to stderr — trim bullets or drop the management section and rerun.
- Roughly 20 financial rows (including spacers) fit for 1-page layout; the script warns if the table overflows.
