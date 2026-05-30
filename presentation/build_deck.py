"""
Build Czech-language PowerPoint deck for gas storage analysis.
Run from project root: uv run python presentation/build_deck.py
"""
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

# ── Colour palette ──────────────────────────────────────────────────────────
RED   = RGBColor(0xCC, 0x00, 0x00)
BLUE  = RGBColor(0x00, 0x35, 0x80)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK  = RGBColor(0x22, 0x22, 0x22)
LGREY = RGBColor(0xF2, 0xF2, 0xF2)
MGREY = RGBColor(0xDD, 0xDD, 0xDD)

SLIDE_W = Inches(10)
SLIDE_H = Inches(7.5)

# ── Helpers ─────────────────────────────────────────────────────────────────

def new_prs() -> Presentation:
    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H
    return prs


def blank_slide(prs: Presentation):
    blank_layout = prs.slide_layouts[6]   # truly blank
    return prs.slides.add_slide(blank_layout)


def set_run(run, text, size_pt, bold=False, color=DARK, font="Calibri"):
    run.text = text
    run.font.name  = font
    run.font.size  = Pt(size_pt)
    run.font.bold  = bold
    run.font.color.rgb = color


def add_textbox(slide, text, left, top, width, height,
                size=14, bold=False, color=DARK,
                align=PP_ALIGN.LEFT, wrap=True,
                italic=False):
    txb = slide.shapes.add_textbox(Inches(left), Inches(top),
                                    Inches(width), Inches(height))
    txb.word_wrap = wrap
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name  = "Calibri"
    run.font.size  = Pt(size)
    run.font.bold  = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return txb


def add_title(slide, text, y=0.25, size=32):
    add_textbox(slide, text,
                left=0.4, top=y, width=9.2, height=0.65,
                size=size, bold=True, color=RED)


def add_subtitle(slide, text, y=0.95):
    add_textbox(slide, text,
                left=0.4, top=y, width=9.2, height=0.45,
                size=13, bold=False, color=BLUE, italic=True)


def add_footer(slide, text):
    add_textbox(slide, text,
                left=0.4, top=7.1, width=9.2, height=0.3,
                size=9, color=RGBColor(0x88, 0x88, 0x88))


def add_body_bullets(slide, items, left, top, width, height, size=13):
    """items = list of strings → bullet list."""
    txb = slide.shapes.add_textbox(Inches(left), Inches(top),
                                    Inches(width), Inches(height))
    txb.word_wrap = True
    tf = txb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.space_before = Pt(3)
        # bullet char
        run = p.add_run()
        run.text = "▪  " + item
        run.font.name  = "Calibri"
        run.font.size  = Pt(size)
        run.font.color.rgb = DARK


def add_table(slide, headers, rows, left, top, width, height,
              col_widths=None):
    """Add a styled table.  col_widths is list of fractions (sum=1)."""
    from pptx.util import Inches, Pt
    ncols = len(headers)
    nrows = len(rows)
    tbl = slide.shapes.add_table(nrows + 1, ncols,
                                  Inches(left), Inches(top),
                                  Inches(width), Inches(height)).table

    # Optional column widths
    if col_widths:
        total_emu = Inches(width)
        for ci, frac in enumerate(col_widths):
            tbl.columns[ci].width = int(total_emu * frac)

    def _cell(row_idx, col_idx, text, bg, fg, bold=False, sz=11, align=PP_ALIGN.CENTER):
        cell = tbl.cell(row_idx, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = bg
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = align
        p.space_before = Pt(2)
        p.space_after  = Pt(2)
        run = p.add_run()
        run.text = text
        run.font.name  = "Calibri"
        run.font.size  = Pt(sz)
        run.font.bold  = bold
        run.font.color.rgb = fg

    # Header row
    for ci, h in enumerate(headers):
        _cell(0, ci, h, BLUE, WHITE, bold=True, sz=11)

    # Data rows — alternating
    for ri, row in enumerate(rows):
        bg = LGREY if ri % 2 == 0 else WHITE
        for ci, val in enumerate(row):
            align = PP_ALIGN.LEFT if ci == 0 else PP_ALIGN.CENTER
            _cell(ri + 1, ci, val, bg, DARK, sz=10, align=align)

    return tbl


# ── SLIDES ───────────────────────────────────────────────────────────────────

def slide_01(prs):
    """Titul"""
    s = blank_slide(prs)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = WHITE

    # Red top bar
    bar = s.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(0.08))
    bar.fill.solid(); bar.fill.fore_color.rgb = RED
    bar.line.fill.background()

    add_textbox(s, "Spolehlivost plynových importů a dimenzování zásobníků",
                left=0.5, top=2.2, width=9, height=1.3,
                size=36, bold=True, color=RED, align=PP_ALIGN.CENTER)

    add_textbox(s, "Analýza minimálního zásobníkového plnění pro českou vyrovnávací zónu",
                left=0.5, top=3.65, width=9, height=0.6,
                size=18, bold=False, color=BLUE, align=PP_ALIGN.CENTER)

    add_footer(s, "ENTSOG fyzické toky  ·  post-2022  ·  NET4GAS")

    # Blue bottom bar
    bot = s.shapes.add_shape(1, Inches(0), Inches(7.38), Inches(10), Inches(0.12))
    bot.fill.solid(); bot.fill.fore_color.rgb = BLUE
    bot.line.fill.background()


def slide_02(prs):
    """Otázka pro vedení"""
    s = blank_slide(prs)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = WHITE

    add_title(s, "Otázka")

    add_textbox(s, "Kolik plynu musí být v zásobnících k 1. říjnu?",
                left=0.5, top=1.35, width=9, height=0.7,
                size=20, bold=True, color=BLUE, align=PP_ALIGN.LEFT)

    add_textbox(s, "Kolik plynu musí být k dispozici na začátku každého zimního měsíce?",
                left=0.5, top=2.15, width=9, height=0.7,
                size=20, bold=True, color=BLUE, align=PP_ALIGN.LEFT)

    add_textbox(s,
        "Tato analýza odpovídá na obě otázky pomocí dvou vzájemně konzistentních modelů "
        "opřených o skutečně pozorovaná data.",
        left=0.5, top=3.2, width=9, height=1.0,
        size=15, bold=False, color=DARK, align=PP_ALIGN.LEFT)


def slide_03(prs):
    """Proč nový přístup — comparison table"""
    s = blank_slide(prs)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = WHITE
    add_title(s, "Proč nový přístup")

    headers = ["", "Status quo", "Tento přístup"]
    rows = [
        ["Datový zdroj",
         "Smluvní alokace nebo historická data",
         "Fyzické toky ENTSOG, post-2022 — co skutečně překročilo hranici"],
        ["Cíl",
         "Paušální TWh cíl",
         "Denní simulace s vazbou na fyzickou těžební křivku"],
        ["Rychlost těžby",
         "Nezohledňuje rychlost těžby",
         "Vázající omezení: rychlost těžby, ne jen objem"],
        ["Transparentnost",
         "Předpoklady ve skrytých proměnných",
         "Srozumitelná a auditovatelná metodika — vhodná pro regulatorní debatu"],
    ]
    add_table(s, headers, rows,
              left=0.4, top=1.1, width=9.2, height=5.8,
              col_widths=[0.18, 0.35, 0.47])


def slide_04(prs):
    """Data a rozsah"""
    s = blank_slide(prs)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = WHITE
    add_title(s, "Data a rozsah")

    items = [
        "Zdroj: ENTSOG Transparency Platform — Agregovaná data, fyzické toky, NET4GAS, všechny vstupy",
        "Období: post-2022-03-01 — vylučuje ruský tranzit a cenový šok 2021",
        "Pokrytí: 4 zimní sezóny (2022/23–2025/26), 760 zimních dní",
        "Kapacita zásobníků: 40,8 TWh (hodnota AGSI+ před zavedením inverzního uskladňování; ověřit aktuální stav)",
        "Zásobníková data: GIE AGSI+, denní granularita",
    ]
    add_body_bullets(s, items, left=0.5, top=1.2, width=9, height=5.8, size=14)


def slide_05(prs):
    """Předpoklady a vstupy"""
    s = blank_slide(prs)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = WHITE
    add_title(s, "Předpoklady a vstupy")

    headers = ["Vstup", "Hodnota / zdroj", "Poznámka"]
    rows = [
        ["Poptávka 1-z-20", "R.max.den + r_30dnu (ERÚ)", "Leden: 367,8 GWh/den špička"],
        ["Importní percentily", "ENTSOG fyzické toky, měsíční", "S1=P10, S2=P20, …, S5=P70"],
        ["Těžební křivka", "GIE zásobníková data + ENTSOG",
         "Blend B1 50/50, B2 75/25 (10% srážka)"],
    ]
    add_table(s, headers, rows,
              left=0.4, top=1.2, width=9.2, height=3.5,
              col_widths=[0.22, 0.38, 0.40])


def slide_06(prs):
    """Dvě větve modelu"""
    s = blank_slide(prs)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = WHITE
    add_title(s, "Dvě větve modelu")

    # Centre label
    add_textbox(s,
        "Peak poptávka 1-z-20  →  Import (scénáře) + Těžba ze zásobníků",
        left=1.5, top=1.25, width=7, height=0.55,
        size=12, bold=True, color=DARK, align=PP_ALIGN.CENTER)

    def box(slide, left, top, w, h, text, bg):
        rect = slide.shapes.add_shape(1,
                                       Inches(left), Inches(top),
                                       Inches(w), Inches(h))
        rect.fill.solid(); rect.fill.fore_color.rgb = bg
        rect.line.color.rgb = BLUE
        tf = rect.text_frame
        tf.word_wrap = True
        from pptx.util import Pt
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        run = p.add_run()
        run.text = text
        run.font.name = "Calibri"
        run.font.size = Pt(12)
        run.font.color.rgb = DARK

    # Left branch
    box(s, 0.3, 2.0, 4.3, 4.8,
        "VĚTEV 1 — Měsíční povinnosti\n(Art. 6, EU Reg. 2017/1938)\n\n"
        "▪  30denní simulace pro každý měsíc zvlášť\n\n"
        "▪  Blend těžební křivky: 50/50 (B1)\n\n"
        "Výsledek:\nMinimální plnění k 1. října, 1. listopadu, … 1. března",
        LGREY)

    # Right branch
    box(s, 5.4, 2.0, 4.3, 4.8,
        "VĚTEV 2 — Sezónní cíl\n\n"
        "▪  Denní simulace říjen–březen (182 dní)\n\n"
        "▪  Blend těžební křivky: 75/25 (B2)\n\n"
        "▪  Rezerva 0,5 TWh k 31. 3.\n\n"
        "Výsledek:\nMinimální plnění k 1. říjnu",
        LGREY)

    # Arrow-ish divider
    add_textbox(s, "→", left=4.65, top=4.05, width=0.7, height=0.5,
                size=24, bold=True, color=BLUE, align=PP_ALIGN.CENTER)


def slide_07(prs):
    """Větev 1: Měsíční povinnosti"""
    s = blank_slide(prs)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = WHITE
    add_title(s, "Větev 1: Minimální plnění zásobníku na začátku měsíce (TWh)", size=24)
    add_subtitle(s, "Blend těžební křivky 50/50 × scénářové importní percentily")

    headers = ["Měsíc",
               "S1 – Vysoký stres",
               "S2 – Stresový ★",
               "S3 – Mírný stres",
               "S4 – Medián",
               "S5 – Příznivý"]
    rows = [
        ["Říjen",   "0,00", "0,00", "0,00", "0,00", "0,00"],
        ["Listopad","1,36", "1,01", "0,10", "0,00", "0,00"],
        ["Prosinec","4,50", "4,12", "3,41", "0,46", "0,00"],
        ["Leden",  "10,56", "8,54", "5,85", "2,31", "0,67"],
        ["Únor",    "6,12", "3,62", "2,19", "1,30", "0,58"],
        ["Březen",  "1,19", "0,34", "0,21", "0,00", "0,00"],
    ]
    add_table(s, headers, rows,
              left=0.4, top=1.45, width=9.2, height=4.6)

    add_textbox(s,
        "★ S2 = doporučená regulatorní kotva  ·  Kapacita zásobníků: 40,8 TWh",
        left=0.4, top=6.3, width=9.2, height=0.4,
        size=10, color=RGBColor(0x44, 0x44, 0x44), italic=True)


def slide_08(prs):
    """Větev 2: Sezónní cíl"""
    s = blank_slide(prs)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = WHITE
    add_title(s, "Větev 2: Minimální plnění k 1. říjnu", size=28)
    add_subtitle(s,
        "Blend těžební křivky 75/25 × scénářové importní percentily  ·  rezerva 0,5 TWh k 31. 3.")

    headers = ["Scénář", "Základ importu", "Plnění (%)", "Plnění (TWh)", "Vázající omezení"]
    rows = [
        ["S1 – Vysoký stres", "P10", "63,1 %", "25,7 TWh", "Operační rezerva 31. 3."],
        ["S2 – Stresový ★",   "P20", "55,1 %", "22,5 TWh", "Operační rezerva 31. 3."],
        ["S3 – Mírný stres",  "P30", "43,0 %", "17,5 TWh", "Operační rezerva 31. 3."],
        ["S4 – Medián",       "P50", "25,6 %", "10,4 TWh", "Operační rezerva 31. 3."],
        ["S5 – Příznivý",     "P70", "14,2 %",  "5,8 TWh", "Operační rezerva 31. 3."],
    ]
    add_table(s, headers, rows,
              left=0.4, top=1.45, width=9.2, height=4.5,
              col_widths=[0.26, 0.15, 0.13, 0.15, 0.31])

    add_textbox(s,
        "★ S2 = doporučená kotva (22,5 TWh, ~55 % kapacity)  ·  "
        "Operační rezerva 0,5 TWh k 31. 3. je zahrnutá v simulaci",
        left=0.4, top=6.3, width=9.2, height=0.4,
        size=10, color=RGBColor(0x44, 0x44, 0x44), italic=True)


def slide_09(prs):
    """Klíčové zjištění: rychlost těžby"""
    s = blank_slide(prs)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = WHITE
    add_title(s, "Klíčové zjištění: rychlost těžby jako vázající omezení", size=24)

    # Callout box
    rect = s.shapes.add_shape(1, Inches(0.4), Inches(1.05), Inches(9.2), Inches(0.75))
    rect.fill.solid(); rect.fill.fore_color.rgb = RGBColor(0xFF, 0xF0, 0xF0)
    rect.line.color.rgb = RED
    tf = rect.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = "TWh cíl bez kontroly rychlosti těžby je neúplný."
    run.font.name = "Calibri"; run.font.size = Pt(15)
    run.font.bold = True; run.font.color.rgb = RED

    bullets = [
        "Těžební kapacita klesá s plněním zásobníku — při nízkém plnění nelze dodat plyn dostatečně rychle",
        "Blend 75/25 (B2) udržuje rychlost těžby nad denní potřebou po celou sezónu",
        "Vázající omezení: operační rezerva 0,5 TWh k 31. 3. (pro všechny scénáře S1–S5)",
        "Čistě empirická křivka (P95) by vedla k cíli ~31,8 TWh pro S2 — rozdíl 9 TWh dokumentuje vliv výběru metodiky",
    ]
    add_body_bullets(s, bullets, left=0.4, top=1.9, width=9.2, height=2.5, size=12)

    headers = ["Těžební křivka", "Import", "Cíl k 1. říjnu"]
    rows = [
        ["Empirická P95",       "S2 scénáře", "~31,8 TWh"],
        ["Blend 75/25 ★",       "S2 scénáře",  "22,5 TWh"],
        ["ENTSOG inženýrská",   "S2 scénáře",  "~14 TWh"],
    ]
    add_table(s, headers, rows,
              left=0.4, top=4.55, width=6.0, height=2.5)


def slide_10(prs):
    """Interpretace scénářů S1–S5"""
    s = blank_slide(prs)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = WHITE
    add_title(s, "Interpretace scénářů")

    headers = ["Scénář", "Základ importu", "Interpretace"]
    rows = [
        ["S1 – Vysoký stres", "P10",
         "Fyzická infrastrukturní krize — panevropská zima, kapacita německých plynovodů omezena"],
        ["S2 – Stresový ★", "P20",
         "Regulatorní kotva — komerční stres, ~1-z-40 při pozorované korelaci poptávky a importů"],
        ["S3 – Mírný stres", "P30",
         "Mírný stres, napjatší než normální zásobování z Německa"],
        ["S4 – Medián", "P50",
         "Centrální případ; spodní hranice pro tržní dopad"],
        ["S5 – Příznivý", "P70",
         "Optimistický; téměř nulová povinnost ve všech měsících kromě ledna/února"],
    ]
    add_table(s, headers, rows,
              left=0.4, top=1.1, width=9.2, height=5.3,
              col_widths=[0.22, 0.15, 0.63])

    add_textbox(s,
        "S2 nejlépe kombinuje konzervativní importní předpoklad s auditovatelnou metodikou",
        left=0.4, top=6.55, width=9.2, height=0.35,
        size=10, color=RGBColor(0x44, 0x44, 0x44), italic=True)


def slide_11(prs):
    """Citlivostní analýza"""
    s = blank_slide(prs)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = WHITE
    add_title(s, "Citlivostní analýza")

    # Left table
    add_textbox(s, "Větev 1 — S2 Leden: vliv těžební křivky",
                left=0.4, top=1.05, width=4.6, height=0.45,
                size=11, bold=True, color=BLUE)
    headers_l = ["Těžební křivka", "Import", "Povinnost leden"]
    rows_l = [
        ["Empirická P95",       "S2",               "13,85 TWh"],
        ["Blend 50/50 ★",       "S2",                "8,54 TWh"],
        ["ENTSOG inženýrská",   "S2",                "4,68 TWh"],
        ["Blend 50/50",         "P99 studené dny",   "2,20 TWh"],
    ]
    add_table(s, headers_l, rows_l,
              left=0.4, top=1.55, width=4.6, height=3.5)

    # Right table
    add_textbox(s, "Větev 2 — S2: citlivost na poptávku",
                left=5.2, top=1.05, width=4.4, height=0.45,
                size=11, bold=True, color=BLUE)
    headers_r = ["Poptávka", "Cíl k 1. říjnu"]
    rows_r = [
        ["Základ",             "22,5 TWh"],
        ["Špička +50 GWh/den", "~30 TWh"],
        ["Špička −50 GWh/den", "~15 TWh"],
    ]
    add_table(s, headers_r, rows_r,
              left=5.2, top=1.55, width=4.4, height=2.7)

    add_textbox(s,
        "Rozsah 2–14 TWh (B1 leden) a 15–30 TWh (B2 sezóna) reprezentuje plný obhajitelný prostor",
        left=0.4, top=6.4, width=9.2, height=0.4,
        size=10, color=RGBColor(0x44, 0x44, 0x44), italic=True)


def slide_12(prs):
    """Výhrady a další kroky"""
    s = blank_slide(prs)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = WHITE
    add_title(s, "Výhrady a doporučené rozšíření")

    add_textbox(s, "Výhrady modelu",
                left=0.4, top=1.05, width=4.5, height=0.45,
                size=13, bold=True, color=BLUE)
    caveats = [
        "Deterministické měsíční importy (konzervativní horní odhady)",
        "Těžební křivka špatně identifikována pod ~20 % plnění",
        "Letní injektáž neověřena (zejm. pro cíle >22 TWh)",
        "Korelace poptávky a importů zachycena scénářově, ne stochasticky",
        "EU Reg. 2025/1733: česká měsíční pravidla jsou přísnější než EU základ (±10 pp pásmo)",
    ]
    add_body_bullets(s, caveats, left=0.4, top=1.55, width=4.5, height=5.5, size=12)

    add_textbox(s, "Doporučené rozšíření",
                left=5.1, top=1.05, width=4.5, height=0.45,
                size=13, bold=True, color=BLUE)
    extensions = [
        "Stochastický model importů (rozdělení místo percentilů)",
        "Propojení zimní sezóny s letní injektáží (multi-year model)",
        "Copula pro korelaci poptávka/import (přesnější 1-z-20 pravděpodobnost)",
        "Scénář výpadku koridoru N-1 (čl. 5 EU Reg. 2017/1938)",
        "Kvantifikace nákladů přísnosti vůči EU Reg. 2025/1733",
    ]
    add_body_bullets(s, extensions, left=5.1, top=1.55, width=4.5, height=5.5, size=12)


def slide_13(prs):
    """Doporučení a výzva k diskusi"""
    s = blank_slide(prs)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = WHITE
    add_title(s, "Doporučení a výzva k diskusi", size=28)

    # Three metric boxes
    def metric_box(slide, left, header, line1, line2):
        rect = slide.shapes.add_shape(1,
                                       Inches(left), Inches(1.15),
                                       Inches(2.85), Inches(2.4))
        rect.fill.solid(); rect.fill.fore_color.rgb = LGREY
        rect.line.color.rgb = BLUE

        add_textbox(slide, header,
                    left=left + 0.1, top=1.2, width=2.65, height=0.45,
                    size=12, bold=True, color=BLUE, align=PP_ALIGN.CENTER)
        add_textbox(slide, line1,
                    left=left + 0.1, top=1.72, width=2.65, height=0.55,
                    size=14, bold=True, color=RED, align=PP_ALIGN.CENTER)
        add_textbox(slide, line2,
                    left=left + 0.1, top=2.32, width=2.65, height=0.55,
                    size=14, bold=True, color=RED, align=PP_ALIGN.CENTER)

    metric_box(s, 0.3,
               "S2 — Regulatorní kotva",
               "Leden: 8,54 TWh",
               "1. října: 22,5 TWh (55 %)")
    metric_box(s, 3.57,
               "Obhajitelný rozsah",
               "Leden: 2–14 TWh",
               "1. října: 7–32 TWh")
    metric_box(s, 6.85,
               "Operační rezerva",
               "31. března: 0,5 TWh",
               "samostatný reg. nástroj")

    add_textbox(s,
        "Čísla S2 jsou navrhovanou regulatorní kotvou — nikoli finálními závěry. "
        "Před externím použitím: (1) ověřte kapacitu zásobníků 40,8 TWh z aktuálního AGSI+; "
        "(2) zvažte soulad s EU Reg. 2025/1733; (3) odsouhlaste metodiku těžební křivky.",
        left=0.4, top=3.75, width=9.2, height=1.6,
        size=13, color=DARK)

    add_footer(s,
        "Metodika: docs/analysis_synthesis_brief.md  ·  "
        "Výsledky: docs/storage_obligations_results.md, docs/storage_target_results.md")


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    prs = new_prs()
    slide_01(prs)
    slide_02(prs)
    slide_03(prs)
    slide_04(prs)
    slide_05(prs)
    slide_06(prs)
    slide_07(prs)
    slide_08(prs)
    slide_09(prs)
    slide_10(prs)
    slide_11(prs)
    slide_12(prs)
    slide_13(prs)

    out = Path(__file__).parent / "uskladneni_plynu.pptx"
    prs.save(str(out))
    print(f"Saved → {out}")


if __name__ == "__main__":
    main()
