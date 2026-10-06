# Meilensteine, Abweichungen, offene Punkte

Stand: 06.10.2026

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

## M2 auf der Uhr (Galaxy Watch8, SM-L315F, Wear OS 6, API 36)

Bestätigt. Die Textgrundlinien weichen höchstens 1 Einheit von der Berechnung
ab, JetBrains Mono wird geladen. Der orange Punkt links am Rand ist die
Benachrichtigungsanzeige von One UI Watch, nicht Teil des Zifferblatts.

Paketnamen auf der Uhr: Wetter `com.samsung.android.watch.weather`,
Samsung Health `com.samsung.android.wear.shealth`, Kalender
`com.samsung.android.calendar`.

## M3 Eingebaute Daten

- Uhrzeit über `DigitalClock`/`TimeText format="hh:mm" hourFormat="24"`.
- Sekunden `:` + `[SECOND_Z]`.
- Wochenleiste: Kästchen und Buchstabe des heutigen Tags wandern per
  `Transform target="x"` auf `100 + 18 × ((DAY_OF_WEEK + 5) % 7)`. Die Farbe
  eines Font lässt sich erst ab v4 per Ausdruck ändern, deshalb liegt der
  hervorgehobene Buchstabe als eigene Ebene über dem gedämpften.
- Datum `[DAY_Z].[MONTH_Z]`.
- ISO-Woche per Ausdruck (Donnerstag der Woche), getestet für jeden Tag 2000–2040.
- Schritte unter 1000 voll, sonst `6.2k` (auf 100 abgeschnitten, nicht gerundet).
  Die Ziffern laufen über `numberFormat("0", …)`, damit eine deutsche Uhr keinen
  Dezimalpunkt in ein Komma verwandelt.
- Akku `[BATTERY_PERCENT]%`.
- Benachrichtigungen: Gruppe bei 0 per `alpha` ausgeblendet. Der Punkt rückt
  bei zwei- und dreistelligen Zahlen nach links.
- `tools/test_expressions.py` prüft alle Ausdrücke offline.

Abweichungen:

- Kalenderwoche ohne führende Null (`kw1`). Die Vorgabe nennt nur `kw41`.

## M4 Wetter

- Temperatur ganzzahlig in °C. Meldet die Uhr Fahrenheit (`TEMPERATURE_UNIT == 2`),
  wird umgerechnet.
- Regenwahrscheinlichkeit `[WEATHER.CHANCE_OF_PRECIPITATION]%`.
- UV-Maximum: `WEATHER.DAYS.0.UV_INDEX`. Liegt der aktuelle Wert darüber, gilt
  der aktuelle. Ohne Tagesvorhersage der aktuelle Wert.
- Leerzustand: nicht verfügbar oder `IS_ERROR` zeigt `--` in muted.
- Veraltete Daten (älter als 3 Stunden laut `WEATHER.LAST_UPDATED`) erscheinen in
  muted. Das ist meine Auslegung von „niemals einen veralteten Wert ohne
  Kennzeichnung“.
- Antippen der Wetterzeile öffnet `com.samsung.android.watch.weather`.

## M5 Complications

- Slot 0 Handy-Akku (`RANGED_VALUE`, `SHORT_TEXT`, `EMPTY`), keine
  Standardquelle. Leer zeigt `--` in muted.
- Slot 1 Nächster Termin (`LONG_TEXT`, `SHORT_TEXT`, `EMPTY`), Standardquelle
  `NEXT_EVENT`. Darstellung `> TITEL TEXT` in Kleinbuchstaben, nach 22 Zeichen
  mit `…` gekürzt. Leer zeigt `> frei` in muted.
- Beide zeichnen sich im Kachelstil selbst. Antippen löst die Tap-Aktion der
  Datenquelle aus.
- Antippen der Schritte-Kachel öffnet `com.samsung.android.wear.shealth`.

Auf der Uhr zu prüfen:

- In welchen Feldern liefert Samsungs Terminquelle Uhrzeit und Titel? Erwartet:
  Uhrzeit im Titel, Termin im Text. Steht es verdreht da, tausche ich die Reihenfolge.
- Liefert `WEATHER.DAYS.0.UV_INDEX` einen plausiblen Wert? Vergleich mit der
  Samsung-Wetter-App.
- Erscheint die Benachrichtigungszahl?

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
