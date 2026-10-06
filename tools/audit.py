#!/usr/bin/env python3
"""Layout and design audit for res/raw/watchface.xml.

Checks the rules from the design handover that the XSD validator cannot see:
  - every tile corner stays at least 6 units inside the round display
  - rendered text stays on the display and inside its tile
  - only JetBrains Mono, font size >= 15, all text lower case
  - only colors from the theme palette
  - ambient mode lights less than 15 % of the display
Exits non-zero if any check fails.
"""
import datetime
import json
import math
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_preview import DEFAULT_WATCHFACE, Context, Renderer, load_config  # noqa: E402
from sample_data import SAMPLE  # noqa: E402

CENTER, RADIUS, EDGE_MARGIN = 225.0, 225.0, 6.0
AMBIENT_LIT_LIMIT = 0.15
FONTS = {"jetbrains_mono_regular", "jetbrains_mono_medium"}
THEMES = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                   "watchface", "themes.json")))
PALETTE = {c.lstrip("#").lower() for t in THEMES["themes"] for c in t["colors"]}

failures = []
VERBOSE = "-v" in sys.argv


def check(ok, msg):
    if VERBOSE or not ok:
        print(("  ok    " if ok else "  FAIL  ") + msg)
    if not ok:
        failures.append(msg)
    check.count += 1


check.count = 0


def tiles(root):
    """Rounded rectangles drawn with a stroke only: the tile frames."""
    for pd in root.iter("PartDraw"):
        ox, oy = int(pd.get("x")), int(pd.get("y"))
        for rr in pd.findall("RoundRectangle"):
            big = float(rr.get("width")) > 30
            if big and rr.find("Stroke") is not None and rr.find("Fill") is None:
                x, y = ox + float(rr.get("x")), oy + float(rr.get("y"))
                yield pd.get("name"), (x, y, x + float(rr.get("width")), y + float(rr.get("height")))


def dist(x, y):
    return math.hypot(x - CENTER, y - CENTER)


def render(root, ambient, theme=None):
    ctx = Context(datetime.datetime(2026, 10, 5, 14, 32, 7), dict(SAMPLE), load_config(root, theme), ambient)
    r = Renderer(ctx, 2)
    r.boxes = []
    img = r.render(root)
    return img, r.boxes


def main():
    args = [a for a in sys.argv[1:] if a != "-v"]
    path = args[0] if args else DEFAULT_WATCHFACE
    root = ET.parse(path).getroot()

    print("Tiles inside the display (corner >= 6 units from the edge)")
    frames = list(tiles(root))
    for name, (x0, y0, x1, y1) in frames:
        worst = max(dist(x, y) for x in (x0, x1) for y in (y0, y1))
        check(worst <= RADIUS - EDGE_MARGIN, f"{name} {x0:g},{y0:g} {x1 - x0:g}x{y1 - y0:g}: "
              f"corner margin {RADIUS - worst:.1f}")

    print("Fonts and text")
    for font in root.iter("Font"):
        check(font.get("family") in FONTS, f"font family {font.get('family')}")
        check(float(font.get("size")) >= 15, f"font size {font.get('size')}")
    img, boxes = render(root, ambient=False)
    for text, x, y, w, h in boxes:
        check(text == text.lower(), f"lower case: {text!r}")
        corners = [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]
        margin = RADIUS - max(dist(cx, cy) for cx, cy in corners)
        check(margin >= 0, f"text {text!r} on display (margin {margin:.1f})")
        cx, cy = x + w / 2, y + h / 2
        for name, (x0, y0, x1, y1) in frames:
            if x0 <= cx <= x1 and y0 <= cy <= y1:
                check(x >= x0 + 2 and x + w <= x1 - 2, f"text {text!r} fits horizontally in {name}")

    print("Colors")
    used = set()
    for el in root.iter():
        for attr in ("color", "backgroundColor", "value", "colors"):
            v = el.get(attr)
            if v and v.startswith("#"):
                for c in v.split():
                    used.add(c.lstrip("#")[-6:].lower())
    allowed = PALETTE | {"000000"}
    check(used <= allowed, f"colors from the palette ({len(used)} used, extra: {sorted(used - allowed)})")

    print("Ambient mode")
    if not any(v.get("mode") == "AMBIENT" for v in root.iter("Variant")):
        print("  WARN  no ambient variants yet (milestone 6)")
        return finish()
    for i, theme in enumerate(THEMES["themes"]):
        name = theme["id"]
        img, _ = render(root, ambient=False, theme=i)
        bg = img.convert("RGB").getpixel((225, 30))
        want = tuple(int(theme["colors"][0].lstrip("#")[k:k + 2], 16) for k in (0, 2, 4))
        check(max(abs(a - b) for a, b in zip(bg, want)) <= 2, f"{name}: active background {bg}")
        amb, texts = render(root, ambient=True, theme=i)
        shown = sorted(t[0] for t in texts)
        check(shown == sorted(["14:32", "05.10", "kw41"]), f"{name}: ambient shows only time, date, week {shown}")
        gray = amb.convert("L")
        w, h = gray.size
        px = gray.load()
        inside = lit = 0
        for yy in range(0, h):
            for xx in range(0, w):
                if math.hypot(xx + 0.5 - w / 2, yy + 0.5 - h / 2) <= w / 2:
                    inside += 1
                    lit += px[xx, yy] > 10
        ratio = lit / inside
        check(ratio < AMBIENT_LIT_LIMIT, f"{name}: lit pixels in ambient {ratio:.1%} (limit {AMBIENT_LIT_LIMIT:.0%})")
        check(amb.convert("RGB").getpixel((30, 225)) == (0, 0, 0), f"{name}: ambient background black")
        print(f"  info  {name}: {ratio:.1%} lit in ambient")

    finish()


def finish():
    print(f"\n{check.count} checks, {len(failures)} failed")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
