# Meilensteine, Abweichungen, offene Punkte

Stand: 05.10.2026

## Geprüfte Fakten aus der Referenz

Quellen: XSD-Spezifikation und Validator aus
[google/watchface](https://github.com/google/watchface) (Commit `b6cdda0`) und
die Seiten unter developer.android.com/training/wearables/wff bzw.
/reference/wear-os/wff.

| Punkt | Ergebnis |
| --- | --- |
| Format-Version | **2**. Wetter ist erst ab v2 verfügbar (`features`-Seite: „WFF version 2 introduced Weather support“). Damit `minSdk = 34` (Wear OS 5). |
| Uhrzeit | `DigitalClock` > `TimeText`. Das Format erlaubt nur kleines `h`: **`hh:mm`** mit `hourFormat="24"`, Sekunden `ss`. `HH:mm` wäre ungültig. |
| Wochentag | `[DAY_OF_WEEK]`, **1 = Sonntag … 7 = Samstag**. Montag-Index = `([DAY_OF_WEEK] + 5) % 7`. |
| Datum | `[DAY_Z]` und `[MONTH_Z]` liefern die führende Null. |
| Kalenderwoche | `[WEEK_IN_YEAR]` ist laut Referenz `ALIGNED_WEEK_OF_YEAR`, also **keine ISO-Woche** (Woche 1 = 1.–7. Januar). Der 05.10.2026 ergäbe 40 statt 41. Die ISO-Woche wird deshalb per Ausdruck aus `DAY_OF_YEAR`, `DAY_OF_WEEK` und `YEAR` berechnet (M3). |
| Wetter | `WEATHER.IS_AVAILABLE`, `WEATHER.IS_ERROR`, `WEATHER.TEMPERATURE`, `WEATHER.TEMPERATURE_UNIT` (1 = °C, 2 = °F), `WEATHER.CHANCE_OF_PRECIPITATION`, `WEATHER.UV_INDEX`, `WEATHER.LAST_UPDATED`, `WEATHER.HOURS.<N>.*` (bis 8 h), `WEATHER.DAYS.<N>.*` (bis 5 Tage). |
| UV-Maximum | Es gibt ein Tagesfeld: **`WEATHER.DAYS.0.UV_INDEX`** (offener Punkt 1, erste Stufe). |
| Temperatur in °C | Werte kommen in der Einheit des Nutzers. Bei `TEMPERATURE_UNIT == 2` wird umgerechnet: `(F − 32) × 5 / 9`. |
| Schritte, Akku, Benachrichtigungen | `[STEP_COUNT]`, `[BATTERY_PERCENT]`, `[UNREAD_NOTIFICATION_COUNT]`, alle seit v1. |
| Complications | Typen `SHORT_TEXT`, `LONG_TEXT`, `RANGED_VALUE`, `EMPTY` u. a. Standardquelle über `DefaultProviderPolicy defaultSystemProvider="NEXT_EVENT"`. Inhalt selbst zeichnen über `[COMPLICATION.TEXT]`, `[COMPLICATION.TITLE]`, `[COMPLICATION.RANGED_VALUE_VALUE]`. |
| Antippen | `<Launch target="paket.name"/>` in `Group` oder `Part*`, seit v1. |
| Themen | `ColorConfiguration` mit `ColorOption colors="#… #… …"`, Zugriff per `[CONFIGURATION.theme.<index>]`. Flavors ab v2. |
| Ambient | `<Variant mode="AMBIENT" target="alpha" value="0"/>` usw. |
| Textausrichtung | `verticalAlign` existiert in v2 nicht. Text wird in seiner Box vertikal zentriert. Die Boxen sind so berechnet, dass die Grundlinien denen in `reference.svg` entsprechen (JetBrains Mono: Grundlinie = Boxmitte + 0,36 × Schriftgröße). |

## Umgebung (Cloud-Sitzung)

- Keine direkte Verbindung zur Uhr möglich, kein Emulator (kein KVM). Getestet
  wird über GitHub Actions → Release `testbuild` → Bugjaeger auf dem Handy, siehe
  README.
- `dl.google.com` (Android-SDK, Google Maven) ist in der Cloud-Umgebung gesperrt.
  Der offizielle Gradle-Build und das Memory-Footprint-Tool laufen deshalb in
  GitHub Actions. Lokal prüfe ich mit dem XSD-Validator, einem aapt2-Notbau,
  dem Offline-Renderer und dem Audit.

## M1 Umgebung

Erledigt:

- Gradle-Wrapper (Gradle 9.2.1, AGP 9.0.0), JDK 17, `./gradlew :app:assembleDebug`.
- Pflichtdateien laut Vorgabe, `hasCode="false"`, Property
  `com.google.wear.watchface.format.version = 2`.
- `Makefile` mit `build`, `validate`, `install`, `screenshot` (plus `preview`, `tools`).
- CI mit Validator, Memory-Footprint, Audit und Release `testbuild`.

Abweichungen:

- Die Uhr ist nicht per `adb` an *meine* Umgebung gekoppelt, sondern an dein
  Handy (Bugjaeger). `getprop` und `pm list packages` musst du dort ausführen.

## M2 Statisches Layout

Erledigt: alle Kacheln mit den Beispieltexten aus `reference.svg`, Thema Tokyo
Night. Offline-Render deckt sich mit der Referenz, Audit 127/127 grün.

Abweichungen und Entscheidungen:

- Uhrzeit in **JetBrains Mono Medium**, alles andere Regular. Die Vorgabe nennt
  beide Schnitte, legt aber nicht fest, wofür Medium dient.
- `preview.png` ist vorerst ein Offline-Render. Ein echter Screenshot folgt in M7.
- Offener Punkt 6 (Breite der Waybar): passt bei Schriftgröße 16. Der Abstand
  zwischen Datum und `kw41` beträgt rund 27 Einheiten.

Auf der Uhr zu prüfen:

- Sitzen die Grundlinien wie im Referenzbild? Die vertikale Zentrierung von Text
  ist aus der Doku abgeleitet. Weicht sie ab, verschiebe ich alle Texte um
  denselben Betrag.
- Wird JetBrains Mono geladen? Fällt die Uhr auf die Systemschrift zurück, wäre
  das am fehlenden Monospace-Look sofort sichtbar.

## Offene Punkte

1. UV-Maximum: Tagesfeld `WEATHER.DAYS.0.UV_INDEX` vorhanden. Ob Samsung es
   befüllt, zeigt erst M4 auf der Uhr.
2. Kalenderwoche: Quelle ist nicht ISO. Berechnung per Ausdruck in M3, offline
   gegen alle Tage 2020–2040 getestet.
3. Wochenleiste Mo–So: weiterhin Annahme, umgesetzt wie vorgegeben.
4. Schritte-Format `6.2k`: über `numberFormat` geplant (M3).
5. Benachrichtigungszähler: Quelle existiert seit v1. Ob Samsung ihn liefert,
   zeigt M3.
6. Waybar-Breite: passt (siehe M2).
