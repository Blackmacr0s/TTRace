Das Django Projekt ist aktuell unter http://afkor.pythonanywhere.com/ erreichbar.
Navigation ist noch rudimentär und einige Sachen sind leer geschaltet oder laufen auf 404.
Ihr müsst nen bisschen testen um die funktionierenden Weg zusehen.

Die wichtigen Dateien sind eigentlich:

models.py - SQL Datenbankersteller

views.py  - komplette Backend Code

Rest ist hauptsächlich für die Anzeige des Code im Web.

Enthält noch eine Menge Code, welcher refactored werden müsste. ;)

Bin mir nicht sicher, ob die SQL Struktur optimal ist. 
Die Turnierspiele Tabelle führt zu sehr viel Code, weil ich immer prüfen muss ob jemand
Spieler 1 oder Spieler 2 ist. Denke ein Design mit doppelten Dateneinträgen für eine Partie
aus der Sicht jedes einzelnen Spielers macht mehr Sinn also: Spieler= A 0:11 0:11 0:11 Gegner= B
und Spieler1 = B 11:0 11:0 11:0 Gegner A.

Bei der Auslosung Runde 1 hab ich noch immer das alte System drin.

Ich hab noch keine Testcases geschrieben kA ob irgendwo wo Fehler im Algo sind, ausserdem
fehlen noch die Freilose. Keine Ahnung wie stark die potenziellen Auswirkungen auf den Algo
sind.
