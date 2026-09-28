#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "playwright",
# ]
# ///

"""
Branded Handout PDF Creator — Automata Learning Lab
Generates professional PDF handouts from JSON content using HTML+CSS → Playwright.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

# Brand files live in the skill's assets/ folder, next to scripts/
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
LOGO = ASSETS_DIR / "logo.svg"
FOOTER_MARK = ASSETS_DIR / "footer-mark.svg"


# ============================================================================
# BRAND TOKENS
# ============================================================================

COLORS = {
    "ink_black": "#000000",
    "warm_cream": "#F5F3EB",
    "white": "#FFFFFF",
    "coral": "#E86B5A",
    "golden": "#F5C542",
    "sage": "#7CB56B",
    "sky": "#5B9BD5",
    "coral_light": "#FBEAE7",
    "golden_light": "#FEF8E6",
    "sage_light": "#EEF5EC",
    "sky_light": "#E8F1F9",
    "gray_100": "#F5F4F1",
    "gray_300": "#DDD9D2",
    "gray_500": "#8A847A",
    "gray_600": "#5C5750",
    "gray_800": "#2A2825",
}

CALLOUT_STYLES = {
    "info": {"border": COLORS["sky"], "bg": COLORS["sky_light"], "label": "INFO"},
    "tip": {"border": COLORS["golden"], "bg": COLORS["golden_light"], "label": "TIP"},
    "success": {"border": COLORS["sage"], "bg": COLORS["sage_light"], "label": "SUCCESS"},
    "alert": {"border": COLORS["coral"], "bg": COLORS["coral_light"], "label": "ALERT"},
}


# ============================================================================
# HTML GENERATION
# ============================================================================

def get_css(accent_color: str) -> str:
    accent = COLORS.get(accent_color, COLORS["coral"])
    return f"""
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    @page {{
        size: A4;
        margin: 20mm 18mm 25mm 18mm;
    }}

    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}

    body {{
        font-family: 'IBM Plex Sans', 'Arial', sans-serif;
        font-size: 11pt;
        line-height: 1.6;
        color: {COLORS["gray_800"]};
        background: {COLORS["warm_cream"]};
        max-width: 800px;
        margin: 0 auto;
        padding: 40px;
    }}

    /* ── Header ──────────────────────────────────────────── */

    .header {{
        margin-bottom: 28px;
        page-break-inside: avoid;
    }}

    .brand-logo {{
        height: 44px;
        margin-bottom: 12px;
    }}

    .footer-mark {{
        height: 16px;
        vertical-align: middle;
        margin-right: 6px;
    }}


    .title {{
        font-size: 28pt;
        font-weight: 700;
        line-height: 1.15;
        color: {COLORS["ink_black"]};
        margin-bottom: 6px;
    }}

    .subtitle {{
        font-size: 13pt;
        font-weight: 400;
        color: {COLORS["gray_600"]};
        margin-bottom: 16px;
        line-height: 1.4;
    }}

    .accent-bar {{
        display: flex;
        height: 5px;
        margin-bottom: 0;
    }}

    .accent-bar span {{
        flex: 1;
    }}

    .accent-bar .bar-coral {{ background: {COLORS["coral"]}; }}
    .accent-bar .bar-golden {{ background: {COLORS["golden"]}; }}
    .accent-bar .bar-sage {{ background: {COLORS["sage"]}; }}
    .accent-bar .bar-sky {{ background: {COLORS["sky"]}; }}

    /* ── Sections ────────────────────────────────────────── */

    .section {{
        background: {COLORS["white"]};
        border: 2px solid {COLORS["ink_black"]};
        padding: 20px 24px;
        margin-bottom: 20px;
        page-break-inside: avoid;
    }}

    .section-heading {{
        font-size: 15pt;
        font-weight: 600;
        color: {COLORS["ink_black"]};
        line-height: 1.3;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid {COLORS["gray_300"]};
        display: flex;
        align-items: center;
        gap: 10px;
    }}

    .section-heading .accent-pip {{
        display: inline-block;
        width: 4px;
        height: 20px;
        background: {accent};
        flex-shrink: 0;
    }}

    .section-body {{
        margin-bottom: 12px;
        line-height: 1.65;
    }}

    /* ── Subsections ─────────────────────────────────────── */

    .subsection {{
        margin-top: 16px;
        padding-top: 12px;
        border-top: 1px solid {COLORS["gray_300"]};
    }}

    .subsection-heading {{
        font-size: 12pt;
        font-weight: 600;
        color: {COLORS["ink_black"]};
        margin-bottom: 8px;
        line-height: 1.4;
    }}

    /* ── Lists ───────────────────────────────────────────── */

    .item-list {{
        list-style: none;
        padding: 0;
        margin-bottom: 12px;
    }}

    .item-list li {{
        padding: 4px 0 4px 18px;
        position: relative;
        line-height: 1.55;
    }}

    .item-list li::before {{
        content: '\\2022';
        position: absolute;
        left: 0;
        color: {accent};
        font-weight: 700;
        font-size: 14px;
    }}

    .item-list li strong {{
        color: {COLORS["ink_black"]};
    }}

    /* ── Callouts ────────────────────────────────────────── */

    .callout {{
        padding: 14px 18px;
        margin: 14px 0;
        border-left: 4px solid;
        page-break-inside: avoid;
    }}

    .callout-label {{
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        font-size: 8pt;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }}

    .callout-text {{
        font-size: 10.5pt;
        line-height: 1.55;
    }}

    .callout-info {{
        border-color: {COLORS["sky"]};
        background: {COLORS["sky_light"]};
    }}
    .callout-info .callout-label {{ color: {COLORS["sky"]}; }}

    .callout-tip {{
        border-color: {COLORS["golden"]};
        background: {COLORS["golden_light"]};
    }}
    .callout-tip .callout-label {{ color: #c5a020; }}

    .callout-success {{
        border-color: {COLORS["sage"]};
        background: {COLORS["sage_light"]};
    }}
    .callout-success .callout-label {{ color: {COLORS["sage"]}; }}

    .callout-alert {{
        border-color: {COLORS["coral"]};
        background: {COLORS["coral_light"]};
    }}
    .callout-alert .callout-label {{ color: {COLORS["coral"]}; }}

    /* ── Code Blocks ─────────────────────────────────────── */

    .code-block {{
        margin: 14px 0;
        page-break-inside: avoid;
    }}

    .code-lang {{
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        font-size: 8pt;
        font-weight: 500;
        color: {COLORS["gray_500"]};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }}

    .code-content {{
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        font-size: 9pt;
        line-height: 1.5;
        background: {COLORS["gray_100"]};
        border: 1px solid {COLORS["gray_300"]};
        padding: 14px 16px;
        white-space: pre-wrap;
        word-wrap: break-word;
        color: {COLORS["ink_black"]};
    }}

    /* ── Footer ──────────────────────────────────────────── */

    .footer {{
        margin-top: 32px;
        page-break-inside: avoid;
    }}

    .footer .accent-bar {{
        margin-bottom: 10px;
    }}

    .footer-brand {{
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        font-size: 8pt;
        font-weight: 500;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: {COLORS["gray_600"]};
        text-align: center;
    }}

    .footer-note {{
        font-size: 9pt;
        color: {COLORS["gray_500"]};
        text-align: center;
        margin-top: 6px;
    }}

    /* ── Links ───────────────────────────────────────────── */

    a {{
        color: {accent};
        text-decoration: underline;
        text-underline-offset: 2px;
    }}

    a:hover {{
        opacity: 0.8;
    }}
    """


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


import re

_URL_RE = re.compile(r'(https?://[^\s<>&\)]+)')


def linkify(text: str) -> str:
    """Escape HTML first, then convert bare URLs into clickable <a> tags."""
    escaped = escape_html(text)
    return _URL_RE.sub(r'<a href="\1">\1</a>', escaped)


def render_items(items: list) -> str:
    if not items:
        return ""
    html = '<ul class="item-list">'
    for item in items:
        if isinstance(item, dict):
            bold = escape_html(item.get("bold", ""))
            text = linkify(item.get("text", ""))
            url = item.get("url", "")
            if bold and url:
                html += f'<li><strong><a href="{escape_html(url)}">{bold}</a>:</strong> {text}</li>'
            elif bold:
                html += f"<li><strong>{bold}:</strong> {text}</li>"
            elif url:
                html += f'<li><a href="{escape_html(url)}">{text}</a></li>'
            else:
                html += f"<li>{text}</li>"
        else:
            html += f"<li>{linkify(str(item))}</li>"
    html += "</ul>"
    return html


def render_callout(callout: dict) -> str:
    ctype = callout.get("type", "tip")
    style = CALLOUT_STYLES.get(ctype, CALLOUT_STYLES["tip"])
    title = callout.get("title", style["label"])
    text = linkify(callout.get("text", ""))
    return f"""
    <div class="callout callout-{ctype}">
        <div class="callout-label">{escape_html(title)}</div>
        <div class="callout-text">{text}</div>
    </div>
    """


def render_code(code: dict) -> str:
    lang = code.get("language", "")
    content = escape_html(code.get("content", ""))
    lang_label = f'<div class="code-lang">{escape_html(lang)}</div>' if lang else ""
    return f"""
    <div class="code-block">
        {lang_label}
        <div class="code-content">{content}</div>
    </div>
    """


def render_subsection(sub: dict) -> str:
    html = '<div class="subsection">'
    heading = sub.get("heading", "")
    if heading:
        html += f'<h3 class="subsection-heading">{escape_html(heading)}</h3>'
    body = sub.get("body", "")
    if body:
        html += f'<div class="section-body">{linkify(body)}</div>'
    html += render_items(sub.get("items", []))
    callout = sub.get("callout")
    if callout:
        html += render_callout(callout)
    code = sub.get("code")
    if code:
        html += render_code(code)
    html += "</div>"
    return html


def render_section(section: dict) -> str:
    html = '<div class="section">'
    heading = section.get("heading", "")
    if heading:
        html += f'<h2 class="section-heading"><span class="accent-pip"></span>{escape_html(heading)}</h2>'
    body = section.get("body", "")
    if body:
        html += f'<div class="section-body">{linkify(body)}</div>'
    html += render_items(section.get("items", []))
    callout = section.get("callout")
    if callout:
        html += render_callout(callout)
    code = section.get("code")
    if code:
        html += render_code(code)
    for sub in section.get("subsections", []):
        html += render_subsection(sub)
    html += "</div>"
    return html


def accent_bar() -> str:
    return """
    <div class="accent-bar">
        <span class="bar-coral"></span>
        <span class="bar-golden"></span>
        <span class="bar-sage"></span>
        <span class="bar-sky"></span>
    </div>
    """


def generate_html(data: dict) -> str:
    title = data.get("title", "Handout")
    subtitle = data.get("subtitle", "")
    accent_color = data.get("accent_color", "coral")
    sections = data.get("sections", [])
    footer_note = data.get("footer_note", "")

    css = get_css(accent_color)

    sections_html = "\n".join(render_section(s) for s in sections)

    subtitle_html = f'<div class="subtitle">{escape_html(subtitle)}</div>' if subtitle else ""
    footer_note_html = f'<div class="footer-note">{escape_html(footer_note)}</div>' if footer_note else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape_html(title)}</title>
    <style>{css}</style>
</head>
<body>

    <div class="header">
        <img class="brand-logo" src="{LOGO.as_uri()}" alt="Automata Learning Lab">
        <h1 class="title">{escape_html(title)}</h1>
        {subtitle_html}
        {accent_bar()}
    </div>

    {sections_html}

    <div class="footer">
        {accent_bar()}
        <div class="footer-brand"><img class="footer-mark" src="{FOOTER_MARK.as_uri()}" alt="">Automata Learning Lab</div>
        {footer_note_html}
    </div>

</body>
</html>"""


# ============================================================================
# MAIN
# ============================================================================

def slugify(text: str) -> str:
    safe = "".join(c for c in text if c.isalnum() or c in (" ", "-", "_")).strip()
    return safe.replace(" ", "-").lower()[:50]


def validate(data: dict) -> list[str]:
    """Return one readable message per problem, so the agent can fix the JSON and rerun."""
    errors = []
    if not isinstance(data.get("title"), str) or not data["title"].strip():
        errors.append('"title" is missing or empty.')
    if data.get("accent_color", "coral") not in ("coral", "golden", "sage", "sky"):
        errors.append(f'"accent_color" is "{data["accent_color"]}". Use coral, golden, sage, or sky.')
    sections = data.get("sections")
    if not isinstance(sections, list) or not sections:
        errors.append('"sections" must be a non-empty list.')
        return errors
    for i, sec in enumerate(sections):
        blocks = [(f"sections[{i}]", sec)]
        blocks += [(f"sections[{i}].subsections[{j}]", sub) for j, sub in enumerate(sec.get("subsections", []))]
        for where, block in blocks:
            if not block.get("heading"):
                errors.append(f'{where} has no "heading".')
            if "callout" in block and not block["callout"].get("text"):
                errors.append(f'{where}.callout has no "text".')
            if block.get("callout", {}).get("type", "tip") not in CALLOUT_STYLES:
                errors.append(f'{where}.callout.type must be one of: {", ".join(CALLOUT_STYLES)}.')
            if "code" in block and not block["code"].get("content"):
                errors.append(f'{where}.code has no "content".')
    return errors


def main():
    parser = argparse.ArgumentParser(description="Render a branded PDF handout from JSON.")
    parser.add_argument("content", help='Path to the content JSON, or "-" to read stdin')
    parser.add_argument("--out", default="handouts", help="Output folder (default: ./handouts)")
    args = parser.parse_args()

    if args.content == "-":
        content_json = sys.stdin.read()
    else:
        with open(args.content, "r") as f:
            content_json = f.read()

    try:
        data = json.loads(content_json)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON — {e}")
        sys.exit(1)

    errors = validate(data)
    if errors:
        print("Error: the content JSON needs fixing before rendering:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    title = data.get("title", "Handout")
    timestamp = datetime.now().strftime("%Y%m%d")
    slug = slugify(title)
    filename = f"handout-{slug}-{timestamp}.pdf"

    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    # Generate HTML
    html_content = generate_html(data)

    # Save the HTML (for reference and as the source for PDF conversion)
    html_path = output_dir / f"handout-{slug}-{timestamp}.html"
    html_path.write_text(html_content, encoding="utf-8")

    # Convert to PDF using Playwright (Chromium)
    print("Generating PDF via Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file://{html_path.resolve()}")
        # Wait for Google Fonts to load
        page.wait_for_timeout(2000)
        page.pdf(
            path=str(output_path),
            format="A4",
            margin={
                "top": "20mm",
                "right": "18mm",
                "bottom": "25mm",
                "left": "18mm",
            },
            print_background=True,
        )
        browser.close()

    print(f"\n✓ Handout created successfully!")
    print(f"  PDF:  {output_path}")
    print(f"  HTML: {html_path}")

    return output_path


if __name__ == "__main__":
    main()
