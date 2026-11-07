"""
Pitch pack: a 3-page PDF marketing plan for one brand, built from what the
dashboard already computes (budget split, audience, Project 1 messaging, ad copy,
2027 calendar and a growth target). Uses only built-in PDF fonts so it works on
Streamlit Cloud without extra font files.
"""
import io
from datetime import date

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

NAVY = colors.HexColor("#1E3A5F")
INK = colors.HexColor("#101828")
INK2 = colors.HexColor("#475467")
LINE = colors.HexColor("#E4E7EC")
SOFT = colors.HexColor("#F2F5F9")
GREY = colors.HexColor("#D0D5DD")
GOOD = colors.HexColor("#067647")
BAD = colors.HexColor("#B42318")

W = A4[0] - 2 * 1.8 * cm

st_title = ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=INK)
st_sub = ParagraphStyle("s", fontName="Helvetica", fontSize=10.5, leading=14, textColor=INK2,
                        spaceAfter=10)
st_h = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=NAVY,
                      spaceBefore=12, spaceAfter=6)
st_body = ParagraphStyle("b", fontName="Helvetica", fontSize=10, leading=14, textColor=INK,
                         alignment=TA_LEFT, spaceAfter=6)
st_small = ParagraphStyle("sm", fontName="Helvetica", fontSize=8.5, leading=11, textColor=INK2)
st_cell = ParagraphStyle("c", fontName="Helvetica", fontSize=9, leading=11.5, textColor=INK)
st_cellb = ParagraphStyle("cb", parent=st_cell, fontName="Helvetica-Bold")
st_kpi_l = ParagraphStyle("kl", fontName="Helvetica", fontSize=8.5, leading=11, textColor=INK2)
st_kpi_v = ParagraphStyle("kv", fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=INK)


def _rs(x):
    return f"Rs. {x:,.0f}"


def _esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _table(rows, widths, header=True):
    data = [[Paragraph(_esc(c), st_cellb if (header and i == 0) else st_cell) for c in r]
            for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, hAlign="LEFT")
    style = [("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
             ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5)]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), SOFT),
                  ("LINEBELOW", (0, 0), (-1, 0), 0.8, GREY)]
    t.setStyle(TableStyle(style))
    return t


def _kpis(items):
    cells = [[Paragraph(_esc(lbl), st_kpi_l), Paragraph(_esc(val), st_kpi_v),
              Paragraph(_esc(note), st_small)] for lbl, val, note in items]
    t = Table([cells], colWidths=[W / len(items)] * len(items), hAlign="LEFT")
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LINE),
                           ("LINEAFTER", (0, 0), (-2, -1), 0.6, LINE),
                           ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9)]))
    return t


def _alloc_bars(rows, colors_map):
    """rows: (platform, share %, spend, revenue, roas). Draws labelled horizontal bars."""
    h_row = 26
    d = Drawing(W, h_row * len(rows) + 4)
    label_w, val_w = 80, 170
    track_w = W - label_w - val_w
    for i, (p, share, spend, rev, roas) in enumerate(rows):
        y = d.height - (i + 1) * h_row
        d.add(String(0, y + 9, p, fontName="Helvetica-Bold", fontSize=9.5, fillColor=INK))
        d.add(Rect(label_w, y + 7, track_w, 9, fillColor=SOFT, strokeColor=None))
        d.add(Rect(label_w, y + 7, track_w * share / 100, 9,
                   fillColor=colors.HexColor(colors_map[p]), strokeColor=None))
        d.add(String(label_w + track_w + 8, y + 9,
                     f"{share:.1f}%   {_rs(spend)}   ROAS {roas:.2f}" if spend > 1 else "not funded",
                     fontName="Helvetica", fontSize=8.5, fillColor=INK2))
    return d


def _calendar_chart(plan):
    d = Drawing(W, 150)
    ch = VerticalBarChart()
    ch.x, ch.y, ch.width, ch.height = 38, 22, W - 50, 112
    ch.data = [list(plan.budget / 1e6)]
    ch.categoryAxis.categoryNames = list(plan.month)
    ch.categoryAxis.labels.fontName = "Helvetica"
    ch.categoryAxis.labels.fontSize = 8
    ch.valueAxis.labels.fontName = "Helvetica"
    ch.valueAxis.labels.fontSize = 8
    ch.valueAxis.valueMin = 0
    ch.valueAxis.labelTextFormat = "%.1fM"
    ch.valueAxis.strokeColor = GREY
    ch.categoryAxis.strokeColor = GREY
    ch.valueAxis.gridStrokeColor = LINE
    ch.valueAxis.visibleGrid = True
    ch.barSpacing = 2
    ch.bars.strokeColor = None
    for i, n in enumerate(plan.campaign_days):
        ch.bars[(0, i)].fillColor = NAVY if n > 0 else GREY
    d.add(ch)
    return d


def build_pitch_pack(ctx):
    """ctx: dict with everything the dashboard computed for one brand (see app.py)."""
    buf = io.BytesIO()
    brand = ctx["brand"]

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(INK2)
        canvas.drawString(1.8 * cm, 1.0 * cm,
                          f"{brand} marketing plan  |  Ad budget optimizer by Usama Hanif  |  "
                          f"Ad data simulated; customer messaging from real reviews")
        canvas.drawRightString(A4[0] - 1.8 * cm, 1.0 * cm, f"Page {doc.page}")
        canvas.setFillColor(NAVY)
        canvas.rect(0, A4[1] - 0.35 * cm, A4[0], 0.35 * cm, stroke=0, fill=1)
        canvas.restoreState()

    s = []
    # ---------------- PAGE 1: the plan ----------------
    s.append(Paragraph(f"{_esc(brand)} marketing plan", st_title))
    s.append(Paragraph(f"Where to spend the next {_rs(ctx['budget'])} a month, who to target, "
                       f"what to say and when to push. Prepared {date.today():%d %B %Y}.", st_sub))
    s.append(_kpis([
        ("Expected revenue", _rs(ctx["revenue"]), f"ROAS {ctx['revenue'] / ctx['budget']:.2f} per month"),
        ("Expected profit", _rs(ctx["profit"]), f"after a {ctx['margin']:.0%} margin and ad spend"),
        ("Gain vs equal split", f"{ctx['gain_equal']:+.1f}%", "same budget, smarter split"),
        (f"Gain vs all on {ctx['best']}", f"{ctx['gain_best']:+.0f}%", "why one platform is not enough"),
    ]))
    s.append(Paragraph("1. Where to spend", st_h))
    s.append(_alloc_bars(ctx["alloc_rows"], ctx["colors"]))
    s.append(Spacer(1, 4))
    s.append(Paragraph(_esc(ctx["why"]), st_body))

    s.append(Paragraph("2. Who to target", st_h))
    rows = [["Platform", "Core age", "Core city", "Device", "Best-return age"]]
    rows += [list(r) for r in ctx["audience_rows"]]
    s.append(_table(rows, [W * 0.18, W * 0.16, W * 0.2, W * 0.16, W * 0.3]))

    s.append(Paragraph("3. What to say (from real customer reviews)", st_h))
    rows = [["", "Message", "Evidence"]]
    rows += [list(r) for r in ctx["say_rows"]]
    s.append(_table(rows, [W * 0.16, W * 0.6, W * 0.24]))
    s.append(Paragraph(f"Based on {ctx['reviews']} real {brand} reviews and comments (Project 1), "
                       "labelled by a multilingual sentiment model. Aspects with fewer than 10 "
                       "mentions are left out.", st_small))

    # ---------------- PAGE 2: ad copy ----------------
    s.append(PageBreak())
    s.append(Paragraph(f"4. Ready-to-use ad copy: {ctx['campaign']}", st_h))
    s.append(Paragraph("Headline A carries the lead message and Headline B the test message. Run "
                       "both with equal budget for a week, then keep the winner.", st_body))
    en, ru = ctx["copy_core"]
    s.append(_table([["", "English", "Roman Urdu"],
                     ["Headline A", en["headline_a"], ru["headline_a"]],
                     ["Headline B", en["headline_b"], ru["headline_b"]],
                     ["Ad text A", en["text_a"], ru["text_a"]],
                     ["Ad text B", en["text_b"], ru["text_b"]],
                     ["Hashtags", en["hashtags"], ""]],
                    [W * 0.15, W * 0.425, W * 0.425]))
    s.append(Paragraph("Platform playbook", st_h))
    rows = [["Platform", "Monthly budget", "Format", "Creative tips"]]
    rows += [list(r) for r in ctx["playbook_rows"]]
    s.append(_table(rows, [W * 0.13, W * 0.17, W * 0.25, W * 0.45]))
    if ctx.get("google"):
        gg = ctx["google"]
        s.append(Paragraph("Google search ad", st_h))
        s.append(_table([["Headlines (each 30 characters or fewer)", " | ".join(gg["google_headlines"])],
                         ["Descriptions (each 90 or fewer)", " | ".join(gg["google_descriptions"])],
                         ["Keywords", ", ".join(gg["keywords"])]],
                        [W * 0.3, W * 0.7], header=False))
    s.append(Spacer(1, 6))
    s.append(Paragraph("Sample copy written by the tool for a class project. It is not the "
                       "brand's real advertising and uses none of its real slogans.", st_small))

    # ---------------- PAGE 3: calendar and growth ----------------
    s.append(PageBreak())
    s.append(Paragraph("5. When to push: 2027 calendar", st_h))
    s.append(Paragraph(f"Yearly budget {_rs(ctx['yearly'])}. Navy months include a campaign "
                       "window; grey months run always-on ads only.", st_body))
    s.append(_calendar_chart(ctx["cal_plan"]))
    rows = [["Campaign", "Event (expected)", "Run ads", "Spend per day"]]
    for _, r in ctx["cal_dates"].iterrows():
        rows.append([r.campaign, f"{r.event_date:%d %b %Y}",
                     f"{r.ads_from:%d %b} to {r.ads_to:%d %b}", f"{r.weight:.1f}x normal"])
    s.append(_table(rows, [W * 0.3, W * 0.22, W * 0.28, W * 0.2]))
    s.append(Paragraph("Eid dates depend on the moon sighting and can move by a day or two.",
                       st_small))

    s.append(Paragraph("6. Growth target", st_h))
    g = ctx["goal"]
    s.append(Paragraph(
        f"To grow monthly revenue by 25% (to {_rs(g['target'])}), {brand} would need about "
        f"<b>{_rs(g['budget'])}</b> a month, {g['budget'] / ctx['budget'] - 1:+.0%} more budget. "
        f"Each extra rupee buys less than the one before, so growth gets expensive: "
        + ("the last rupees would still be profitable." if g["profitable"] else
           "the last rupees would fall below break-even, so profit would drop."), st_body))

    s.append(Paragraph("7. How this plan was made", st_h))
    s.append(Paragraph(
        "The optimizer learns how fast each platform's returns flatten out and splits the budget so "
        "the next rupee earns about the same everywhere. Tested against a known true optimum, it "
        "captured 99.8% or more of the best possible revenue. The ad data is simulated (no access "
        "to the brand's real ad accounts), so the numbers show the method rather than real results; "
        "run on the brand's own ad data, the same tool would give a real plan.", st_body))
    s.append(Paragraph(f"Live dashboard: {ctx['dashboard_url']}<br/>Code: {ctx['repo_url']}",
                       st_small))

    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.6 * cm,
                            title=f"{brand} marketing plan", author="Usama Hanif")
    doc.build(s, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
