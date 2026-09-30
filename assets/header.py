#!/usr/bin/env python3
"""Profile header art. Writes header-light.svg and header-dark.svg next to this file.

All lettering is converted to outlines with HarfBuzz, so the SVGs carry no
fonts, scripts, or remote resources. Needs `hb-vector` (brew install harfbuzz)
and the Monaspace Nerd Fonts (Xenon, Krypton, Radon) in ~/Library/Fonts.

Edit the words, colours, or positions below, then run: python3 assets/header.py
The figure numbers in the art must match the `fig.` labels in README.md.
"""
import math
import os
import random
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.expanduser("~/Library/Fonts/")
FACES = {
    "name": "MonaspiceXeNerdFont-Bold.otf",
    "label": "MonaspiceKrNerdFont-Medium.otf",
    "code": "MonaspiceKrNerdFont-Regular.otf",
    "hand": "MonaspiceRnNerdFont-Italic.otf",
}
THEMES = {
    "light": dict(paper="#F5EFE3", grid="#E8E0D1", ink="#211C16", ink2="#5B5246",
                  ink3="#6E6457", red="#B93B17", margin="#E4A58D", grain=0.28),
    "dark": dict(paper="#1D1A16", grid="#28241F", ink="#EFE8DB", ink2="#B7AD9C",
                 ink3="#968B7B", red="#FF7B50", margin="#5E3426", grain=0.22),
}
W, H = 1200, 340

_glyphs = {}


def glyph(face, ch):
    """Outline one character at 1000 units per em. Returns (id, path, advance)."""
    key = (face, ch)
    if key not in _glyphs:
        svg = subprocess.run(
            ["hb-vector", "--font-size=1000", "--margin=0", "--logical", "--precision=0",
             "--features=-calt", FONTS + FACES[face], ch],
            capture_output=True, text=True, check=True).stdout
        advance = float(re.search(r'viewBox="\S+ \S+ (\S+)', svg).group(1))
        _glyphs[key] = (f"{face[0]}{len(_glyphs)}", "".join(re.findall(r' d="([^"]+)"', svg)), advance)
    return _glyphs[key]


def text(face, s, x, y, size, fill, track=0.0, anchor="start"):
    """Outlined text with its baseline at (x, y); track adds em space per character."""
    uses, pos = [], 0.0
    for ch in s:
        gid, d, advance = glyph(face, ch)
        if d:
            uses.append(f'<use xlink:href="#{gid}" x="{pos:.0f}"/>')
        pos += advance + track * 1000
    width = (pos - track * 1000) * size / 1000
    x -= {"start": 0, "middle": width / 2, "end": width}[anchor]
    return (f'<g transform="translate({x:.1f} {y:.1f}) scale({size / 1000:.4f})" fill="{fill}">'
            + "".join(uses) + "</g>")


def width(face, s, size, track=0.0):
    return sum(glyph(face, ch)[2] + track * 1000 for ch in s) * size / 1000 - track * size


# Hand-drawn marks. A fixed seed keeps every build identical.
rng = random.Random(11)


def stroke(d, colour, w=2.4):
    return (f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="{w}" '
            'stroke-linecap="round" stroke-linejoin="round"/>')


def hand_line(x1, y1, x2, y2, j=1.2):
    """A slightly wobbly pen line."""
    dx, dy = x2 - x1, y2 - y1
    n = math.hypot(dx, dy) or 1
    px, py = -dy / n, dx / n
    a, b = rng.uniform(-j, j), rng.uniform(-j, j)
    return (f"M{x1:.1f},{y1:.1f}C{x1 + dx / 3 + px * a:.1f},{y1 + dy / 3 + py * a:.1f} "
            f"{x1 + 2 * dx / 3 + px * b:.1f},{y1 + 2 * dy / 3 + py * b:.1f} {x2:.1f},{y2:.1f}")


def hand_box(x, y, w, h, o=4):
    """A pen rectangle whose strokes overshoot at the corners."""
    def r():
        return rng.uniform(-1.5, 1.5)
    return (hand_line(x - o, y + r(), x + w + o, y + r()) + hand_line(x + w + r(), y - o, x + w + r(), y + h + o)
            + hand_line(x + w + o, y + h + r(), x - o, y + h + r()) + hand_line(x + r(), y + h + o, x + r(), y - o))


def squiggle(x1, x2, y, amp=2.6, half=7):
    d, x, up = f"M{x1:.1f},{y:.1f}", x1, True
    while x < x2:
        d += f"Q{x + half / 2:.1f},{y - amp if up else y + amp:.1f} {x + half:.1f},{y:.1f}"
        x, up = x + half, not up
    return d


def tick(x, y, s=1.0):
    return f"M{x:.1f},{y:.1f}l{4 * s:.1f},{5 * s:.1f}c{2 * s:.1f},{-5 * s:.1f} {5 * s:.1f},{-9 * s:.1f} {9 * s:.1f},{-12 * s:.1f}"


def arrow(x1, y1, cx, cy, x2, y2, head=8):
    """Quadratic curve from (x1, y1) to (x2, y2) with an open arrowhead at the end."""
    ang = math.atan2(y2 - cy, x2 - cx)
    h1 = (x2 - head * math.cos(ang - 0.45), y2 - head * math.sin(ang - 0.45))
    h2 = (x2 - head * math.cos(ang + 0.45), y2 - head * math.sin(ang + 0.45))
    return (f"M{x1:.1f},{y1:.1f}Q{cx:.1f},{cy:.1f} {x2:.1f},{y2:.1f}"
            f"M{h1[0]:.1f},{h1[1]:.1f}L{x2:.1f},{y2:.1f}L{h2[0]:.1f},{h2[1]:.1f}")


def tilt(svg, degrees, x, y):
    """Hand-placed notes sit slightly off the horizontal."""
    return f'<g transform="rotate({degrees} {x} {y})">{svg}</g>'


def compose(t):
    rng.seed(11)
    ink, pencil = [], []  # pencil: the red annotations, drawn last with a rough edge
    # Paper: faint grid, a margin rule, grain, and three punched holes (cut out by the mask).
    grid = "".join(f"M{x},0V{H}" for x in range(20, W, 20)) + "".join(f"M0,{y}H{W}" for y in range(20, H, 20))
    ink.append(f'<rect width="{W}" height="{H}" rx="10" fill="{t["paper"]}"/>')
    ink.append(f'<path d="{grid}" stroke="{t["grid"]}" stroke-width="1"/>')
    ink.append(f'<rect width="{W}" height="{H}" filter="url(#grain)"/>')
    ink.append(f'<path d="M78,0V{H}M82,0V{H}" stroke="{t["margin"]}" stroke-width="1.2"/>')

    # Identity.
    name, nx, ny, ns = "David Teren", 112, 168, 64
    ink.append(text("name", name, nx, ny, ns, t["ink"]))
    label = "TOOLS FOR RUBY, RAILS & AI-ASSISTED DEVELOPMENT"
    track = (width("name", name, ns) - width("label", label, 13)) / (len(label) - 1) / 13
    ink.append(text("label", label, nx + 2, ny + 32, 13, t["ink2"], track=track))
    ink.append(text("label", "NO. 01", W - 40, 44, 11, t["ink3"], track=0.2, anchor="end"))

    # Fig. 1: a comparison operator changed by a mutant that no test caught.
    cx, cy, cs = 620, 124, 40
    cw = width("code", "x", cs)
    gx = cx + 6 * cw
    ink.append(text("code", "total > limit", cx, cy, cs, t["ink"]))
    ink.append(text("label", "FIG. 1  EXAMPLE MUTANT", cx, cy + 34, 11, t["ink3"], track=0.12))
    pencil.append(stroke(hand_line(gx - 3, cy + 5, gx + cw + 4, cy - 30), t["red"], 3.4))
    pencil.append(tilt(text("hand", ">=", gx + cw / 2 + 4, cy - 52, 36, t["red"], anchor="middle"), -4, gx, cy - 52))
    pencil.append(stroke(arrow(872, 58, 848, 36, 818, 54), t["red"], 2))
    pencil.append(tilt(text("hand", "no test noticed", 880, 68, 22, t["red"]), -2.5, 880, 68))

    # Fig. 2: a review note on a method whose name hides a side effect.
    fx, fy, fs = 620, 226, 20
    fw = width("code", "x", fs)
    ink.append(text("code", "def fetch_user", fx, fy, fs, t["ink"]))
    ink.append(text("label", "FIG. 2  EXAMPLE REVIEW NOTE", fx, 310, 11, t["ink3"], track=0.12))
    pencil.append(stroke(squiggle(fx + 4 * fw, fx + 14 * fw, fy + 7), t["red"], 1.8))
    pencil.append(tilt(text("hand", "a fetch that writes?", fx, fy + 32, 18, t["red"]), -1.5, fx, fy + 32))

    # Fig. 3: roles by actions, with one permission bounded by a per-record rule.
    x0, y0, c = 884, 206, 24
    cells = ("".join(f"M{x0},{y0 + r * c}h{3 * c}" for r in range(4))
             + "".join(f"M{x0 + k * c},{y0}v{3 * c}" for k in range(4)))
    ink.append(f'<path d="{cells}" stroke="{t["ink2"]}" stroke-width="1.2" fill="none"/>')
    for col, row in [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2)]:
        ink.append(stroke(tick(x0 + col * c + 6, y0 + row * c + 12, 0.9), t["ink"], 2))
    ink.append(text("label", "FIG. 3  EXAMPLE RULE", x0, 310, 11, t["ink3"], track=0.12))
    pencil.append(stroke(hand_box(x0 + 2 * c - 3, y0 + c - 3, c + 6, c + 6), t["red"], 2.2))
    pencil.append(tilt(text("hand", "not the initiator", x0 + 3 * c + 20, y0 + c + 17, 18, t["red"]), -2, x0 + 3 * c + 20, y0 + c + 17))

    r, g, b = (int(t["ink"][i:i + 2], 16) / 255 for i in (1, 3, 5))
    holes = "".join(f'<circle cx="38" cy="{y}" r="10" fill="#000"/>' for y in (85, 170, 255))
    defs = "".join(f'<path id="{gid}" transform="scale(1 -1)" d="{d}"/>' for gid, d, _ in _glyphs.values() if d)
    filters = (
        '<filter id="grain" x="0" y="0" width="100%" height="100%">'
        '<feTurbulence type="fractalNoise" baseFrequency=".8" numOctaves="3" seed="8" stitchTiles="stitch"/>'
        f'<feColorMatrix values="0 0 0 0 {r:.2f} 0 0 0 0 {g:.2f} 0 0 0 0 {b:.2f} {t["grain"]} 0 0 0 {-t["grain"] / 2:.3f}"/></filter>'
        '<filter id="rough" x="-2%" y="-10%" width="104%" height="120%">'
        '<feTurbulence type="fractalNoise" baseFrequency=".7" numOctaves="2" seed="4"/>'
        '<feDisplacementMap in="SourceGraphic" scale="1.8" xChannelSelector="R" yChannelSelector="G"/></filter>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<defs>{defs}{filters}<mask id="m"><rect width="{W}" height="{H}" fill="#fff"/>{holes}</mask></defs>'
            f'<g mask="url(#m)">' + "".join(ink) + '<g filter="url(#rough)">' + "".join(pencil) + "</g></g></svg>\n")


def luminance(hex_colour):
    c = [int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


if __name__ == "__main__":
    for mode, t in THEMES.items():
        # Text in the art must meet WCAG contrast: 4.5:1 for small text, 3:1 for large.
        for key, minimum in (("ink", 4.5), ("ink2", 4.5), ("ink3", 4.5), ("red", 4.5)):
            ratio = contrast(t[key], t["paper"])
            assert ratio >= minimum, f"{mode} {key} contrast {ratio:.2f} < {minimum}"
        with open(os.path.join(HERE, f"header-{mode}.svg"), "w") as f:
            f.write(compose(t))
        print(f"header-{mode}.svg", os.path.getsize(os.path.join(HERE, f"header-{mode}.svg")), "bytes")
