# AET-R01 – Service-Discovery im After Sales

## Run-Metadaten

- **Run-ID:** R01
- **Datum:** 14.09.2026
- **Rolle:** Business Owner
- **Ausgangsunternehmen:** Mittelständischer Maschinenbauer, ca. 650 Mitarbeitende
- **Bereich:** After Sales / Service
- **Run-Status:** Erfolgreich
- **Journey-Ausgang:** Kein KI-Use-Case erforderlich
- **Diagnosehinweis:** Der ursprüngliche Run dokumentiert das fachliche Ergebnis und sichtbare Findings. Die nachgelagerte technische Diagnose der fünf beauftragten Findings ist in Abschnitt 9 ergänzt; Produktänderungen wurden dabei nicht vorgenommen.

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

## 9. Technische Diagnose der Findings

Die Diagnose basiert auf dem Produktcode und den vorhandenen Tests des Branches `issue-429-agentic-runs`. Es wurden keine Produktänderungen, Fixes oder neuen Tests vorgenommen.

### 9.1 Falsche Next Action nach gespeicherter Fokuswahl

**Relevante Code-Stellen**

- `ki_radar/architecture/stage_focus_views.py:47-63` speichert die `StageFocusDecision` und leitet auf den Value Stream zurück.
- `ki_radar/use_cases/value_stream_journey.py:169-185` ersetzt bei aktivem Value Stream mit Phasen, aber ohne Prozessanalyse, den aktuellen Prozessschritt durch die Fokusauswahl.
- `ki_radar/use_cases/value_stream_journey.py:81-104` setzt dabei fest `action_label="Fokusphase auswählen"` und verlinkt nur auf den Phasenabschnitt.
- `templates/architecture/value_stream_detail.html:192-199` wertet die gespeicherte Fokusentscheidung für die einzelne Phasenkarte dagegen korrekt aus und zeigt für die ausgewählte Phase „Prozess im Detail analysieren“.

**Technische Ursache**

Die Bedingung in `build_value_stream_journey()` prüft `has_stages`, `not has_analysis`, den aktiven Value Stream und einen aktuellen Prozessschritt, aber nicht, ob `value_stream.stage_focus_decision` bereits existiert. Solange noch keine Prozessanalyse angelegt ist, überschreibt `_guide_focus_stage_selection()` deshalb die prominente Next Action auch nach erfolgreicher Fokuswahl. Journey-Navigation und Phasenkarte leiten ihren Zustand aus unterschiedlichen Bedingungen ab.

**Erwartetes vs. tatsächliches Verhalten**

- Erwartet: Nach gespeicherter Fokusentscheidung führt die prominente Next Action zur Prozessdetailanalyse der gewählten Phase.
- Tatsächlich: Bis zur Anlage einer ersten Prozessanalyse bleibt die prominente Next Action „Fokusphase auswählen“; nur die gewählte Phasenkarte bietet den korrekten Einstieg.

**Vorhandene Tests**

- `tests/test_issue_58_value_stream_next_action.py:84-93` erwartet „Fokusphase auswählen“ für einen aktiven Value Stream ohne `StageFocusDecision`.
- `tests/test_issue_58_value_stream_next_action.py:133-147` prüft die Seite ebenfalls nur vor einer Phasenauswahl.
- Ein Test für den Zustand „`StageFocusDecision` vorhanden, aber noch keine `ProcessAnalysis` vorhanden“ fehlt.

**Einordnung:** **Bug.** Die gespeicherte Zustandsänderung wird von der zentralen Next-Action-Logik nicht berücksichtigt.

### 9.2 Status „Bestätigt“ bei ausdrücklich nicht bestätigter Ursache

**Relevante Code-Stellen**

- `ki_radar/architecture/models.py:147-150` modelliert Hypothese und bestätigte Ursache als zwei optionale Freitextfelder; ein eigener Bestätigungsstatus existiert nicht.
- `ki_radar/architecture/forms.py:327-335` weist lediglich per Hilfetext darauf hin, in `confirmed_causes` nur bestätigte Ursachen einzutragen.
- `templates/architecture/includes/process_findings_summary.html:18-24` zeigt für jede nicht leere `cause_hypotheses` den Hypothesen-Badge und für jeden nicht leeren Wert in `confirmed_causes` pauschal den Badge „Bestätigt“.

**Technische Ursache**

Das Template verwendet ausschließlich die Leer-/Nicht-leer-Prüfung des Freitextfelds. Ein Satz wie „Keine Ursache wurde bestätigt“ ist technisch ein befülltes Feld und löst daher denselben Badge aus wie eine tatsächlich bestätigte Ursache. Der Code interpretiert keine Negation und hat kein strukturiertes Merkmal, mit dem Inhalt und Bestätigungsstatus getrennt werden könnten.

**Erwartetes vs. tatsächliches Verhalten**

- Erwartet: Eine ausdrücklich als unbestätigt dokumentierte Aussage darf nicht als „Bestätigt“ gekennzeichnet werden; ohne bestätigte Ursache sollte das Feld leer bleiben beziehungsweise „Noch nicht bestätigt“ erscheinen.
- Tatsächlich: Jeder nicht leere Inhalt des Felds `confirmed_causes` erhält den Badge „Bestätigt“, unabhängig von seiner Aussage.

**Vorhandene Tests**

- `tests/test_issue_318_diagnosis_integration.py:225-242` prüft die getrennte Anzeige der Diagnosefelder, aber nicht die Badge-Semantik bei negierendem Inhalt.
- `tests/test_issue_318_diagnosis_integration.py:245-260` prüft, dass ohne offene Hypothese kein Hypothesen-Badge erscheint; dabei ist tatsächlich eine bestätigte Ursache befüllt.
- `tests/test_issue_318_diagnosis_readiness.py:267-279` prüft optionale Felder und Hilfetexte.
- Ein Test mit einem negierenden Text in `confirmed_causes` fehlt.

**Einordnung:** **UX-Semantik.** Die Anzeige folgt der vorgesehenen Feldsemantik, kann aber widersprüchliche Freitexte nicht abbilden und erzeugt dadurch eine fachlich falsche Kennzeichnung.

### 9.3 Pauschale Bezeichnung nicht bevorzugter Lösungen als „Verworfen“

**Relevante Code-Stellen**

- `ki_radar/architecture/models.py:218-253` definiert nur die Empfehlungszustände `candidate`, `preferred` und `rejected`; der Anzeigename von `rejected` ist „Verworfen“.
- `ki_radar/architecture/solution_selection.py:149-163` setzt bei jeder Auswahl sämtliche aktiven, nicht ausgewählten Optionen per Sammelupdate auf `REJECTED` und die gewählte Option auf `PREFERRED`.
- `ki_radar/architecture/solution_retirement.py:33-44` verwendet denselben Status `REJECTED` auch für eine ausdrücklich nicht weiterverfolgte Option, unterscheidet aktive Optionen aber separat über einen Retirement-Datensatz.
- `templates/architecture/solution_option_compare.html:77` und `templates/architecture/process_analysis_detail.html:207-210` zeigen den Modell-Anzeigenamen unverändert an.
- `templates/architecture/solution_option_compare.html:104-110` kündigt dieses Verhalten ausdrücklich an: Die gewählte Option wird bevorzugt, die übrigen werden verworfen.

**Technische Ursache**

Das Domänenmodell kennt keinen Zustand wie „derzeit nicht bevorzugt“, „zurückgestellt“ oder „spätere Ergänzung“. Der Auswahlservice bildet eine Präferenzentscheidung bewusst als binäre Trennung in eine bevorzugte und ausschließlich verworfene Restmenge ab. Zusätzlich bezeichnet `REJECTED` sowohl eine weiterhin aktive, nur nicht gewählte Alternative als auch eine separat ausgemusterte Option. Die pauschale Bezeichnung ist daher keine zufällige Template-Ausgabe, sondern persistiertes, beabsichtigtes Verhalten mit zwei fachlich unterschiedlichen Bedeutungen.

**Erwartetes vs. tatsächliches Verhalten**

- Erwartet aus dem Run-Kontext: Eine weiterhin plausible spätere Ergänzung bleibt als nicht bevorzugt oder zurückgestellt erkennbar.
- Tatsächlich: Jede aktive Alternative außer der aktuell gewählten wird als `rejected` gespeichert und bis zu einer möglichen späteren Neuauswahl überall als „Verworfen“ angezeigt; aus dem Status allein ist eine echte Ausmusterung nicht unterscheidbar.

**Vorhandene Tests**

- `tests/test_solution_option_comparison.py:297-338` erwartet ausdrücklich `REJECTED` für die nicht gewählte organisatorische Option und `PREFERRED` für die gewählte Assistenz.
- `tests/test_solution_selection_ux.py:128-165` bestätigt dasselbe Verhalten über den UI-POST und die anschließende Ergebnisanzeige.
- Es gibt keinen Test und keinen Modellzustand für „nicht bevorzugt, aber weiterhin valide/später prüfbar“.

**Einordnung:** **UX-Semantik.** Das Verhalten ist im aktuellen Modell und in den Tests beabsichtigt, die Semantik ist für nicht endgültig ausgeschlossene Alternativen jedoch zu absolut.

### 9.4 Größenlimit bei „Antworten analysieren“

**Relevante Code-Stellen**

- `config/settings/base.py:212-220` setzt `ACCELERATOR_LLM_MAX_INPUT_CHARS` standardmäßig auf 12.000 Zeichen; die Einstellung kann je Umgebung überschrieben werden.
- `ki_radar/core/llm_policy.py:43-53` validiert für diese Einstellung einen Bereich von 1 bis 100.000 Zeichen; `ki_radar/core/llm_policy.py:177-193` übernimmt den effektiven Wert in die Accelerator-Policy.
- `ki_radar/accelerator/analysis_service.py:108-134` baut aus allen beantworteten Fragen einschließlich Labels, IDs und Zielpfaden das Analyseobjekt.
- `ki_radar/accelerator/analysis_service.py:247-258` serialisiert dieses Objekt, addiert den System-Prompt und bricht bei `input_chars > policy.max_input_chars` mit `input_too_large` und der im Run sichtbaren Meldung ab.
- `ki_radar/accelerator/views.py:340-342` aktiviert die Analyse allein anhand des abgeschlossenen Session-Status und eines verfügbaren Katalogs. Die Größe wird vor Anzeige der Aktion nicht geprüft.
- `templates/accelerator/capture_review.html:69-83` nennt nur eine begrenzte Anzahl von Analyseanfragen, aber weder Zeichenzahl noch Grenzwert oder verbleibenden Spielraum.
- `ki_radar/accelerator/views.py:349-363` fängt den Fehler ab, zeigt die Meldung und leitet unverändert auf die Review-Seite zurück.

**Technische Ursache**

Der Schutzmechanismus begrenzt nicht nur die sichtbaren Antworten, sondern die Länge von System-Prompt plus kompaktem JSON mit Antwort- und Katalogmetadaten. Überschreitet dieser Gesamtwert die effektive Konfiguration, wird die Analyse vor Provideraufruf, Quotenreservierung und Anlage eines `CaptureAnalysis`-Datensatzes abgebrochen. Da die Review-Seite keine identische Vorberechnung ausführt, bleibt das Überschreiten bis zum Klick unsichtbar. Der effektive Wert der Laufzeitumgebung des ursprünglichen Runs lässt sich aus dem Repository allein nicht bestimmen; die eindeutige Fehlermeldung stammt jedoch genau aus dieser Prüfung.

**Erwartetes vs. tatsächliches Verhalten**

- Erwartet: Überlange Eingaben werden kontrolliert abgefangen; der nutzbare Grenzwert beziehungsweise eine drohende Überschreitung ist vor dem Analyseversuch erkennbar.
- Tatsächlich: Der kontrollierte Abbruch funktioniert, wird aber erst nach dem Klick sichtbar. Ein unveränderter Wiederholungsversuch trifft deterministisch dieselbe Prüfung.

**Vorhandene Tests**

- `tests/test_capture_analysis_service.py:74-83` erzwingt ein zu kleines Limit und prüft `input_too_large` sowie, dass keine Quote verbraucht wird.
- `tests/test_accelerator_llm.py:57-80` prüft das Einlesen und die gültigen Grenzen der Policy-Konfiguration.
- `tests/test_capture_analysis_views.py:104-124` prüft allgemein, dass Analysefehler zur Review-Seite zurückführen und eine frühere erfolgreiche Analyse erhalten bleibt.
- Ein UI-Test für Vorwarnung, Größenanzeige oder Deaktivierung der Aktion bei zu großer Eingabe fehlt.

**Einordnung:** **erwartetes Verhalten** für den technischen Schutzmechanismus; die fehlende Vorabtransparenz ist eine UX-Lücke.

### 9.5 Notwendige Doppeleingabe nach fehlgeschlagener Analyse

**Relevante Code-Stellen**

- `ki_radar/accelerator/analysis_service.py:253-278` prüft das Eingabelimit, bevor ein Analyselauf oder Feldvorschläge angelegt werden.
- `ki_radar/accelerator/views.py:349-363` bietet im Fehlerfall nur die Rückleitung auf die unveränderte Review-Seite.
- `ki_radar/accelerator/services.py:107-109` und `ki_radar/accelerator/services.py:179-212` machen eine abgeschlossene Capture Session absichtlich unveränderlich.
- `templates/accelerator/capture_review.html:25-50` zeigt die gespeicherten Antworten weiterhin lesbar an, bietet bei abgeschlossener Session aber keinen Bearbeitungs- oder Übernahmepfad.
- `templates/accelerator/analysis_detail.html:58-100` macht Feld- und strukturierte Vorschläge nur aus einer vorhandenen Analyse zugänglich.
- `templates/accelerator/_adoption_controls.html:32-63` erlaubt eine direkte oder bearbeitete Übernahme nur für bereits erzeugte Vorschlagskandidaten.

**Technische Ursache**

Die Übernahme in reguläre Fachobjekte ist vollständig an erfolgreich erzeugte Analysevorschläge gekoppelt. Beim Größenfehler entsteht wegen des frühen Abbruchs weder ein Analysedatensatz noch ein Vorschlag, aus dem der Adoption-Flow arbeiten könnte. Die Originalantworten gehen nicht verloren, bleiben nach Abschluss aber schreibgeschützt und können nur abgelesen werden. Es existiert kein deterministisches Mapping, kein Teilanalyse-/Chunking-Pfad und kein Fallback, der die Capture-Antworten in reguläre Eingabeformulare vorbefüllt. Deshalb muss der Inhalt für den manuellen Produktpfad erneut übertragen werden.

**Erwartetes vs. tatsächliches Verhalten**

- Erwartet: Nach einem kontrollierten Analysefehler bleiben die Eingaben nicht nur erhalten, sondern können ohne erneute vollständige Eingabe weiterverwendet oder gezielt gekürzt werden.
- Tatsächlich: Die Antworten bleiben lesbar erhalten, aber der einzige Übernahmepfad setzt eine erfolgreiche Analyse voraus; nach `input_too_large` bleibt nur Wiederholen mit unverändertem Ergebnis oder manuelle Neuerfassung im regulären Produktpfad.

**Vorhandene Tests**

- `tests/test_capture_session_services.py:162-199` prüft, dass abgeschlossene Sessions vollständig und irreversibel sind und nicht weiter bearbeitet werden können.
- `tests/test_block4_completion.py:213-248` prüft bei einem Providerfehler, dass Antworten und frühere erfolgreiche Vorschläge erhalten bleiben, keine Teilvorschläge und keine Fachobjekte entstehen.
- `tests/test_capture_analysis_views.py:104-124` prüft Rückleitung und Erhalt einer früheren erfolgreichen Vorschau.
- Es gibt keinen Test für einen manuellen Fallback, Vorbefüllung aus den Originalantworten, Teilanalyse oder Kürzung nach `input_too_large`.

**Einordnung:** **UX-Semantik.** Es liegt kein Datenverlust und kein fehlerhafter Abbruch vor, sondern eine fehlende Recovery- und Übergabemöglichkeit im vorgesehenen Workflow.

### 9.6 Prüfstatus

Die genannten Tests wurden im Quellstand identifiziert und inhaltlich geprüft. Eine lokale Testausführung war in der bereitgestellten Umgebung nicht möglich, weil das verfügbare Python keine Django-Abhängigkeit enthält (`ModuleNotFoundError: No module named 'django'`). Es wurden bewusst keine Abhängigkeiten installiert und keine Test- oder Produktdateien verändert.

## 10. Screenshots

- [Discovery als abgeschlossen markiert](screenshots/AET-R01-01-discovery-complete.jpg)
- [Bevorzugte Lösung und Non-AI-Journey-Ausgang](screenshots/AET-R01-02-solution-selection.jpg)

## 11. Abschluss

**Run-Status: erfolgreich.** Der sichtbare Discovery-Pfad wurde fachlich abgeschlossen. Es gab weder einen Produktabbruch noch einen Agent- oder Toolabbruch.
