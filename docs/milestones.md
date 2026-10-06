# Meilensteine, Abweichungen, offene Punkte

Stand: 06.10.2026 (M1–M7 umgesetzt und auf der Uhr bestätigt)

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
| Themen | `ColorConfiguration`/`ColorOption colors="…"` erlaubt laut XSD **höchstens 5 Farben** (alle Versionen 1–5). Für 10 Rollen deshalb `ListConfiguration` mit einer Kopie des Layouts je Thema (siehe M6). Flavors ab v2, `MultipleInstancesAllowed` und `FlavorsSupported` müssen `true` sein. |
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

Auf der Uhr bestätigt (06.10.): Reihenfolge Uhrzeit/Titel richtig, UV-Wert
stimmt mit der Samsung-Wetter-App, Benachrichtigungszahl verschwindet bei 0,
Tap-Ziele öffnen die richtigen Apps, Handy-Akku über Phone Battery
Complication funktioniert.

Befund: Samsungs Terminquelle hängt einen Doppelpunkt an die Uhrzeit
(`> 14:00: abgesagt: …`). Behoben in M6: Ein Ausdruck entfernt ihn, egal ob die
Uhrzeit im Titel oder am Anfang des Texts steht (`H:MM:` und `HH:MM:`).

## M6 Themen und Always-on-Display

Abweichung (mit dir abgestimmt): Eine Farboption fasst höchstens 5 Farben. Statt
einer `ColorConfiguration` mit 10 Farben je Option gibt es eine
`ListConfiguration` „Thema“ mit vier Optionen. Die Quelle ist
`watchface/watchface.template.xml` mit Farbrollen `@{rolle}`.
`tools/build_watchface.py` kopiert jeden `<ThemeSwitch>`-Block einmal pro Thema
aus `watchface/themes.json`. Die erzeugte `res/raw/watchface.xml` ist
eingecheckt, die CI prüft, dass sie aktuell ist.

- Vier Flavors (je Thema einer) mit Icon, `MultipleInstancesAllowed = true`.
- Themen-Icons (192 px) aus dem Offline-Renderer.
- Always-on-Display: Szene schwarz, die Themenfläche liegt im aktiven Teil.
  Sichtbar: Uhrzeit ohne Sekunden, Datum, Kalenderwoche (Rolle text). Alles
  andere inkl. Complications ausgeblendet. Offline gemessen 2,6 % leuchtende
  Pixel je Thema.

Entscheidungen:

- Abweichung auf deinen Wunsch: Der dünne Rahmen um die Uhrzeit, den die
  Vorgabe im AOD vorsieht, entfällt.
- Datum und Kalenderwoche behalten im AOD ihre Position aus der Waybar.

Befund aus dem Test (06.10.): Der Doppelpunkt stand weiter da
(`> 27 min.: test`). Samsungs Terminquelle schickt `<Zeit>: <Titel>`, und die
Zeit ist auch relativ (`27 min.`). Neue Lösung: Makros in
`tools/build_watchface.py` suchen das erste `": "` in den ersten 16 Zeichen
(WFF hat kein `indexOf`) und entfernen den Doppelpunkt. Ein leerer Titel zählt
wie kein Titel. Nach dem Codex-Review nur noch, wenn Titel bzw. Text mit einer
Ziffer beginnt. Texte wie `Abgesagt: Kino` bleiben damit unverändert.

Auf der Uhr bestätigt (06.10.): Doppelpunkt-Fix und Always-on-Display ohne
Rahmen. Themenwechsel unter *Anpassen* → *Thema* funktioniert (wischen bzw.
drehen, nicht tippen).

## M7 Abschluss

- `preview.png` ist der echte Screenshot von der Uhr aus M2 (Beispieldaten,
  Tokyo Night). Der orange System-Indikator für Benachrichtigungen am linken
  Rand ist übermalt.
- README mit Build, Installation (PC und nur Handy), Zuweisung der
  Complication-Felder und Themen.
- XML-Validator und Memory-Footprint laufen bei jedem Push in der CI.

## Nach M7: Englisch und zweisprachige Doku

- Kacheltitel auf Englisch: `~/rain`, `~/steps`, `~/battery`, `> free`
  (`~/temp` und `~/uv max` waren es schon). Datum, `kw41` und die Wochenleiste
  `m d m d f s s` bleiben auf deinen Wunsch im bisherigen Format.
- Texte im Editor der Uhr: Englisch als Standard (`values/`), Deutsch als
  Übersetzung (`values-de/`).
- `README.md` auf Englisch, `README.de.md` auf Deutsch. `tools/check_readmes.py`
  (`make docs`, CI) prüft gleiche Gliederung, Sprachlinks, Links und Anker.
- Nachbesserung zum zweiten Codex-Befund: `make icons` erzeugt zuerst die XML,
  sonst bekäme ein neues Thema ein leeres Icon. Das Audit prüft jetzt den
  Hintergrund jedes Icons.
- `preview.png` zeigt noch die deutschen Titel aus M2 und wird durch einen neuen
  Screenshot ersetzt.

## Offene Punkte

Alle sechs Punkte aus dem Handover sind geklärt:

1. UV-Maximum: `WEATHER.DAYS.0.UV_INDEX`, auf der Uhr bestätigt.
2. Kalenderwoche: per Ausdruck, offline für 2000–2040 und auf der Uhr bestätigt.
3. Wochenleiste Mo–So: umgesetzt und auf der Uhr bestätigt.
4. Schritte-Format `6.2k`: per Ausdruck umgesetzt.
5. Benachrichtigungszähler: funktioniert auf der Uhr.
6. Waybar-Breite: passt bei Schriftgröße 16.
