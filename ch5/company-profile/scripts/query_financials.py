#!/usr/bin/env python3
"""Query a private company-financials database and emit a profile.json-ready
"financials" block.

Usage:
  python3 query_financials.py <db.sql | db.sqlite> "<company name or NIF>"
  python3 query_financials.py <db> --list          # list all companies
  python3 query_financials.py <db> "<query>" --raw # raw row dump instead

Accepts either a SQL dump (.sql, loaded into in-memory SQLite) or a SQLite
file. Expects the schema bundled at assets/mock_company_db.sql (tables
`companies` and `financials`); if the user's database differs, inspect it
with --list / sqlite3 directly and adapt.

Matching: exact NIF first, then case-insensitive substring on name. If
multiple companies match, all candidates are listed and the script exits
non-zero — pick one and re-run with the NIF.
"""
import json
import sqlite3
import sys

ROWS = [
    ("Revenue", "revenue", True, False),
    ("Revenue Growth (%)", "revenue_growth_pct", False, "pct"),
    ("COGS", "cogs", False, "neg"),
    ("Gross Margin", "gross_margin", True, False),
    ("Gross Margin (%)", "gross_margin_pct", False, "pct"),
    ("External Services", "external_services", False, "neg"),
    ("Personnel Costs", "personnel_costs", False, "neg"),
    ("Other Gains & Losses", "other_gains_losses", False, False),
    ("EBITDA", "ebitda", True, False),
    ("EBITDA Margin (%)", "ebitda_margin_pct", False, "pct"),
    ("SPACER1", None, None, None),
    ("Exports", "exports", True, False),
    ("Exports (% of revenue)", "exports_pct_revenue", False, "pct"),
    ("Employees", "employees", True, False),
    ("SPACER2", None, None, None),
    ("Fixed Assets", "fixed_assets", True, False),
    ("Inventories", "inventories", False, False),
    ("Net Financial Debt", "net_financial_debt", True, False),
    ("NFD/EBITDA", "nfd_ebitda", False, "ratio"),
    ("Equity", "equity", True, False),
]


def open_db(path):
    if path.endswith(".sql"):
        con = sqlite3.connect(":memory:")
        with open(path, encoding="utf-8") as f:
            con.executescript(f.read())
    else:
        con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def convert(col, kind, val):
    if val is None:
        return "n/a"
    if kind == "pct":
        return f"{val:.0f}%" if float(val) == int(val) else f"{val}%"
    if kind == "ratio":
        return f"{val}x"
    if kind == "neg":
        v = -abs(val)
        return int(v) if float(v) == int(v) else v
    return int(val) if isinstance(val, float) and val == int(val) else val


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    db_path, query = sys.argv[1], sys.argv[2]
    con = open_db(db_path)

    if query == "--list":
        for r in con.execute("SELECT id, name, nif, country, city FROM companies ORDER BY name"):
            print(f"{r['id']:>4}  {r['name']}  (NIF {r['nif']}, {r['city']}, {r['country']})")
        return

    rows = con.execute("SELECT * FROM companies WHERE nif = ?", (query,)).fetchall()
    if not rows:
        rows = con.execute(
            "SELECT * FROM companies WHERE lower(name) LIKE ?", (f"%{query.lower()}%",)
        ).fetchall()
    if not rows:
        print(f"No company matching {query!r}. Use --list to see all entries.", file=sys.stderr)
        sys.exit(2)
    if len(rows) > 1:
        print(f"Ambiguous — {len(rows)} matches. Re-run with the NIF:", file=sys.stderr)
        for r in rows:
            print(f"  {r['name']} (NIF {r['nif']}, {r['city']})", file=sys.stderr)
        sys.exit(3)

    comp = rows[0]
    fin = con.execute(
        "SELECT * FROM financials WHERE company_id = ? ORDER BY year", (comp["id"],)
    ).fetchall()
    if not fin:
        print(f"Company found but has no financial rows: {comp['name']}", file=sys.stderr)
        sys.exit(4)

    if "--raw" in sys.argv:
        for r in fin:
            print(dict(r))
        return

    years = [str(r["year"]) for r in fin]
    out_rows = []
    for label, col, bold, kind in ROWS:
        if col is None:
            out_rows.append({"spacer": True})
            continue
        values = [convert(col, kind, r[col]) for r in fin]
        row = {"label": label, "values": values}
        if bold:
            row["bold"] = True
        out_rows.append(row)

    result = {
        "_company": {k: comp[k] for k in comp.keys()},
        "financials": {
            "title": "FINANCIAL DATA",
            "units_note": "€ thousands (company database)",
            "years": years,
            "rows": out_rows,
        },
    }

    # optional enrichment tables/columns (present in newer databases)
    def safe(sql, params):
        try:
            return con.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            return []

    sh = safe("SELECT name, pct FROM shareholders WHERE company_id = ?", (comp["id"],))
    if sh:
        result["shareholders"] = [{"name": r["name"], "pct": r["pct"]} for r in sh]
    mg = safe("SELECT name, role FROM management WHERE company_id = ?", (comp["id"],))
    if mg:
        result["management"] = [{"name": r["name"], "role": r["role"]} for r in mg]
    keys = comp.keys()
    if "description" in keys and comp["description"]:
        result["description"] = comp["description"]
    if "portfolio" in keys and comp["portfolio"]:
        result["portfolio"] = [p.strip() for p in comp["portfolio"].split(";") if p.strip()]

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
