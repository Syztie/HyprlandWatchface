# Watchface Hyprland – Übergabe für Claude Code

Oct 5, 2026

## Auftrag

Baue ein eigenes Zifferblatt für eine Samsung Galaxy Watch im Stil eines Hyprland-Desktops: Waybar oben, darunter gerahmte Kacheln in Monospace-Schrift auf dunklem Grund. Das Design ist abgestimmt, dieses Dokument ist die verbindliche Vorgabe.

So sollst du vorgehen:

- Setze das Zifferblatt deklarativ im Watch Face Format (XML) um, ohne eigenen Code auf der Uhr.
- Prüfe jeden Namen einer Datenquelle, jedes Attribut und die Mindestversion gegen die offizielle Referenz unter developer.android.com/training/wearables/wff, bevor du ihn verwendest. Die Namen in diesem Dokument sind Erwartungen, keine geprüften Fakten.
- Arbeite in den Meilensteinen am Ende des Dokuments und halte nach jedem an, damit ich auf der Uhr testen kann.
- Frag nach, wenn eine Vorgabe technisch nicht geht. Ändere das Design nicht stillschweigend.
- Antworte auf Deutsch. Bezeichner im Code bleiben englisch.

## Zielgerät und Technik

Zielgerät ist eine Galaxy Watch 7, 8 oder Ultra mit rundem Display und Wear OS 5 oder neuer. Die genaue Variante und die Wear-OS-Version liest du zu Beginn per `adb shell getprop` aus.

| Punkt | Vorgabe |
| --- | --- |
| Format | Watch Face Format, reine Ressourcen, `android:hasCode="false"` im Manifest |
| Format-Version | Niedrigste Version, die Wetterdaten und alle genutzten Quellen abdeckt, mindestens 2. Property `com.google.wear.watchface.format.version`, `minSdkVersion` passend dazu |
| Koordinatenraum | `<WatchFace width="450" height="450">`, eine einzige `res/raw/watchface.xml`, keine Shapes-Datei |
| Pflichtdateien | `AndroidManifest.xml`, `res/raw/watchface.xml`, `res/xml/watch_face_info.xml` (mit `Editable` und `FlavorsSupported` auf true), `res/drawable/preview.png`, `res/values/strings.xml` |
| Schrift | JetBrains Mono (OFL) in `res/font`, Regular und Medium |
| Entwicklungsrechner | Arch Linux, Hyprland. Kein Watch Face Studio. Android Studio ist optional, der Build muss über die Kommandozeile laufen |
| Build | Gradle-Wrapper, `./gradlew :app:assembleDebug`, JDK 17, Android-SDK per `sdkmanager` |
| Deployment | `adb` über WLAN (Entwickleroptionen und kabelloses Debugging auf der Uhr), `adb install`, danach das Zifferblatt auf der Uhr auswählen |
| Prüfung | XML-Validator und Memory-Footprint-Tool aus [github.com/google/watchface](https://github.com/google/watchface) vor jedem Meilenstein |

Lege im Repo ein `Makefile` oder `justfile` mit den Zielen `build`, `validate`, `install` und `screenshot` an. Als Vorlage für die Projektstruktur dienen die [offiziellen Beispiele](https://github.com/android/wear-os-samples/tree/main/WatchFaceFormat). Die Struktur und die Manifest-Einträge stehen in der [Setup-Anleitung](https://developer.android.com/training/wearables/wff/setup).

## Layout

Das Zifferblatt hat fünf Zeilen von oben nach unten: Waybar, Uhrzeit, Wetter, Schritte und Akku, nächster Termin. Alle Maße gelten im Koordinatenraum 450 × 450 mit dem Mittelpunkt 225/225. Jede Ecke einer Kachel muss mindestens 6 Einheiten vom Displayrand entfernt bleiben.

| Element | x, y, Breite × Höhe | Inhalt | Schrift |
| --- | --- | --- | --- |
| Waybar | 90, 58, 270 × 38 | Wochenleiste, Datum `05.10`, Kalenderwoche `kw41` | 16 |
| Uhrzeit-Kachel | 42, 109, 366 × 93 | `14:32` im 24-Stunden-Format, mittig | 74 |
| Sekunden | rechtsbündig bei x 396, Grundlinie y 190 | `:07`, gedämpfte Farbe | 22 |
| Benachrichtigungen | rechtsbündig bei x 396, Grundlinie y 134 | Punkt plus Anzahl, bei 0 unsichtbar | 18 |
| Kachel `~/temp` | 32, 215, 122 × 74 | `14°`, ganzzahlig, Grad Celsius | Titel 18, Wert 29 |
| Kachel `~/regen` | 164, 215, 122 × 74 | `40%` Regenwahrscheinlichkeit | Titel 18, Wert 29 |
| Kachel `~/uv max` | 296, 215, 122 × 74 | `3`, höchster UV-Index des Tages | Titel 18, Wert 29 |
| Kachel `~/schritte` | 58, 302, 135 × 64 | `6.2k`, unter 1000 die volle Zahl | Titel 18, Wert 24 |
| Kachel `~/akku` | 202, 302, 190 × 64 | Uhr-Symbol `78%`, Handy-Symbol `64%` | Titel 18, Wert 22 |
| Terminzeile | mittig bei x 225, Grundlinie y 402 | `> 15:00 titel`, höchstens 22 Zeichen | 19 |

Gestaltungsregeln:

- Jeder Kacheltitel beginnt mit `~/` und steht klein und gedämpft oben links in der Kachel.
- Alle Texte sind klein geschrieben und in JetBrains Mono gesetzt.
- Kacheln haben keinen Füllton, einen Rahmen von 1,5 Einheiten und einen Eckenradius von 6. Die Uhrzeit-Kachel ist die aktive Kachel und hat einen Rahmen von 3 Einheiten in der Akzentfarbe.
- Die Wochenleiste zeigt sieben Buchstaben `m d m d f s s`. Der heutige Tag ist wie ein aktiver Hyprland-Workspace hervorgehoben: gefülltes Kästchen in der Akzentfarbe, Buchstabe in der Hintergrundfarbe. Die übrigen Tage sind gedämpft.
- Das Uhr-Symbol ist ein kleiner Kreisumriss, das Handy-Symbol ein kleines stehendes Rechteck mit runden Ecken. Beide werden als Formen gezeichnet, nicht als Bilddateien.

Referenzbild als SVG im selben Koordinatenraum (Thema Tokyo Night). Speichere es als `docs/reference.svg` und vergleiche jeden Screenshot damit:

```xml
<svg viewBox="0 0 450 450" xmlns="http://www.w3.org/2000/svg" font-family="JetBrains Mono, monospace">
  <circle cx="225" cy="225" r="225" fill="#1a1b26"/>
  <rect x="90" y="58" width="270" height="38" rx="6" fill="none" stroke="#414868" stroke-width="1.5"/>
  <rect x="100" y="66" width="18" height="22" rx="4" fill="#7aa2f7"/>
  <g font-size="16" text-anchor="middle" fill="#565f89">
    <text x="109" y="83" fill="#1a1b26">m</text><text x="127" y="83">d</text><text x="145" y="83">m</text>
    <text x="163" y="83">d</text><text x="181" y="83">f</text><text x="199" y="83">s</text><text x="217" y="83">s</text>
  </g>
  <text x="236" y="83" font-size="16" fill="#c0caf5">05.10</text>
  <text x="350" y="83" font-size="16" text-anchor="end" fill="#7dcfff">kw41</text>
  <rect x="42" y="109" width="366" height="93" rx="6" fill="none" stroke="#7aa2f7" stroke-width="3"/>
  <text x="219" y="183" font-size="74" text-anchor="middle" fill="#c0caf5">14:32</text>
  <circle cx="376" cy="128" r="4" fill="#bb9af7"/>
  <text x="396" y="134" font-size="18" text-anchor="end" fill="#bb9af7">3</text>
  <text x="396" y="190" font-size="22" text-anchor="end" fill="#565f89">:07</text>
  <g fill="none" stroke="#414868" stroke-width="1.5">
    <rect x="32" y="215" width="122" height="74" rx="6"/><rect x="164" y="215" width="122" height="74" rx="6"/>
    <rect x="296" y="215" width="122" height="74" rx="6"/>
    <rect x="58" y="302" width="135" height="64" rx="6"/><rect x="202" y="302" width="190" height="64" rx="6"/>
  </g>
  <g font-size="18" fill="#565f89">
    <text x="43" y="241">~/temp</text><text x="175" y="241">~/regen</text><text x="307" y="241">~/uv max</text>
    <text x="69" y="326">~/schritte</text><text x="213" y="326">~/akku</text>
  </g>
  <text x="43" y="276" font-size="29" fill="#e0af68">14°</text>
  <text x="175" y="276" font-size="29" fill="#7aa2f7">40%</text>
  <text x="307" y="276" font-size="29" fill="#ff9e64">3</text>
  <text x="69" y="355" font-size="24" fill="#bb9af7">6.2k</text>
  <circle cx="221" cy="347" r="7" fill="none" stroke="#9ece6a" stroke-width="2"/>
  <text x="235" y="355" font-size="22" fill="#9ece6a">78%</text>
  <rect x="298" y="337" width="11" height="18" rx="2.5" fill="none" stroke="#7dcfff" stroke-width="2"/>
  <text x="317" y="355" font-size="22" fill="#7dcfff">64%</text>
  <text x="225" y="402" font-size="19" text-anchor="middle" fill="#e0af68">&gt; 15:00 termin</text>
</svg>
```

## Datenquellen

Neun Anzeigen kommen aus eingebauten Quellen, zwei aus Complication-Feldern, eine ist offen. Die Namen in der dritten Spalte sind die erwarteten Bezeichner. Prüfe sie gegen die [XML-Referenz](https://developer.android.com/reference/wear-os/wff/watch-face), bevor du sie verwendest.

| Anzeige | Herkunft | Erwarteter Bezeichner | Hinweis |
| --- | --- | --- | --- |
| Uhrzeit, Sekunden | eingebaut | `DigitalClock` mit `TimeText`, Formate `HH:mm` und `ss` | Sekunden nur im aktiven Modus |
| Wochentag | eingebaut | `[DAY_OF_WEEK]` | Zählweise prüfen, die Woche beginnt hier am Montag |
| Datum | eingebaut | `[DAY]`, `[MONTH]` | Zweistellig mit führender Null |
| Kalenderwoche | eingebaut | `[WEEK_IN_YEAR]` | Muss der ISO-Woche entsprechen. Der 05.10.2026 ist KW 41 |
| Temperatur | eingebaut, Wetter | `[WEATHER.TEMPERATURE]` | Grad Celsius |
| Regenwahrscheinlichkeit | eingebaut, Wetter | `[WEATHER.CHANCE_OF_PRECIPITATION]` | Wert für jetzt, 0 bis 100 |
| UV-Maximum | offen | `[WEATHER.UV_INDEX]`, `[WEATHER.HOURS.<N>.UV_INDEX]` | Siehe offene Punkte |
| Schritte | eingebaut | `[STEP_COUNT]` |  |
| Akku Uhr | eingebaut | `[BATTERY_PERCENT]` |  |
| Akku Handy | Complication-Feld | `ComplicationSlot`, Typ `SHORT_TEXT` oder `RANGED_VALUE` | Datenquelle ist eine Zusatz-App, zum Beispiel [Phone Battery Complication](https://play.google.com/store/apps/details?id=com.weartools.phonebattcomp) |
| Nächster Termin | Complication-Feld | `ComplicationSlot`, Typ `SHORT_TEXT` oder `LONG_TEXT`, Standardquelle nächster Termin | Vom Nutzer frei umbelegbar |
| Benachrichtigungen | eingebaut | `[UNREAD_NOTIFICATION_COUNT]` | Verfügbarkeit und Mindestversion prüfen |

Für alle Wetterwerte gilt: Vor dem Zugriff `[WEATHER.IS_AVAILABLE]` prüfen und `[WEATHER.IS_ERROR]` beachten, wie in der [Wetter-Anleitung](https://developer.android.com/training/wearables/wff/weather) beschrieben. Die Complication-Felder richtest du nach der [Complication-Anleitung](https://developer.android.com/training/wearables/wff/complications) ein. Beide Felder zeichnen ihren Inhalt selbst im Stil der Kacheln, nicht im Standard-Look der Datenquelle.

## Farbthemen

Vier Themen sind an der Uhr umschaltbar, Tokyo Night ist der Standard. Jedes Thema belegt dieselben zehn Rollen.

| Rolle | Verwendung | Tokyo Night | Catppuccin Mocha | Gruvbox Dark | Nord |
| --- | --- | --- | --- | --- | --- |
| bg | Hintergrund | `#1a1b26` | `#1e1e2e` | `#282828` | `#2e3440` |
| border | Kachelrahmen | `#414868` | `#45475a` | `#504945` | `#434c5e` |
| muted | Kacheltitel, Sekunden, übrige Wochentage | `#565f89` | `#6c7086` | `#928374` | `#616e88` |
| text | Uhrzeit, Datum | `#c0caf5` | `#cdd6f4` | `#ebdbb2` | `#d8dee9` |
| accent | aktiver Rahmen, heutiger Tag, Regen | `#7aa2f7` | `#89b4fa` | `#83a598` | `#81a1c1` |
| yellow | Temperatur, Termin | `#e0af68` | `#f9e2af` | `#fabd2f` | `#ebcb8b` |
| orange | UV-Maximum | `#ff9e64` | `#fab387` | `#fe8019` | `#d08770` |
| purple | Schritte, Benachrichtigungen | `#bb9af7` | `#cba6f7` | `#d3869b` | `#b48ead` |
| green | Akku Uhr | `#9ece6a` | `#a6e3a1` | `#b8bb26` | `#a3be8c` |
| cyan | Akku Handy, Kalenderwoche | `#7dcfff` | `#89dceb` | `#8ec07c` | `#88c0d0` |

Setze die Themen als eine Farbkonfiguration mit vier Optionen um, jede Option mit allen zehn Farben in dieser Reihenfolge. Die Elemente greifen über den Index auf ihre Rolle zu. Der Aufbau steht in der Anleitung zu [User Configurations](https://developer.android.com/training/wearables/wff/personalization/user-configurations). Lege zusätzlich je Thema einen Flavor an, damit die Themen in der Begleit-App als Voreinstellung erscheinen.

## Always-on-Display, Antippen, Leerzustände

Im Always-on-Display bleiben nur Uhrzeit, Datum und Kalenderwoche sichtbar, alles andere wird ausgeblendet.

- Der Hintergrund ist reines Schwarz `#000000`, unabhängig vom Thema.
- Sichtbar sind die Uhrzeit ohne Sekunden, das Datum und die Kalenderwoche in der Rolle text, dazu der Rahmen der Uhrzeit-Kachel als dünne Linie von 1,5 Einheiten.
- Ausgeblendet sind die Wochenleiste, die Benachrichtigungen, alle Wetter-Kacheln, Schritte, Akku und die Terminzeile.
- Es gibt keine gefüllten Flächen. Der Anteil leuchtender Pixel bleibt unter 15 Prozent.
- Setze das mit Varianten für den Ambient-Modus um, siehe [Anleitung zum Ambient-Modus](https://developer.android.com/training/wearables/wff/ambient).

Antippen öffnet die passende App:

| Bereich | Ziel |
| --- | --- |
| Wetterzeile (alle drei Kacheln) | Wetter-App der Uhr |
| Kachel `~/schritte` | Samsung Health |
| Terminzeile | Tap-Aktion der Complication, standardmäßig der Kalender |
| Handy-Akku | Tap-Aktion der Complication, aktualisiert den Wert |

Die Paketnamen der Wetter-App und von Samsung Health ermittelst du auf der Uhr mit `adb shell pm list packages`.

Leerzustände:

- Wetter nicht verfügbar oder fehlerhaft: Alle drei Wetter-Kacheln zeigen `--` in der Rolle muted.
- Handy-Akku ohne Daten oder ohne zugewiesene Quelle: `--` in der Rolle muted.
- Kein Termin: Die Zeile zeigt `> frei` in der Rolle muted.
- Keine ungelesenen Benachrichtigungen: Punkt und Zahl sind unsichtbar.
- Niemals einen veralteten Wert ohne Kennzeichnung stehen lassen.

## Offene Punkte

Sechs Punkte sind nicht abschließend geklärt und müssen an der Referenz oder auf der Uhr geprüft werden. Melde das Ergebnis jeweils, bevor du weiterbaust.

1. UV-Maximum. Ein fertiges Tagesmaximum ist in der Wetter-Anleitung nicht dokumentiert. Prüfe in dieser Reihenfolge:
   - Gibt es in der Referenz doch ein Tagesfeld für den UV-Index, nimm das.
   - Sonst bilde das Maximum aus dem aktuellen Wert und der Stundenvorhersage. Sie reicht höchstens 8 Stunden voraus und deckt damit nur den Rest des Tages ab.
   - Liefert die UV-Quelle auf der Uhr keine brauchbaren Werte, wird die Kachel zu einem Complication-Feld für die UV-Anzeige von Samsung Weather. Ein Entwickler berichtete Ende 2024 von genau diesem Problem auf Samsung-Uhren.
2. Kalenderwoche. Die Quelle muss die ISO-Woche liefern. Testwerte: 05.10.2026 ist KW 41, 01.01.2027 ist KW 53, 04.01.2027 ist KW 1. Weicht die Quelle ab, berechne die ISO-Woche per Ausdruck.
3. Wochenleiste. Die Vorgabe ist eine Leiste Montag bis Sonntag mit hervorgehobenem heutigem Tag. Das ist eine Annahme und wird noch bestätigt.
4. Schritte-Format. Lässt sich `6.2k` nicht per Ausdruck erzeugen, zeige die volle Zahl.
5. Benachrichtigungszähler. Ist die Quelle auf der Uhr nicht verfügbar, entfällt die Anzeige ersatzlos.
6. Breite der Waybar. Passen Wochenleiste, Datum und Kalenderwoche bei Schriftgröße 16 nicht hinein, verkleinere zuerst die Kästchen der Wochenleiste. Die Schrift bleibt bei mindestens 15.

## Reihenfolge

Baue in sieben Meilensteinen und halte nach jedem an, bis ich das Ergebnis auf der Uhr bestätigt habe.

1. Umgebung. Android-SDK, JDK 17 und Gradle-Wrapper einrichten, die Uhr per `adb` über WLAN koppeln, ein leeres Zifferblatt bauen und installieren.
2. Statisches Layout. Alle Kacheln mit festen Beispieltexten im Thema Tokyo Night. Screenshot von der Uhr neben `docs/reference.svg` legen.
3. Eingebaute Daten. Uhrzeit, Sekunden, Wochenleiste, Datum, Kalenderwoche, Schritte, Akku der Uhr, Benachrichtigungen.
4. Wetter. Temperatur, Regenwahrscheinlichkeit, UV-Test nach den offenen Punkten, dazu die Leerzustände.
5. Complication-Felder. Nächster Termin und Handy-Akku, danach die Tap-Aktionen.
6. Themen und Always-on-Display. Vier Farbthemen mit Flavors, dann die Ambient-Varianten.
7. Abschluss. XML-Validator und Memory-Footprint ohne Fehler, `preview.png` aus einem echten Screenshot, eine `README.md` mit Build, Installation und der Zuweisung der beiden Complication-Felder.

Nach jedem Meilenstein lieferst du einen Screenshot von der Uhr (`adb exec-out screencap -p`) und eine Liste der Abweichungen von diesem Dokument.
