#!/usr/bin/env python3
"""Generate a one-page company profile PDF (tear-sheet style) from a JSON spec.

Usage: python3 generate_profile.py profile.json output.pdf

See references/profile-schema.md for the JSON schema.
Requires: reportlab (Pillow only if embedding logo/photo images).
"""
import json
import sys

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas as _canvas

# ---------------------------------------------------------------- palette
NAVY = HexColor("#2B3A55")        # headings, table header, heavy title
NAVY_LIGHT = HexColor("#57657F")  # light half of the title
TEXT = HexColor("#333A45")        # body text
GRAY = HexColor("#8C93A0")        # website, footer, notes
RULE = HexColor("#D8DBE0")        # hairlines
BAR_BG = HexColor("#EEF0F3")      # HQ bar
ROW_BG = HexColor("#F2F3F6")      # bold financial rows
WHITE = HexColor("#FFFFFF")

PAGE_W, PAGE_H = landscape(A4)    # 842 x 595
MARGIN = 42
FOOTER_Y = 34
GUTTER = 28
LEFT_W = 358
LEFT_X = MARGIN
RIGHT_X = MARGIN + LEFT_W + GUTTER
RIGHT_W = PAGE_W - MARGIN - RIGHT_X

_warned = False


def warn(msg):
    global _warned
    _warned = True
    print(f"WARNING: {msg}", file=sys.stderr)


def fmt_value(v):
    """Numbers -> thousands separators, negatives in parentheses. Strings pass through."""
    if isinstance(v, bool) or v is None:
        return "n/a"
    if isinstance(v, (int, float)):
        neg = v < 0
        a = abs(v)
        s = f"{a:,.1f}" if isinstance(a, float) and a != int(a) else f"{int(round(a)):,}"
        return f"({s})" if neg else s
    return str(v)


def spaced_text(c, x, y, text, font, size, color, char_space=1.5, right=False, center=False):
    c.setFillColor(color)
    w = c.stringWidth(text, font, size) + char_space * max(len(text) - 1, 0)
    if right:
        x -= w
    elif center:
        x -= w / 2
    t = c.beginText(x, y)
    t.setFont(font, size)
    t.setCharSpace(char_space)
    t.textOut(text)
    t.setCharSpace(0)  # Tc persists in graphics state beyond ET — must reset
    c.drawText(t)
    return w


def section_heading(c, x, y, text, width):
    spaced_text(c, x, y, text.upper(), "Helvetica-Bold", 10.5, NAVY, char_space=2.2)
    c.setStrokeColor(RULE)
    c.setLineWidth(0.8)
    c.line(x, y - 8, x + width, y - 8)
    return y - 26


# ---------------------------------------------------------------- header
def draw_logo_box(c, spec):
    box = 78
    x = PAGE_W - MARGIN - box
    y = PAGE_H - MARGIN - box + 8
    c.setStrokeColor(RULE)
    c.setLineWidth(0.8)
    c.setFillColor(WHITE)
    c.rect(x, y, box, box, stroke=1, fill=1)

    logo = spec.get("logo") or {}
    path = logo.get("path")
    if path:
        try:
            img = ImageReader(path)
            iw, ih = img.getSize()
            pad = 10
            avail = box - 2 * pad
            scale = min(avail / iw, avail / ih)
            w, h = iw * scale, ih * scale
            c.drawImage(img, x + (box - w) / 2, y + (box - h) / 2, w, h,
                        preserveAspectRatio=True, mask="auto")
            return
        except Exception as e:  # noqa: BLE001
            warn(f"could not embed logo image ({e}); using generated monogram")

    # generated monogram logo
    cx = x + box / 2
    shape = (logo.get("shape") or "triangle").lower()
    text = (logo.get("text") or spec.get("company_name", "").split()[0] if spec.get("company_name") else "LOGO")
    text = (text or "LOGO").upper()[:12]
    sy = y + box * 0.56
    r = 13
    c.setFillColor(NAVY)
    p = c.beginPath()
    if shape == "circle":
        c.circle(cx, sy, r, stroke=0, fill=1)
    elif shape == "diamond":
        p.moveTo(cx, sy + r); p.lineTo(cx + r, sy); p.lineTo(cx, sy - r); p.lineTo(cx - r, sy)
        p.close(); c.drawPath(p, stroke=0, fill=1)
    elif shape == "hexagon":
        import math
        for i in range(6):
            a = math.pi / 6 + i * math.pi / 3
            px, py = cx + r * math.cos(a), sy + r * math.sin(a)
            (p.moveTo if i == 0 else p.lineTo)(px, py)
        p.close(); c.drawPath(p, stroke=0, fill=1)
    elif shape == "bars":
        for i, h in enumerate((0.5, 0.8, 1.1)):
            c.rect(cx - 12 + i * 9, sy - r, 6, 2 * r * h / 1.1, stroke=0, fill=1)
    else:  # triangle
        p.moveTo(cx, sy + r); p.lineTo(cx + r, sy - r); p.lineTo(cx - r, sy - r)
        p.close(); c.drawPath(p, stroke=0, fill=1)
    size = 6.5 if len(text) <= 8 else 5.2
    spaced_text(c, cx, y + 13, text, "Helvetica-Bold", size, NAVY, char_space=1.6, center=True)


def draw_header(c, spec):
    name = spec.get("company_name", "Company")
    parts = name.split(None, 1)
    bold = spec.get("display_bold") or parts[0]
    light = spec.get("display_light")
    if light is None:
        light = parts[1] if len(parts) > 1 else ""

    y = PAGE_H - MARGIN - 24
    w = spaced_text(c, MARGIN, y, bold.upper(), "Helvetica-Bold", 27, NAVY, char_space=1.2)
    if light:
        spaced_text(c, MARGIN + w + 8, y, light.upper(), "Helvetica", 27, NAVY_LIGHT, char_space=1.2)

    if spec.get("website"):
        c.setFont("Helvetica", 10)
        c.setFillColor(GRAY)
        c.drawString(MARGIN, y - 20, spec["website"])

    draw_logo_box(c, spec)

    rule_y = PAGE_H - MARGIN - 68
    c.setStrokeColor(RULE)
    c.setLineWidth(0.8)
    c.line(MARGIN, rule_y, PAGE_W - MARGIN, rule_y)
    return rule_y - 30


# ---------------------------------------------------------------- left column
def draw_gradient_box(c, x, y, w, h, idx):
    shades = [("#33415C", "#1F2A40"), ("#4A5872", "#33415C"), ("#7A8499", "#5C6880")]
    top, bot = shades[idx % len(shades)]
    t, b = HexColor(top), HexColor(bot)
    steps = 40
    for i in range(steps):
        f = i / (steps - 1)
        col = Color(t.red + (b.red - t.red) * f,
                    t.green + (b.green - t.green) * f,
                    t.blue + (b.blue - t.blue) * f)
        c.setFillColor(col)
        c.rect(x, y + h - (i + 1) * h / steps, w, h / steps + 0.5, stroke=0, fill=1)


def draw_photos(c, photos, y):
    n = min(len(photos), 3)
    if n == 0:
        return y
    gap = 8
    w = (LEFT_W - gap * (n - 1)) / n
    h = 72
    y -= h
    for i, ph in enumerate(photos[:3]):
        x = LEFT_X + i * (w + gap)
        path = ph.get("path")
        drawn = False
        if path:
            try:
                c.saveState()
                p = c.beginPath()
                p.rect(x, y, w, h)
                c.clipPath(p, stroke=0)
                img = ImageReader(path)
                iw, ih = img.getSize()
                scale = max(w / iw, h / ih)
                c.drawImage(img, x + (w - iw * scale) / 2, y + (h - ih * scale) / 2,
                            iw * scale, ih * scale, mask="auto")
                c.restoreState()
                drawn = True
            except Exception as e:  # noqa: BLE001
                c.restoreState()
                warn(f"could not embed photo {path} ({e}); using placeholder")
        if not drawn:
            draw_gradient_box(c, x, y, w, h, i)
            label = f"[{ph.get('label', 'PHOTO')}]".upper()
            lines = simpleSplit(label, "Helvetica-Bold", 7.5, w - 12)
            ty = y + h / 2 + (len(lines) - 1) * 5
            for ln in lines:
                spaced_text(c, x + w / 2, ty - 3, ln, "Helvetica-Bold", 7.5, WHITE,
                            char_space=0.8, center=True)
                ty -= 10
    return y - 22


def draw_left(c, spec, top_y):
    y = section_heading(c, LEFT_X, top_y, "Business Areas & Location", LEFT_W)

    if spec.get("headquarters"):
        bar_h = 22
        y -= bar_h - 8
        c.setFillColor(BAR_BG)
        c.rect(LEFT_X, y - 6, LEFT_W, bar_h, stroke=0, fill=1)
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(TEXT)
        c.drawString(LEFT_X + 10, y, f"Headquarters: {spec['headquarters']}")
        y -= 16
    if spec.get("registry_line"):
        c.setFont("Helvetica", 8)
        c.setFillColor(GRAY)
        c.drawString(LEFT_X + 10, y, spec["registry_line"])
        y -= 12
    y -= 8

    for bullet in spec.get("business_bullets", []):
        lines = simpleSplit(bullet, "Helvetica", 9.5, LEFT_W - 18)
        c.setFillColor(TEXT)
        c.setFont("Helvetica", 9.5)
        c.drawString(LEFT_X, y + 1, "–")
        for ln in lines:
            c.drawString(LEFT_X + 14, y, ln)
            y -= 13.5
        y -= 6

    y -= 4
    y = draw_photos(c, spec.get("photos", []), y)

    sh = spec.get("shareholders") or []
    if sh:
        y = section_heading(c, LEFT_X, y, "Shareholders", LEFT_W)
        y += 4
        for s in sh:
            c.setFont("Helvetica", 10)
            c.setFillColor(TEXT)
            c.drawString(LEFT_X + 4, y, s.get("name", ""))
            c.setFont("Helvetica-Bold", 10)
            c.drawRightString(LEFT_X + LEFT_W - 4, y, str(s.get("pct", "")))
            y -= 8
            c.setStrokeColor(RULE)
            c.setLineWidth(0.6)
            c.line(LEFT_X, y, LEFT_X + LEFT_W, y)
            y -= 14
        if spec.get("shareholders_note"):
            for ln in simpleSplit(spec["shareholders_note"], "Helvetica-Oblique", 7.5, LEFT_W):
                c.setFont("Helvetica-Oblique", 7.5)
                c.setFillColor(GRAY)
                c.drawString(LEFT_X, y, ln)
                y -= 10
        y -= 6

    mg = spec.get("management") or []
    if mg:
        y = section_heading(c, LEFT_X, y, "Management", LEFT_W)
        y += 4
        for m in mg:
            c.setFont("Helvetica", 9.5)
            c.setFillColor(TEXT)
            c.drawString(LEFT_X + 4, y, m.get("name", ""))
            c.setFillColor(GRAY)
            c.drawRightString(LEFT_X + LEFT_W - 4, y, m.get("role", ""))
            y -= 14

    if y < FOOTER_Y + 18:
        warn(f"left column overflows the page by {FOOTER_Y + 18 - y:.0f}pt — trim bullets/sections")
    return y


# ---------------------------------------------------------------- right column
def draw_financials(c, spec, top_y):
    fin = spec.get("financials")
    if not fin:
        return
    y = section_heading(c, RIGHT_X, top_y, fin.get("title", "Financial Data"), RIGHT_W)

    if fin.get("units_note"):
        c.setFont("Helvetica-Oblique", 7.5)
        c.setFillColor(GRAY)
        c.drawRightString(RIGHT_X + RIGHT_W, y + 6, fin["units_note"])
        y -= 4

    years = [str(v) for v in fin.get("years", [])]
    ncols = max(len(years), 1)
    val_w = min(64.0, (RIGHT_W * 0.55) / ncols)
    label_w = RIGHT_W - ncols * val_w

    row_h = 18
    # header row
    c.setFillColor(NAVY)
    c.rect(RIGHT_X, y - row_h + 6, RIGHT_W, row_h, stroke=0, fill=1)
    c.setFont("Helvetica-Bold", 9.5)
    c.setFillColor(WHITE)
    for i, yr in enumerate(years):
        c.drawRightString(RIGHT_X + label_w + (i + 1) * val_w - 8, y - 8, yr)
    y -= row_h

    rows = fin.get("rows", [])
    for row in rows:
        if row.get("spacer"):
            y -= 9
            continue
        bold = row.get("bold", False)
        if bold:
            c.setFillColor(ROW_BG)
            c.rect(RIGHT_X, y - row_h + 6, RIGHT_W, row_h, stroke=0, fill=1)
        font = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font, 9.5)
        c.setFillColor(TEXT if not bold else NAVY)
        label = row.get("label", "")
        if c.stringWidth(label, font, 9.5) > label_w - 12:
            c.setFont(font, 8.2)
        c.drawString(RIGHT_X + 8, y - 7, label)
        c.setFont(font, 9.5)
        values = row.get("values", [])
        for i in range(ncols):
            v = fmt_value(values[i]) if i < len(values) else "n/a"
            c.drawRightString(RIGHT_X + label_w + (i + 1) * val_w - 8, y - 7, v)
        # hairline under non-bold rows
        c.setStrokeColor(RULE)
        c.setLineWidth(0.4)
        c.line(RIGHT_X, y - row_h + 6, RIGHT_X + RIGHT_W, y - row_h + 6)
        y -= row_h

    if y < FOOTER_Y + 14:
        warn(f"financial table overflows the page by {FOOTER_Y + 14 - y:.0f}pt — remove rows")


# ---------------------------------------------------------------- footer
def draw_footer(c, spec):
    c.setStrokeColor(RULE)
    c.setLineWidth(0.8)
    c.line(MARGIN, FOOTER_Y + 12, PAGE_W - MARGIN, FOOTER_Y + 12)
    branding = spec.get("branding") or {}
    firm = branding.get("firm_name", "")
    text = firm.upper()
    if branding.get("confidential", True):
        text = f"{text} – STRICTLY CONFIDENTIAL" if text else "STRICTLY CONFIDENTIAL"
    spaced_text(c, MARGIN, FOOTER_Y, text, "Helvetica", 8, GRAY, char_space=1.5)
    pn = branding.get("page_number")
    if pn is not None:
        c.setFont("Helvetica", 9)
        c.setFillColor(GRAY)
        c.drawRightString(PAGE_W - MARGIN, FOOTER_Y, str(pn))
    if spec.get("sources_note"):
        c.setFont("Helvetica-Oblique", 6.5)
        c.setFillColor(GRAY)
        c.drawRightString(PAGE_W - MARGIN, FOOTER_Y + 16, spec["sources_note"])


# ---------------------------------------------------------------- main
def generate(spec, out_path):
    c = _canvas.Canvas(out_path, pagesize=landscape(A4))
    c.setTitle(f"{spec.get('company_name', 'Company')} – Profile")
    body_top = draw_header(c, spec)
    draw_left(c, spec, body_top)
    draw_financials(c, spec, body_top)
    draw_footer(c, spec)
    c.save()


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        spec = json.load(f)
    generate(spec, sys.argv[2])
    print(f"Wrote {sys.argv[2]}" + ("  (with layout warnings — see stderr)" if _warned else ""))


if __name__ == "__main__":
    main()
