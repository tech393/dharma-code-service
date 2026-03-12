"""
Dharma Code™ PDF Microservice
Awakened Academy · Liberated Life LLC

Receives: name, birth_date, birth_time, birth_place, reading_text
Returns:  PDF as base64 string

Deploy once to Railway. Make.com calls it automatically.
"""

import io
import base64
import math
import random
from flask import Flask, request, jsonify

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph, Spacer, Flowable,
    BaseDocTemplate, PageTemplate, Frame,
    NextPageTemplate, PageBreak
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

app = Flask(__name__)

# ── Palette ───────────────────────────────────────────────────────────────────
DEEP_SPACE  = colors.HexColor("#0A0612")
MIDNIGHT    = colors.HexColor("#110D1F")
GOLD        = colors.HexColor("#D4AF5A")
GOLD_BRIGHT = colors.HexColor("#F0CC7A")
GOLD_DIM    = colors.HexColor("#7A5C20")
CREAM       = colors.HexColor("#EDE0FF")
LAVENDER    = colors.HexColor("#B39DDB")
MUTED       = colors.HexColor("#7B6A9A")
STAR_WHITE  = colors.HexColor("#F8F4FF")
W, H = A4


def spaced(text):
    return "  ".join(text.upper())


# ── Visual helpers ─────────────────────────────────────────────────────────────
def draw_stars(canv, w, h, count=140, seed=0):
    rng = random.Random(seed)
    canv.saveState()
    for _ in range(count):
        x     = rng.uniform(0, w)
        y     = rng.uniform(0, h)
        size  = rng.choice([0.3, 0.4, 0.5, 0.7, 1.0, 1.3, 1.8])
        alpha = rng.uniform(0.3, 1.0)
        if rng.random() < 0.12:
            canv.setFillColor(colors.Color(1.0, 0.85, 0.5, alpha=alpha * 0.8))
        else:
            canv.setFillColor(colors.Color(0.92, 0.88, 1.0, alpha=alpha))
        canv.circle(x, y, size, fill=1, stroke=0)
    # Hero stars with glow
    rng2 = random.Random(seed + 99)
    for _ in range(5):
        x = rng2.uniform(12 * mm, w - 12 * mm)
        y = rng2.uniform(12 * mm, h - 12 * mm)
        for glow, a in [(3, 0.05), (2, 0.10), (1.2, 0.28), (0.6, 0.9)]:
            canv.setFillColor(colors.Color(0.95, 0.92, 1.0, alpha=a))
            canv.circle(x, y, glow, fill=1, stroke=0)
    canv.restoreState()


def draw_nebula(canv, cx, cy, rx, ry, col, alpha=0.10):
    canv.saveState()
    for i in range(12, 0, -1):
        f  = i / 12
        a2 = alpha * f * 0.6
        canv.setFillColor(colors.Color(col.red, col.green, col.blue, alpha=a2))
        canv.ellipse(cx - rx * f, cy - ry * f, cx + rx * f, cy + ry * f, fill=1, stroke=0)
    canv.restoreState()


def draw_border(canv, w, h):
    canv.saveState()
    m = 7 * mm
    canv.setStrokeColor(colors.Color(0.70, 0.52, 0.22, alpha=0.65))
    canv.setLineWidth(0.8)
    canv.rect(m, m, w - 2 * m, h - 2 * m, fill=0, stroke=1)
    canv.setStrokeColor(colors.Color(0.70, 0.52, 0.22, alpha=0.22))
    canv.setLineWidth(0.3)
    im = m + 2.5
    canv.rect(im, im, w - 2 * im, h - 2 * im, fill=0, stroke=1)
    canv.setFillColor(colors.Color(0.83, 0.69, 0.35, alpha=0.85))
    canv.setFont("Helvetica", 9)
    for cx2, cy2 in [(m, m), (w - m, m), (m, h - m), (w - m, h - m)]:
        canv.drawCentredString(cx2, cy2 - 3, "✦")
    canv.restoreState()


def draw_mandala(canv, cx, cy, radius=28 * mm, alpha=0.25):
    canv.saveState()
    canv.setStrokeColor(colors.Color(0.83, 0.69, 0.35, alpha=alpha))
    for r in [radius, radius * 0.7, radius * 0.45, radius * 0.2]:
        canv.setLineWidth(0.4)
        canv.circle(cx, cy, r, fill=0, stroke=1)
    canv.setLineWidth(0.3)
    for i in range(8):
        angle = i * math.pi / 4
        x1 = cx + math.cos(angle) * radius * 0.2
        y1 = cy + math.sin(angle) * radius * 0.2
        x2 = cx + math.cos(angle) * radius
        y2 = cy + math.sin(angle) * radius
        canv.line(x1, y1, x2, y2)
    canv.setFillColor(colors.Color(0.83, 0.69, 0.35, alpha=alpha * 1.3))
    for i in range(8):
        angle = i * math.pi / 4 + math.pi / 8
        px = cx + math.cos(angle) * radius
        py = cy + math.sin(angle) * radius
        d  = 2.5
        p  = canv.beginPath()
        p.moveTo(px, py + d)
        p.lineTo(px + d, py)
        p.lineTo(px, py - d)
        p.lineTo(px - d, py)
        p.close()
        canv.drawPath(p, fill=1, stroke=0)
    canv.restoreState()


# ── Page backgrounds ───────────────────────────────────────────────────────────
def cover_bg(canv, doc):
    canv.saveState()
    canv.setFillColor(DEEP_SPACE)
    canv.rect(0, 0, W, H, fill=1, stroke=0)
    for i in range(20):
        f = i / 20
        canv.setFillColor(colors.Color(0.04 + f * 0.07, 0.03 + f * 0.04, 0.07 + f * 0.14, alpha=0.18))
        canv.rect(0, H * f / 2, W, H * 0.06, fill=1, stroke=0)
    draw_nebula(canv, W * 0.15, H * 0.78, 70 * mm, 50 * mm, colors.HexColor("#4A1F8A"), alpha=0.15)
    draw_nebula(canv, W * 0.88, H * 0.28, 60 * mm, 40 * mm, colors.HexColor("#1F3D8A"), alpha=0.12)
    draw_nebula(canv, W * 0.5,  H * 0.52, 90 * mm, 65 * mm, colors.HexColor("#6A2090"), alpha=0.09)
    draw_stars(canv, W, H, count=200, seed=7)
    draw_border(canv, W, H)
    canv.restoreState()


def inner_bg(canv, doc):
    canv.saveState()
    canv.setFillColor(MIDNIGHT)
    canv.rect(0, 0, W, H, fill=1, stroke=0)
    for i in range(10):
        f = i / 10
        canv.setFillColor(colors.Color(0.10, 0.05, 0.20, alpha=0.10 * (1 - f)))
        canv.rect(0, H - (i + 1) * 20 * mm, W, 20 * mm, fill=1, stroke=0)
    draw_nebula(canv, W * 0.88, H * 0.18, 50 * mm, 35 * mm, colors.HexColor("#3D1F6A"), alpha=0.09)
    draw_nebula(canv, W * 0.05, H * 0.60, 40 * mm, 30 * mm, colors.HexColor("#4A1F8A"), alpha=0.07)
    draw_stars(canv, W, H, count=70, seed=doc.page * 3 + 1)
    draw_border(canv, W, H)
    # Header
    canv.setFillColor(colors.Color(0.07, 0.03, 0.14, alpha=1))
    canv.rect(0, H - 13 * mm, W, 13 * mm, fill=1, stroke=0)
    canv.setStrokeColor(GOLD_DIM)
    canv.setLineWidth(0.6)
    canv.line(0, H - 13 * mm, W, H - 13 * mm)
    canv.setFillColor(MUTED)
    canv.setFont("Helvetica", 6.5)
    name_display = getattr(doc, '_recipient_name', 'Your Reading')
    canv.drawCentredString(W / 2, H - 8.5 * mm,
        spaced(name_display) + "  ·  " + spaced("Dharma Code™ Reading"))
    # Footer
    canv.setStrokeColor(GOLD_DIM)
    canv.setLineWidth(0.4)
    canv.line(15 * mm, 12 * mm, W - 15 * mm, 12 * mm)
    canv.setFillColor(MUTED)
    canv.setFont("Helvetica", 6.5)
    canv.drawCentredString(W / 2, 7 * mm,
        spaced("Dharma Code™ by Awakened Academy") + "  ·  " + spaced("Confidential"))
    canv.restoreState()


# ── Flowables ──────────────────────────────────────────────────────────────────
class CoverPage(Flowable):
    def __init__(self, name, birth_date, birth_time, birth_place):
        super().__init__()
        self.name        = name
        self.birth_date  = birth_date
        self.birth_time  = birth_time
        self.birth_place = birth_place

    def wrap(self, aw, ah):
        self.width  = aw
        self.height = ah
        return aw, ah

    def draw(self):
        c  = self.canv
        cx = self.width / 2
        h  = self.height
        c.saveState()

        draw_mandala(c, cx, h - 72 * mm, radius=38 * mm, alpha=0.20)

        c.setFillColor(MUTED)
        c.setFont("Helvetica", 7.5)
        c.drawCentredString(cx, h - 22 * mm,
            spaced("Awakened Academy") + "  ·  " + spaced("Dharma Code™"))
        c.setStrokeColor(GOLD_DIM)
        c.setLineWidth(0.5)
        c.line(cx - 48 * mm, h - 25.5 * mm, cx + 48 * mm, h - 25.5 * mm)

        c.setFillColor(LAVENDER)
        c.setFont("Helvetica", 8)
        c.drawCentredString(cx, h - 36 * mm, spaced("Your Personal Reading"))

        c.setFillColor(GOLD)
        c.setFont("Helvetica", 13)
        c.drawCentredString(cx, h - 47 * mm, "✦  ✦  ✦")

        # Glowing title
        for gsz, ga in [(52, 0.04), (50, 0.09), (48, 0.16)]:
            c.setFillColor(colors.Color(0.83, 0.69, 0.35, alpha=ga))
            c.setFont("Helvetica-Bold", gsz)
            c.drawCentredString(cx, h - 74 * mm, "Dharma Code™")
        c.setFillColor(GOLD_BRIGHT)
        c.setFont("Helvetica-Bold", 48)
        c.drawCentredString(cx, h - 74 * mm, "Dharma Code™")

        c.setStrokeColor(GOLD)
        c.setLineWidth(1.5)
        c.line(cx - 58 * mm, h - 78 * mm, cx + 58 * mm, h - 78 * mm)
        c.setStrokeColor(colors.Color(0.83, 0.69, 0.35, alpha=0.20))
        c.setLineWidth(5)
        c.line(cx - 52 * mm, h - 78 * mm, cx + 52 * mm, h - 78 * mm)

        c.setFillColor(STAR_WHITE)
        c.setFont("Helvetica", 19)
        c.drawCentredString(cx, h - 91 * mm, self.name)

        birth_line = spaced(self.birth_date)
        if self.birth_time and self.birth_time.lower() != "unknown":
            birth_line += "  ·  " + spaced(self.birth_time)
        birth_line += "  ·  " + spaced(self.birth_place)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8)
        c.drawCentredString(cx, h - 99 * mm, birth_line)

        c.setStrokeColor(colors.Color(0.45, 0.22, 0.75, alpha=0.35))
        c.setLineWidth(0.4)
        c.line(cx - 58 * mm, h / 2 + 6 * mm, cx - 20 * mm, h / 2 + 6 * mm)
        c.line(cx + 20 * mm, h / 2 + 6 * mm, cx + 58 * mm, h / 2 + 6 * mm)
        c.setFillColor(GOLD)
        c.setFont("Helvetica", 14)
        c.drawCentredString(cx, h / 2 + 2 * mm, "✦  ✦  ✦")

        c.setFillColor(STAR_WHITE)
        c.setFont("Helvetica-Oblique", 15)
        c.drawCentredString(cx, h / 2 - 14 * mm, "Your gifts are real. Your path is clear.")

        draw_mandala(c, cx, h / 2 - 36 * mm, radius=13 * mm, alpha=0.28)

        c.setFillColor(MUTED)
        c.setFont("Helvetica", 6.5)
        c.drawCentredString(cx, 18 * mm,
            spaced("Confidential") + "  ·  " + spaced(f"Prepared Exclusively for {self.name}") + "  ·  " + spaced("2026"))
        c.restoreState()


class CosmicDivider(Flowable):
    def __init__(self, before=6 * mm, after=6 * mm):
        super().__init__()
        self._b = before
        self._a = after

    def wrap(self, aw, ah):
        self.width  = aw
        self.height = 8 * mm + self._b + self._a
        return self.width, self.height

    def draw(self):
        c  = self.canv
        cx = self.width / 2
        y  = self._a + 4 * mm
        c.saveState()
        c.setStrokeColor(colors.Color(0.50, 0.35, 0.10, alpha=0.50))
        c.setLineWidth(0.5)
        c.line(0, y, cx - 18, y)
        c.line(cx + 18, y, self.width, y)
        c.setFillColor(GOLD)
        c.setFont("Helvetica", 10)
        c.drawCentredString(cx, y - 3.5, "✦  ✦  ✦")
        c.restoreState()


class SectionHeader(Flowable):
    def __init__(self, number, label):
        super().__init__()
        self._num   = number
        self._label = label

    def wrap(self, aw, ah):
        self.width  = aw
        self.height = 20 * mm
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        y_base = 8 * mm
        c.setFillColor(GOLD_BRIGHT)
        c.setFont("Helvetica-Bold", 32)
        c.drawString(0, y_base, str(self._num))
        c.setFillColor(LAVENDER)
        c.setFont("Helvetica", 9)
        c.drawString(14 * mm, y_base + 8 * mm, spaced(self._label))
        c.setStrokeColor(colors.Color(0.50, 0.35, 0.10, alpha=0.50))
        c.setLineWidth(0.5)
        c.line(0, y_base - 2 * mm, self.width, y_base - 2 * mm)
        c.restoreState()


class PullQuote(Flowable):
    def __init__(self, text):
        super().__init__()
        self._text = text

    def wrap(self, aw, ah):
        self.width  = aw
        self.height = 20 * mm
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(colors.Color(0.18, 0.08, 0.35, alpha=0.60))
        c.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=0)
        c.setFillColor(GOLD)
        c.rect(0, 0, 3, self.height, fill=1, stroke=0)
        c.rect(self.width - 3, 0, 3, self.height, fill=1, stroke=0)
        c.setFillColor(GOLD_BRIGHT)
        c.setFont("Helvetica-BoldOblique", 13)
        c.drawCentredString(self.width / 2, self.height / 2 - 2, f'"{self._text}"')
        c.restoreState()


class CTAStep(Flowable):
    def __init__(self, number, title, body, link=None):
        super().__init__()
        self._num   = number
        self._title = title
        self._body  = body
        self._link  = link

    def wrap(self, aw, ah):
        self.width  = aw
        self.height = 26 * mm
        return self.width, self.height

    def draw(self):
        c = self.canv
        h = self.height
        c.saveState()
        c.setFillColor(colors.Color(0.10, 0.05, 0.20, alpha=0.85))
        c.roundRect(0, 0, self.width, h, 5, fill=1, stroke=0)
        c.setStrokeColor(colors.Color(0.45, 0.25, 0.75, alpha=0.50))
        c.setLineWidth(0.6)
        c.roundRect(0, 0, self.width, h, 5, fill=0, stroke=1)
        c.setFillColor(GOLD)
        c.circle(8 * mm, h - 7 * mm, 5 * mm, fill=1, stroke=0)
        c.setFillColor(DEEP_SPACE)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(8 * mm, h - 8.5 * mm, str(self._number).zfill(2))
        c.setFillColor(GOLD_BRIGHT)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(17 * mm, h - 7.5 * mm, self._title)
        c.setFillColor(CREAM)
        c.setFont("Helvetica", 10)
        max_w = self.width - 19 * mm
        words = self._body.split()
        line, y = "", h - 14 * mm
        for word in words:
            test = (line + " " + word).strip()
            if c.stringWidth(test, "Helvetica", 10) <= max_w:
                line = test
            else:
                c.drawString(17 * mm, y, line)
                y -= 4.8 * mm
                line = word
        if line:
            c.drawString(17 * mm, y, line)
        if self._link:
            c.setFillColor(GOLD)
            c.setFont("Helvetica-Bold", 9.5)
            c.drawString(17 * mm, 3.5 * mm, self._link + "  →")
        c.restoreState()

    @property
    def _number(self):
        return self._num


class CTAButtons(Flowable):
    def __init__(self, b1, b2):
        super().__init__()
        self._b1 = b1
        self._b2 = b2

    def wrap(self, aw, ah):
        self.width  = aw
        self.height = 14 * mm
        return self.width, self.height

    def draw(self):
        c  = self.canv
        bw = (self.width - 6 * mm) / 2
        bh = 11 * mm
        c.saveState()
        c.setFillColor(GOLD)
        c.roundRect(0, 1.5 * mm, bw, bh, 4, fill=1, stroke=0)
        c.setFillColor(DEEP_SPACE)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawCentredString(bw / 2, 6 * mm, self._b1)
        c.setFillColor(colors.Color(0.18, 0.08, 0.35, alpha=0.90))
        c.roundRect(bw + 6 * mm, 1.5 * mm, bw, bh, 4, fill=1, stroke=0)
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.2)
        c.roundRect(bw + 6 * mm, 1.5 * mm, bw, bh, 4, fill=0, stroke=1)
        c.setFillColor(GOLD_BRIGHT)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawCentredString(bw + 6 * mm + bw / 2, 6 * mm, self._b2)
        c.restoreState()


class StatsBar(Flowable):
    def __init__(self, stats):
        super().__init__()
        self._stats = stats

    def wrap(self, aw, ah):
        self.width  = aw
        self.height = 20 * mm
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(colors.Color(0.12, 0.06, 0.25, alpha=0.90))
        c.roundRect(0, 0, self.width, self.height, 5, fill=1, stroke=0)
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.8)
        c.roundRect(0, 0, self.width, self.height, 5, fill=0, stroke=1)
        n     = len(self._stats)
        col_w = self.width / n
        for i, (num, label) in enumerate(self._stats):
            cx = col_w * i + col_w / 2
            c.setFillColor(GOLD_BRIGHT)
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(cx, 11.5 * mm, num)
            c.setFillColor(LAVENDER)
            c.setFont("Helvetica", 7)
            c.drawCentredString(cx, 6 * mm, spaced(label))
            if i < n - 1:
                c.setStrokeColor(colors.Color(0.5, 0.3, 0.8, alpha=0.3))
                c.setLineWidth(0.4)
                c.line(col_w * (i + 1), 3 * mm, col_w * (i + 1), 17 * mm)
        c.restoreState()


# ── Styles ─────────────────────────────────────────────────────────────────────
def make_styles():
    return {
        "section_label": ParagraphStyle("section_label",
            fontName="Helvetica", fontSize=8, leading=12,
            textColor=GOLD, alignment=TA_CENTER, spaceBefore=10, spaceAfter=6),
        "body": ParagraphStyle("body",
            fontName="Helvetica", fontSize=12, leading=20,
            textColor=CREAM, spaceAfter=12, alignment=TA_JUSTIFY),
        "body_bold": ParagraphStyle("body_bold",
            fontName="Helvetica-Bold", fontSize=13, leading=20,
            textColor=STAR_WHITE, spaceAfter=8),
        "body_italic": ParagraphStyle("body_italic",
            fontName="Helvetica-Oblique", fontSize=12, leading=20,
            textColor=GOLD_BRIGHT, spaceAfter=10, alignment=TA_JUSTIFY),
        "next_label": ParagraphStyle("next_label",
            fontName="Helvetica", fontSize=8, leading=12,
            textColor=GOLD, alignment=TA_CENTER, spaceBefore=6, spaceAfter=14),
        "closing": ParagraphStyle("closing",
            fontName="Helvetica-Oblique", fontSize=10, leading=15,
            textColor=MUTED, alignment=TA_CENTER, spaceAfter=4),
    }


# ── PDF builder ────────────────────────────────────────────────────────────────
def build_pdf(name, birth_date, birth_time, birth_place, reading_text):
    """
    Takes reading text (plain text from Claude) and renders into
    the full Dharma Code™ PDF. Returns bytes.
    """
    buf    = io.BytesIO()
    margin = 18 * mm

    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=margin, rightMargin=margin,
        topMargin=0, bottomMargin=0,
    )
    doc._recipient_name = name

    cover_frame = Frame(margin, 0, W - 2 * margin, H, id="cover")
    cover_tpl   = PageTemplate("cover", frames=[cover_frame], onPage=cover_bg)
    inner_frame = Frame(margin, 14 * mm, W - 2 * margin, H - 27 * mm, id="inner")
    inner_tpl   = PageTemplate("inner", frames=[inner_frame], onPage=inner_bg)
    doc.addPageTemplates([cover_tpl, inner_tpl])

    S  = make_styles()
    sp = lambda n=1: Spacer(1, n * 3.5 * mm)

    # ── Parse reading into sections ────────────────────────────────────────────
    # The reading from Claude comes as plain text.
    # We split on section headings and render accordingly.
    sections = parse_reading(reading_text)

    story = [
        NextPageTemplate("cover"),
        CoverPage(name, birth_date, birth_time, birth_place),
        NextPageTemplate("inner"),
        PageBreak(),
    ]

    section_names = [
        "You Are an Awakened Guide",
        "Your Gifts",
        "Your Shadow Code",
        "What You Need",
    ]

    # Opening block (before section 1)
    if "opening" in sections:
        story += render_text_block(sections["opening"], S, sp, bold_first=True)
        story.append(CosmicDivider())

    # Numbered sections
    for i, key in enumerate(["section1", "section2", "section3", "section4"], 1):
        if key in sections:
            story.append(SectionHeader(i, section_names[i - 1]))
            story.append(sp(0.5))
            story += render_text_block(sections[key], S, sp, bold_first=True)
            if key == "section1":
                story.append(sp(0.5))
                story.append(PullQuote("Your hardest years are your credential."))
            if i < 4:
                story.append(CosmicDivider())

    # CTA / Next Steps
    story += [
        CosmicDivider(),
        Paragraph(spaced("Your Next Steps"), S["next_label"]),
        CTAStep("01",
            "Access Your Free Awakened Abundance Course",
            "Your Sacred Abundance Calculator, 6 income streams, the 4 Keys, and 3 guided meditations. One click — no login required.",
            "Access Free Course"),
        sp(0.5),
        CTAStep("02",
            "Book Your Free Sacred Abundance Coaching Call",
            "A certified guide has your full reading. In 30 minutes they walk you through your exact path and your real first step.",
            "Book Your Free Session"),
        sp(0.5),
        CTAStep("03",
            "Begin",
            "Not when you feel ready. Now. Your chart says now. Your gifts say now.",
            None),
        sp(1),
        CTAButtons("Access Free Course  →", "Book Your Free Session  →"),
        sp(1),
        StatsBar([
            ("1,250+", "Students"),
            ("25+",    "Countries"),
            ("20 yrs", "Teaching"),
            ("85K+",   "5-Star Reviews"),
        ]),
        sp(0.5),
        Paragraph("Developed over 20 years by the founders of spiritual life coaching.", S["closing"]),
    ]

    doc.build(story)
    buf.seek(0)
    return buf.read()


def parse_reading(text):
    """
    Split the Claude reading text into sections by heading keywords.
    Returns dict with keys: opening, section1, section2, section3, section4
    """
    import re
    sections = {}
    lines    = text.strip().split("\n")

    # Markers that indicate section boundaries
    # These match the headings Claude actually writes per the system prompt
    markers = {
        "section1": ["You Are an Awakened Guide", "AWAKENED GUIDE"],
        "section2": ["Your Gifts", "YOUR GIFTS"],
        "section3": ["Your Shadow Code", "SHADOW CODE"],
        "section4": ["What You Need", "WHAT YOU NEED"],
        "cta":      ["Your Next Step", "YOUR NEXT STEP", "NEXT STEP"],
    }

    current = "opening"
    buffer  = []

    for line in lines:
        stripped = line.strip()
        matched = False
        for sec, keywords in markers.items():
            for kw in keywords:
                # Require the line to essentially BE the heading, not just contain it
                # (stripped line equals keyword, or stripped line starts with keyword and is short)
                if (stripped.lower() == kw.lower() or
                        (stripped.lower().startswith(kw.lower()) and len(stripped) < 50)):
                    if buffer:
                        sections[current] = "\n".join(buffer).strip()
                    current = sec
                    buffer  = []
                    matched = True
                    break
            if matched:
                break
        if not matched:
            buffer.append(line)

    if buffer:
        sections[current] = "\n".join(buffer).strip()

    return sections


def render_text_block(text, S, sp, bold_first=False):
    """Convert a block of plain text into Paragraph flowables."""
    elements   = []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    for i, para in enumerate(paragraphs):
        if not para:
            continue
        # Arrow lines
        if para.startswith("→") or para.startswith("->"):
            for line in para.split("\n"):
                line = line.strip()
                if line:
                    elements.append(Paragraph(line, ParagraphStyle("arrow",
                        fontName="Helvetica", fontSize=11, leading=17,
                        textColor=CREAM, spaceAfter=5, leftIndent=12)))
        # Checkmark lines
        elif para.startswith("✓") or para.startswith("✔"):
            for line in para.split("\n"):
                line = line.strip()
                if line:
                    elements.append(Paragraph(line, ParagraphStyle("check",
                        fontName="Helvetica", fontSize=11, leading=17,
                        textColor=GOLD_BRIGHT, spaceAfter=5, leftIndent=12)))
        # First paragraph bold
        elif i == 0 and bold_first:
            elements.append(Paragraph(para, S["body_bold"]))
        # Italic if short (closing lines)
        elif len(para) < 120 and para.endswith(".") and i == len(paragraphs) - 1:
            elements.append(Paragraph(para, S["body_italic"]))
        else:
            elements.append(Paragraph(para, S["body"]))
    return elements


# ── Flask endpoint ─────────────────────────────────────────────────────────────
@app.route("/generate", methods=["POST"])
def generate():
    """
    POST body (JSON):
    {
      "name":         "Emma Calloway",
      "birth_date":   "March 14, 1985",
      "birth_time":   "7:23 AM",
      "birth_place":  "Vancouver, Canada",
      "reading_text": "Hi Emma, ..."
    }

    Returns JSON:
    {
      "pdf_base64": "...",
      "filename":   "dharma-code-emma-calloway.pdf"
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    required = ["name", "birth_date", "birth_place", "reading_text"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    name         = data["name"]
    birth_date   = data.get("birth_date", "")
    birth_time   = data.get("birth_time", "unknown")
    birth_place  = data.get("birth_place", "")
    reading_text = data["reading_text"]

    try:
        pdf_bytes = build_pdf(name, birth_date, birth_time, birth_place, reading_text)
        filename  = "dharma-code-" + name.lower().replace(" ", "-") + ".pdf"
        from flask import Response
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Dharma Code PDF Generator"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
