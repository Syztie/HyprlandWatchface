#!/usr/bin/env python3
"""Checks the data expressions in res/raw/watchface.xml against known answers.

Renders the watch face offline for chosen dates and sample values and looks
at the resulting texts and positions. The ISO week is compared with Python's
isocalendar() for every day from 2000 to 2040.
"""
import datetime
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_preview import DEFAULT_WATCHFACE, Context, Renderer, load_config  # noqa: E402
from sample_data import SAMPLE  # noqa: E402
from wff_expr import evaluate  # noqa: E402

ROOT = ET.parse(DEFAULT_WATCHFACE).getroot()
failures = []


def ctx_for(when, **sources):
    data = dict(SAMPLE)
    data.update(sources)
    return Context(when, data, load_config(ROOT, None), False)


def texts(when, **sources):
    r = Renderer(ctx_for(when, **sources), 1)
    r.boxes = []
    r.render(ROOT)
    return [b[0] for b in r.boxes]


def named(tag, name):
    return next(e for e in ROOT.iter(tag) if e.get("name") == name)


def transform(el, target, ctx):
    t = next(t for t in el.findall("Transform") if t.get("target") == target)
    return evaluate(t.get("value"), ctx)


def expect(label, got, want):
    ok = got == want
    if not ok:
        failures.append(label)
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}: {got!r}" + ("" if ok else f" (expected {want!r})"))


def d(s):
    return datetime.datetime.fromisoformat(s)


def main():
    print("Weekday strip (Monday first)")
    box = named("PartDraw", "weekday_today_box")
    letter = named("PartText", "weekday_today")
    param = letter.find(".//Parameter").get("expression")
    for day, x, ch in [("2026-10-05", 100, "m"), ("2026-10-06", 118, "d"), ("2026-10-09", 172, "f"),
                       ("2026-10-10", 190, "s"), ("2026-10-11", 208, "s")]:
        ctx = ctx_for(d(day + "T12:00"))
        expect(f"{day} box x", transform(box, "x", ctx), x)
        expect(f"{day} letter x", transform(letter, "x", ctx), x)
        expect(f"{day} letter", evaluate(param, ctx), ch)

    print("Date and ISO week")
    expect("date 05.10.2026", "05.10" in texts(d("2026-10-05T14:32:07")), True)
    expect("date 01.02.2027", "01.02" in texts(d("2027-02-01T08:00")), True)
    for day, kw in [("2026-10-05", "kw41"), ("2027-01-01", "kw53"), ("2027-01-04", "kw1")]:
        expect(f"{day} {kw}", kw in texts(d(day + "T12:00")), True)
    week = named("PartText", "iso_week").find(".//Parameter").get("expression")
    day, bad, n = d("2000-01-01T12:00"), [], 0
    while day.year <= 2040:
        n += 1
        if evaluate(week, ctx_for(day)) != str(day.isocalendar()[1]):
            bad.append(day.date())
        day += datetime.timedelta(days=1)
    expect(f"ISO week for all {n} days 2000-2040, mismatches", bad[:5], [])

    print("Clock")
    t = texts(d("2026-10-05T09:05:03"))
    expect("time 09:05", "09:05" in t, True)
    expect("seconds :03", ":03" in t, True)
    expect("time 23:59", "23:59" in texts(d("2026-10-05T23:59:00")), True)

    print("Steps")
    for steps, want in [(0, "0"), (999, "999"), (1000, "1.0k"), (6214, "6.2k"), (6299, "6.2k"),
                        (12345, "12.3k"), (100000, "100.0k")]:
        expect(f"{steps} steps", want in texts(d("2026-10-05T12:00"), STEP_COUNT=steps), True)

    print("Watch battery")
    for pct in (5, 78, 100):
        expect(f"{pct}%", f"{pct}%" in texts(d("2026-10-05T12:00"), BATTERY_PERCENT=pct), True)

    print("Notifications")
    group = named("Group", "notifications")
    dot = named("PartDraw", "notification_dot")
    for count, alpha, x in [(0, 0, None), (3, 255, 372), (12, 255, 361), (150, 255, 351)]:
        ctx = ctx_for(d("2026-10-05T12:00"), UNREAD_NOTIFICATION_COUNT=count)
        expect(f"{count} unread: alpha", transform(group, "alpha", ctx), alpha)
        if x is not None:
            expect(f"{count} unread: dot x", transform(dot, "x", ctx), x)
            expect(f"{count} unread: text", str(count) in texts(d("2026-10-05T12:00"),
                                                                 UNREAD_NOTIFICATION_COUNT=count), True)

    print("Weather")
    cond = next(c for c in ROOT.iter("Condition")
                if any(e.get("name") == "weather_missing" for e in c.iter("Expression")))
    exprs = {e.get("name"): e.text.strip() for e in cond.iter("Expression")}
    now = d("2026-10-05T14:32:07")
    ms = now.timestamp() * 1000
    for label, src, name, want in [
        ("available", {}, "weather_missing", False),
        ("not available", {"WEATHER.IS_AVAILABLE": False}, "weather_missing", True),
        ("error", {"WEATHER.IS_ERROR": True}, "weather_missing", True),
        ("updated 30 min ago", {"WEATHER.LAST_UPDATED": ms - 1800e3}, "weather_stale", False),
        ("updated 4 h ago", {"WEATHER.LAST_UPDATED": ms - 4 * 3600e3}, "weather_stale", True),
    ]:
        expect(f"{label}: {name}", bool(evaluate(exprs[name], ctx_for(now, **src))), want)
    for label, src, want in [
        ("14 C", {}, "14°"),
        ("57.2 F -> 14 C", {"WEATHER.TEMPERATURE_UNIT": 2, "WEATHER.TEMPERATURE": 57.2}, "14°"),
        ("-3.4 C", {"WEATHER.TEMPERATURE": -3.4}, "-3°"),
        ("rain 40", {}, "40%"),
        ("rain 0", {"WEATHER.CHANCE_OF_PRECIPITATION": 0}, "0%"),
    ]:
        expect(f"weather {label}", want in texts(now, **src), True)
    uv = named("PartText", "uv_value").find(".//Parameter").get("expression")
    for label, src, want in [
        ("daily 3, now 2", {}, "3"),
        ("daily 3, now 5", {"WEATHER.UV_INDEX": 5}, "5"),
        ("no daily, now 4", {"WEATHER.DAYS.0.IS_AVAILABLE": False, "WEATHER.UV_INDEX": 4}, "4"),
    ]:
        expect(f"uv max {label}", evaluate(uv, ctx_for(now, **src)), want)

    print("Complications")
    for label, slot, want in [
        ("title + text", {"type": "LONG_TEXT", "TITLE": "15:00", "TEXT": "Zahnarzt"}, "> 15:00 zahnarzt"),
        ("text only", {"type": "LONG_TEXT", "TEXT": "Team Meeting"}, "> team meeting"),
        ("long text", {"type": "LONG_TEXT", "TITLE": "15:00", "TEXT": "Quartalsplanung mit allen"},
         "> 15:00 quartalsplanu…"),
        ("empty", None, "> frei"),
        ("colon in title", {"type": "LONG_TEXT", "TITLE": "14:00:", "TEXT": "Abgesagt: Kino"},
         "> 14:00 abgesagt: kino"),
        ("colon in text", {"type": "LONG_TEXT", "TEXT": "14:00: Abgesagt: Kino"}, "> 14:00 abgesagt: kino"),
        ("colon, one-digit hour", {"type": "LONG_TEXT", "TEXT": "9:30: Arzt"}, "> 9:30 arzt"),
        ("no time", {"type": "LONG_TEXT", "TEXT": "Urlaub"}, "> urlaub"),
        ("title with colon, no time", {"type": "LONG_TEXT", "TEXT": "Abgesagt: Kino"}, "> abgesagt: kino"),
        ("other source with colon", {"type": "SHORT_TEXT", "TEXT": "Projekt: Planung"}, "> projekt: planung"),
        ("title word with colon", {"type": "LONG_TEXT", "TITLE": "Hinweis:", "TEXT": "Kino"}, "> hinweis: kino"),
        ("relative time in text", {"type": "LONG_TEXT", "TEXT": "27 min.: Test"}, "> 27 min. test"),
        ("relative time, empty title", {"type": "LONG_TEXT", "TITLE": "", "TEXT": "27 min.: Test"},
         "> 27 min. test"),
        ("relative time in title", {"type": "LONG_TEXT", "TITLE": "27 min.:", "TEXT": "Test"}, "> 27 min. test"),
        ("hours and minutes", {"type": "LONG_TEXT", "TEXT": "1 Std. 5 Min.: Arzt"}, "> 1 std. 5 min. arzt"),
        ("second colon kept", {"type": "LONG_TEXT", "TEXT": "14:00: Abgesagt: Kino"}, "> 14:00 abgesagt: kino"),
        ("very short text", {"type": "SHORT_TEXT", "TEXT": "a"}, "> a"),
    ]:
        expect(f"event {label}", want in texts(now, __slot1=slot), True)
    for label, slot, want in [
        ("ranged 64", {"type": "RANGED_VALUE", "RANGED_VALUE_VALUE": 64.4}, "64%"),
        ("short text", {"type": "SHORT_TEXT", "TEXT": "71%"}, "71%"),
        ("empty", None, "--"),
    ]:
        expect(f"phone battery {label}", want in texts(now, __slot0=slot), True)

    print(f"\n{len(failures)} failed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
