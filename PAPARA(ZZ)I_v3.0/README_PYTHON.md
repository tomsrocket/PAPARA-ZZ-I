# PAPARA(ZZ)I Python

Diese Fassung bildet den zentralen Arbeitsablauf der lokalen PAPARA(ZZ)I-3.0-
Testversion ohne MATLAB nach. Die vorhandenen Bilder und PAPARA-Textdateien
bleiben das Datenformat; es wird keine Datenbank eingeführt.

## Enthaltene Funktionen

- vorhandene freie Annotationen laden und anzeigen
- neue Annotationen als farbige offene Kreise setzen
- Annotationen auswählen, umbenennen und löschen
- Keyword-Dateien im alten Format sowie `#MODE=INDIVIDUAL` und `#MODE=SINGLE`
- Längen- und optionale Breitenmessungen
- Maßstab pro Bild
- nutzbare Rechteck- und Polygonflächen
- Bilder als unbrauchbar markieren
- Zoom, Verschieben, Helligkeit, Kontrast und Gamma
- sichtbaren Bildausschnitt mit Overlays als PNG oder JPG exportieren
- Abundanz-, Winkel- und Größenexporte im bisherigen Ordneraufbau
- ein Keyword stapelweise in allen Bildern ersetzen
- automatische `.bak`-Sicherung vor dem Überschreiben einer vorhandenen Datei

Nicht enthalten sind WoRMS, Objektivkorrektur und die in der lokalen MATLAB-
Testversion bereits deaktivierte Raster-/Zufallspunktanalyse. EPS- und TIFF-
Bildexport wurden wie in der Testversion durch PNG und JPG ersetzt.

## Direkt starten

Vorausgesetzt werden Python 3.10 oder neuer, Tkinter und Pillow. Unter Windows
kann `PAPARAZZI_Python_Starten.bat` doppelt angeklickt werden. Das Skript richtet
beim ersten Start eine lokale Python-Umgebung ein und lädt Pillow. Unter Linux
steht entsprechend `PAPARAZZI_Python_Starten.sh` zur Verfügung.

Alternativ im Terminal:

```text
python -m pip install -r requirements.txt
python -m paparazzi_py
```

Optional können Bilderordner und Benutzername direkt angegeben werden:

```text
python -m paparazzi_py "C:\Bilder\Projekt" --user anna
```

## Bedienung

1. Benutzername und Bilderordner auswählen.
2. Eine Keyword-Textdatei laden.
3. Keyword auswählen und mit der linken Maustaste ins Bild klicken.
4. Ein Klick auf einen Kreis wählt ihn aus. `Umschalt` + Klick benennt ihn mit
   dem aktuellen Keyword um. Rechtsklick oder `Entf` löscht ihn nach Rückfrage.
5. Das Mausrad zoomt; mit der mittleren Maustaste wird das Bild verschoben.
6. `Esc` beendet das aktive Zeichen- oder Messwerkzeug. Beim Polygon beendet
   ein Rechtsklick die Punkteingabe.

Annotationen werden sofort gespeichert. Vor jeder späteren Änderung einer
bereits vorhandenen Datei wird außerdem eine Datei mit der Endung `.bak`
angelegt beziehungsweise aktualisiert.

## Windows-Programm ohne Python erstellen

Auf einem Windows-Rechner mit installiertem Python genügt ein Doppelklick auf
`build_windows.bat`. Das fertige Programm liegt anschließend unter:

```text
dist\PAPARAZZI-Python\PAPARAZZI-Python.exe
```

Der gesamte Ordner `dist\PAPARAZZI-Python` kann auf den Arbeitsrechner kopiert
werden. Dort werden weder MATLAB noch Python benötigt.

## Tests

```text
python -m unittest discover -s tests -v
```

## Lizenz und Herkunft

PAPARA(ZZ)I wurde ursprünglich von Yann Marcon und Autun Purser entwickelt.
Diese kompatible Python-Neuentwicklung wird entsprechend dem Original unter
GNU GPL Version 3 oder später weitergeführt. Der vollständige Lizenztext liegt
in `gpl.txt`.

