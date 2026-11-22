#!/usr/bin/env python3
"""news-image-20261122-entry: a one-page newspaper front page summing up
Sunday 22 November 2026, drawn from scratch with pure Python stdlib.

The program draws a 1024x1024 PNG with a masthead naming the date, six
story panels (each with a hand-drawn vector pictogram and short labels),
and a footer ticker of further headlines from the same day. Output is
fully deterministic: no randomness, no time, no network.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---- palette ------------------------------------------------------------
PAPER = (247, 242, 231)   # newsprint cream
INK = (18, 18, 20)        # near-black ink
RED = (176, 30, 30)       # headline red
BLUE = (31, 78, 121)      # deep blue
NAVY = (16, 32, 56)       # ticker band
GOLD = (201, 148, 42)
GREEN = (46, 125, 50)
ORANGE = (214, 96, 20)
SKY = (168, 205, 230)
SEA = (46, 110, 158)
GREY = (110, 110, 108)
LIGHT = (232, 226, 212)

# ---- 5x7 bitmap font ----------------------------------------------------
# Each glyph: 7 strings of 5 chars, '#' = ink.
_G = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '>': ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
}

CHAR_W, CHAR_H = 5, 7


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def wrap_text(s, max_width, scale):
    """Greedy word wrap; returns list of lines that fit max_width."""
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---- canvas ---------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def border(self, x, y, w, h, c, t=2):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            for a in range(t):
                self.set(x0 + a, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d <= r * r:
                        self.set(xx, yy, c)
                else:
                    if r * r - 2 * r <= d <= r * r:
                        self.set(xx, yy, c)

    def triangle(self, p0, p1, p2, c):
        # barycentric fill
        xs = [p0[0], p1[0], p2[0]]
        ys = [p0[1], p1[1], p2[1]]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        d = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
        if d == 0:
            return
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                a = ((p1[1] - p2[1]) * (xx - p2[0]) + (p2[0] - p1[0]) * (yy - p2[1])) / d
                b = ((p2[1] - p0[1]) * (xx - p2[0]) + (p0[0] - p2[0]) * (yy - p2[1])) / d
                cc = 1 - a - b
                if a >= 0 and b >= 0 and cc >= 0:
                    self.set(xx, yy, c)

    def text(self, s, x, y, scale, c):
        s = s.upper()
        cx = x
        for ch in s:
            glyph = _G.get(ch, _G['?'])
            for row in range(CHAR_H):
                bits = glyph[row]
                for col in range(CHAR_W):
                    if bits[col] == '1':
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, c)
            cx += 6 * scale
        return cx

    def text_centred(self, s, cx, y, scale, c):
        w = text_width(s, scale)
        self.text(s, cx - w // 2, y, scale, c)

    def para(self, s, x, y, max_w, scale, c, leading=None):
        if leading is None:
            leading = 9 * scale
        for line in wrap_text(s, max_w, scale):
            self.text(line, x, y, scale, c)
            y += leading
        return y


# ---- pictograms ------------------------------------------------------------
def pic_gulf(cv, x, y, w, h):
    """Strait of Hormuz: tanker on the sea, drones above, blast star."""
    cv.rect(x, y, w, h, SKY)
    # sun
    cv.circle(x + w - 26, y + 24, 14, GOLD)
    # sea
    cv.rect(x, y + h * 3 // 5, w, h * 2 // 5, SEA)
    for k in range(3):
        yy = y + h * 3 // 5 + 12 + k * 14
        for xx in range(x + 8, x + w - 8, 26):
            cv.line(xx, yy, xx + 12, yy, (220, 235, 245), 2)
    # tanker hull
    hx, hy = x + w // 2 - 62, y + h * 3 // 5 - 6
    cv.rect(hx, hy, 124, 22, INK)
    cv.rect(hx + 8, hy - 22, 34, 22, INK)          # bridge block
    cv.rect(hx + 88, hy - 14, 26, 14, RED)         # funnel
    cv.line(hx, hy + 22, hx + 124, hy + 22, RED, 3)
    # explosion star above the ship
    ex, ey = hx + 100, hy - 44
    for dx, dy in [(0, -18), (13, -13), (18, 0), (13, 13), (0, 18),
                   (-13, 13), (-18, 0), (-13, -13)]:
        cv.line(ex, ey, ex + dx, ey + dy, ORANGE, 4)
    cv.circle(ex, ey, 9, (255, 190, 60))
    # two drones with dotted paths
    for dx0, dy0 in [(x + 18, y + 30), (x + 52, y + 18)]:
        cv.circle(dx0, dy0, 4, INK)
        cv.line(dx0 - 8, dy0, dx0 + 8, dy0, INK, 2)
        cv.line(dx0, dy0 - 8, dx0, dy0 + 8, INK, 2)


def pic_summit(cv, x, y, w, h):
    """Three leaders at a summit table, three flags behind."""
    cv.rect(x, y, w, h, LIGHT)
    flags = [(RED, "USA"), (GOLD, "CHN"), (BLUE, "RUS")]
    for i, (fc, _) in enumerate(flags):
        fx = x + 22 + i * (w - 44) // 2
        cv.vline(fx, y + 14, 74, INK, 3)
        cv.rect(fx + 3, y + 16, 30, 20, fc)
        cv.rect(fx + 3, y + 16, 30, 7, PAPER if fc is RED else fc)
    # table
    cv.rect(x + 10, y + h - 46, w - 20, 10, (122, 84, 40))
    cv.rect(x + 10, y + h - 36, w - 20, 4, INK)
    # three seated figures
    cols = [NAVY, RED, BLUE]
    for i, c in enumerate(cols):
        fx = x + w // 2 + (i - 1) * 52
        cv.circle(fx, y + h - 78, 15, (232, 190, 150))   # head
        cv.rect(fx - 20, y + h - 62, 40, 20, c)          # shoulders
        cv.rect(fx - 20, y + h - 62, 40, 5, PAPER)       # shirt line


def pic_cop(cv, x, y, w, h):
    """Globe with a leaf: the climate talks in Antalya."""
    cv.rect(x, y, w, h, SKY)
    cx, cy, r = x + w // 2, y + h // 2 + 4, 52
    cv.circle(cx, cy, r, SEA)
    # land blobs
    cv.circle(cx - 18, cy - 14, 14, GREEN)
    cv.circle(cx + 16, cy + 6, 12, GREEN)
    cv.circle(cx + 4, cy - 26, 9, GREEN)
    cv.circle(cx - 26, cy + 20, 8, GREEN)
    cv.circle(cx, cy, r, INK, fill=False)
    # sun rays top-right
    sx, sy = x + w - 24, y + 22
    cv.circle(sx, sy, 10, GOLD)
    for dx, dy in [(0, -16), (12, -12), (16, 0), (12, 12), (0, 16)]:
        cv.line(sx, sy, sx + dx, sy + dy, GOLD, 3)
    # leaf bottom-left
    lx, ly = x + 20, y + h - 26
    cv.triangle((lx, ly - 22), (lx - 14, ly), (lx + 2, ly - 4), GREEN)
    cv.line(lx - 12, ly - 2, lx + 2, ly - 2, GREEN, 3)


def pic_baltic(cv, x, y, w, h):
    """Cargo ship on fire in the Baltic Sea."""
    cv.rect(x, y, w, h, (70, 90, 110))
    cv.rect(x, y + h * 3 // 5, w, h * 2 // 5, (30, 60, 90))
    for k in range(3):
        yy = y + h * 3 // 5 + 12 + k * 14
        for xx in range(x + 8, x + w - 8, 26):
            cv.line(xx, yy, xx + 12, yy, (180, 200, 220), 2)
    hx, hy = x + w // 2 - 58, y + h * 3 // 5 - 4
    cv.rect(hx, hy, 116, 20, (40, 40, 44))
    cv.rect(hx + 10, hy - 20, 30, 20, (40, 40, 44))
    cv.rect(hx + 66, hy - 12, 24, 12, (40, 40, 44))
    # flames
    for fx, fh in [(hx + 20, 34), (hx + 48, 44), (hx + 76, 30)]:
        cv.triangle((fx - 10, hy - 16), (fx + 10, hy - 16), (fx, hy - 16 - fh),
                    ORANGE)
        cv.triangle((fx - 5, hy - 16), (fx + 5, hy - 16), (fx, hy - 16 - fh + 12),
                    (255, 190, 60))
    # smoke
    cv.circle(hx + 30, hy - 58, 9, (200, 200, 200))
    cv.circle(hx + 52, hy - 70, 11, (215, 215, 215))
    cv.circle(hx + 74, hy - 56, 8, (200, 200, 200))


def pic_nigeria(cv, x, y, w, h):
    """Overturned boat on a river, lifebuoy in the water."""
    cv.rect(x, y, w, h, SKY)
    cv.rect(x, y + h // 2, w, h // 2, SEA)
    for k in range(3):
        yy = y + h // 2 + 12 + k * 14
        for xx in range(x + 8, x + w - 8, 26):
            cv.line(xx, yy, xx + 12, yy, (220, 235, 245), 2)
    # capsized hull: dark arc
    cx, cy = x + w // 2, y + h // 2 + 6
    for yy in range(cy - 26, cy + 2):
        half = int(((26 ** 2 - (yy - cy) ** 2) ** 0.5))
        cv.rect(cx - half, yy, 2 * half, 1, INK)
    cv.rect(cx - 52, cy - 2, 104, 6, INK)
    # lifebuoy
    bx, by = x + w - 34, y + h - 30
    cv.circle(bx, by, 13, PAPER)
    cv.circle(bx, by, 13, RED, fill=False)
    cv.circle(bx, by, 6, SEA)
    for dx, dy in [(-9, -9), (9, -9), (-9, 9), (9, 9)]:
        cv.rect(bx + dx - 3, by + dy - 3, 6, 6, RED)


def pic_estonia(cv, x, y, w, h):
    """A closed border: fence, barrier stripes and a stop sign."""
    cv.rect(x, y, w, h, LIGHT)
    # fence posts and rails
    for px in range(x + 14, x + w - 10, 26):
        cv.vline(px, y + 18, h - 40, INK, 4)
    cv.hline(x + 10, y + 34, w - 20, INK, 4)
    cv.hline(x + 10, y + h - 30, w - 20, INK, 4)
    # red-white barrier
    by = y + h - 52
    for i in range(6):
        cv.rect(x + 14 + i * 20, by, 20, 12, RED if i % 2 == 0 else PAPER)
    cv.border(x + 14, by, 120, 12, INK, 2)
    # stop sign
    sx, sy = x + w - 34, y + 30
    cv.circle(sx, sy, 16, RED)
    cv.circle(sx, sy, 16, PAPER, fill=False)
    cv.rect(sx - 9, sy - 2, 18, 4, PAPER)


# ---- page layout ------------------------------------------------------------
def draw_page(cv):
    M = 24                      # outer margin
    WID = W - 2 * M             # 976

    # ===== masthead =====
    cv.text_centred("THE WORLD IN ONE DAY", W // 2, 34, 6, INK)
    cv.hline(M, 96, WID, INK, 3)
    cv.text_centred("SUNDAY 22 NOVEMBER 2026", W // 2, 110, 4, RED)
    cv.text_centred("SIX STORIES THAT DEFINED THE DAY - FROM THE MORNING PAPERS",
                    W // 2, 140, 2, GREY)
    cv.hline(M, 166, WID, INK, 3)

    # ===== six story panels, 3 x 2 grid =====
    gy, gh, gw = 182, 330, (WID - 32) // 3
    panels = [
        ("GULF ON EDGE", RED,
         "IRAN SAYS IT DOWNED TWO US DRONES OVER THE STRAIT OF HORMUZ, AS "
         "TANKERS ARE HIT OFF OMAN AND BAHRAIN PROBES A PATRIOT CRASH.",
         pic_gulf),
        ("SHENZHEN SUMMIT", BLUE,
         "TRUMP, XI AND PUTIN MEET AT THE APEC SUMMIT. TRUMP CALLS THE "
         "TALKS MOMENTOUS; ZELENSKYY WARNS ON UKRAINE.",
         pic_summit),
        ("COP31 NEARS A DEAL", GREEN,
         "CLIMATE TALKS IN ANTALYA CLOSE TO A FINAL PACT AFTER A ROW OVER "
         "FOSSIL FUELS PUSHES THE SUMMIT INTO OVERTIME.",
         pic_cop),
        ("BALTIC BLAZE", ORANGE,
         "DRONES HIT A RUSSIAN CARGO SHIP IN THE BALTIC SEA. THE VESSEL "
         "CATCHES FIRE; FINLAND TIGHTENS SECURITY.",
         pic_baltic),
        ("BOAT TRAGEDY IN NIGERIA", NAVY,
         "24 PEOPLE DIE WHEN A BOAT CAPSIZES ON ITS WAY TO A FUNERAL. "
         "RESCUERS SEARCH THE RIVER FOR THE MISSING.",
         pic_nigeria),
        ("ESTONIA SHUTS BORDER", RED,
         "TALLINN WILL CLOSE ITS FRONTIER WITH RUSSIA. MOSCOW DECRIES A "
         "NEW IRON CURTAIN AS TENSIONS RISE IN EUROPE.",
         pic_estonia),
    ]
    for i, (head, col, body, pic) in enumerate(panels):
        px = M + (i % 3) * (gw + 16)
        py = gy + (i // 3) * (gh + 16)
        cv.border(px, py, gw, gh, INK, 2)
        pic(cv, px + 10, py + 10, gw - 20, 140)
        tx = px + 12
        y = py + 162
        for line in wrap_text(head, gw - 24, 3):
            cv.text(line, tx, y, 3, col)
            y += 27
        cv.hline(tx, y + 2, gw - 24, INK, 2)
        cv.para(body, tx, y + 12, gw - 24, 2, INK)

    # ===== footer ticker =====
    ty = 874
    cv.rect(M, ty, WID, 98, NAVY)
    cv.text("ALSO TODAY", M + 14, ty + 12, 3, GOLD)
    cv.para("MEXICO ARRESTS CARTEL CHIEF EL CHAPO ISIDRO; 11 KILLED IN "
            "SINALOA * BOLSONARO IN INTENSIVE CARE * MODI OPENS THE "
            "NITISH SETU BRIDGE IN BIHAR * INDIA FACE NEW ZEALAND IN THE "
            "WELLINGTON TEST * CYCLONE AKVAN CANCELS FLIGHTS IN RANCHI",
            M + 14, ty + 40, WID - 28, 2, (235, 238, 242), leading=16)

    cv.text_centred("DRAWN FROM THE DAY'S REPORTING - SUNDAY 22 NOVEMBER 2026",
                    W // 2, 990, 1, GREY)


# ---- PNG writer ---------------------------------------------------------------
def chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    c += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return c


def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(outdir, exist_ok=True)
    cv = Canvas(W, H, PAPER)
    draw_page(cv)
    path = os.path.join(outdir, "entry.png")
    size = write_png(cv, path)
    print(f"wrote {path}: {W}x{H}, {size} bytes")


if __name__ == "__main__":
    main()
