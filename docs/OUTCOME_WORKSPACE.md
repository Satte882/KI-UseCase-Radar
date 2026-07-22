# Wirkung & Betrieb

## Zielbild

`Wirkung & Betrieb` ist ein kompakter Review- und Entscheidungs-Snapshot. Der Arbeitsraum ersetzt weder das bestehende Use-Case-Formular noch Jira, Azure DevOps, GitHub oder ein anderes operatives Delivery-System.

Die Navigation umfasst:

```text
Übergabe → Pilot → Wirkung → Ergebnisentscheidung → Betrieb → Abschluss
```

Jeder Bereich zeigt vorhandene Informationen und führt ausschließlich zu einer bereits bestehenden, fachlich führenden Oberfläche. Es entsteht keine parallele Dateneingabe.

Der Arbeitsraum verwendet weiterhin dieselbe `JourneyState`-/`JourneyStep`-Logik. Es gibt keine zweite Journey-Engine und keine unabhängige Lifecycle-Statuslogik.

## Systemgrenze

### Externes Delivery-System

Jira, Azure DevOps, GitHub oder ein vergleichbares Werkzeug bleiben führend für:

- Backlog, Epics, Stories und Tasks,
- Sprint- und Release-Planung,
- technische Detailprobleme,
- tägliche Maßnahmen und Fortschrittsmeldungen,
- Ressourcenplanung,
- Incident-, Change- und Service-Management.

### KI-Radar

KI-Radar bleibt führend für:

- Baseline, Ziel und gemessenen Ist-Wert,
- Messzeitraum, Messmethode und Nachweislink,
- Governance-Auflagen und Verantwortlichkeiten,
- Lifecycle-Reviews mit Begründung und Statuswechsel,
- Go-live- und Abschlussentscheidung,
- Management-Reviews und Lessons Learned.

Der Informationsrückfluss bleibt ein manueller Review-Snapshot. Es gibt keine Live-Synchronisation und keine doppelte Pflege operativer Maßnahmen.

## Führende Oberfläche je Bereich

| Bereich | Aktion und führende Oberfläche |
|---|---|
| Übergabe | Delivery Package prüfen, vervollständigen oder verbindlich übergeben |
| Pilot | tatsächlich hinterlegten externen Delivery-Link öffnen |
| Wirkung | direkt zum nächsten fehlenden Metrikfeld im bestehenden Use-Case-Formular springen |
| Ergebnisentscheidung | bei vollständiger Messung das bestehende Review-Formular für `GO_LIVE` öffnen |
| Betrieb | bei fälligem Termin das bestehende Review-Formular öffnen; sonst neutralen Status anzeigen |
| Abschluss | das bestehende Review-Formular für `END` und die Abschlussangaben öffnen |

Ein CTA wird nur angezeigt, wenn Zieloberfläche und Berechtigung tatsächlich vorhanden sind.

## Pilot-Link und unveränderliche Übergaben

- Ein gestarteter Pilot mit externem Delivery-Link zeigt `Externen Pilot öffnen`.
- Ein noch bearbeitbares Delivery Package ohne Link zeigt für berechtigte Benutzer `Delivery-Link ergänzen`.
- Ein bereits übergebenes Package bleibt unveränderlich. Fehlt dort der Link, zeigt die Oberfläche bewusst einen neutralen Hinweis; sie verweist nicht auf eine unzulässige Bearbeitung.
- Die frühere Selbstverlinkung `Pilotübersicht öffnen` ist entfernt. Es wird keine interne Pilotübersicht erfunden.

## Ergebnisentscheidung und Abschluss

Die Deep Links verwenden das bestehende Lifecycle-Review:

- `Go-live entscheiden` öffnet das Review-Formular mit `GO_LIVE` und Zielstatus `Betrieb` vorbelegt.
- `Abschluss dokumentieren` öffnet dasselbe Formular mit `END` und Zielstatus `Beendet` vorbelegt.

Formular-, Service- und Gate-Logik bleiben unverändert führend. Der Arbeitsraum speichert keine Entscheidung selbst.

## Kompakter Snapshot

Der gemeinsame Use-Case-Bereich zeigt weiterhin:

- Lifecycle-Status,
- Baseline, Ziel, Ist-Wert und Ergebnis,
- Business und Technical Owner,
- nächsten Review-Termin,
- aktuelle Delivery-Package-Version und Status.

Die Darstellung ist verdichtet, damit der phasenspezifische Handlungsstatus sichtbar bleibt.

## Sidebar und Benutzer-Menü

Die sechs Bereiche besitzen getrennte Sidebar-Einstiege. Der Footer zeigt dauerhaft nur Avatar und Benutzername. Administration und Abmelden liegen in einem aufklappbaren Account-Menü.

## Bewusste Nicht-Ziele

Dieses Inkrement implementiert nicht:

- ein neues Pilot- oder Betriebsdatenmodell,
- eine zweite Bearbeitungsoberfläche,
- Fortschrittsprozente oder operative Maßnahmenlisten,
- Jira-, Azure-DevOps- oder GitHub-Synchronisation,
- versionierte Wirkungsmessungen,
- eine neue persistierte Scale-/Continue-/Stop-Entscheidung,
- neue Lifecycle-Status oder Berechtigungsmodelle.

Es entsteht keine Migration.

## Abnahmekriterien

- Die sechs Bereiche besitzen unterscheidbare Kontexte.
- CTAs führen nur zu vorhandenen und zulässigen Zieloberflächen.
- Pilot öffnet ausschließlich einen echten externen Link.
- Fehlende oder unzulässige Aktionen werden als bewusster neutraler Zustand dargestellt.
- Wirkung, Go-live und Abschluss verwenden die bestehenden Formulare.
- Der Account-Footer blockiert keinen dauerhaften Platz für Administration und Abmelden.
- Die bestehende Systemgrenze bleibt sichtbar.
- Es entsteht kein neues Datenmodell und keine Migration.
