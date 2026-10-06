"""Sample values matching docs/reference.svg, used by the preview renderer."""

SAMPLE = {
    "UNREAD_NOTIFICATION_COUNT": 3,
    "STEP_COUNT": 6214,
    "BATTERY_PERCENT": 78,
    "WEATHER.IS_AVAILABLE": True,
    "WEATHER.IS_ERROR": False,
    "WEATHER.TEMPERATURE": 14,
    "WEATHER.TEMPERATURE_UNIT": 1,
    "WEATHER.CHANCE_OF_PRECIPITATION": 40,
    "WEATHER.UV_INDEX": 2,
    "WEATHER.DAYS.0.IS_AVAILABLE": True,
    "WEATHER.DAYS.0.UV_INDEX": 3,
    # Complication slots: slot id -> data the provider would send.
    "__slot0": {"type": "RANGED_VALUE", "RANGED_VALUE_VALUE": 64, "RANGED_VALUE_MIN": 0, "RANGED_VALUE_MAX": 100},
    "__slot1": {"type": "LONG_TEXT", "TEXT": "termin", "TITLE": "15:00"},
}
