# render_passport.py — draws the invented passport spread for make.fun
# "The Passport Page of a Country That Isn't There".
#
# Country: the Republic of Vestmara, a North Atlantic island republic
# (capital Hrafnholm). Holder: Elin Margret Haldorsdottir, 32, a licensed
# deep-sea fisher. Every date is consistent: born 14 Mar 1994, passport
# issued 02 Jun 2026, expires 01 Jun 2036; every stamp falls Jun-Oct 2026.
# The MRZ check digits follow ICAO 9303 (weights 7,3,1).
#
# Deterministic: fixed seed, no timestamps, no network. Run:
#   python3 render_passport.py            -> writes entry.png (1024x640 JPEG)
#   python3 render_passport.py --check    -> same, plus prints a fit report
#
# The output is a JPEG under 1 MiB and at most 1024x1024, per the bounty gate.

import math
import random
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 640
QUALITY = 90

# ---------------------------------------------------------------- palette
DESK = (43, 54, 70)
DESK_DK = (30, 38, 50)
PAGE = (246, 241, 226)
PAGE_EDGE = (214, 205, 184)
NAVY = (18, 44, 84)
NAVY_LT = (38, 74, 128)
GOLD = (164, 124, 42)
INK = (24, 28, 36)
GREY = (96, 96, 92)
RULE = (150, 142, 122)
MRZ_BG = (232, 226, 208)
STAMP_BLUE = (42, 77, 143)
STAMP_RED = (158, 52, 48)
STAMP_PURPLE = (104, 74, 138)
STAMP_GREEN = (46, 110, 78)

FDIR = "/usr/share/fonts/truetype/dejavu/"
LDIR = "/usr/share/fonts/truetype/liberation/"


def font(path, size):
    return ImageFont.truetype(path, size)


def B(s):
    return font(FDIR + "DejaVuSans-Bold.ttf", s)


def R(s):
    return font(FDIR + "DejaVuSans.ttf", s)


def SB(s):
    return font(LDIR + "LiberationSans-Bold.ttf", s)


def SR(s):
    return font(LDIR + "LiberationSans-Regular.ttf", s)


def SI(s):
    return font(LDIR + "LiberationSans-Italic.ttf", s)


def SERIF(s):
    return font(LDIR + "LiberationSerif-Regular.ttf", s)


def SERIFB(s):
    return font(LDIR + "LiberationSerif-Bold.ttf", s)


def SERIFI(s):
    return font(LDIR + "LiberationSerif-Italic.ttf", s)


def MONO(s):
    return font(FDIR + "DejaVuSansMono.ttf", s)


def MONOB(s):
    return font(FDIR + "DejaVuSansMono-Bold.ttf", s)


# ---------------------------------------------------------------- helpers
def text(draw, xy, s, f, fill, anchor="la"):
    draw.text(xy, s, font=f, fill=fill, anchor=anchor)


def centered(draw, cx, y, s, f, fill):
    text(draw, (cx, y), s, f, fill, anchor="ma")


def fit(draw, s, f, max_w):
    """Shrink font size until the string fits max_w; returns (font, size)."""
    size = f.size
    while f.getlength(s) > max_w and size > 6:
        size -= 1
        f = ImageFont.truetype(f.path, size)
    return f


def guilloche(base, box, color, step=9, alpha=16):
    """Faint wavy security lines inside box."""
    ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    x0, y0, x1, y1 = box
    for yy in range(y0, y1, step):
        pts = []
        for xx in range(x0, x1 + 1, 8):
            pts.append((xx, yy + 2.2 * math.sin(xx / 26.0 + yy / 9.0)))
        d.line(pts, fill=color + (alpha,), width=1)
    base.alpha_composite(ov)


def rounded_stamp(draw, box, color, width=2):
    draw.rounded_rectangle(box, radius=6, outline=color, width=width)


# ---------------------------------------------------------------- MRZ (ICAO 9303)
def mrz_check(s):
    vals = {}
    for i in range(10):
        vals[str(i)] = i
    for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        vals[ch] = 10 + i
    vals["<"] = 0
    weights = (7, 3, 1)
    total = 0
    for i, ch in enumerate(s):
        total += vals[ch] * weights[i % 3]
    return str(total % 10)


def mrz_lines():
    surname = "HALDORSDOTTIR"
    given = "ELIN<MARGRET"
    line1 = ("P<VSM" + surname + "<<" + given).ljust(44, "<")[:44]
    doc = "VM2041793"
    nat = "VSM"
    dob = "940314"
    sex = "F"
    exp = "360601"
    pers = "<" * 14
    body = (doc + mrz_check(doc) + nat + dob + mrz_check(dob) + sex + exp
            + mrz_check(exp) + pers + mrz_check(pers))
    line2 = body + mrz_check(body)
    assert len(line1) == 44 and len(line2) == 44, (line1, line2)
    return line1, line2


# ---------------------------------------------------------------- portrait
def draw_portrait(rng):
    """Flat-illustration passport photo, 128x150: Elin, 32, dark hair,
    wool fisherman's sweater, pale northern light. Returns an RGB image."""
    pw, ph = 128, 150
    img = Image.new("RGB", (pw, ph), (172, 190, 206))
    d = ImageDraw.Draw(img)
    # backdrop: soft vertical gradient + faint arcs
    for yy in range(ph):
        t = yy / ph
        c = tuple(int(a + (b - a) * t) for a, b in
                  zip((186, 201, 214), (158, 178, 196)))
        d.line([(0, yy), (pw, yy)], fill=c)
    for r in (26, 44, 62):
        d.arc([64 - r, 30 - r, 64 + r, 30 + r], 200, 340,
              fill=(150, 168, 188), width=1)
    # shoulders / wool sweater
    d.polygon([(8, 150), (20, 118), (48, 106), (80, 106), (108, 118),
               (120, 150)], fill=(44, 62, 88))
    d.polygon([(20, 118), (48, 106), (80, 106), (108, 118), (104, 128),
               (24, 128)], fill=(56, 76, 104))
    # sweater ribs
    for xx in range(28, 104, 6):
        d.line([(xx, 128), (xx - 3, 150)], fill=(36, 52, 76), width=1)
    # collar
    d.polygon([(48, 106), (80, 106), (74, 118), (54, 118)], fill=(30, 44, 66))
    # neck (single tone; no dark band under the chin)
    d.polygon([(56, 84), (72, 84), (74, 110), (54, 110)], fill=(226, 188, 160))
    # hair back mass ends just below the chin so nothing dark sits
    # under the jaw (that read as a beard); bob-length, not shoulder
    d.ellipse([34, 8, 94, 86], fill=(58, 42, 30))
    # thin face-framing locks, clear of the jawline
    d.polygon([(34, 44), (38, 96), (42, 96), (42, 60)], fill=(58, 42, 30))
    d.polygon([(94, 44), (90, 96), (86, 96), (86, 60)], fill=(58, 42, 30))
    # face: rounder, no separate chin bulge
    d.ellipse([40, 18, 88, 82], fill=(233, 197, 168))
    # cheek shading + faint blush
    d.polygon([(43, 58), (56, 62), (52, 74), (43, 70)], fill=(226, 186, 156))
    d.polygon([(85, 58), (72, 62), (76, 74), (85, 70)], fill=(226, 186, 156))
    d.ellipse([44, 62, 54, 70], fill=(232, 178, 158))
    d.ellipse([74, 62, 84, 70], fill=(232, 178, 158))
    # ears
    d.ellipse([37, 48, 43, 62], fill=(228, 190, 160))
    d.ellipse([85, 48, 91, 62], fill=(228, 190, 160))
    # brows
    d.line([(47, 45), (58, 43)], fill=(58, 42, 30), width=2)
    d.line([(70, 43), (81, 45)], fill=(58, 42, 30), width=2)
    # eyes
    for cx in (53, 75):
        d.ellipse([cx - 6, 48, cx + 6, 56], fill=(245, 244, 240))
        d.ellipse([cx - 3, 48, cx + 3, 56], fill=(96, 72, 44))
        d.ellipse([cx - 1, 49, cx + 1, 54], fill=(20, 16, 12))
        d.ellipse([cx + 1, 49, cx + 3, 51], fill=(255, 255, 255))
        d.line([(cx - 6, 48), (cx + 6, 48)], fill=(58, 42, 30), width=1)
    # nose: one soft line
    d.line([(64, 55), (63, 66)], fill=(220, 180, 154), width=2)
    d.line([(61, 67), (67, 67)], fill=(212, 172, 146), width=1)
    # lips (muted rose), slightly wider, faint lower-lip line
    d.polygon([(56, 74), (64, 72), (72, 74), (64, 79)], fill=(180, 114, 100))
    d.line([(58, 81), (70, 81)], fill=(214, 172, 146), width=1)
    # hair: shallow cap over the forehead, side part sweeping right
    d.pieslice([38, 2, 90, 40], 180, 360, fill=(58, 42, 30))
    # hair strands
    for x0, y0, x1, y1 in ((40, 20, 36, 52), (88, 20, 92, 52),
                           (46, 12, 42, 40), (82, 12, 86, 40)):
        d.line([(x0, y0), (x1, y1)], fill=(74, 56, 40), width=1)
    # faint grain so the photo reads as a photo, not clip-art
    ov = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for _ in range(260):
        x, y = rng.randrange(pw), rng.randrange(ph)
        od.point((x, y), fill=(255, 255, 255, rng.randrange(8, 26)))
        od.point((x, y), fill=(0, 0, 0, rng.randrange(6, 18)))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    return img


# ---------------------------------------------------------------- emblem
def draw_emblem(draw, cx, cy, r):
    """Circular seal: puffin head in profile over three waves, ringed."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=NAVY, width=2)
    draw.ellipse([cx - r + 4, cy - r + 4, cx + r - 4, cy + r - 4],
                 outline=GOLD, width=1)
    # waves
    for i, yy in enumerate((cy + 8, cy + 13, cy + 18)):
        pts = []
        for xx in range(cx - r + 8, cx + r - 7):
            pts.append((xx, yy + 2 * math.sin(xx / 5.0 + i)))
        draw.line(pts, fill=NAVY_LT, width=1)
    # puffin head: dark cap, white cheek, orange beak
    draw.ellipse([cx - 13, cy - 16, cx + 11, cy + 6], fill=(24, 28, 36))
    draw.ellipse([cx - 4, cy - 8, cx + 10, cy + 4], fill=(250, 248, 240))
    draw.polygon([(cx + 8, cy - 6), (cx + 17, cy - 2), (cx + 8, cy + 1)],
                 fill=(196, 92, 32))
    draw.ellipse([cx - 2, cy - 11, cx + 1, cy - 8], fill=(250, 248, 240))


# ---------------------------------------------------------------- stamps
def oval_stamp(size, color, lines, sub=""):
    """A rotated oval entry/exit stamp on its own RGBA tile."""
    w, h = size
    tile = Image.new("RGBA", (w + 30, h + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    cx, cy = (w + 30) // 2, (h + 30) // 2
    d.ellipse([cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2],
              outline=color + (215,), width=2)
    d.ellipse([cx - w // 2 + 5, cy - h // 2 + 5, cx + w // 2 - 5,
               cy + h // 2 - 5], outline=color + (200,), width=1)
    f1 = B(13)
    f2 = B(11)
    f3 = R(10)
    y = cy - 24
    for i, ln in enumerate(lines):
        ff = f1 if i == 0 else f2
        d.text((cx, y), ln, font=ff, fill=color + (225,), anchor="ma")
        y += 15 if i == 0 else 13
    if sub:
        d.text((cx, y + 1), sub, font=f3, fill=color + (210,), anchor="ma")
    return tile


def rect_stamp(w, h, color, lines, sub=""):
    tile = Image.new("RGBA", (w + 30, h + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    d.rounded_rectangle([15, 15, 15 + w, 15 + h], radius=4,
                        outline=color + (215,), width=2)
    d.rounded_rectangle([19, 19, 15 + w - 4, 15 + h - 4], radius=3,
                        outline=color + (190,), width=1)
    cx = 15 + w // 2
    y = 15 + 10
    for i, ln in enumerate(lines):
        ff = B(12) if i == 0 else (B(11) if i == 1 else R(10))
        d.text((cx, y), ln, font=ff, fill=color + (225,), anchor="ma")
        y += 14
    if sub:
        d.text((cx, y + 1), sub, font=R(9), fill=color + (205,), anchor="ma")
    return tile


def paste_rotated(base, tile, xy, angle):
    rot = tile.rotate(angle, resample=Image.BICUBIC, expand=False)
    base.alpha_composite(rot, xy)


# ---------------------------------------------------------------- page
def render(out_path="entry.png"):
    rng = random.Random(20261121)
    img = Image.new("RGB", (W, H), DESK)
    d = ImageDraw.Draw(img)
    # desk vignette
    for i in range(90):
        a = 26 - i // 4
        d.rectangle([i, i, W - 1 - i, H - 1 - i], outline=(0, 0, 0, 0))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rectangle([0, 0, W, 40], fill=(0, 0, 0, 40))
    od.rectangle([0, H - 40, W, H], fill=(0, 0, 0, 46))
    img = Image.alpha_composite(img.convert("RGBA"), ov)
    d = ImageDraw.Draw(img)

    # open booklet: two cream pages, centre gutter
    bx0, by0, bx1, by1 = 42, 46, 982, 594
    d.rounded_rectangle([bx0 + 3, by0 + 5, bx1 + 3, by1 + 5], radius=4,
                        fill=(16, 20, 28))
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=4, fill=PAGE)
    d.rectangle([bx0, by0, bx0 + 3, by1], fill=PAGE_EDGE)
    d.rectangle([bx1 - 3, by0, bx1, by1], fill=PAGE_EDGE)
    # gutter shadow
    gov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gov)
    for i in range(9):
        gd.rectangle([512 - 9 + i, by0, 512 - 8 + i, by1],
                     fill=(60, 50, 30, 14))
        gd.rectangle([512 + i, by0, 512 + 1 + i, by1], fill=(60, 50, 30, 14))
    gd.line([(512, by0), (512, by1)], fill=(90, 78, 55, 110), width=1)
    img = Image.alpha_composite(img, gov)
    d = ImageDraw.Draw(img)
    guilloche(img, (bx0 + 8, by0 + 8, 504, by1 - 8), NAVY_LT)
    guilloche(img, (520, by0 + 8, bx1 - 8, by1 - 8), NAVY_LT)
    d = ImageDraw.Draw(img)

    # ================================================= LEFT PAGE: data page
    draw_emblem(d, 118, 92, 26)
    centered(d, 300, 66, "REPUBLIC OF VESTMARA", SERIFB(21), NAVY)
    centered(d, 300, 92, "LÝÐVELDIÐ VESTMARA  ·  PASSPORT  ·  VEGABRÉF",
             SB(10), GOLD)
    d.line([(64, 116), (492, 116)], fill=RULE, width=1)
    # type / code / number row
    centered(d, 278, 126, "Type  P      Code  VSM      No.  VM 20417 93",
             MONOB(13), INK)
    d.line([(64, 148), (492, 148)], fill=RULE, width=1)

    # photo
    photo = draw_portrait(rng)
    img.paste(photo, (66, 160))
    d = ImageDraw.Draw(img)
    d.rectangle([66, 160, 66 + 128, 160 + 150], outline=NAVY, width=2)
    d.rectangle([70, 164, 70 + 120, 164 + 142], outline=(255, 255, 255, 90),
                width=1)
    text(d, (130, 314), "PHOTO", R(8), GREY, anchor="ma")

    # data fields right of the photo
    fx, fw = 212, 280
    fields = [
        ("SURNAME  /  EFTIRNAFN", "HALDÓRSDÓTTIR"),
        ("GIVEN NAMES  /  FORNÖFN", "ELÍN MARGRÉT"),
        ("NATIONALITY  /  RÍKISFANG", "VESTMARA"),
        ("DATE OF BIRTH  /  FÆÐINGARDAGUR", "14 MAR 1994"),
        ("PLACE OF BIRTH  /  FÆÐINGARSTAÐUR", "HRAFNHÓLM"),
        ("SEX  /  KYN", "F"),
    ]
    y = 158
    for label, value in fields:
        text(d, (fx, y), label, R(8), GREY)
        text(d, (fx, y + 11), value, SB(15), NAVY)
        y += 27
    d.line([(fx, y + 2), (492, y + 2)], fill=RULE, width=1)

    # second row: issue / expiry / authority
    y2 = 348
    text(d, (66, y2), "DATE OF ISSUE  /  ÚTGÁFUDAGUR", R(8), GREY)
    text(d, (66, y2 + 11), "02 JUN 2026", SB(15), NAVY)
    text(d, (220, y2), "DATE OF EXPIRY  /  GILDISTÍMI", R(8), GREY)
    text(d, (220, y2 + 11), "01 JUN 2036", SB(15), NAVY)
    text(d, (374, y2), "AUTHORITY  /  ÚTGEFANDI", R(8), GREY)
    text(d, (374, y2 + 11), "HRAFNHÓLM", SB(13), NAVY)
    text(d, (374, y2 + 27), "PASSPORT OFFICE", SB(13), NAVY)

    # observations — the telling detail that ties holder to country
    y3 = 402
    d.line([(66, y3), (492, y3)], fill=RULE, width=1)
    text(d, (66, y3 + 8), "OBSERVATIONS  /  ATHUGASEMDIR", R(8), GREY)
    text(d, (66, y3 + 20),
         "HOLDER IS A LICENSED DEEP-SEA FISHER — VESSEL FV SÆHRAFEN.",
         SR(11), INK)
    text(d, (66, y3 + 36),
         "THIS PASSPORT REMAINS THE PROPERTY OF THE REPUBLIC.",
         SR(11), INK)

    # signature
    y4 = 462
    text(d, (150, y4), "Elín Margrét Haldórsdóttir", SERIFI(17), INK)
    d.line([(66, y4 + 26), (240, y4 + 26)], fill=INK, width=1)
    text(d, (66, y4 + 31), "HOLDER'S SIGNATURE  /  UNDIRSKRIFT", R(8), GREY)
    # small note right of signature
    text(d, (492, y4 + 4), "32 PAGES", SB(10), NAVY, anchor="ra")

    # MRZ
    mrz_y = 512
    d.rectangle([56, mrz_y - 6, 500, mrz_y + 40], fill=MRZ_BG)
    d.rectangle([56, mrz_y - 6, 500, mrz_y + 40], outline=RULE, width=1)
    l1, l2 = mrz_lines()
    text(d, (64, mrz_y), l1, MONO(13), INK)
    text(d, (64, mrz_y + 18), l2, MONO(13), INK)

    # ============================================== RIGHT PAGE: visas/stamps
    centered(d, 741, 64, "VISAS", SERIFB(19), NAVY)
    centered(d, 741, 88, "STAMPS  ·  ÁRITANIR", SB(10), GOLD)
    d.line([(532, 112), (962, 112)], fill=RULE, width=1)

    # --- Alderva visitor visa sticker (top left of right page)
    vx0, vy0, vx1, vy1 = 548, 126, 758, 246
    d.rounded_rectangle([vx0, vy0, vx1, vy1], radius=5, fill=(238, 240, 226),
                        outline=NAVY_LT, width=2)
    d.rounded_rectangle([vx0 + 4, vy0 + 4, vx1 - 4, vy1 - 4], radius=4,
                        outline=GOLD, width=1)
    centered(d, (vx0 + vx1) // 2, vy0 + 10, "ALDERVA", SERIFB(16), NAVY)
    centered(d, (vx0 + vx1) // 2, vy0 + 30, "VISITOR VISA  ·  SINGLE ENTRY",
             SB(9), NAVY_LT)
    d.line([(vx0 + 12, vy0 + 48), (vx1 - 12, vy0 + 48)], fill=RULE, width=1)
    visa_rows = [
        ("VALID", "09 JUL – 07 AUG 2026"),
        ("STAY", "30 DAYS"),
        ("ISSUED", "REYKJAVÍK, 01 JUL 2026"),
        ("No.", "AL-884120-V"),
    ]
    yy = vy0 + 54
    for k, v in visa_rows:
        text(d, (vx0 + 12, yy), k, R(8), GREY)
        text(d, (vx0 + 62, yy), v, SB(10), INK)
        yy += 15
    # flag bars on the visa
    for i, c in enumerate(((46, 90, 160), (250, 248, 240), (158, 52, 48))):
        d.rectangle([vx1 - 46 + i * 12, vy1 - 16, vx1 - 36 + i * 12, vy1 - 8],
                    fill=c, outline=NAVY_LT, width=1)

    # --- stamps (rotated, translucent ink)
    paste_rotated(img,
                  oval_stamp((150, 84), STAMP_BLUE,
                             ["SKARLAND", "ENTRY", "18 JUN 2026"],
                             sub="BERGEN · 041"),
                  (782, 128), -8)
    paste_rotated(img,
                  rect_stamp(150, 62, STAMP_RED,
                             ["SKARLAND", "EXIT  25 JUN 2026"],
                             sub="BERGEN · OFFICER 17"),
                  (782, 226), 6)
    paste_rotated(img,
                  oval_stamp((150, 84), STAMP_PURPLE,
                             ["ALDERVA", "ENTRY", "09 JUL 2026"],
                             sub="REYKJAVÍK · 112"),
                  (548, 262), -11)
    paste_rotated(img,
                  rect_stamp(158, 74, STAMP_GREEN,
                             ["VESTMARA", "DEPARTURE", "02 OCT 2026"],
                             sub="HRAFNHÓLM · HARBOUR 3"),
                  (742, 296), 4)
    d = ImageDraw.Draw(img)

    # --- conditions box: the paperwork detail that reveals the country
    cx0, cy0, cx1, cy1 = 548, 392, 962, 516
    d.rounded_rectangle([cx0, cy0, cx1, cy1], radius=4, fill=(250, 247, 238),
                        outline=NAVY_LT, width=1)
    text(d, (cx0 + 12, cy0 + 10), "CONDITIONS OF ISSUE", SB(11), NAVY)
    d.line([(cx0 + 12, cy0 + 28), (cx1 - 12, cy0 + 28)], fill=RULE, width=1)
    conds = [
        "1.  The holder must report to the Harbourmaster",
        "      within 24 hours of landing in Vestmara.",
        "2.  Fishing in Vestmaran waters without a licence",
        "      is prohibited; the catch is forfeit.",
        "3.  In fog, the harbour bell answers before the light.",
    ]
    yy = cy0 + 34
    for ln in conds:
        text(d, (cx0 + 12, yy), ln, SR(11), INK)
        yy += 15
    # harbour fee stamp overlapping the conditions box corner
    fee = Image.new("RGBA", (150, 150), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fee)
    fd.ellipse([15, 15, 135, 135], outline=STAMP_RED + (220,), width=2)
    fd.ellipse([22, 22, 128, 128], outline=STAMP_RED + (200,), width=1)
    fd.text((75, 42), "HARBOUR", font=B(13), fill=STAMP_RED + (225,),
            anchor="ma")
    fd.text((75, 58), "FEE PAID", font=B(13), fill=STAMP_RED + (225,),
            anchor="ma")
    fd.text((75, 76), "450 kr", font=B(15), fill=STAMP_RED + (225,),
            anchor="ma")
    fd.text((75, 96), "HRAFNHÓLM", font=R(9), fill=STAMP_RED + (210,),
            anchor="ma")
    paste_rotated(img, fee, (822, 408), -14)

    # right-page footer (kept clear of the fee stamp)
    d = ImageDraw.Draw(img)
    text(d, (700, 560), "32 PAGES  ·  IF FOUND, RETURN TO THE NEAREST",
         R(9), GREY, anchor="ma")
    text(d, (700, 574), "VESTMARAN CONSULATE  ·  REWARD 500 kr",
         R(9), GREY, anchor="ma")

    # page numbers
    text(d, (66, 576), "4", R(10), GREY)
    text(d, (962, 576), "5", R(10), GREY, anchor="ra")

    img = img.convert("RGB")
    img.save(out_path, format="JPEG", quality=QUALITY,
             optimize=True, progressive=False)
    return img


def check_report():
    import os
    img = Image.open("entry.png")
    size = os.path.getsize("entry.png")
    print("size=%dx%d bytes=%d (limit 1048576) mrz=%r"
          % (img.size[0], img.size[1], size, mrz_lines()))
    print("gate:", "PASS" if img.size[0] <= 1024 and img.size[1] <= 1024
          and size <= 1048576 else "FAIL")


if __name__ == "__main__":
    render()
    if "--check" in sys.argv:
        check_report()
