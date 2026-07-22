# KI-Radar Produkt-Roadmap

**Stand:** 22.07.2026  
**Status:** verbindliche fachliche Reihenfolge, kein Terminversprechen  
**Pflege:** Nach jedem relevanten Merge werden Status, Datum und nächster verbindlicher Umfang aktualisiert.

## Legende

- `[x]` umgesetzt und auf `main` enthalten
- `[ ]` geplant oder noch nicht vollständig geschlossen
- **Grundlage vorhanden:** Teilfunktionen oder Datenfelder existieren bereits, der fachliche Ablauf ist aber noch nicht durchgängig abgeschlossen

## Produktgrenze

KI-Radar ist ein Portfolio-, Governance- und Entscheidungs-Cockpit für KI-Vorhaben. Es ersetzt kein operatives Projektmanagement- oder Delivery-System.

**Externes Delivery-System bleibt führend für:**

- Backlog, Tasks, Sprints und technische Detailprobleme
- tägliche Maßnahmen, Ressourcen und operativen Fortschritt
- Release-, Incident-, Change- und Service-Steuerung

**KI-Radar bleibt führend für:**

- fachliche Herkunft, Nutzenhypothese und Erfolgsmetriken
- Governance, Bewertung, Freigabe und Auflagen
- Delivery Readiness und verbindliche Übergabe
- entscheidungsrelevante Review-Snapshots
- Folgeentscheidungen, Ownership und Abschluss

Der erste Rückfluss aus Jira, Azure DevOps, GitHub oder einem anderen Delivery-System erfolgt bewusst **manuell zum Review-Termin**. Eine Live-Synchronisation ist kein aktueller Umfang.

---

## 1. Bereits umgesetzt

### 1.1 Discovery, Fokus und Business Architecture

- [x] **22.07.2026:** Fachdomänen und Business Capabilities
- [x] **22.07.2026:** End-to-End-Value-Streams und geordnete Phasen
- [x] **22.07.2026:** Fokus-Screening nach Impact, Potenzial, Problemintensität, Datenzugänglichkeit und Veränderungsaufwand
- [x] **22.07.2026:** serverseitiges Gate vor dem Prozess-Deep-Dive
- [x] **22.07.2026:** Prozessanalyse mit Rollen, Systemen, Datenobjekten, Bottlenecks und Baselines
- [x] **22.07.2026:** Vergleich organisatorischer, regelbasierter, technischer und KI-gestützter Lösungsoptionen
- [x] **22.07.2026:** nachvollziehbare Herkunftskette über `UseCaseOrigin`

### 1.2 Use Case, Bewertung und Freigabe

- [x] **22.07.2026:** direkter und systematisch abgeleiteter Use-Case-Intake
- [x] **22.07.2026:** Nutzenhypothese, Baseline, Zielwert und primäre Erfolgsmetrik
- [x] **22.07.2026:** versionierte Bewertungen
- [x] **22.07.2026:** Governance-, Datenschutz-, Security- und Rechtsprüfungen
- [x] **22.07.2026:** getrennte Bewertung und finale Freigabe
- [x] **22.07.2026:** deterministische serverseitige Hard Gates
- [x] **22.07.2026:** Portfolio- und Entscheidungsansichten mit konkreten Next Actions

### 1.3 Delivery Readiness und Übergabe

- [x] **22.07.2026:** versioniertes Delivery Package nach final positiver Freigabe
- [x] **22.07.2026:** System-, Daten-, Integrations- und Architekturkontext
- [x] **22.07.2026:** MVP-Scope, Anforderungen, Akzeptanzkriterien, Tests und Messplan
- [x] **22.07.2026:** Risiken, Annahmen, Abhängigkeiten und Architekturentscheidungen
- [x] **22.07.2026:** Statusfolge `Entwurf → Bereit zur Übergabe → Übergeben`
- [x] **22.07.2026:** übergebene Package-Versionen sind unveränderlich
- [x] **22.07.2026:** Link zum externen Delivery-System

### 1.4 Geführte Journey und Arbeitsräume

- [x] **22.07.2026:** zentrale `JourneyState`-/`JourneyStep`-Logik
- [x] **22.07.2026:** stabile Hauptleiste für Auswahl und Freigabe
- [x] **22.07.2026:** zweiter Arbeitsraum `Wirkung & Betrieb`
- [x] **22.07.2026:** Variante A als verbindliche Navigation: `Übergabe → Pilot → Wirkung → Ergebnisentscheidung → Betrieb → Abschluss`
- [x] **22.07.2026:** sichtbare Verantwortungsgrenze zwischen KI-Radar und externem Delivery-System
- [x] **22.07.2026:** responsive Desktop- und Mobile-Darstellung ohne horizontale Seitenüberläufe

### 1.5 Lifecycle-Grundlagen

- [x] **22.07.2026:** Lifecycle-Status `Idee`, `Prüfung`, `Pilot`, `Betrieb`, `Beendet`
- [x] **22.07.2026:** Lifecycle-Reviews mit Statuswechseln und Begründung
- [x] **22.07.2026:** Pilotbeginn, geplantes Pilotende und nächster Review-Termin als Datenfelder
- [x] **22.07.2026:** aktueller Ist-Wert, Messzeitraum, Messdatum und Messnachweis als Datenfelder
- [x] **22.07.2026:** technische Verantwortung, Support-Verantwortung und Kostenfelder
- [x] **22.07.2026:** Beendigungsgrund, Daten- und Zugangsbehandlung, Lessons Learned und Ersatzlösung
- [x] **22.07.2026:** geschlossener Übergang `Prüfung → Pilot` nur nach verbindlicher Übergabe der aktuellsten Delivery-Package-Version
- [x] **22.07.2026:** separate Next Action `Pilot starten`; die Delivery-Übergabe startet den Pilot nicht automatisch
- [x] **22.07.2026:** Pilotstart ausschließlich durch `KI-Koordinator` oder den zuständigen Benutzer mit Rolle `Business Owner`
- [x] **22.07.2026:** tatsächlicher Pilotbeginn als Pflichtdatum, nicht zukünftig und nicht vor `handed_over_at`
- [x] **22.07.2026:** atomare Speicherung von Pilotbeginn, Statuswechsel und Lifecycle-Review
- [x] **22.07.2026:** Golden-Path-Test vom Value Stream bis zum Pilotstart einschließlich serverseitiger Negativ- und Manipulationstests
- [x] **22.07.2026:** Browserabnahme der Pilotstart-Next-Action auf Desktop und Mobile ohne horizontalen Seitenüberlauf
- [ ] ein einzelner getesteter Use Case vom Value Stream bis zum Abschluss
- [ ] versionierte Messungen und Wirkungsreviews
- [ ] persistierte Scale-/Continue-/Stop-Entscheidung

---

## 2. Nächster verbindlicher Umfang

### Golden Path bis zum Abschluss

**Status am 22.07.2026:** geplant, noch nicht umgesetzt.

- [ ] denselben Use Case von Value Stream und Fokus bis Delivery, Pilot, Betrieb und Abschluss führen
- [ ] Go-live ohne Messwert oder Messnachweis serverseitig blockieren
- [ ] bei verfehltem Ziel eine ausdrücklich bestätigte Ausnahme verlangen
- [ ] Abschluss ohne Beendigungsgrund und Daten-/Zugangsbehandlung blockieren
- [ ] Demo-Szenario und E2E-Test für den vollständigen Lebenszyklus ergänzen

**Nicht Bestandteil dieses Inkrements:**

- neues versioniertes Wirkungsmessungsmodell
- Jira-/Azure-DevOps-Synchronisation
- Messzeitreihen
- lernendes System

Erst nach Abschluss und Abnahme dieses Inkrements wird der nächste Roadmap-Punkt begonnen.

---

## 3. Geplante Folgeinkremente

Die Reihenfolge ist verbindlich, solange keine dokumentierte Produktentscheidung sie ändert.

### 3.1 Versionierte Wirkungsmessungen

- [ ] Messwert und Zeitpunkt versioniert speichern
- [ ] Zeitraum, Stichprobengröße und betrachtete Population speichern
- [ ] Messmethode und Methodenversion speichern
- [ ] Datenqualität und Confidence dokumentieren
- [ ] Nachweisquelle verknüpfen
- [ ] Verlauf statt Überschreiben eines einzelnen Ist-Werts ermöglichen

### 3.2 Versionierte Wirkungsreviews

- [ ] quantitative und qualitative Ergebnisse bündeln
- [ ] Probleme, Nebenwirkungen und Nutzerfeedback strukturiert erfassen
- [ ] offene Governance-Auflagen übernehmen
- [ ] Confidence der Ergebnisbewertung dokumentieren
- [ ] Empfehlung und tatsächliche Folgeentscheidung miteinander verknüpfen

### 3.3 Strukturierte Ergebnisentscheidung

- [ ] kontrollierte Entscheidungstypen einführen:
  - skalieren
  - Pilot verlängern
  - nachbessern
  - begrenzt betreiben
  - produktiv setzen
  - pausieren
  - beenden
- [ ] Begründung, Entscheider, Zeitpunkt und Bedingungen speichern
- [ ] erwarteten nächsten Effekt und nächsten Review festlegen
- [ ] Entscheidung versionieren und auditierbar machen

### 3.4 Lifecycle-Event-Log

- [ ] Ereignistyp, alten und neuen Status speichern
- [ ] Zeitpunkt und Akteursrolle speichern
- [ ] Entscheidungsgrund, Blocker und Warnungen erfassen
- [ ] verwendete Bewertungs-, Evidenz- und Review-Version referenzieren
- [ ] Time-to-Value und Verweildauer je Phase ableitbar machen

### 3.5 Verdichtete Delivery-Ergebnisse

- [ ] geplanten und tatsächlichen Start sowie Abschluss speichern
- [ ] geplante und tatsächliche Delivery-Dauer vergleichen
- [ ] Pilotumfang und erreichte Akzeptanzkriterien erfassen
- [ ] Defekt-/Fehlerquote und wesentliche Scope-Änderungen dokumentieren
- [ ] tatsächliche Einmal- und Betriebskosten speichern
- [ ] Releases oder produktive Versionen auf Managementebene referenzieren

### 3.6 Nutzung und Adoption

- [ ] berechtigte und aktive Nutzer erfassen
- [ ] Nutzungshäufigkeit und Abbruchquote erfassen
- [ ] Human-Override-Quote erfassen
- [ ] Nutzerzufriedenheit dokumentieren
- [ ] Zeit bis zur produktiven Nutzung ableiten

### 3.7 Optionale Integration externer Delivery-Systeme

- [ ] erst nach stabiler manueller Review-Strecke bewerten
- [ ] nur verdichtete, entscheidungsrelevante Daten übernehmen
- [ ] keine doppelte Task-, Sprint- oder Maßnahmenpflege erzeugen
- [ ] Jira, Azure DevOps oder GitHub nicht als führendes Delivery-System ersetzen
- [ ] Synchronisationsquelle, Aktualität und Konfliktbehandlung sichtbar machen

### 3.8 Grundlage für ein später lernendes System

- [ ] eindeutige versionierte Feature-Snapshots definieren
- [ ] kontrollierte Kategorien statt freier Personennamen als Lernmerkmale verwenden
- [ ] verworfene, pausierte und gescheiterte Vorhaben mit Gründen erhalten
- [ ] Zielgrößen definieren:
  - Zielerreichung
  - Time-to-Value
  - realisierter Nutzen
  - Kostenabweichung
  - Adoption
  - nachhaltiger Betrieb
  - Abbruch- oder Erfolgsgrund
- [ ] Datenqualitäts- und Bias-Prüfungen vor Modellentwicklung durchführen
- [ ] erst danach Empfehlungen, Prognosen oder Ähnlichkeitsanalysen evaluieren

Ein späteres Modell darf keine Freigaben oder Lifecycle-Entscheidungen autonom auslösen. Es kann Muster, Risiken und vergleichbare historische Fälle sichtbar machen.

---

## 4. Daten, die langfristig erhalten bleiben müssen

Für spätere Auswertungen und Lernverfahren sind nicht nur erfolgreiche Fälle relevant.

- [x] fachlicher Kontext, Organisationseinheit, Fachdomäne und Capability
- [x] Value-Stream-Fokusmerkmale, Prozesse, Systeme, Daten und Bottlenecks
- [x] verglichene und verworfene Lösungsoptionen
- [x] Nutzenhypothese, Baseline, Ziel und primäre Erfolgsmetrik
- [x] Bewertungen, Confidence-Faktoren, Governance-Prüfungen und Freigaben
- [x] versionierte Delivery Packages und Architekturentscheidungen
- [x] Lifecycle-Reviews, Maßnahmen und Abschlussinformationen
- [ ] versionierte Messreihen
- [ ] versionierte Wirkungsreviews und Ergebnisentscheidungen
- [ ] verdichtete Delivery-, Adoptions- und Betriebsdaten
- [ ] strukturierte Gründe für Erfolg, Nachbesserung, Pause und Beendigung

Personennamen, sensible Rohdaten und unstrukturierte Dokumentinhalte sollen nicht als Lernmerkmale verwendet werden. Geeignet sind pseudonymisierte Rollen, kontrollierte Kategorien, versionierte Merkmals-Snapshots und klar definierte Zielgrößen.

---

## 5. Pflege- und Umsetzungsregeln

1. Vor neuen Produktänderungen diese Roadmap und relevante ADRs lesen.
2. Nur der unter **Nächster verbindlicher Umfang** beschriebene Punkt darf ohne neue Produktentscheidung begonnen werden.
3. Folgeinkremente nicht vorziehen oder in einen großen PR bündeln.
4. Jeder PR besitzt einen klaren Scope und explizite Nicht-Ziele.
5. Nach einem Merge werden erledigte Checkboxen, Datum und nächster Umfang aktualisiert.
6. Änderungen der Systemgrenze oder Roadmap-Reihenfolge werden im PR begründet und bei Bedarf als ADR dokumentiert.
7. `OPEN_QUESTIONS.md` bleibt für ungeklärte Betriebs- und Konfigurationsfragen; die Produktreihenfolge steht hier.

## 6. Festgelegte Entscheidungen vom 22.07.2026

- Variante A ist die verbindliche Navigation für `Wirkung & Betrieb`.
- KI-Radar bleibt Entscheidungs-Cockpit und kein operatives Delivery-System.
- Der erste Rückfluss aus Delivery erfolgt als manueller Review-Snapshot.
- `JourneyState` bleibt die zentrale Status- und Next-Action-Logik.
- Der nächste Implementierungsumfang ist ausschließlich der Golden Path desselben Use Cases bis Betrieb und Abschluss einschließlich der vorhandenen Go-live- und Abschluss-Gates.
