# KI-Radar Execution Plan

**Stand:** 23.08.2026

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

**#351 – Discovery→Use-Case-Konsistenzprüfung** wurde am 23.08.2026 als dritter Schritt der First Wave abgeschlossen. Die Prüfung wird explizit durch den Nutzer gestartet, vergleicht den aktuellen Use Case read-only mit seiner belastbaren Discovery-Herkunft, arbeitet mit einer engen Context-Allowlist und source-gebundenen Findings und verändert keine fachlichen Daten oder Entscheidungen. Bei fehlender, veralteter oder mehrdeutiger Herkunft wird fail-closed gearbeitet.

**#350 – Grounded KI-Entwurf für Delivery-MVP-Scope** wurde am 23.08.2026 abgeschlossen. Der Delivery-Bereich kann nun auf Nutzeranforderung einen source-gebundenen, editierbaren MVP-Scope-Entwurf erzeugen; Übernahme bleibt eine bewusste fachliche Aktion über den regulären Schreibpfad.

**#349 – First-Wave LLM-Task-Runtime** wurde am 23.08.2026 abgeschlossen. Der gemeinsame Runtime-Layer bündelt Provider-/Privacy-Policy, Quotas, technische Run-Metadaten und Fehlerbehandlung für die ersten task-spezifischen KI-Funktionen, ohne fachliche Kontexte oder Ergebnisse in den Core-Layer zu ziehen.

**#328 – KI-Rollout konsolidieren** wurde am 23.08.2026 abgeschlossen. Die Analysen #325, #326 und #327 wurden in eine bewusst kleine First Wave überführt; daraus entstanden #349, #350 und #351. Der Rollout bleibt task-spezifisch, nutzerinitiiert und ohne automatische Freigabe-, Status- oder Domainänderungen.

**#333 – Scale Readiness vor produktivem Betrieb** wurde am 23.08.2026 abgeschlossen. Die bestehende Ergebnisentscheidung bündelt nun sechs Prüfdimensionen aus Pilotwirkung, Governance, Delivery, ML Test Score und Betriebsnachweisen. Hard Blocker verhindern den Go-live, ein Conditional Go verlangt Maßnahme, Owner und Frist, und der bestehende `Review` bleibt die einzige persistente Lifecycle-Entscheidungsquelle.

**#320 – Delivery-Readiness analysieren** wurde am 23.08.2026 als reine Re-Analyse abgeschlossen. Die mit #321 geschlossenen Owner-, Source-Decision-, Finding- und Review-Reset-Lücken sind weiterhin wirksam; es wurde keine verbleibende Restlücke festgestellt.

**#310 – Reiseveranstalter E2E-Demo und lokale UI-Abnahme** wurde am 23.08.2026 im regulären Browser abgeschlossen. Der Referenzfall wurde vom Value Stream über Fokus, Prozessanalyse und technologieoffenen Lösungsvergleich bis zum bewerteten und governance-seitig vorbereiteten KI-Use-Case durchgeführt.

---

# Aktueller Ablaufplan

| Reihenfolge | Issue | Inhalt | Warum an dieser Stelle? | Geschätzter Aufwand | Komplexität |
|---:|---|---|---|---:|---|
| **1** | **#330 – Django-Ninja Read-only API** | Ergänzt eine kleine Read-only API für Use Cases und Delivery Readiness mit expliziten Response-Schemas, API-Key und OpenAPI/Swagger. Bestehende Domain-/Readiness-Logik wird wiederverwendet und nicht dupliziert. | Die von der API konsumierten Use-Case-, Delivery- und Readiness-Verträge sind stabil. Die First-Wave-KI-Änderungen #349–#351 sind abgeschlossen und erzeugen keine notwendige Vorbedingung mehr. | **1–1,5 Tage / 8–12 h** | **mittel** |
| **2 / geparkt** | **#307 – optionaler Entscheidungsraum** | Ergänzt für echte strittige Entscheidungen einen zusätzlichen Decision Case mit Perspektiven, Evidenz, Readiness, RAPID/DACI, Constraints und Eskalation. | Das Issue ist ausdrücklich als Prio 3 geparkt und wird nicht automatisch nach #330 umgesetzt. Vor Start ist eine neue Priorisierungsentscheidung plus Gap-Analyse gegen `main` erforderlich. | **5–10 Tage** | **sehr hoch** |

---

# Abhängigkeitsbild

```text
#310 + #320/#321 + #333 abgeschlossen
              ↓
#325 → #326 + #327 → #328 abgeschlossen
              ↓
#349 → #350 → #351 abgeschlossen
              ↓
#330 Read-only API
              ↓
#307 optionaler Entscheidungsraum (geparkt / nur nach expliziter Re-Priorisierung)
```

Zwischen #330 und #307 besteht keine harte technische Abhängigkeit. Die Reihenfolge ist eine Produkt-/Rework-Entscheidung: #330 ist klein, klar abgegrenzt und nutzt bereits stabile Verträge; #307 ist ein bewusst geparkter, großer Governance-Subworkflow.

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
