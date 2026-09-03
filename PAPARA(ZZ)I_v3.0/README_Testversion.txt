PAPARA(ZZ)I 3.0 – lokale Test-Erweiterung
===========================================

Diese Dateien sind für die lokale Testkopie gedacht. Das GitHub-Repository
wird dadurch nicht verändert.

Enthaltene Änderungen
---------------------
1. Manuelle Annotationen werden als offene Kreise dargestellt.
2. Die Farbe wird aus einer optionalen Farbnummer in der Keyword-Datei gelesen.
3. Eine Keyword-Datei kann individuell gefärbt oder einfarbig verwendet werden.
4. Der alte Java-/Split-Toolbar-Code wurde für aktuelle MATLAB-Versionen ersetzt.
5. Die gespeicherten Annotationstexte bleiben im bisherigen Format:
      X-Koordinate<TAB>Y-Koordinate<TAB>Keyword

So werden die Dateien verwendet
-------------------------------
1. Beende PAPARA(ZZ)I.
2. Sichere deinen gesamten Ordner PAPARA(ZZ)I_v3.0_Test.
3. Kopiere die Dateien aus diesem Patch-Ordner in deine Testkopie und ersetze
   die gleichnamigen Dateien.
4. Kopiere zusätzlich fcn_color_id.m und fcn_keyword_color.m in denselben
   Ordner wie PAPARAZZI.m.
5. MATLAB neu starten oder im Command Window eingeben:
      clear functions
      rehash
      PAPARAZZI

Keyword-Datei mit individuellen Farben
--------------------------------------
Die Trennung zwischen Keyword und Farbnummer ist ein TABULATOR:

#MODE=INDIVIDUAL
#DEFAULT=1
Bauten_Typ_1<TAB>1
Bauten_Typ_2<TAB>2
Bauten_Typ_3<TAB>3
Sand<TAB>8
Kies<TAB>9

In der tatsächlichen Datei muss <TAB> durch die Tabulatortaste ersetzt werden.

Keyword-Datei mit einer gemeinsamen Farbe
-----------------------------------------
#MODE=SINGLE
#COLOR=5
Bauten_Typ_1
Bauten_Typ_2
Bauten_Typ_3
Sand
Kies

Farbnummern
-----------
1  Blau       2  Orange     3  Grün       4  Violett
5  Türkis     6  Rot        7  Magenta    8  Gelb
9  Schwarz   10  Grau      11  Weiß      12  Dunkelblau

Hinweise
--------
- Die Farbe ist nur eine Darstellungshilfe. Der gespeicherte Keyword-Text ist
  die eigentliche Annotation.
- Wenn keine Farbnummer angegeben ist, wird die Standardfarbe verwendet.
- Die Messfunktion bleibt an die ausgewählte Annotation gekoppelt.
- Der Punktgenerator im Toolbar-Dropdown ist in dieser Testversion nicht mehr
  als Dropdown verfügbar; manuelle Punktannotation ist davon unabhängig.
- Die Änderungen sind zunächst als Testversion zu betrachten.

Export der Standbilder mit Annotationen
---------------------------------------
- Im Toolbar gibt es zwei Export-Schaltflächen: PNG und JPG.
- Vor dem Export müssen die Annotationen eingeblendet sein ("Show annotations").
- Der Export nimmt den aktuellen Bildausschnitt mit den sichtbaren, farbigen
  Annotationen und offenen Kreisen auf.
- Die Dateien werden automatisch im Ordner
      <Bildordner>\<Benutzer>_exported_images\free_annotations\
  gespeichert.
- Die Originalbilder und die Annotationstextdateien werden nicht verändert.
