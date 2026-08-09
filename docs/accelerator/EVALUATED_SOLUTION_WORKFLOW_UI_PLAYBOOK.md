# Evaluated Solution Workflow – UI-Playbook nach AP5

Stand: AP5 – Initial Critic, Quoten-/Provider-Integration und Failure Preservation

## Zweck

Dieser Zwischenstand prüft den ersten vollständigen erweiterten Pfad ohne Repair:

`Generate -> deterministic Validate -> Initial Critic -> Human Review`

Die bestehende Block-7-Preview bleibt die maßgebliche Nutzeroberfläche. AP5 fügt bewusst noch keine Finding-Darstellung und keinen Repair-Button hinzu.

## Voraussetzungen

- lokaler Stack läuft auf dem aktuellen `main` nach Merge von AP5;
- eine Prozessanalyse erfüllt die bestehende Block-7-Readiness;
- OpenRouter ist für einen normalen Generierungs- und Critic-Aufruf konfiguriert.

## Playbook A – erfolgreicher erweiterter Pfad

1. Eine für Block 7 bereite Prozessanalyse öffnen.
2. „3 Lösungsentwürfe mit KI erstellen“ starten.
3. Nach erfolgreicher Generierung die bestehende Preview öffnen.
4. Prüfen, dass weiterhin genau die drei bekannten Lösungsrichtungen mit Original, Quelle, Annahmen/offener Evidenz und Unsicherheit angezeigt werden.
5. Prüfen, dass keine Lösung automatisch ausgewählt, bewertet, priorisiert oder in Governance-/Delivery-Felder übernommen wurde.
6. Die Preview normal für die menschliche Prüfung weiterverwenden.

Erwartung: Die deterministisch valide Preview wird zuerst gespeichert. Der Initial Critic läuft anschließend automatisch als eigener Quality-Step. Ein zusätzlicher Critic-Startbutton existiert nicht.

## Playbook B – Failure Preservation

Mit einer Testkonfiguration, in der der Critic nach erfolgreicher Generierung wegen Provider-/Quota-Verfügbarkeit nicht ausgeführt werden kann:

1. Die Generierung bis zur erfolgreichen Preview durchführen.
2. Die Preview erneut öffnen bzw. aktualisieren.
3. Prüfen, dass die drei zuvor erzeugten Lösungsrichtungen vollständig erhalten bleiben.
4. Prüfen, dass die menschliche Review der Preview weiterhin möglich ist.
5. Prüfen, dass kein automatischer Domain Write, keine Auswahl und keine Governance-Wirkung entstanden ist.

Erwartung: Ein Critic-, Quota-, Provider-, Output- oder Critic-Contract-Fehler darf die bereits erfolgreiche Generation weder auf `failed` zurücksetzen noch deren Preview leeren oder verändern.

## In AP5 bewusst noch nicht klickbar

Folgende Punkte gehören erst zu AP9 und sind in diesem Zwischenstand **nicht** über die UI abnehmbar:

- Anzeige einzelner Critic-Findings;
- Kennzeichnung reparierbarer Findings;
- Repair-Aktion;
- Stale-/CAS-Hinweis bei nachträglich geänderter Preview;
- explizite Human-Review-Statusdarstellung des Quality-Workflows.

Diese Abgrenzung ist beabsichtigt und kein fehlender AP5-Umfang.
