# AET-R01 – Service-Discovery im After Sales

## Run-Metadaten

- **Run-ID:** R01
- **Datum:** 14.09.2026
- **Rolle:** Business Owner
- **Ausgangsunternehmen:** Mittelständischer Maschinenbauer, ca. 650 Mitarbeitende
- **Bereich:** After Sales / Service
- **Run-Status:** Erfolgreich
- **Journey-Ausgang:** Kein KI-Use-Case erforderlich
- **Diagnosehinweis:** Dieser Bericht dokumentiert ausschließlich den fachlichen Run und sichtbare Findings. Eine technische Ursachenanalyse wurde nicht durchgeführt.

## 1. Value Stream und Abgrenzung

Gewählt wurde der End-to-End-Value-Stream **„Serviceanliegen End-to-End“**.

**Start:** Eingang eines Kundenanliegens im Service.

**Ende:** Eine fachlich geprüfte Lösung oder Maßnahme liegt vor; gegebenenfalls benötigte Ersatzteile sind geklärt, der Kunde ist informiert und der Vorgang ist dokumentiert abgeschlossen.

Zum Umfang gehören Erfassung, Triage, Zuständigkeitsklärung, Zusammenführen vorhandener Ticket-, ERP-, E-Mail- und Dateiinformationen, fachliche Klärung zwischen Service, Technik und Ersatzteilbereich, Entscheidung, Koordination, Kundenkommunikation und Abschluss.

Nicht im Umfang liegen Produktentwicklung und konstruktive Änderungen als eigener Value Stream, strategische Sortiments- oder Preisentscheidungen, Lieferantenbeschaffung, Rechnungswesen sowie die physische Durchführung längerer Vor-Ort-Reparaturen.

Der Value Stream wurde in sechs Phasen strukturiert:

1. Anliegen erfassen
2. Einordnen und zustellen
3. Kontext vervollständigen
4. Fachlich klären und entscheiden
5. Lösung koordinieren und kommunizieren
6. Abschluss und Lernen

## 2. Fokus / Deep Dive

Vertieft wurde Phase 4 **„Fachlich klären und entscheiden“**, einschließlich der unmittelbar vorgelagerten Kontextvervollständigung.

Der Fokus startet, sobald ein erfasstes Serviceanliegen für eine belastbare Beantwortung Informationen oder Beiträge weiterer Bereiche benötigt. Er endet mit einer fachlich geprüften Lösungsentscheidung samt dokumentierter Begründung und den benötigten Informationen für Kundenantwort oder Maßnahmenplanung.

Heutiger Ablauf:

1. Service prüft Anliegen und vorhandenen Kontext.
2. Informationslücken und benötigte Beteiligte werden identifiziert.
3. Kontext wird aus Ticket, ERP, E-Mail und Dateien gesucht und zusammengeführt.
4. Eine interne Rückfrage wird an Technik und/oder Ersatzteilbereich übergeben.
5. Fachpersonen bewerten und antworten.
6. Service gleicht Antworten und mögliche Widersprüche ab.
7. Bei neuen Lücken beginnt eine weitere Schleife.
8. Entscheidung, Quellen, offene Punkte und nächste Schritte werden dokumentiert.

Service steuert Fall und Kundenkontakt; Technik bewertet technische Fragen und Risiken; der Ersatzteilbereich klärt Identifikation, Verfügbarkeit und Alternativen.

## 3. Identifiziertes Problem

Für die fachliche Klärung fehlt ein durchgängiger, gemeinsam sichtbarer Fallkontext. Dadurch entstehen Suche, Wartezeiten, wiederholte Rückfragen und variable Abstimmungsschleifen zwischen Service, Technik und Ersatzteilbereich. Die Bearbeitungszeiten sind zu hoch und schwanken stark.

## 4. Ursachen, Evidenz und offene Hypothesen

Als Ausgangsfakten dokumentiert wurden:

- Ticket- und ERP-Daten sind nicht durchgehend verknüpft.
- Einzelne Teams arbeiten zusätzlich mit E-Mail und Dateien.
- Zwischen Service, Technik und Ersatzteilbereich sind mehrere Abstimmungen nötig.
- Bearbeitungszeiten sind zu hoch und schwanken stark.

Eine einzelne kausale Ursache wurde nicht als bestätigt bewertet. Plausibel, aber offen sind folgende Hypothesen:

- Anliegen werden nicht einheitlich mit einem ausreichenden Mindestkontext erfasst.
- Zuständigkeit und Priorität sind nicht immer eindeutig.
- Expertenanfragen enthalten zu wenig Kontext.
- Antworten werden nicht strukturiert in den Fall zurückgeführt.
- Ähnliche gelöste Fälle und technische Dokumente sind schwer auffindbar.
- Fehlende Fristen, Eskalationen oder Vertretungsregeln verlängern Wartezeiten.

Eine belastbare Baseline fehlt. Zu erheben sind Median und P80/P90 der Durchlaufzeit vom Klärbedarf bis zur Entscheidung, aktive Bearbeitungs- und Wartezeit, Anzahl bereichsübergreifender Rückfrageschleifen und Weiterleitungen, Vollständigkeit beim ersten Übergabepunkt, First-Time-Right, Wiederöffnungen und Suchzeit je Fall.

## 5. Betrachtete Lösungsalternativen

Alle Nutzen- und Lösungsfit-Aussagen wurden als Hypothese beziehungsweise unbestätigt behandelt.

| Alternative | Typ | KI | Bewertung im Run |
| --- | --- | --- | --- |
| Klärungsstandard und Fallverantwortung | Organisatorisch / Prozess | Nein | Schnell pilotierbar, hohe Machbarkeit, geringe Integration; adressiert Verantwortung und Übergaben, Medienbrüche nur teilweise. |
| Regelbasierter Workflow mit Fallakte und Messung | Hybride Non-AI-Lösung | Nein | Kombiniert Mindestkontext, Rollen, Routing, Aufgaben, Status, Fristen, Eskalationen, ERP-Referenzen und Ereignisdaten; mittlerer Aufwand. |
| Standard Case-Management-Plattform | Standardsoftware | Nein | Breite Abdeckung, aber lange Einführung, hoher Integrations- und Change-Aufwand; aktuell voraussichtlich unverhältnismäßig. |
| Integriertes Service-Fallcockpit | Individuelle Software | Nein | Hohe fachliche Passung möglich, aber Bau-, Betriebs-, Integrations- und Verschuldungsrisiken. |
| Prozess- und Durchlaufzeitanalytik | Analytics / ergänzend | Nein | Schafft Baseline und Transparenz, löst den Prozess allein jedoch nicht. |
| Wissens- und Klärungsassistent | GenAI-Assistenz | Ja | Als spätere Ergänzung plausibel; benötigt saubere Fallakte, aktuelle und berechtigte Quellen sowie Evaluation. Risiken sind falsche oder veraltete Aussagen, Rechteverletzungen und Automationsbias. |
| Organisatorischer Pilot ohne neue Technik | Keine technische Lösung | Nein | Geringstes Investitionsrisiko und geeignet zur Hypothesenprüfung; Such- und Medienbruchprobleme bleiben. |

## 6. Bevorzugte Lösung und Begründung

Bevorzugt wurde **„Regelbasierter Workflow mit Fallakte und Messung“**, ergänzt um den organisatorischen Klärungsstandard.

Die Lösung deckt Schleifen, fehlende Transparenz und unvollständigen gemeinsamen Kontext breiter ab als eine rein organisatorische Maßnahme, bleibt gegenüber neuer Standardsoftware oder Individualentwicklung jedoch fokussierter und risikoärmer. Die Messkomponente schafft zunächst die fehlende Baseline und prüft die Ursachenhypothesen. Die Entscheidung steht unter dem Vorbehalt eines begrenzten Piloten und der Prüfung vorhandener Funktionen des Ticketsystems.

Eine KI-Assistenz wurde nicht bevorzugt, weil Datenzugriff, Dokumentqualität und der messbare Anteil des Suchaufwands offen sind. Außerdem ersetzt KI weder Verantwortung noch Fristen oder Prozessregeln.

## 7. KI-Use-Case

Es ist **kein KI-Use-Case** entstanden. Die Discovery endete regulär mit einer fachlich begründeten Non-AI-Entscheidung; es wurde kein künstlicher KI-Use-Case angelegt.

## 8. Relevante UX-, Methodik- und Funktionsfindings

- **Gute Führung:** Beobachtung, Hypothese, Evidenz und Messgrößen werden nachvollziehbar getrennt. Unterschiedliche Lösungstypen lassen sich ohne künstlichen Gesamtscore vergleichen; ein Non-AI-Ergebnis wird regulär akzeptiert.
- **Analyseblockade:** „Antworten analysieren“ endete mit „Die für die Analyse vorgesehenen Antworten überschreiten das Größenlimit.“ Ein sichtbarer Grenzwert oder eine Vorwarnung war zuvor nicht erkennbar. Ein Wiederholungsversuch blieb unverändert; danach wurde der manuelle Weg genutzt.
- **Doppeleingabe:** Nach der fehlgeschlagenen Analyse mussten wesentliche Inhalte manuell erneut übertragen werden.
- **Widersprüchliche Next Action:** Nach gespeichertem Fokus blieb die prominente nächste Aktion „Fokusphase auswählen“, obwohl Phase 4 sichtbar ausgewählt war. Der korrekte Einstieg „Prozess im Detail analysieren“ war nur in der Phasenkarte zu finden.
- **Unklare Evidenzkennzeichnung:** Der Bereich „Bestätigte Ursache“ zeigte den Status „Bestätigt“, obwohl im Inhalt ausdrücklich festgehalten war, dass keine Ursache bestätigt ist.
- **Zu absolute Entscheidungsbezeichnung:** Nicht bevorzugte Optionen wurden als „Verworfen“ markiert, obwohl die GenAI-Assistenz bewusst als mögliche spätere Ergänzung dokumentiert war.
- **Wiederholbare Auswahloberfläche:** Nach getroffener Entscheidung blieben ein leeres Begründungsfeld und die aktive Auswahlaktion sichtbar, während die auditierte Begründung bereits in der Historie vorhanden war.

## 9. Screenshots

- [Discovery als abgeschlossen markiert](screenshots/AET-R01-01-discovery-complete.jpg)
- [Bevorzugte Lösung und Non-AI-Journey-Ausgang](screenshots/AET-R01-02-solution-selection.jpg)

## 10. Abschluss

**Run-Status: erfolgreich.** Der sichtbare Discovery-Pfad wurde fachlich abgeschlossen. Es gab weder einen Produktabbruch noch einen Agent- oder Toolabbruch.
