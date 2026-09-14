# Unabhängiger Plausibilitätsreview AET-R01

## Urteil

**teilweise robust**

Der Run entwickelt aus einem plausibel abgegrenzten Klärungsprozess eine vorsichtige, pilotierbare Non-AI-Lösung und macht wesentliche Wissenslücken transparent. Methodisch positiv sind insbesondere der Verzicht auf eine behauptete bestätigte Einzelursache, die vorgesehene Baseline-Messung und die Einordnung von KI als mögliche spätere Ergänzung. Die Herleitung ist jedoch nicht vollständig belastbar: Die Fokuswahl ist nicht gegenüber anderen Phasen priorisiert, das zentrale Problem enthält bereits eine unbestätigte Kausalannahme, die Alternativen sind teilweise überlappend und die bevorzugte Lösung wird vor Prüfung der Ursachenhypothesen sowie vorhandener Systemfunktionen festgelegt. Die Screenshots liefern außerdem keine belastbare visuelle Bestätigung des dokumentierten Abschlusses.

## Fachliche Plausibilitätsprüfung

### Value Stream und E2E-Abgrenzung

Die sechs Phasen bilden den Informations-, Entscheidungs- und Kommunikationsfluss eines Serviceanliegens schlüssig ab. Start, Ende, Rollen und Ausschlüsse sind verständlich beschrieben; der Deep Dive lässt sich darin sauber verorten.

Die Bezeichnung „Serviceanliegen End-to-End“ ist allerdings weiter als die tatsächlich gewählte Grenze. Wenn eine physische Reparatur oder eine andere Umsetzung erforderlich ist, endet der betrachtete Ablauf bereits mit Entscheidung, Koordination und Kommunikation und damit vor der realisierten Kundenlösung. Fachlich sauberer wäre entweder eine Bezeichnung wie „Serviceanliegen bis zur Lösungsentscheidung und Übergabe“ oder eine explizite Begründung, weshalb die Umsetzung nicht Teil des relevanten E2E-Kundenergebnisses ist.

### Fokusentscheidung

Phase 4 einschließlich der vorgelagerten Kontextvervollständigung ist angesichts bereichsübergreifender Rückfragen, Suche und schwankender Bearbeitungszeiten ein plausibler Fokus. Nicht dokumentiert ist jedoch, warum dieser Fokus im Vergleich zu Erfassung, Routing, Umsetzung oder Abschluss den größten erwarteten Hebel besitzt. Es fehlen fallbezogene Beobachtungen, Volumen, Zeitanteile oder eine qualitative Priorisierung der sechs Phasen. Die Wahl ist deshalb nachvollziehbar, aber nicht unabhängig abgesichert.

### Problem, Beobachtungen, Hypothesen und Ursachen

Der Run analysiert formal das Problem vor der Lösung und erklärt transparent, dass keine einzelne Ursache bestätigt wurde. Die Liste offener Hypothesen und der Messplan sind methodisch sinnvoll.

Die Trennung ist inhaltlich dennoch nicht vollständig sauber:

- Die als „Ausgangsfakten“ bezeichneten Aussagen haben keine dokumentierte Herkunft, Fallbeispiele oder Messbasis. Sie sind als gesetzter Ausgangsrahmen verwendbar, aber nicht als im Run beobachtete Evidenz verifiziert.
- Das Problemstatement erklärt, ein fehlender durchgängiger gemeinsamer Fallkontext verursache Suche, Wartezeit und Schleifen. Damit wird eine konkrete Ursache bereits behauptet, obwohl sie im folgenden Abschnitt ausdrücklich nicht bestätigt ist. Aus nicht verknüpften Systemen und mehreren Abstimmungen folgt nicht automatisch, dass genau der gemeinsame Fallkontext der dominante Engpass ist.
- Suche, aktive Bearbeitung, fachlich notwendige Klärung und organisatorische Wartezeit werden noch nicht getrennt. Dadurch bleibt offen, ob Datenzugriff, Übergabequalität, Kapazität, Zuständigkeit, Fristen oder tatsächliche fachliche Komplexität den größten Anteil ausmachen.

Unbekannte Fakten werden für die Prozessleistung transparent benannt. Zusätzlich offen bleiben insbesondere Fallvolumen und Fallsegmente, SLA- beziehungsweise Kundenauswirkung, Anteil vermeidbarer gegenüber fachlich notwendiger Schleifen, heutige Funktionen des Ticketsystems sowie Aufwand und Akzeptanz der vorgesehenen Fallakte.

### Lösungsalternativen und bevorzugte Lösung

Es werden mehrere Lösungstypen einschließlich organisatorischem Pilot, Standardsoftware, Individualsoftware, Analytics und GenAI betrachtet. Das ist technologieoffen und verhindert eine künstliche KI-Pflicht.

Die Alternativen sind aber nicht vollständig als echte, vergleichbare Optionen ausgearbeitet. Klärungsstandard, organisatorischer Pilot und Analytics sind zugleich Bestandteile oder Vorstufen des bevorzugten regelbasierten Workflows; Standard-Case-Management, individuelles Fallcockpit und eine mögliche Erweiterung des vorhandenen Ticketsystems überschneiden sich funktional. Zudem fehlen unterschiedliche Lösungsansätze je Ursachenhypothese, etwa eine reine Verbesserung der Erfassung, verbindliche Zuständigkeits- und Eskalationsregeln, bessere Wissensauffindbarkeit oder Kapazitätsmaßnahmen. Ein expliziter Vergleich anhand nachgewiesener Engpasswirkung, Umsetzungsaufwand, Risiko und Reversibilität liegt nicht vor.

Der „regelbasierte Workflow mit Fallakte und Messung“ ist aus der angenommenen Diagnose plausibel ableitbar und durch Pilotvorbehalt sowie Prüfung vorhandener Funktionen sinnvoll abgesichert. Belastbar ausgewählt ist er noch nicht: Gerade die Messung soll erst zeigen, welche Ursachen tatsächlich relevant sind. Methodisch wäre daher ein Diagnose- und Prozesspilot als nächster Schritt robuster als die bereits relativ konkrete Festlegung auf eine Fallakte mit Workflow.

### Non-AI-Abschluss

Der Non-AI-Abschluss ist fachlich plausibel. Verantwortung, Fristen, Routing und strukturierte Übergaben sind primär Prozess- und Workflowfragen; für eine KI-first-Entscheidung fehlen belastbare Daten zu Suchaufwand, Dokumentqualität, Zugriffsrechten und Qualitätsanforderungen.

Zu absolut ist dagegen die Aussage, es sei „kein KI-Use-Case entstanden“. Die vorliegende Evidenz rechtfertigt, derzeit keinen KI-Use-Case zu bevorzugen, aber noch keinen dauerhaften Ausschluss. Falls die Messung einen erheblichen Anteil an Dokumentensuche, Fallähnlichkeit, Zusammenfassung oder Antwortvorbereitung bestätigt, könnte eine eng begrenzte Assistenz auch ohne vollständig perfektionierte Fallakte prüfenswert sein. Das fachlich saubere Ergebnis lautet daher: **kein hinreichend begründeter KI-first-Use-Case im aktuellen Erkenntnisstand; erneute Prüfung nach Baseline und Ursachenvalidierung.**

## Einordnung der dokumentierten Findings

| Finding | Einfluss auf die fachliche Qualität | Einordnung |
| --- | --- | --- |
| Evidenzbereich zeigt „Bestätigt“, obwohl keine Ursache bestätigt ist | Hoch: Hypothesen können fälschlich als gesicherte Diagnose gelesen und zur Lösungsbegründung verwendet werden. | Methodik-/Auditabilitätsproblem mit Produktursprung |
| Nicht bevorzugte Optionen werden als „Verworfen“ bezeichnet | Mittel bis hoch: reversible oder spätere Ergänzungen, insbesondere GenAI, werden semantisch zu endgültig geschlossen. | Entscheidungs- und Methodikproblem mit Produktursprung |
| Größenlimit bei „Antworten analysieren“ und anschließende manuelle Doppeleingabe | Indirekt relevant: Übertragungs-, Kürzungs- und Konsistenzrisiko; im Bericht ist kein konkreter fachlicher Informationsverlust nachgewiesen. | Primär UX-/Produktproblem |
| Widersprüchliche nächste Aktion nach gespeicherter Fokuswahl | Kein erkennbarer Einfluss auf das erzielte fachliche Ergebnis, kann aber Fehlbedienung oder Wiederholung begünstigen. | Primär UX-/Produktproblem |
| Auswahloberfläche bleibt nach Entscheidung erneut aktiv | Kein erkennbarer Einfluss auf die dokumentierte Entscheidung, schwächt aber Zustandsklarheit und Auditgefühl. | Primär UX-/Produktproblem |
| Screenshot `AET-R01-01-discovery-complete.jpg` ist nicht visuell auswertbar | Hoch für die Nachprüfbarkeit: Der behauptete Abschlusszustand kann anhand des freigegebenen Belegs nicht kontrolliert werden. | Artefakt-/Evidenzproblem |
| Screenshot `AET-R01-02-solution-selection.jpg` zeigt eine GitHub-Repositoryansicht statt der Lösungsauswahl | Hoch für die Nachprüfbarkeit: bevorzugte Lösung, Non-AI-Ausgang und die dazu berichteten UI-Zustände werden visuell nicht belegt. | Artefakt-/Evidenzproblem |

## Wichtigste fachliche Risiken und Lücken

1. Der fehlende gemeinsame Fallkontext wird kausal stärker behauptet, als es die dokumentierte Evidenz erlaubt.
2. Die Fokusphase ist plausibel, aber nicht im Vergleich zum übrigen Value Stream priorisiert oder mit Fall- und Zeitdaten belegt.
3. Die bevorzugte Lösung bündelt bereits Prozessstandard, Fallakte, Workflow und Messung, bevor die offenen Ursachenhypothesen validiert sind.
4. Die Lösungsalternativen überlappen und werden nicht anhand einheitlicher, evidenzbasierter Entscheidungskriterien verglichen.
5. Der Non-AI-Entscheid ist für den aktuellen Stand tragfähig, der generelle KI-Abschluss sollte jedoch ausdrücklich vorläufig bleiben.
6. Die beiden freigegebenen Screenshots belegen weder Discovery-Abschluss noch Lösungsauswahl; dadurch bleiben mehrere Run- und UI-Aussagen ausschließlich Selbstauskunft des Berichts.
