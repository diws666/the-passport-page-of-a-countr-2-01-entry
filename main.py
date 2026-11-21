#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic stdlib-only generator of an invented passport spread.

Open passport spread for the Republic of Veltis, a fictional river-delta
trading republic (independent of the earlier Kolmara mountain-republic
entry): a data page with a drawn portrait + machine-readable zone, and a
visa/stamp page with arrival/departure stamps from neighbouring countries
plus a river-pilotage fee endorsement that reveals the place.

Encodes a PNG with zlib (no image library). Same bytes every run.
Output: /output/entry.png (<= 1 048 576 bytes, <= 1024 x 1024 px).
"""

import zlib
import struct
import os
import math

W, H = 1024, 1024

# --------------------------------------------------------------------------- palette
PAPER = (247, 244, 236, 255)      # off-white passport paper
INK = (22, 28, 38, 255)            # dark document ink
INK_SOFT = (95, 100, 110, 255)     # secondary text
LINE = (132, 126, 114, 255)        # rules / borders
GOLD = (158, 128, 72, 255)         # issuing seal
GOLD_DARK = (112, 86, 40, 255)
BLUE = (38, 80, 132, 255)          # stamp ink (Korvaine)
RED = (168, 52, 48, 255)           # stamp ink (Saltholm)
GREEN = (62, 112, 72, 255)         # endorsement ink
SKIN = (228, 196, 168, 255)
SKIN_SHADE = (196, 160, 128, 255)
HAIR = (46, 38, 34, 255)

# --------------------------------------------------------------------------- bitmap font (5x7)
# rows: 7 strings of 5 chars, '#' = ink
_F = {
    ' ': ["     "] * 7,
    "'": ["  #  ", "  #  ", "     ", "     ", "     ", "     ", "     "],
    '-': ["     ", "     ", "     ", "#####", "     ", "     ", "     "],
    '.': ["     ", "     ", "     ", "     ", "     ", "  #  ", "  #  "],
    ':': ["     ", "     ", "  #  ", "     ", "  #  ", "     ", "     "],
    ';': ["     ", "     ", "  #  ", "     ", "  #  ", "  #  ", "     "],
    '/': ["    #", "   # ", "  #  ", " #   ", "#    ", "     ", "     "],
    '&': [" .##.", "#..#.", "#..#.", ".##. ", "..#.#", ".#.#.", "##.#."],
    '@': [" .##.", "#..#.", "#.#.#", "#.#.#", "#..#.", ".##.#", "..#.."],
    '#': ["#.#.#", "#.#.#", "#####", "#.#.#", "#.#.#", "#.#.#", "#.#.#"],
    '$': [" .##.", "#....", "#.###", "#..#.", ".###.", "....#", ".##.."],
    '<': ["    #", "   # ", "  #  ", "   # ", "    #", "     ", "     "],
    '0': [" .##.", "#..#.", "#.#.#", "#.#.#", "#.#.#", "#..#.", ".##."],
    '1': ["  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", "###."],
    '2': [" .##.", "#..#.", "....#", "....#", ".##..", "#....", "###."],
    '3': [" .##.", "#..#.", "....#", ".##..", "....#", "#..#.", ".##."],
    '4': ["....#", "...#.", "..#.#", ".#.#.#", "#####", "....#", "....#"],
    '5': ["#####", "#....", "#.###", "#..#.", "....#", "#..#.", ".##."],
    '6': [" .##.", "#....", "#.###", "#..#.", "#..#.", "#..#.", ".##."],
    '7': ["#####", "....#", "....#", "...#.", "..#..", "..#..", "..#.."],
    '8': [" .##.", "#..#.", "#..#.", ".##.", "#..#.", "#..#.", ".##."],
    '9': [" .##.", "#..#.", "#..#.", ".####", "....#", "#..#.", ".##."],
}
_UC = {
    'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'B': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    'C': [".###.", "#...#", "#....", "#....", "#...#", "#...#", ".###."],
    'D': ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    'E': ["#####", "#....", "#....", "###..", "#....", "#....", "#####"],
    'F': ["#####", "#....", "#....", "###..", "#....", "#....", "#...."],
    'G': [".###.", "#...#", "#....", "#.##.", "#...#", "#...#", ".###."],
    'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'I': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    'J': ["####.", "...#.", "...#.", "...#.", "#..#.", "#..#.", ".###."],
    'K': ["#...#", "#.#..", "#..#.", "#.#..", "#..#.", "#.#..", "#...#"],
    'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    'M': ["#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#", "#...#"],
    'N': ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'Q': [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#.#..", "#..#."],
    'S': [".###.", "#....", "#....", ".##..", "....#", "#...#", ".###."],
    'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'U': ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'V': ["#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#.", ".#.#."],
    'W': ["#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    'X': ["#...#", "#.#.#", ".#.#.", "..#..", ".#.#.", "#.#.#", "#...#"],
    'Y': ["#...#", "#.#.#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    'Z': ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
}
_F.update(_UC)
for _c, _rows in _F.items():
    _F[_c] = [r[:5].ljust(5) for r in _rows]
FONT = _F
FW, FH = 5, 7
PITCH = 6
LINEPITCH = 9


def _bit(rows, row, col):
    return rows[row][col] == '#'


# --------------------------------------------------------------------------- canvas
class Img:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.buf = bytearray([0]) * (w * h * 3)

    def _idx(self, x, y):
        return (y * self.w + x) * 3

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = self._idx(x, y)
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def fill_rect(self, x0, y0, x1, y1, c):
        self.rect(x0, y0, x1, y1, c)

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            self.set(x, y, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, c, fill=False, thick=1):
        r2 = r * r
        inner = (r - thick) * (r - thick) if r > thick else 0
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                d = (x - cx) * (x - cx) + (y - cy) * (y - cy)
                if fill:
                    if d <= r2:
                        self.set(x, y, c)
                else:
                    if inner <= d <= r2:
                        self.set(x, y, c)

    def text(self, x, y, s, c, scale=1):
        cx = x
        for ch in s:
            if ch == ' ':
                cx += PITCH * scale
                continue
            rows = FONT.get(ch)
            if rows is None:
                cx += PITCH * scale
                continue
            for row in range(FH):
                for col in range(FW):
                    if _bit(rows, row, col):
                        bx = cx + col * scale
                        by = y + row * scale
                        for dy in range(scale):
                            for dx in range(scale):
                                self.set(bx + dx, by + dy, c)
            cx += PITCH * scale
        return cx - x

    def textw(self, s, scale=1):
        return len(s) * PITCH * scale


# --------------------------------------------------------------------------- MRZ (TD3, two lines of 44) with correct check digits
def _mrz_val(ch):
    if ch == '<':
        return 0
    if ch.isdigit():
        return int(ch)
    return ord(ch) - ord('A') + 10


def mrz_chd(s):
    total = 0
    for i, ch in enumerate(s):
        total += _mrz_val(ch) * (7, 3, 1)[i % 3]
    return total % 10


def build_mrz(surname, given, docno, nationality, dob, sex, expiry):
    line1 = "P<" + nationality + surname + "<<" + given
    line1 = line1.ljust(44, "<")[:44]

    docno_field = docno.ljust(9, "<")[:9]
    cd_docno = mrz_chd(docno_field)
    cd_dob = mrz_chd(dob)
    cd_exp = mrz_chd(expiry)
    personal = "<" * 14
    cd_personal = mrz_chd(personal)
    comp_src = (docno_field + str(cd_docno) + dob + str(cd_dob) +
                expiry + str(cd_exp) + personal + str(cd_personal))
    cd_comp = mrz_chd(comp_src)

    l2 = ["<"] * 44
    l2[0:9] = list(docno_field)
    l2[9] = str(cd_docno)
    l2[10:13] = list(nationality)
    l2[13:19] = list(dob)
    l2[19] = str(cd_dob)
    l2[20] = sex
    l2[21:27] = list(expiry)
    l2[27] = str(cd_exp)
    l2[28:42] = list(personal)
    l2[42] = str(cd_personal)
    l2[43] = str(cd_comp)
    line2 = "".join(l2)
    assert len(line1) == 44 and len(line2) == 44
    return line1, line2


# --------------------------------------------------------------------------- portrait
def draw_portrait(img, cx, cy, r):
    """Stylised bust: a woman in her mid-thirties, river-trader character.

    Head, neck, shoulders, long hair, simple facial features and shading.
    Entirely drawn; no photo pasted in.
    """
    # garment / shoulders
    img.rect(cx - r - 14, cy + 6, cx + r + 14, cy + r + 26, INK)
    img.rect(cx - r - 8, cy + 6, cx + r + 8, cy + 16, INK)
    # neck
    img.rect(cx - 6, cy - 8, cx + 6, cy + 6, SKIN)
    # head (left side shaded)
    img.circle(cx, cy - 18, r, SKIN, fill=True)
    img.fill_rect(cx - r - 2, cy - 20, cx - 3, cy - 10, SKIN_SHADE)
    # hair (fuller at back, side locks at front)
    img.circle(cx, cy - 24, r + 5, HAIR, fill=True)
    img.rect(cx - r - 5, cy - 18, cx + r + 5, cy - 4, HAIR)
    img.circle(cx, cy - 18, r - 2, SKIN, fill=True)
    img.fill_rect(cx - r + 2, cy - 20, cx - 3, cy - 10, SKIN_SHADE)
    # eyes
    for dx in (-5, -4, 3, 4):
        img.set(cx + dx, cy - 22, INK)
    # brows
    img.line(cx - 7, cy - 25, cx - 3, cy - 25, INK)
    img.line(cx + 2, cy - 25, cx + 6, cy - 25, INK)
    # nose
    img.line(cx, cy - 19, cx + 1, cy - 16, INK)
    img.line(cx + 1, cy - 16, cx + 2, cy - 15, INK)
    # mouth
    img.line(cx - 3, cy - 13, cx + 3, cy - 13, INK)
    # age lines (mid-thirties)
    img.line(cx - 6, cy - 14, cx - 4, cy - 14, SKIN_SHADE)
    img.line(cx + 4, cy - 14, cx + 6, cy - 14, SKIN_SHADE)
    # side locks
    img.line(cx - 10, cy - 19, cx - 12, cy - 10, HAIR)
    img.line(cx - 11, cy - 18, cx - 13, cy - 9, HAIR)
    # collar line
    img.line(cx - 11, cy + 8, cx + 11, cy + 8, INK)


# --------------------------------------------------------------------------- stamp
def draw_stamp(img, cx, cy, r, ink, top, date, bottom):
    """Circular ink stamp: double ring, radial ticks, top/date/bottom text."""
    img.circle(cx, cy, r, ink, fill=False, thick=2)
    img.circle(cx, cy, r - 6, ink, fill=False, thick=1)
    for a in range(0, 360, 18):
        rad = math.radians(a)
        x1 = cx + (r - 4) * math.cos(rad)
        y1 = cy + (r - 4) * math.sin(rad)
        x2 = cx + r * math.cos(rad)
        y2 = cy + r * math.sin(rad)
        img.line(int(x1), int(y1), int(x2), int(y2), ink)
    if top:
        img.text(cx - img.textw(top, 1) // 2, cy - r + 5, top, ink, scale=1)
    img.text(cx - img.textw(date, 1) // 2, cy - 2, date, ink, scale=1)
    if bottom:
        img.text(cx - img.textw(bottom, 1) // 2, cy + r - 11, bottom, ink, scale=1)


# --------------------------------------------------------------------------- build
def main():
    img = Img(W, H)
    img.rect(0, 0, W - 1, H - 1, PAPER)

    # ---- single source of truth for every field (consistency is everything)
    COUNTRY = "REPUBLIC OF VELTIS"
    CAPITAL = "DRENMOUTH"
    NATIONALITY = "VLT"
    SURNAME = "DORN"
    GIVEN = "ELSIRA"
    SEX = "F"
    DOB = "12.04.1988"
    DOB_MRZ = "880412"
    PLACE_OF_BIRTH = CAPITAL
    ISSUE = "14.03.2023"
    EXPIRY = "14.03.2033"
    EXPIRY_MRZ = "330314"
    DOCNO = "VLT884127"
    ISSUING_AUTH = "OFFICE OF PASSPORT & SEAL"
    OCCUPATION = "RIVER TRADER"

    # stamps (every date after issue, before expiry)
    STAMP_ARR_TOP = "REPUBLIC OF KORVAINE"
    STAMP_ARR_DATE = "05.09.2024"
    STAMP_ARR_BOTTOM = "VEYKENS FERRY"
    STAMP_DEP_TOP = "SALTHOLM"
    STAMP_DEP_DATE = "18.11.2025"
    STAMP_DEP_BOTTOM = "PORT GRIS"
    ENDORSE_DATE = "02.07.2025"

    mrz1, mrz2 = build_mrz(SURNAME, GIVEN, DOCNO, NATIONALITY,
                           DOB_MRZ, SEX, EXPIRY_MRZ)

    # page rectangles
    LPAGE = (40, 40, 510, 985)     # left = data page
    RPAGE = (540, 40, 1010, 985)   # right = visa / stamp page

    for (x0, y0, x1, y1) in (LPAGE, RPAGE):
        img.rect(x0, y0, x1, y1, LINE)
        img.rect(x0 + 2, y0 + 2, x1 - 2, y1 - 2, LINE)
    img.line(514, 40, 514, 985, LINE)   # binding gutter
    img.line(516, 40, 516, 985, LINE)

    # ---------------- left page: data page
    lx0, ly0, lx1, ly1 = LPAGE
    img.text(lx0 + 15, ly0 + 12, COUNTRY, INK, scale=3)
    img.text(lx0 + 15, ly0 + 12 + 3 * LINEPITCH + 4, "PASSPORT", INK, scale=1)
    # issuing seal emblem (gold) beside the title
    sx = lx0 + 15 + img.textw(COUNTRY, 3) + 10
    sy = ly0 + 12 + (3 * LINEPITCH) // 2
    img.circle(sx, sy, 14, GOLD, fill=False, thick=2)
    img.circle(sx, sy, 14, GOLD_DARK, fill=False, thick=1)
    img.text(sx - 5, sy - 3, "VLT", GOLD_DARK, scale=1)
    img.line(sx + 17, sy, sx + 30, sy, LINE)

    # portrait box (top-left of data page)
    pbx0, pby0, pbx1, pby1 = lx0 + 15, ly0 + 60, lx0 + 150, ly0 + 200
    img.rect(pbx0, pby0, pbx1, pby1, LINE)
    img.rect(pbx0 + 1, pby0 + 1, pbx1 - 1, pby1 - 1, LINE)
    draw_portrait(img, (pbx0 + pbx1) // 2, (pby0 + pby1) // 2, 42)

    # data fields to the right of the portrait
    fx = pbx1 + 20
    fields = [
        ("SURNAME", SURNAME),
        ("GIVEN NAMES", GIVEN),
        ("NATIONALITY", NATIONALITY),
        ("DATE OF BIRTH", DOB),
        ("PLACE OF BIRTH", PLACE_OF_BIRTH),
        ("SEX", SEX),
        ("DATE OF ISSUE", ISSUE),
        ("DATE OF EXPIRY", EXPIRY),
        ("PASSPORT NO.", DOCNO),
        ("ISSUING AUTHORITY", ISSUING_AUTH),
        ("PLACE OF ISSUE", CAPITAL),
        ("OCCUPATION", OCCUPATION),
    ]
    fy = ly0 + 66
    value_x = fx + max(len(label) for label, _ in fields) * PITCH + 16
    for label, value in fields:
        img.text(fx, fy, label, INK_SOFT, scale=1)
        img.text(value_x, fy, value, INK, scale=2)
        fy += 28

    # MRZ band at the bottom of the data page
    mrz_y = ly1 - 70
    img.line(lx0 + 15, mrz_y - 8, lx1 - 15, mrz_y - 8, LINE)
    img.text(lx0 + 15, mrz_y - 6, "MACHINE READABLE ZONE", INK_SOFT, scale=1)
    img.text(lx0 + 15, mrz_y + 6, mrz1, INK, scale=1)
    img.text(lx0 + 15, mrz_y + 6 + 10, mrz2, INK, scale=1)
    img.text(lx0 + 15, mrz_y + 28, "DOCUMENT NO. " + DOCNO, INK_SOFT, scale=1)

    # ---------------- right page: visas / stamps
    rx0, ry0, rx1, ry1 = RPAGE
    img.text(rx0 + 15, ry0 + 12, "VISAS AND ENDORSEMENTS", INK, scale=2)
    img.line(rx0 + 15, ry0 + 12 + 2 * LINEPITCH + 4, rx1 - 15,
             ry0 + 12 + 2 * LINEPITCH + 4, LINE)

    # stamp 1: Korvaine arrival (blue)
    draw_stamp(img, rx0 + 150, ry0 + 150, 40, BLUE,
               STAMP_ARR_TOP, STAMP_ARR_DATE, STAMP_ARR_BOTTOM)
    img.text(rx0 + 15, ry0 + 205, "Arrival - Korvaine (river border)", INK_SOFT, scale=1)

    # stamp 2: Saltholm departure (red)
    draw_stamp(img, rx0 + 320, ry0 + 260, 38, RED,
               STAMP_DEP_TOP, STAMP_DEP_DATE, STAMP_DEP_BOTTOM)
    img.text(rx0 + 15, ry0 + 315, "Departure - Saltholm (port)", INK_SOFT, scale=1)

    # paperwork detail: river pilotage / transit fee endorsement (green)
    # reveals Veltis is a river-delta trading state
    ex = rx0 + 15
    ey = ry0 + 375
    img.rect(ex, ey, ex + 230, ey + 120, LINE)
    img.rect(ex + 1, ey + 1, ex + 229, ey + 119, LINE)
    img.text(ex + 8, ey + 8, "RIVER VELT DELTA PILOTAGE", GREEN, scale=1)
    img.text(ex + 8, ey + 8 + 10, "& TRANSIT AUTHORITY - DRENMOUTH", GREEN, scale=1)
    img.line(ex + 8, ey + 8 + 16, ex + 220, ey + 8 + 16, GREEN)
    img.text(ex + 8, ey + 8 + 20, "Transit fee 12 fl. paid", INK, scale=1)
    img.text(ex + 8, ey + 8 + 30, "Craft MORNINGSIDE  -  Master E. DORN", INK, scale=1)
    img.text(ex + 8, ey + 8 + 40, ENDORSE_DATE, INK, scale=1)
    img.circle(ex + 206, ey + 46, 8, GREEN, fill=False, thick=2)
    img.text(ex + 8, ey + 8 + 56, "Endorsement required for river craft", INK_SOFT, scale=1)
    img.text(ex + 8, ey + 8 + 66, "trading the Velt delta.", INK_SOFT, scale=1)

    # page folios
    img.text(lx0 + 15, ly1 - 8, "P.1", INK_SOFT, scale=1)
    img.text(rx1 - 20 - img.textw("P.2", 1), ry1 - 8, "P.2", INK_SOFT, scale=1)

    # ------------------------------------------------------------------ encode PNG
    # filter type 0 (none) per scanline
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)
        raw.extend(img.buf[y * stride:(y + 1) * stride])
    compressed = zlib.compress(bytes(raw), 6)

    def chunk(ctype, data):
        c = ctype.encode() if isinstance(ctype, str) else ctype
        body = data.encode() if isinstance(data, str) else data
        length = struct.pack(">I", len(body))
        crc = struct.pack(">I", zlib.crc32(c + body) & 0xFFFFFFFF)
        return length + c + body + crc

    png = bytearray()
    png += b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)  # 8-bit RGB
    png += chunk("IHDR", ihdr)
    png += chunk("IDAT", compressed)
    png += chunk("IEND", b"")

    os.makedirs("/output", exist_ok=True)
    out = bytes(png)
    with open("/output/entry.png", "wb") as f:
        f.write(out)
    print("wrote /output/entry.png  %d bytes  %dx%d" % (len(out), W, H))


if __name__ == "__main__":
    main()
