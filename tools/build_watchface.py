#!/usr/bin/env python3
"""Generates res/raw/watchface.xml and res/values/theme_strings.xml.

A ColorOption in the Watch Face Format holds at most five colors, but the
design uses ten color roles. So the theme is a ListConfiguration instead: each
<ThemeSwitch> block of watchface/watchface.template.xml is copied once per
theme from watchface/themes.json, with @{role} replaced by that theme's color.

Usage: build_watchface.py [--check]
  --check  exit 1 if the generated file is out of date instead of writing it
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "watchface", "watchface.template.xml")
THEMES = os.path.join(ROOT, "watchface", "themes.json")
RES = os.path.join(ROOT, "app", "src", "main", "res")
OUTPUT = os.path.join(RES, "raw", "watchface.xml")
STRINGS = os.path.join(RES, "values", "theme_strings.xml")

SWITCH = re.compile(r'(?P<indent>[ \t]*)<ThemeSwitch name="(?P<name>\w+)" width="(?P<w>\d+)" '
                    r'height="(?P<h>\d+)">\n(?P<body>[\s\S]*?)\n[ \t]*</ThemeSwitch>')
COMMENT = re.compile(r"[ \t]*<!--[\s\S]*?-->\n?")
ROLE = re.compile(r"@\{(\w+)\}")
MACRO = re.compile(r"@@(\w+)@@")

Q = "&quot;"
TITLE = "[COMPLICATION.TITLE]"
TEXT = "[COMPLICATION.TEXT]"
COLON_SEARCH = 16  # the time part ("14:00", "27 min.", "1 Std. 5 Min.") ends within 16 chars


def _sub(value, start, end):
    """subText with both indices clamped, so short strings never fail."""
    length = f"textLength({value})"
    return f"subText({value}, clamp({start}, 0, {length}), clamp({end}, 0, {length}))"


def _first_colon(value, found, missing):
    """Nested ternary over the first ": " at index 1..COLON_SEARCH (WFF has no indexOf)."""
    expr = missing
    for i in range(COLON_SEARCH, 0, -1):
        expr = f"({_sub(value, i, i + 2)} == {Q}: {Q} ? {found(i)} : {expr})"
    return expr


def _starts_with_digit(value):
    """True when the first character is 0-9: only then is the head a time."""
    first = _sub(value, 0, 1)
    return "(" + " || ".join(f"{first} == {Q}{d}{Q}" for d in "0123456789") + ")"


def macros():
    """Expressions too long to maintain by hand, XML-escaped for attributes."""
    length = f"textLength({TEXT})"
    tlen = f"textLength({TITLE})"
    return {
        # A title counts only when it is present and not empty.
        "event_has_title": f"{TITLE} != null &amp;&amp; {tlen} &gt; 0",
        # Title without a trailing colon ("14:00:" -> "14:00"), but only when
        # it starts with a digit, so a title like "Hinweis:" stays as it is.
        "event_title": (f"({_starts_with_digit(TITLE)} &amp;&amp; {_sub(TITLE, f'{tlen} - 1', tlen)} == {Q}:{Q}"
                        f" ? {_sub(TITLE, 0, f'{tlen} - 1')} : {TITLE})"),
        # Text split at its first ": " when it starts with a time ("14:00: x",
        # "27 min.: x"); head is the time, tail keeps the space. Any other text
        # ("Abgesagt: Kino") is left untouched: head is the text, tail empty.
        "event_head": (f"({_starts_with_digit(TEXT)} ? "
                       f"{_first_colon(TEXT, lambda i: _sub(TEXT, 0, i), TEXT)} : {TEXT})"),
        "event_tail": (f"({_starts_with_digit(TEXT)} ? "
                       f"{_first_colon(TEXT, lambda i: _sub(TEXT, i + 1, length), f'{Q}{Q}')} : {Q}{Q})"),
    }


def shift(text, spaces):
    pad = " " * spaces
    return "\n".join(pad + line if line.strip() else line for line in text.split("\n"))


def colorize(body, roles, colors):
    def repl(m):
        if m.group(1) not in roles:
            raise SystemExit(f"unknown color role @{{{m.group(1)}}}")
        return "#ff" + colors[roles.index(m.group(1))].lstrip("#").lower()
    return ROLE.sub(repl, body)


def expand(m, cfg):
    ind, name, w, h = m.group("indent"), m.group("name"), m.group("w"), m.group("h")
    body = COMMENT.sub("", m.group("body"))
    options = []
    for i, theme in enumerate(cfg["themes"]):
        inner = shift(colorize(body, cfg["roles"], theme["colors"]), 6)
        options.append(f'{ind}    <ListOption id="{i}">\n'
                       f'{ind}      <Group name="{name}_{theme["id"]}" x="0" y="0" width="{w}" height="{h}">\n'
                       f'{inner}\n'
                       f'{ind}      </Group>\n'
                       f'{ind}    </ListOption>')
    return (f'{ind}<Group name="{name}" x="0" y="0" width="{w}" height="{h}">\n'
            f'{ind}  <ListConfiguration id="theme">\n' + "\n".join(options) + "\n"
            f'{ind}  </ListConfiguration>\n'
            f'{ind}</Group>')


def configuration(cfg):
    default = next(i for i, t in enumerate(cfg["themes"]) if t["id"] == cfg["default"])
    opts = "\n".join(f'      <ListOption id="{i}" displayName="theme_{t["id"]}" icon="theme_{t["id"]}" />'
                     for i, t in enumerate(cfg["themes"]))
    flavors = "\n".join(f'      <Flavor id="{t["id"]}" displayName="theme_{t["id"]}" icon="theme_{t["id"]}">\n'
                        f'        <Configuration id="theme" optionId="{i}" />\n'
                        f'      </Flavor>' for i, t in enumerate(cfg["themes"]))
    return (f'  <UserConfigurations>\n'
            f'    <ListConfiguration id="theme" displayName="theme_label" defaultValue="{default}">\n'
            f'{opts}\n'
            f'    </ListConfiguration>\n'
            f'    <Flavors defaultValue="{cfg["default"]}">\n'
            f'{flavors}\n'
            f'    </Flavors>\n'
            f'  </UserConfigurations>')


def theme_strings(cfg):
    names = "\n".join(f'    <string name="theme_{t["id"]}">{t["name"]}</string>' for t in cfg["themes"])
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            "<!-- GENERATED by tools/build_watchface.py from watchface/themes.json. -->\n"
            f"<resources>\n{names}\n</resources>\n")


def check_themes(cfg):
    for t in cfg["themes"]:
        if len(t["colors"]) != len(cfg["roles"]):
            raise SystemExit(f"theme {t['id']}: {len(t['colors'])} colors, expected {len(cfg['roles'])}")
        icon = os.path.join(RES, "drawable", f"theme_{t['id']}.png")
        if not os.path.exists(icon):
            raise SystemExit(f"theme {t['id']}: icon {os.path.relpath(icon, ROOT)} missing, run 'make icons'")


def generate():
    cfg = json.load(open(THEMES))
    check_themes(cfg)
    src = open(TEMPLATE).read()
    header_end = src.index("-->") + 3
    head = ('<?xml version="1.0" encoding="utf-8"?>\n'
            "<!-- GENERATED by tools/build_watchface.py from watchface/watchface.template.xml\n"
            "     and watchface/themes.json. Do not edit by hand: run \"make generate\". -->")
    body = src[header_end:]
    body = body.replace("  <!-- @THEME_CONFIGURATION@ -->", configuration(cfg))
    defs = macros()
    body = MACRO.sub(lambda m: defs[m.group(1)], body)
    body = SWITCH.sub(lambda m: expand(m, cfg), body)
    if "ThemeSwitch" in body or ROLE.search(body) or MACRO.search(body):
        raise SystemExit("unexpanded ThemeSwitch or color role left in output")
    return {OUTPUT: head + body, STRINGS: theme_strings(cfg)}


def main():
    outputs = generate()
    if "--check" in sys.argv:
        stale = [p for p, text in outputs.items()
                 if not os.path.exists(p) or open(p).read() != text]
        for p in stale:
            print(f"{os.path.relpath(p, ROOT)} is out of date: run 'make generate'")
        if stale:
            sys.exit(1)
        print("generated files are up to date")
        return
    for path, text in outputs.items():
        with open(path, "w") as f:
            f.write(text)
        print(f"wrote {os.path.relpath(path, ROOT)} ({text.count(chr(10)) + 1} lines)")


if __name__ == "__main__":
    main()
