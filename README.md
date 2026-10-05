# Hyprland Watch Face

Zifferblatt für die Samsung Galaxy Watch (Wear OS 5+, rund) im Stil eines
Hyprland-Desktops: Waybar oben, darunter gerahmte Kacheln in JetBrains Mono.
Umgesetzt im [Watch Face Format](https://developer.android.com/training/wearables/wff)
Version 2, rein deklarativ (`android:hasCode="false"`).

![Vorschau](app/src/main/res/drawable/preview.png)

## Projektaufbau

| Pfad | Inhalt |
| --- | --- |
| `app/src/main/res/raw/watchface.xml` | Das Zifferblatt (Koordinatenraum 450 × 450) |
| `app/src/main/res/xml/watch_face_info.xml` | Vorschau, Editierbarkeit, Flavors |
| `app/src/main/res/font/` | JetBrains Mono Regular und Medium (OFL, siehe `docs/OFL-JetBrainsMono.txt`) |
| `docs/reference.svg` | Verbindliches Referenzbild |
| `docs/milestones.md` | Stand je Meilenstein, Abweichungen, offene Punkte |
| `tools/` | Validator-Setup, Offline-Renderer, Layout-Audit |
| `keystore/debug.keystore` | Fester Debug-Schlüssel, damit lokale und CI-Builds sich gegenseitig überschreiben können |

## Testen nur mit Handy und Uhr

Jeder Push baut in GitHub Actions die APK, prüft sie (XML-Validator,
Memory-Footprint, Layout-Audit) und legt sie als Pre-Release **testbuild** ab:

- Release-Seite: <https://github.com/syztie/hyprlandwatchface/releases/tag/testbuild>
- APK direkt: <https://github.com/syztie/hyprlandwatchface/releases/download/testbuild/hyprland-watchface.apk>

### Einmalig einrichten

1. **Uhr:** Einstellungen → Info zur Uhr → Software-Info → *Softwareversion* 7× antippen.
   Danach unter Einstellungen → Entwickleroptionen *ADB-Debugging* und
   *Kabelloses Debugging* einschalten. Uhr und Handy müssen im selben WLAN sein.
2. **Handy:** [Bugjaeger Mobile ADB](https://play.google.com/store/apps/details?id=eu.sisik.hackendebug)
   installieren (ADB auf dem Handy, kein PC nötig).
3. **Koppeln:** Auf der Uhr unter *Kabelloses Debugging* → *Neues Gerät koppeln*.
   In Bugjaeger *Pair device* wählen und IP, Port und Kopplungscode von der Uhr
   eintippen. Danach in Bugjaeger mit der IP und dem Port verbinden, die die Uhr
   unter *Kabelloses Debugging* anzeigt (anderer Port als beim Koppeln).

### Jeder Testlauf

1. APK über den Link oben auf dem Handy herunterladen.
2. In Bugjaeger mit der Uhr verbinden → Paket-Symbol (*Install APK*) → die
   heruntergeladene `hyprland-watchface.apk` wählen.
3. Auf der Uhr das Zifferblatt lange gedrückt halten, nach rechts wischen bis
   **Hyprland** erscheint (sonst über *+ Hinzufügen*) und antippen.
4. **Screenshot:** Home- und Zurück-Taste der Uhr gleichzeitig drücken. Das Bild
   landet automatisch in der Galerie des Handys (Album *Watch*). Alternativ in
   Bugjaeger *Screenshot*.
5. Screenshot hier im Chat hochladen.

Shell-Befehle (z. B. `getprop`, `pm list packages`) laufen in Bugjaeger unter
*Shell*.

## Entwicklung am Rechner (Arch Linux)

Voraussetzungen: JDK 17, Android-SDK (`sdkmanager "platforms;android-36" "build-tools;36.0.0" "platform-tools"`),
Python 3 mit Pillow (für Vorschau und Audit).

```sh
make build        # ./gradlew :app:assembleDebug
make validate     # XSD-Validator (WFF v2), Memory-Footprint, Layout-Audit
make install      # adb install -r … (Uhr per adb über WLAN verbunden)
make screenshot   # adb exec-out screencap -p > screenshots/…
make preview      # Offline-Vorschau aktiv und Ambient nach build/preview/
```

Uhr per WLAN verbinden: auf der Uhr *Kabelloses Debugging* → *Neues Gerät
koppeln*, dann `adb pair IP:PORT` mit dem Code und `adb connect IP:PORT`.

`make tools` baut den offiziellen XML-Validator und das Memory-Footprint-Tool
aus [google/watchface](https://github.com/google/watchface) (fester Commit) nach
`tools/bin/`.

### Offline-Vorschau und Audit

`tools/render_preview.py` zeichnet das Teilset von WFF nach, das dieses
Zifferblatt nutzt, mit Beispieldaten aus `tools/sample_data.py`. Das ersetzt
keinen Screenshot von der Uhr, reicht aber für Layout-Vergleiche mit
`docs/reference.svg`. `tools/audit.py` prüft die Gestaltungsregeln, die der
XSD-Validator nicht sieht: Abstand der Kachel-Ecken zum Displayrand, Text auf
dem Display und in seiner Kachel, Schriftart und -größe, Kleinschreibung,
Palette und den Anteil leuchtender Pixel im Always-on-Display.
