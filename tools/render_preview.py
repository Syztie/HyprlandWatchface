#!/usr/bin/env python3
"""Approximate offline renderer for the subset of Watch Face Format used here.

This is a development aid, not a replacement for a screenshot from the watch.
It renders res/raw/watchface.xml with sample data so layout, themes and the
ambient variant can be checked without a device.

Text placement follows the WFF rule that a PartText centres its line box
(ascent + descent) vertically inside its bounds.

Usage:
  render_preview.py [--ambient] [--theme N] [--scale S] [--set KEY=VALUE ...]
                    [--watchface PATH] -o out.png
"""
import argparse
import datetime
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wff_expr import evaluate, format_template  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "app", "src", "main", "res")
DEFAULT_WATCHFACE = os.path.join(RES, "raw", "watchface.xml")


def parse_color(value, ctx):
    value = value.strip()
    if value.startswith("["):
        value = str(ctx.lookup(value[1:-1]))
    value = value.lstrip("#")
    if len(value) == 6:
        value = "ff" + value
    a, r, g, b = (int(value[i:i + 2], 16) for i in range(0, 8, 2))
    return (r, g, b, a)


class Context:
    """Sample data for sources, complications and configurations."""

    def __init__(self, now, sources, config, ambient):
        self.now = now
        self.sources = dict(sources)
        # Weather sample data is 30 minutes old unless a test says otherwise.
        self.sources.setdefault("WEATHER.LAST_UPDATED", (now.timestamp() - 1800) * 1000)
        self.config = config
        self.ambient = ambient

    def lookup(self, name):
        if name in self.sources:
            return self.sources[name]
        if name.startswith("COMPLICATION."):
            return None
        if name.startswith("CONFIGURATION."):
            parts = name.split(".")
            option = self.config.get(parts[1])
            if option is None:
                raise KeyError(name)
            if isinstance(option, list):
                return option[int(parts[2])] if len(parts) > 2 else option[0]
            return option
        value = time_source(name, self.now)
        if value is None:
            raise KeyError(name)
        return value


def time_source(name, now):
    dow = (now.isoweekday() % 7) + 1  # WFF: 1 = Sunday ... 7 = Saturday
    table = {
        "DAY": now.day, "DAY_Z": f"{now.day:02d}",
        "MONTH": now.month, "MONTH_Z": f"{now.month:02d}",
        "YEAR": now.year, "DAY_OF_YEAR": now.timetuple().tm_yday,
        "DAY_OF_WEEK": dow, "HOUR_0_23": now.hour, "HOUR_0_23_Z": f"{now.hour:02d}",
        "MINUTE": now.minute, "MINUTE_Z": f"{now.minute:02d}",
        "SECOND": now.second, "SECOND_Z": f"{now.second:02d}",
        "WEEK_IN_YEAR": (now.timetuple().tm_yday - 1) // 7 + 1,
        "UTC_TIMESTAMP": now.timestamp() * 1000,
    }
    return table.get(name)


class Renderer:
    def __init__(self, ctx, scale):
        self.ctx = ctx
        self.s = scale
        self.fonts = {}

    def font(self, family, size):
        key = (family, size)
        if key not in self.fonts:
            path = os.path.join(RES, "font", family + ".ttf")
            self.fonts[key] = ImageFont.truetype(path, round(size * self.s))
        return self.fonts[key]

    def render(self, root):
        w, h = int(root.get("width")), int(root.get("height"))
        self.img = Image.new("RGBA", (w * self.s, h * self.s), (0, 0, 0, 255))
        scene = root.find("Scene")
        bg = self.variant_attr(scene, "backgroundColor", scene.get("backgroundColor", "#ff000000"))
        self.img.paste(Image.new("RGBA", self.img.size, parse_color(bg, self.ctx)))
        self.children(scene, 0, 0, 1.0)
        mask = Image.new("L", self.img.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, w * self.s - 1, h * self.s - 1), fill=255)
        out = Image.new("RGBA", self.img.size, (0, 0, 0, 255))
        out.paste(self.img, (0, 0), mask)
        return out.resize((w, h), Image.LANCZOS) if self.s > 1 else out

    def variant_attr(self, el, attr, default):
        if self.ctx.ambient:
            for v in el.findall("Variant"):
                if v.get("mode") == "AMBIENT" and v.get("target") == attr:
                    return v.get("value")
        return default

    def attr(self, el, name, default=None):
        """Attribute value after Transform (expression) and ambient Variant."""
        value = el.get(name, default)
        for t in el.findall("Transform"):
            if t.get("target") == name:
                value = evaluate(t.get("value"), self.ctx)
        return self.variant_attr(el, name, value)

    def pos(self, el, ox, oy):
        return ox + int(float(self.attr(el, "x", 0))), oy + int(float(self.attr(el, "y", 0)))

    def alpha_of(self, el):
        return max(0.0, min(1.0, float(self.attr(el, "alpha", "255")) / 255.0))

    def children(self, parent, ox, oy, alpha):
        for el in parent:
            tag = el.tag
            if tag == "Group":
                a = alpha * self.alpha_of(el)
                if a > 0:
                    self.children(el, *self.pos(el, ox, oy), a)
            elif tag == "Condition":
                self.condition(el, ox, oy, alpha)
            elif tag == "PartDraw":
                a = alpha * self.alpha_of(el)
                if a > 0:
                    self.part_draw(el, *self.pos(el, ox, oy), a)
            elif tag == "PartText":
                a = alpha * self.alpha_of(el)
                if a > 0:
                    self.part_text(el, *self.pos(el, ox, oy), a)
            elif tag == "ComplicationSlot":
                self.complication(el, ox, oy, alpha)
            elif tag == "DigitalClock":
                a = alpha * self.alpha_of(el)
                if a > 0:
                    self.digital_clock(el, *self.pos(el, ox, oy), a)

    def condition(self, el, ox, oy, alpha):
        exprs = {e.get("name"): (e.text or "").strip()
                 for e in el.find("Expressions").findall("Expression")}
        for comp in el.findall("Compare"):
            if evaluate(exprs[comp.get("expression")], self.ctx):
                self.children(comp, ox, oy, alpha)
                return
        default = el.find("Default")
        if default is not None:
            self.children(default, ox, oy, alpha)

    def complication(self, el, ox, oy, alpha):
        slot_id = el.get("slotId")
        data = self.ctx.sources.get(f"__slot{slot_id}")
        kind = data["type"] if data else "EMPTY"
        for comp in el.findall("Complication"):
            if comp.get("type") == kind:
                saved = dict(self.ctx.sources)
                for k, v in (data or {}).items():
                    if k != "type":
                        self.ctx.sources["COMPLICATION." + k] = v
                self.children(comp, ox + int(el.get("x")), oy + int(el.get("y")), alpha)
                self.ctx.sources = saved
                return

    # Drawing -------------------------------------------------------------

    def layer(self):
        return Image.new("RGBA", self.img.size, (0, 0, 0, 0))

    def composite(self, layer, alpha):
        if alpha < 1:
            r, g, b, a = layer.split()
            a = a.point(lambda p: int(p * alpha))
            layer = Image.merge("RGBA", (r, g, b, a))
        self.img.alpha_composite(layer)

    def part_draw(self, el, ox, oy, alpha):
        s = self.s
        layer = self.layer()
        d = ImageDraw.Draw(layer)
        for shape in el:
            if shape.tag not in ("Rectangle", "RoundRectangle", "Ellipse"):
                continue
            x = (ox + float(shape.get("x"))) * s
            y = (oy + float(shape.get("y"))) * s
            w = float(shape.get("width")) * s
            h = float(shape.get("height")) * s
            r = float(shape.get("cornerRadiusX", 0)) * s
            fill = shape.find("Fill")
            stroke = shape.find("Stroke")
            if fill is not None:
                self.shape(d, shape.tag, (x, y, x + w, y + h), r, fill=parse_color(fill.get("color"), self.ctx))
            if stroke is not None:
                t = float(stroke.get("thickness")) * s
                # Strokes are centred on the outline, as on Android.
                box = (x - t / 2, y - t / 2, x + w + t / 2, y + h + t / 2)
                self.shape(d, shape.tag, box, r + t / 2, outline=parse_color(stroke.get("color"), self.ctx),
                           width=max(1, round(t)))
        self.composite(layer, alpha)

    @staticmethod
    def shape(d, tag, box, r, **kw):
        if tag == "Ellipse":
            d.ellipse(box, **kw)
        elif tag == "RoundRectangle":
            d.rounded_rectangle(box, radius=r, **kw)
        else:
            d.rectangle(box, **kw)

    def text_of(self, font_el):
        lower = font_el.find("Lower")
        if lower is not None:
            return self.text_of(lower).lower()
        tmpl = font_el.find("Template")
        if tmpl is None:
            return font_el.text or ""
        params = [p.get("expression") for p in tmpl.findall("Parameter")]
        # Template text may be split around Parameter children (CDATA, tails).
        text = (tmpl.text or "") + "".join((p.tail or "") for p in tmpl.findall("Parameter"))
        return format_template(text, [evaluate(p, self.ctx) for p in params])

    def part_text(self, el, ox, oy, alpha, text=None, font_el=None, align=None):
        text_el = el.find("Text")
        if font_el is None:
            font_el = text_el.find("Font")
            text = self.text_of(font_el)
            align = text_el.get("align", "CENTER")
            if text_el.get("ellipsis") == "TRUE":
                font = self.font(font_el.get("family"), float(font_el.get("size")))
                limit = int(el.get("width")) * self.s
                while text and font.getlength(text) > limit:
                    text = text[:-2] + "…"
        self.draw_text(text, font_el, align, ox, oy, int(el.get("width")), int(el.get("height")), alpha)

    def draw_text(self, text, font_el, align, x, y, w, h, alpha):
        s = self.s
        size = float(font_el.get("size"))
        font = self.font(font_el.get("family"), size)
        color = parse_color(self.variant_attr(font_el, "color", font_el.get("color", "#ffffffff")), self.ctx)
        ascent, descent = font.getmetrics()
        width = font.getlength(text)
        if align == "START":
            tx = x * s
        elif align == "END":
            tx = (x + w) * s - width
        else:
            tx = (x + w / 2) * s - width / 2
        top = (y + h / 2) * s - (ascent + descent) / 2
        layer = self.layer()
        ImageDraw.Draw(layer).text((tx, top), text, font=font, fill=color)
        self.composite(layer, alpha)
        self.boxes.append((text, tx / s, top / s, width / s, (ascent + descent) / s))

    def digital_clock(self, el, ox, oy, alpha):
        for tt in el.findall("TimeText"):
            if self.alpha_of(tt) == 0:
                continue
            fmt = tt.get("format")
            now = self.ctx.now
            text = (fmt.replace("hh", f"{now.hour:02d}").replace("mm", f"{now.minute:02d}")
                    .replace("ss", f"{now.second:02d}"))
            font_el = tt.find("Font")
            self.draw_text(text, font_el, tt.get("align", "CENTER"), ox + int(tt.get("x")),
                           oy + int(tt.get("y")), int(tt.get("width")), int(tt.get("height")),
                           alpha * self.alpha_of(tt))


def load_config(root, theme):
    config = {}
    ucs = root.find("UserConfigurations")
    if ucs is None:
        return config
    for cc in ucs.findall("ColorConfiguration"):
        opts = cc.findall("ColorOption")
        chosen = opts[theme] if theme is not None else next(
            o for o in opts if o.get("id") == cc.get("defaultValue"))
        config[cc.get("id")] = chosen.get("colors").split()
    return config


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--watchface", default=DEFAULT_WATCHFACE)
    ap.add_argument("--ambient", action="store_true")
    ap.add_argument("--theme", type=int)
    ap.add_argument("--scale", type=int, default=4)
    ap.add_argument("--time", default="2026-10-05T14:32:07")
    ap.add_argument("--set", action="append", default=[], help="KEY=VALUE sample data")
    ap.add_argument("--boxes", help="write measured text boxes to this file")
    args = ap.parse_args()

    from sample_data import SAMPLE
    sources = dict(SAMPLE)
    for kv in args.set:
        k, v = kv.split("=", 1)
        sources[k] = None if v == "None" else (float(v) if re.fullmatch(r"-?\d+(\.\d+)?", v) else v)

    root = ET.parse(args.watchface).getroot()
    ctx = Context(datetime.datetime.fromisoformat(args.time), sources, load_config(root, args.theme), args.ambient)
    r = Renderer(ctx, args.scale)
    r.boxes = []
    img = r.render(root)
    img.convert("RGB").save(args.output)
    if args.boxes:
        with open(args.boxes, "w") as f:
            for b in r.boxes:
                f.write("%r\t%.1f\t%.1f\t%.1f\t%.1f\n" % b)


if __name__ == "__main__":
    main()
