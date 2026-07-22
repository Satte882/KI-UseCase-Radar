# Wirkung & Betrieb

## Status dieses Inkrements

Dieses Inkrement finalisiert die Navigation und Informationshierarchie für Wirkung und Betrieb. Es führt kein neues fachliches Datenmodell für Pilotfortschritt, Ergebnisreviews, Skalierungsentscheidungen oder Betrieb ein.

Ziele:

1. die Systemgrenze zu Jira, Azure DevOps, GitHub und ähnlichen Delivery-Systemen verbindlich festlegen,
2. den zweiten Arbeitsraum in die bestehende `JourneyState`-/`JourneyStep`-Logik integrieren,
3. eine fokussierte Hauptleiste für den zweiten Arbeitsraum bereitstellen,
4. die nächsten fachlichen Inkremente auf einen kleinen, abnehmbaren Umfang begrenzen.

## Systemgrenze

KI-Radar bleibt ein Portfolio-, Governance- und Entscheidungs-Cockpit. Es wird kein operatives Projektmanagementsystem.

### Führendes externes Delivery-System

Jira, Azure DevOps, GitHub oder ein vergleichbares Werkzeug bleiben führend für:

- Backlog, Epics, Stories und Tasks,
- Sprint- und Release-Planung,
- technische Detailprobleme,
- tägliche Maßnahmen und Fortschrittsmeldungen,
- Ressourcenplanung,
- Incident-, Change- und Service-Management.

### Führendes System für Portfolioentscheidungen

KI-Radar bleibt führend für:

- Baseline, Ziel und gemessenen Ist-Wert,
- Messzeitraum, Messmethode und Nachweislink,
- wesentliche Probleme und offene Governance-Auflagen,
- Empfehlung und Begründung für die Folgeentscheidung,
- spätere Scale-, Continue-, Nachbesserungs- oder Stop-Entscheidung,
- Business- und Technical-Ownership,
- wiederkehrende Management-Reviews,
- Abschlussbewertung und Lessons Learned.

## Rückfluss der Informationen

Der erste produktive Ausbaustand verwendet bewusst einen **manuellen Review-Snapshot**:

```text
Jira / Azure DevOps / GitHub
→ Pilotteam bereitet entscheidungsrelevante Ergebnisse vor
→ Business Owner oder Koordinator bestätigt den Snapshot zum Review-Termin
→ KI-Radar dokumentiert Evidenz und Entscheidung
```

Es gibt zunächst:

- keine Live-Synchronisation,
- keinen automatischen Import von Tasks oder Sprintdaten,
- keine doppelte Pflege operativer Maßnahmen,
- keine Annahme, dass täglicher Fortschritt in KI-Radar nachgeführt wird.

Eine spätere Integration darf ausschließlich verdichtete, entscheidungsrelevante Informationen übernehmen. Das externe System bleibt für operative Daten führend.

## Eine Journey statt paralleler Statuslogik

Der zweite Arbeitsraum verwendet weiterhin:

- `JourneyState`,
- `JourneyStep`,
- dieselbe Next-Action-Auswahl,
- dieselben Zustände `complete`, `current`, `blocked`, `upcoming` und `optional`.

`build_outcome_workspace_journey()` erweitert die vorhandene Use-Case-Journey um:

```text
Übergabe
→ Pilot
→ Wirkungsmessung
→ Ergebnisentscheidung
→ Betrieb
→ Abschluss
```

Die bestehende Auswahl- und Freigabe-Journey bleibt Teil desselben Objekts. Es gibt keine zweite Journey-Engine und keine unabhängige Template-Statuslogik.

## Navigationsentscheidung: getrennter Arbeitsraum

Nach der lokalen Desktop- und Mobile-Abnahme wurde die fokussierte Variante A ausgewählt.

Beim Wechsel zu Wirkung & Betrieb zeigt die stabile Hauptleiste nur:

```text
Übergabe → Pilot → Wirkung → Ergebnisentscheidung → Betrieb → Abschluss
```

Die Trennung reduziert die Breite der stabilen Hauptleiste und hält den aktuellen Aufgabenraum
auf Desktop und Mobile schneller erfassbar. Der Zusammenhang zur Auswahl und Freigabe bleibt
über die deutlich getrennten Arbeitsräume in der Sidebar erhalten. Die zuvor angebotene
durchgängige Vergleichsvariante ist nicht mehr Bestandteil der Oberfläche.

## Bereits genutzte Daten

Der Bereich verwendet ausschließlich bestehende Daten:

- Use-Case-Lifecycle,
- Pilotbeginn und geplantes Pilotende,
- nächster Review-Termin,
- Baseline, Ziel und Ist-Wert,
- Messmethode und Messnachweis,
- Delivery-Package-Status und Link zum Delivery-System,
- Business Owner, Technical Owner und Support-Verantwortung,
- Abschlussinformationen am Use Case.

Das Inkrement erzeugt keine Migration.

## Bewusste Nicht-Ziele

Dieses Inkrement implementiert nicht:

- ein neues Pilot-Datenmodell,
- Fortschrittsprozente,
- Maßnahmenlisten,
- Jira- oder Azure-DevOps-Synchronisation,
- eine persistierte Scale-/Stop-Entscheidung,
- neue Hard Gates für Betrieb oder Abschluss,
- Benachrichtigungen oder Eskalationen.

## Geplante kleine Folgeinkremente

1. **Pilotübersicht aus bestehenden Daten**
   - Pilotstatus, Zeitraum, Owner, Zielmetrik, Review-Termin und Delivery-Link.
2. **Versioniertes Wirkungsreview**
   - Mess-Snapshot, Nachweis, qualitative Ergebnisse, Probleme und Empfehlung.
3. **Ergebnisentscheidung**
   - skalieren, verlängern, nachbessern, in Betrieb überführen oder beenden.
4. **Betriebsreview**
   - Ownership, Nutzenstatus, Auflagen und nächster Review.
5. **Abschluss**
   - Stilllegung, Datenbehandlung, Ersatzlösung und Lessons Learned.

Jedes Inkrement erhält einen eigenen Branch, eigenen PR, eigene Tests und eine getrennte fachliche Abnahme.

## Abnahmekriterien

- Die Sidebar zeigt zwei klar getrennte Arbeitsräume.
- Der zweite Arbeitsraum nutzt die gesamte verfügbare Inhaltsbreite.
- Die Hauptleiste zeigt im zweiten Arbeitsraum nur Übergabe bis Abschluss.
- Desktop und Mobile bleiben bedienbar.
- Die Systemgrenze ist auf der Seite und in dieser Dokumentation sichtbar.
- Es entsteht kein neues Datenmodell und keine Migration.
- Die Next Action stammt weiterhin aus derselben Journey-State-Logik.
- Bestehende Auswahl-, Freigabe- und Delivery-Seiten bleiben unverändert nutzbar.
