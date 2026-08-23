# KI-Radar Execution Plan

**Stand:** 22.08.2026  
**Zweck:** Konkrete Abarbeitungsreihenfolge offener Issues nach fachlichen und technischen Abhängigkeiten.

## Leitprinzip

Dieser Plan beantwortet nicht, welches Thema laut Produkt-Roadmap grundsätzlich wichtiger ist, sondern **in welcher Reihenfolge die offenen Arbeitspakete sinnvoll umgesetzt werden sollten, um Rework zu vermeiden**.

Entscheidend sind insbesondere:

- zuerst Domain-, Journey- und Entscheidungssemantik stabilisieren;
- danach Funktionen anbauen, die diese Semantik konsumieren;
- API-Verträge erst auf ausreichend stabilen internen Verträgen aufsetzen;
- Analyse-Issues vor nachgelagerten Implementierungen abschließen;
- E2E-Demo erst nach Abschluss des zusammengehörigen fachlichen Blocks durchführen;
- unabhängige Stränge parallelisieren, wenn keine relevante Kopplung besteht.

Die Produkt-Roadmap unter [`../ROADMAP.md`](../ROADMAP.md) bleibt davon getrennt und beschreibt Produktstand und strategische Richtung.

---

## Kürzlich abgeschlossen

**#310 – Reiseveranstalter E2E-Demo und lokale UI-Abnahme** wurde am 23.08.2026 im regulären Browser abgeschlossen. Der Referenzfall wurde vom Value Stream über Fokus, Prozessanalyse und technologieoffenen Lösungsvergleich bis zum bewerteten und governance-seitig vorbereiteten KI-Use-Case durchgeführt. No-AI- und Hybrid-Semantik wurden gegengeprüft; unbekannte Baseline und Zielwerte blieben ohne künstliche Platzhalter offen. Die dabei gefundenen Darstellungs- und Eingabeschärfen wurden als eng begrenzte UI-Korrekturen behoben und regressionsseitig abgesichert.

**#340 – Unbekannte Baseline/Zielwerte im Guided Intake** wurde am 22.08.2026 als fokussierter P1-Fix umgesetzt. Frühe Use Cases können nun ohne erfundene numerische Baseline oder Zielwerte bis zur strukturierten Bewertung aufgenommen werden. Positive Freigaben sowie Pilot-/Go-live-Gates verlangen die relevanten Messwerte weiterhin serverseitig; die Diagnose-Readiness aus #318 blieb unverändert.

**#323 – SIPOC-Leitfrage** wurde am 22.08.2026 als kleines Methodik-/UX-Inkrement umgesetzt. Die bestehende `ProcessAnalysis` zeigt SIPOC nun als kompakten Denk- und Scopingrahmen `Supplier → Input → Process → Output → Customer`. Vorhandene Felder für Daten/Dokumente, Ergebnis sowie Übergaben/Schnittstellen werden weiterverwendet; es entstanden keine neuen SIPOC-Modelle, Pflichtfelder oder Journey-Stufen.

**#331 – Fokuswahl, Evidenz, Time-to-Value und No-AI-Ausgang** wurde am 22.08.2026 abgeschlossen. Damit ist die Discovery-Lösungsentscheidung stabilisiert: hypothesenfähige Fokuswahl, separates Verbesserungspotenzial, persistente Evidenzbasis, Time-to-Value als Trade-off, Hybrid-Semantik und ein gültiger No-AI-Ausgang sind umgesetzt.

**#322 – Ursprungsprozess → Use Case** wurde am 22.08.2026 umgesetzt. Der direkte Intake kann optional eine vorhandene Prozessanalyse als kanonischen Ursprung verwenden; Discovery übernimmt den bereits bekannten Prozess. Phase, Value Stream, strategisches Ziel und vorhandener Fokuskontext werden aus `UseCaseOrigin` und der bestehenden Architecture-Hierarchie abgeleitet statt redundant am Use Case gespeichert. Bestehende Use Cases ohne Ursprung bleiben unverändert gültig.

---

# Aktueller Ablaufplan

| Reihenfolge | Issue | Inhalt | Warum an dieser Stelle? | Geschätzter Aufwand | Komplexität |
|---:|---|---|---|---:|---|
| **1** | **#320 – Delivery-Readiness analysieren** | Prüft `ReadinessFinding → ActionableFinding → Next Action → Bearbeitung` sowie Technical-Owner- und Sektionsstatus-Semantik Ende-zu-Ende. Das Issue ist ausschließlich Analyse und darf selbst keine Codeänderungen enthalten. | Vor #333 und nachgelagerten Verbrauchern klären, ob die Delivery-/Readiness-Semantik noch reale Lücken besitzt. | **0,5–1 Tag** | **mittel** |
| **2** | **ggf. separates Fix-Issue aus #320** | Nur wenn #320 erneut eine echte Lücke nachweist, wird diese in einem separaten Implementierungs-Issue geschlossen. Inhalt und Umfang hängen vom Analyseergebnis ab. | Eine bestätigte Readiness-/Finding-/Action-Lücke sollte vor weiterem Lifecycle-Hardening geschlossen werden. | **0,5–2 Tage*** | **mittel*** |
| **3** | **#333 – Scale Readiness** | Bündelt vorhandene Pilot-, Wirkungs-, Governance-, Delivery- und ML-Test-Score-Nachweise zu einer kompakten Go-live-/Scale-Readiness-Entscheidung zwischen Pilot/Wirkung und Betrieb. | Erst nach der lokalen Kern-Demo und nach Klärung der Delivery-Readiness-Semantik; #333 soll bestehende Gates aggregieren, nicht duplizieren. | **2–4 Tage*** | **hoch*** |
| **4A** | **#330 – Django-Ninja Read-only API** | Ergänzt eine kleine Read-only API für Use Cases und Delivery Readiness mit expliziten Response-Schemas, API-Key und OpenAPI/Swagger. Bestehende Domain-/Readiness-Logik wird wiederverwendet und nicht dupliziert. | Nach stabiler Delivery-Readiness-Semantik, damit der externe API-Contract nicht kurz danach wegen interner Änderungen nachgezogen werden muss. | **1–1,5 Tage / 8–12 h** | **mittel** |
| **4B** | **#325 – KI-Einsatzbereiche analysieren** | Inventarisiert entlang Use Case, Architektur, Delivery, Governance und Reviews, wo KI-Entwürfe, Rückfragen oder Konsistenzprüfungen einen belastbaren Mehrwert liefern und wo nicht. Es findet noch keine Implementierung statt. | Ebenfalls erst nach #320, damit die Analyse nicht auf einer noch wechselnden Delivery-/Finding-Semantik basiert. Kann danach unabhängig von #330 laufen. | **0,5–1 Tag** | **mittel** |
| **5A** | **#326 – UX, Qualität und Wirkungsmessung** | Definiert das wiederverwendbare UX-Muster für Erzeugen, Prüfen, Übernehmen, Verwerfen und Fehlerzustände sowie Qualitäts- und Erfolgsmetriken für KI-Entwürfe. | Baut auf den in #325 identifizierten Aufgabentypen auf und kann danach parallel zu #327 bearbeitet werden. | **0,5–1 Tag** | **mittel** |
| **5B** | **#327 – technische und fachliche KI-Leitplanken** | Definiert Kontextminimierung, Prompt-/Output-Verträge, Provider-Fehler, Tokenbudgets, Datenschutz, Logging, Kosten und Sicherheitsgrenzen für den KI-Rollout. | Ebenfalls nach #325; technische Leitplanken und UX/Messung können anschließend parallel konkretisiert werden. | **1–1,5 Tage** | **mittel–hoch** |
| **6** | **#328 – KI-Rollout konsolidieren** | Führt #325, #326 und #327 zusammen, entscheidet über priorisierte Rollout-Wellen und leitet daraus kleine Implementierungs-Issues ab. | Erst wenn alle drei Analyseergebnisse vorliegen; sonst würden Rollout-Entscheidungen vorweggenommen. | **0,5 Tag** | **niedrig–mittel** |
| **7** | **#307 – optionaler Entscheidungsraum** | Ergänzt für echte strittige Entscheidungen einen zusätzlichen Decision Case mit Perspektiven, Evidenz, Readiness, RAPID/DACI, Constraints und Eskalation. Das ist ein größerer Governance-Subworkflow. | Spät aufsetzen, wenn Use-Case-, Governance-, Next-Action- und Delivery-Semantik stabiler sind; dadurch sinkt das Integrations- und Rework-Risiko. | **5–10 Tage** | **sehr hoch** |

\* Schritte 3 und 4 sind vor ihrem jeweiligen Gap-Check nur Planungswerte.

---

# Abhängigkeitsbild

```text
#331 + #322 + #323 + #340 + #310 abgeschlossen
  ↓
#320 Analyse
  ↓
ggf. separates Fix-Issue
  ↓
#333 Scale Readiness
  ↓
┌───────────────────────────────┐
│ #330 API                      │
│                               │
│ #325 → #326 + #327 → #328    │
└───────────────────────────────┘
  ↓
#307
```

`#330` und der `#325 → #326/#327 → #328`-Strang besitzen nach Abschluss von #320 keine harte gegenseitige Abhängigkeit und können bei Bedarf parallel laufen.

**Demo-/Deployment-Leitlinie:** Die #310-Strecke ist lokal fachlich abgenommen. Render bleibt ein separater Deployment-/Smoke-Check und war kein Bestandteil oder Blocker dieser Abnahme.

---

# Entscheidungsregeln für Änderungen am Plan

1. **Rework vor nomineller Priorität vermeiden.** Wenn Issue B einen Vertrag, Zustand oder Übergang konsumiert, den Issue A noch verändert, kommt A zuerst.
2. **Analyse vor Verbraucher.** Ein reopened Analyse-Issue wird abgeschlossen und ein daraus notwendiges Fix-Issue umgesetzt, bevor abhängige Funktionen darauf aufsetzen.
3. **E2E-Abnahme nach Blockabschluss.** Ein Referenzdurchlauf wird nicht nach jedem kleinen Teilinkrement wiederholt, wenn mehrere direkt zusammengehörige Änderungen unmittelbar folgen.
4. **Explizite API-Verträge schützen.** Interne Modelle dürfen sich ändern; externe API-Contracts sollen möglichst erst nach Stabilisierung der dafür relevanten Domain-Semantik eingeführt werden.
5. **Parallelisierung nur ohne relevante Kopplung.** Unabhängige Stränge dürfen parallel laufen, solange sie nicht dieselben instabilen Domain-Verträge oder Journeys verändern.
6. **Aufwände sind Planungswerte.** Vor Implementierung bleibt der jeweilige Gap-Check gegen den aktuellen `main` maßgeblich; daraus können Umfang und Reihenfolge angepasst werden.

---

# Pflege

- Nach Abschluss eines Issues den Plan kurz gegen den aktuellen `main` und die verbleibenden offenen Issues prüfen.
- Neue Issues nicht automatisch hinten anhängen, sondern anhand ihrer technischen und fachlichen Abhängigkeiten einordnen.
- Abgeschlossene issue-spezifische Analyse- und Completion-Artefakte werden unter `docs/archive/issues/` abgelegt, sofern sie keine aktive fachliche oder technische Referenz mehr sind.
