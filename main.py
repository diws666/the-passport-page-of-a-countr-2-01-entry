#!/usr/bin/env python3
"""The Passport Page of a Country That Isn't There - v1 build.

Stdlib-only (zlib/struct/os/math/random). Writes one deterministic PNG
to /output/entry.png: an invented passport spread for the Republic of
Kolmara, a fictional mountain republic.

Spread: left page = data page (title band, portrait top-left, data
fields, MRZ strip at the bottom); right page = visa/stamp page with
arrival/departure stamps from three neighbours plus one paperwork
detail (a high-altitude pass permit) that reveals the country's
mountain character.
"""
import zlib
import struct
import os
import math
import random

W, H = 1024, 1024

PAPER = (250, 246, 237)
INK = (20, 30, 40)
INK2 = (60, 78, 96)
BLUE = (24, 52, 94)
SKIN = (244, 214, 174)
SKIN_SHADE = (214, 178, 130)
HAIR = (26, 22, 19)
SHIRT = (20, 36, 60)
SHIRT_LIT = (34, 54, 84)
WHITE = (255, 255, 255)
RED = (172, 56, 50)
GREEN = (92, 138, 68)
PURPLE = (128, 58, 148)

PAGE_W = W // 2  # each page is 512 px wide, full height


def rgba(c):
    return c + (255,)


# pixel buffer, pre-filled with paper colour
pix = bytearray(rgba(PAPER)) * (W * H)


def setpx(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 4
        pix[i:i + 4] = bytes(c + (255,)) if len(c) == 3 else bytes(c)


def rect(x, y, w, h, c):
    cc = bytes(c + (255,)) if len(c) == 3 else bytes(c)
    for yy in range(y, y + h):
        i0 = ((yy * W + x) * 4)
        for xx in range(x, x + w):
            pix[i0 + (xx - x) * 4:i0 + (xx - x) * 4 + 4] = cc


def line(x0, y0, x1, y1, c, thick=1):
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    off = thick // 2
    while True:
        for tx in range(-off, off + 1):
            for ty in range(-off, off + 1):
                setpx(x + tx, y + ty, c)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy


def circle_fill(x0, y0, r, c):
    for yy in range(y0 - r, y0 + r + 1):
        dy_ = yy - y0
        dx_ = int(math.sqrt(max(0, r * r - dy_ * dy_)))
        for xx in range(x0 - dx_, x0 + dx_ + 1):
            setpx(xx, yy, c)


def circle_outline(x0, y0, r, c, thick=1):
    x = r
    y = 0
    err = 0
    while x >= y:
        for dx_, dy_ in ((x, y), (y, x), (-y, x), (-x, y),
                         (-x, -y), (-y, -x), (y, -x), (x, -y)):
            for tx in range(-thick // 2, thick // 2 + 1):
                for ty in range(-thick // 2, thick // 2 + 1):
                    setpx(x0 + dx_ + tx, y0 + dy_ + ty, c)
        y += 1
        err += 1 + 2 * y
        if 2 * (err - x) + 1 > 0:
            x -= 1
            err += 1 - 2 * x


def tri(p0, p1, p2, c):
    pts = sorted([p0, p1, p2], key=lambda p: p[1])
    (x0, y0), (x1, y1), (x2, y2) = pts
    for y in range(y0, y2 + 1):
        if y <= y1:
            t = 0.0 if y1 == y0 else (y - y0) / (y1 - y0)
            xa = x0 + (x1 - x0) * t
            t2 = 0.0 if y2 == y0 else (y - y0) / (y2 - y0)
            xb = x0 + (x2 - x0) * t2
        else:
            t = 0.0 if y2 == y1 else (y - y1) / (y2 - y1)
            xa = x1 + (x2 - x1) * t
            t2 = 0.0 if y2 == y0 else (y - y0) / (y2 - y0)
            xb = x0 + (x2 - x0) * t2
        xa, xb = sorted((xa, xb))
        for x in range(int(math.ceil(xa)), int(math.floor(xb)) + 1):
            setpx(x, y, c)


# ---------------------------------------------------------------- bitmap font
# 5x7 glyphs, rows of 5 chars ('#' = ink, '.' = blank)
GLYPHS = {
    ' ': [".....", ".....", ".....", ".....", ".....", ".....", "....."],
    'A': ["..#..", ".#.#.", "#####", "#...#", "#...#", "#...#", "#...#"],
    'B': ["####.", "#...#", "####.", "#...#", "#...#", "#...#", "####."],
    'C': [".###.", "#....", "#....", "#....", "#....", "#....", ".###."],
    'D': ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    'E': ["#####", "#....", "#....", "#####", "#....", "#....", "#####"],
    'F': ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    'G': [".###.", "#....", "#....", "#..##", "#...#", "#...#", ".###."],
    'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'I': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    'J': ["....#", "....#", "....#", "....#", "#.#.#", "#.#.#", ".###."],
    'K': ["#...#", "#.#..", "##.#.", "#.#..", "#.#..", "#.#..", "#...#"],
    'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    'M': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    'N': ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'Q': [".###.", "#...#", "#...#", "#...#", "#.##.", "#..#.", ".###."],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#.#..", "#.#.."],
    'S': [".###.", "#....", "#....", ".###.", "....#", "....#", ".###."],
    'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'U': ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'V': ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", ".#.#.", ".#.#."],
    'W': ["#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    'X': ["#...#", "#.#..", ".#.#.", "..#..", ".#.#.", "#.#..", "#...#"],
    'Y': ["#...#", "#.#..", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    'Z': ["#####", "...#.", "..#..", ".#...", "#....", "#....", "#####"],
    '0': [".###.", "#...#", "#.#.#", "#.#.#", "#.#.#", "#...#", ".###."],
    '1': ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", "#####"],
    '2': [".###.", "....#", "....#", ".###.", "#....", "#....", ".###."],
    '3': [".###.", "....#", "....#", ".###.", "....#", "....#", ".###."],
    '4': ["#...#", "#...#", "#...#", "#####", "....#", "....#", "....#"],
    '5': ["#####", "#....", "#....", "#####", "....#", "....#", ".###."],
    '6': [".###.", "#....", "#....", "#####", "#...#", "#...#", ".###."],
    '7': ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    '8': [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    '9': [".###.", "#...#", "#...#", ".###.", "....#", "....#", ".###."],
    '.': [".....", ".....", ".....", "..#..", ".....", ".....", "....."],
    ',': [".....", ".....", ".....", "..#..", ".#...", ".....", "....."],
    ':': [".....", "..#..", ".....", "..#..", ".....", ".....", "....."],
    ';': [".....", "..#..", ".....", "..#..", ".#...", ".....", "....."],
    '-': [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    "'": [".....", "#....", ".....", ".....", ".....", ".....", "....."],
    '"': [".....", ".#.#.", ".....", ".....", ".....", ".....", "....."],
    '/': ["....#", "...#.", "..#..", ".#...", "#....", ".....", "....."],
    '(': ["....#", "...#.", "...#.", "...#.", "...#.", "...#.", "....#"],
    ')': ["#....", ".#...", ".#...", ".#...", ".#...", ".#...", "#...."],
    '&': [".###.", "#...#", "#...#", ".###.", "#.#.#", "#.#.#", ".###."],
    '<': ["...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."],
    '>': [".#...", "..#..", "...#.", "#....", "...#.", "..#..", ".#..."],
    '?': [".###.", "....#", "...#.", "..#..", ".....", "..#..", "..#.."],
    '!': ["..#..", "..#..", "..#..", "..#..", ".....", "..#..", "..#.."],
    '@': [".###.", "#...#", "#.#.#", "#.#.#", "#...#", "#...#", ".###."],
    '#': [".#.#.", ".#.#.", "#####", ".#.#.", ".#.#.", "#####", ".#.#."],
    '=': [".....", ".....", "#####", ".....", "#####", ".....", "....."],
    '+': [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    '_': [".....", ".....", ".....", ".....", ".....", ".....", "#####"],
}


def text_w(s, scale, gap=1):
    return len(s) * (5 + gap) * scale - gap * scale if s else 0


def render_text(x, y, s, scale, c, bold=False, gap=1):
    cx = x
    for ch in s.upper():
        g = GLYPHS.get(ch)
        if g is None:
            cx += (5 + gap) * scale
            continue
        for ri, row in enumerate(g):
            for ci, px_ in enumerate(row):
                if px_ == '#':
                    bx = cx + ci * scale
                    by = y + ri * scale
                    bw = scale + 1 if bold else scale
                    rect(bx, by, bw, scale, c)
        cx += (5 + gap) * scale


def center_text(x, y, s, scale, c, bold=False, gap=1):
    render_text(x - text_w(s, scale, gap) // 2, y, s, scale, c, bold, gap)


# ---------------------------------------------------------------- country data
COUNTRY = "REPUBLIC OF KOLMARA"
CAPITAL = "HRAVEN"
NATIONALITY = "KOLMARAN"
NAT_CODE = "KOL"
CURRENCY = "HRN"
HOLDER = "ANNA MIRKA"
SURNAME, GIVEN = "MIRKA", "ANNA"
DOB = "03.09.1988"          # 1988-09-03 -> MRZ 880903
ISSUE = "12.04.2023"        # 2023-04-12
EXPIRY = "11.04.2033"       # 2033-04-11 (10 years after issue)
PASSNO = "V7418209"
AUTHORITY = "PASSPORT OFFICE " + CAPITAL
SEX = "F"
MRZ_DOB = "880903"
MRZ_EXP = "330411"


def mrz_val(ch):
    if ch == '<':
        return 0
    if ch.isdigit():
        return int(ch)
    return ord(ch) - ord('A') + 10


def mrz_check(s):
    w = (7, 3, 1)
    return sum(mrz_val(c) * w[i % 3] for i, c in enumerate(s)) % 10


docnum = PASSNO.ljust(9, '<')
d1 = mrz_check(PASSNO)
d2 = mrz_check(MRZ_DOB)
d3 = mrz_check(MRZ_EXP)
opt = '<' * 14
d4 = mrz_check(opt)
d5 = mrz_check(PASSNO + MRZ_DOB + MRZ_EXP)
assert (d1, d2, d3, d4, d5) == (2, 6, 2, 0, 2), (d1, d2, d3, d4, d5)
MRZ1 = "P<%s<<%s<<%s" % (NAT_CODE, SURNAME, GIVEN)
MRZ1 = MRZ1.ljust(44, '<')
MRZ2 = (docnum + str(d1) + NAT_CODE + MRZ_DOB + str(d2) + SEX + MRZ_EXP
        + str(d3) + opt + str(d4) + str(d5))
assert len(MRZ1) == 44 and len(MRZ2) == 44, (len(MRZ1), len(MRZ2))

# travel history: all dates after issue, before expiry
STAMPS = [
    (640, 220, PURPLE, 11, "STORVIGA", "ENTRY", "18.06.2024"),
    (896, 220, PURPLE, 12, "STORVIGA", "EXIT", "25.06.2024"),
    (640, 400, GREEN, 13, "QENDRU", "ENTRY", "10.03.2025"),
    (896, 400, GREEN, 14, "QENDRU", "EXIT", "22.03.2025"),
    (768, 560, RED, 15, "TARN", "ENTRY", "14.01.2026"),
]


# ---------------------------------------------------------------- drawing
def portrait(cx, cy):
    """Drawn stylised portrait: head, shoulders, shading, features."""
    # neck (right side lit)
    rect(cx - 13, cy + 30, 26, 18, SKIN_SHADE)
    rect(cx, cy + 30, 13, 18, SKIN)
    # head: shade left half, light right half
    circle_fill(cx, cy, 42, SKIN_SHADE)
    rect(cx, cy - 42, 42, 84, SKIN)
    circle_outline(cx, cy, 42, INK, 2)
    # hair
    rect(cx - 42, cy - 48, 84, 30, HAIR)
    rect(cx - 42, cy - 30, 10, 32, HAIR)
    rect(cx + 32, cy - 30, 10, 32, HAIR)
    for bx in range(cx - 26, cx + 27, 7):              # bangs
        line(bx, cy - 9, bx, cy - 4, HAIR, 1)
    # ears
    circle_fill(cx - 41, cy, 6, SKIN)
    circle_fill(cx + 41, cy, 6, SKIN)
    circle_outline(cx - 41, cy, 6, INK, 1)
    circle_outline(cx + 41, cy, 6, INK, 1)
    # face
    rect(cx - 16, cy - 9, 5, 2, INK)                   # left eye
    rect(cx + 11, cy - 9, 5, 2, INK)                   # right eye
    line(cx - 18, cy - 13, cx - 12, cy - 13, HAIR, 1)  # left brow
    line(cx + 12, cy - 13, cx + 18, cy - 13, HAIR, 1)  # right brow
    line(cx - 1, cy - 4, cx + 2, cy + 4, INK, 1)       # nose
    setpx(cx + 1, cy + 7, INK)                         # nostril
    line(cx - 6, cy + 13, cx - 2, cy + 15, INK, 1)     # mouth
    line(cx + 2, cy + 15, cx + 6, cy + 13, INK, 1)
    # white collar
    tri((cx - 14, cy + 48), (cx + 14, cy + 48), (cx, cy + 34), WHITE)
    rect(cx - 58, cy + 48, 116, 44, SHIRT)             # shirt body
    rect(cx + 6, cy + 48, 52, 44, SHIRT_LIT)           # lighting on right side
    rect(cx - 58, cy + 47, 116, 1, INK)                # shirt border
    rect(cx - 58, cy + 90, 116, 1, INK)
    rect(cx - 58, cy + 48, 1, 43, INK)
    rect(cx + 57, cy + 48, 1, 43, INK)


def stamp(cx, cy, r, color, seed, top, bottom, center_lines):
    rnd = random.Random(seed)
    ring = lambda rr, t: circle_outline(cx, cy, rr, color, t)
    ring(r, 2)
    ring(r - 15, 1)
    # radial ticks
    for a in range(0, 360, 12):
        rad = math.radians(a)
        x1 = cx + (r - 6) * math.cos(rad)
        y1 = cy - (r - 6) * math.sin(rad)
        x2 = cx + (r - 14) * math.cos(rad)
        y2 = cy - (r - 14) * math.sin(rad)
        line(int(x1 + rnd.uniform(-1, 1)), int(y1 + rnd.uniform(-1, 1)),
             int(x2 + rnd.uniform(-1, 1)), int(y2 + rnd.uniform(-1, 1)), color, 1)
    # arc text
    def arc(text, a0, a1):
        n = len(text)
        for i, ch in enumerate(text):
            a = math.radians(a0 + (a1 - a0) * (i / max(n - 1, 1)))
            px = cx + (r - 22) * math.cos(a) + rnd.uniform(-1.2, 1.2)
            py = cy - (r - 22) * math.sin(a) + rnd.uniform(-1.2, 1.2)
            render_text(int(px) - 2, int(py) - 3, ch, 1, color)
    arc(top, 140, 40)
    arc(bottom, 220, 320)
    # centre block
    yy = cy - 10
    for ln in center_lines:
        center_text(cx, yy, ln, 1, color)
        yy += 9
    # small star under centre text
    sx, sy = cx, cy + 14
    line(sx - 3, sy, sx + 3, sy, color, 1)
    line(sx, sy - 2, sx, sy + 2, color, 1)
    line(sx - 2, sy - 1, sx + 2, sy + 1, color, 1)
    line(sx - 2, sy + 1, sx + 2, sy - 1, color, 1)


def permit_box(x, y, w, h):
    rect(x, y, w, h, (238, 228, 204))
    rect(x, y, w, 2, INK2)
    rect(x, y + h - 2, w, 2, INK2)
    rect(x, y, 2, h, INK2)
    rect(x + w - 2, y, 2, h, INK2)
    rect(x + 4, y + 4, w - 8, 1, INK2)
    rect(x + 4, y + h - 5, w - 8, 1, INK2)
    rect(x + 4, y + 4, 1, h - 8, INK2)
    rect(x + w - 5, y + 4, 1, h - 8, INK2)
    center_text(x + w // 2, y + 20, "HIGH-ALTITUDE PASS PERMIT", 2, INK, bold=True)
    center_text(x + w // 2, y + 52, "ZONES A-B-C   FEE " + CURRENCY + " 12.00", 2, INK)
    center_text(x + w // 2, y + 82, "ISSUED AT " + CAPITAL + "  05.03.2025", 2, INK)
    center_text(x + w // 2, y + 112, "VALID UNTIL " + EXPIRY, 2, INK)
    center_text(x + w // 2, y + 140, "MOUNTAIN REPUBLIC - BORDER ZONE RULES APPLY", 1, INK)
    circle_outline(x + w - 42, y + 62, 20, RED, 2)
    circle_fill(x + w - 42, y + 62, 6, RED)


def signature(x, y, w, seed):
    rnd = random.Random(seed)
    cx_ = x
    cy_ = y
    for _ in range(12):
        nx = cx_ + rnd.uniform(10, 18)
        ny = cy_ + rnd.uniform(-6, 6)
        line(int(cx_), int(cy_), int(nx), int(ny), INK, 2)
        cx_, cy_ = int(nx), int(ny)


def page_frame(x0):
    rect(x0, 0, PAGE_W, 2, INK2)
    rect(x0, H - 2, PAGE_W, 2, INK2)
    rect(x0, 0, 2, H, INK2)
    rect(x0 + PAGE_W - 2, 0, 2, H, INK2)


def build():
    os.makedirs('/output', exist_ok=True)

    # ----- left page: data page
    page_frame(0)
    # title band
    rect(0, 0, PAGE_W, 60, BLUE)
    center_text(PAGE_W // 2, 8, COUNTRY, 4, WHITE)
    center_text(PAGE_W // 2, 36, "PASSPORT", 3, WHITE)
    rect(0, 66, PAGE_W, 1, INK2)

    # portrait box
    rect(40, 86, 190, 200, WHITE)
    rect(40, 86, 190, 200, INK2) if False else None
    rect(40, 86, 190, 2, INK2)
    rect(40, 284, 190, 2, INK2)
    rect(40, 86, 2, 198, INK2)
    rect(228, 86, 2, 198, INK2)
    portrait(135, 185)

    # data fields
    rows = [
        ("PASSPORT NO.", PASSNO),
        ("SURNAME", SURNAME),
        ("GIVEN NAMES", GIVEN),
        ("NATIONALITY", NATIONALITY),
        ("SEX", SEX),
        ("DATE OF BIRTH", DOB),
        ("PLACE OF BIRTH", CAPITAL),
        ("DATE OF ISSUE", ISSUE),
        ("DATE OF EXPIRY", EXPIRY),
        ("AUTHORITY", AUTHORITY),
    ]
    yy = 315
    for label, value in rows:
        render_text(40, yy, label, 2, INK)
        render_text(205, yy, value, 2, INK, bold=True)
        yy += 33
    render_text(40, yy, "SIGNATURE", 2, INK)
    signature(205, yy + 4, 140, 21)

    # rule above MRZ
    rect(40, 682, 460, 1, INK2)
    center_text(PAGE_W // 2, 696, "MACHINE READABLE ZONE", 1, INK2)

    render_text(40, 714, MRZ1, 2, INK, gap=0)
    render_text(40, 742, MRZ2, 2, INK, gap=0)

    center_text(PAGE_W // 2, 970, COUNTRY + "  -  PASSPORT  " + PASSNO, 1, INK2)

    # ----- right page: stamps & visas
    page_frame(PAGE_W)
    center_text(PAGE_W + PAGE_W // 2, 60, "VISAS  AND  STAMPS", 3, INK)
    rect(PAGE_W, 100, PAGE_W, 1, INK2)

    for cx, cy, color, seed, top, bottom, center_lines in STAMPS:
        stamp(cx, cy, 52, color, seed, top, bottom, center_lines.split("|"))

    permit_box(PAGE_W + 43, 690, PAGE_W - 86, 160)

    center_text(PAGE_W + PAGE_W // 2, 970, COUNTRY + "  -  PASSPORT  " + PASSNO, 1, INK2)

    # ----- encode PNG
    raw = bytes(pix)
    out = bytearray(b'\x89PNG\r\n\x1a\n')

    def chunk(ctype, data):
        nonlocal out
        out += struct.pack('>I', len(data)) + ctype + data
        out += struct.pack('>I', zlib.crc32(ctype + data) & 0xFFFFFFFF)

    scanlines = bytearray()
    for y in range(H):
        scanlines.append(0)  # filter type 0: none
        scanlines += raw[y * W * 4:(y + 1) * W * 4]
    compressed = zlib.compress(bytes(scanlines))

    chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 6, 0, 0, 0))
    chunk(b'IDAT', compressed)
    chunk(b'IEND', b'')

    path = '/output/entry.png'
    with open(path, 'wb') as f:
        f.write(out)
    print("wrote %s: %d bytes, %dx%d" % (path, len(out), W, H))


if __name__ == '__main__':
    build()
