# Block 3 – Abschlussnachweis

**Issue:** #119  
**Ziel:** Persistente, wiederaufnehmbare Erfassung für neue Value Streams und Use Cases ohne LLM, Extraktion oder automatische Fachobjektanlage.

## Umgesetzter Umfang

Block 3 liefert zwei getrennte, versionierte Fragenkataloge und eine kleine `CaptureSession`-Schicht mit:

- Anlage mehrerer paralleler Entwürfe je Nutzer und Capture-Art,
- eigentümergebundener Speicherung und Wiederaufnahme,
- revisionsgeschütztem Schreiben bei parallelen Tabs,
- revisionsneutraler Vor-/Zurück-Navigation,
- Abschluss, Verwerfen und kontrolliertem Ablauf,
- nativen semantischen Textfeldern für Betriebssystem-Diktat wie `WIN + H`,
- schlanker Messung aggregierter aktiver Eingabezeit,
- Retention und physischer Bereinigung terminaler Rohantworten,
- unverändertem direktem Value-Stream- und Use-Case-Anlagepfad.

Capture Sessions bleiben eine temporäre Eingangs- und Herkunftsschicht. Sie erzeugen oder verändern in Block 3 keine regulären Fachobjekte.

## Abnahmematrix für Issue #119

| Abnahmekriterium | Nachweis |
| --- | --- |
| Gap-Analyse dokumentiert | `docs/accelerator/BLOCK_3_GAP_ANALYSIS.md` |
| Value-Stream- und Use-Case-Sessions anlegen | getrennte Startpfade und Tests in `tests/test_value_stream_capture_views.py` sowie `tests/test_use_case_capture_views.py` |
| Speichern und fortsetzen | atomarer Service, persistente Wizard-Schritte und Übersicht „Meine Erfassungen“ |
| Abschließen und verwerfen | terminale Serviceaktionen mit Revisions- und Zustandsprüfung |
| Fragenkataloge versioniert | `ki_radar/accelerator/catalogs.py` und Vertragsregression in `tests/test_capture_catalogs.py` |
| Nur Berechtigte sehen und bearbeiten Sessions | Eigentümerfilter, erneute Rollenprüfung bei jeder Aktion und Direkt-UUID-Regression |
| Keine Änderung regulärer Fachobjekte | Abschlussregressionen prüfen unveränderte `ValueStream`- und `UseCase`-Bestände |
| `WIN + H` ohne Anwendungsintegration | native `<textarea>`-Elemente ohne eigene Tastatur- oder Eingabesteuerung |
| Retention und Löschung getestet | `tests/test_capture_retention.py` und `purge_capture_sessions` |
| Lösung schlank und zweckgebunden | keine Survey-Plattform, keine LLM-Pfade, keine Extraktion und keine zweite fachlich führende Datenquelle |

## Vollständige Regression

Der Merge von AP 10 setzt eine grüne unveränderte Repository-CI voraus. Der Lauf umfasst:

1. Lockfile- und Dependency-Installation,
2. repo-weites Ruff-Linting und `ruff format --check .`,
3. Django-System- und Migrationsprüfung,
4. vollständige Pytest-Suite,
5. Bandit und Dependency Audit,
6. lokale, Produktions- und Staging-Compose-Validierung,
7. Produktions- und Entwicklungs-Image-Build.

Die Block-3-Regressionsabdeckung liegt insbesondere in:

- `tests/test_capture_catalogs.py`,
- `tests/test_capture_session_model.py`,
- `tests/test_capture_session_services.py`,
- `tests/test_value_stream_capture_views.py`,
- `tests/test_use_case_capture_views.py`,
- `tests/test_capture_overview.py`,
- `tests/test_capture_retention.py`,
- `tests/test_capture_measurement_privacy.py`,
- `tests/test_block3_real_demo_acceptance.py`.

## Konkrete `[Real-DEMO]`-Rückwärtsprobe

Die Rückwärtsprobe liest `real_demo.v1.json` als konkreten bekannten Beschaffungspfad und prüft:

- sämtliche narrativen Blueprint-Blattfelder unter Value Stream, Prozessanalyse, Lösungsoptionen und Use Case werden durch die Zielpfade der beiden Kataloge abgedeckt,
- technische Schlüssel, Workflow-, Bewertungs- und Entscheidungszustände bleiben ausdrücklich außerhalb der Capture-Kataloge,
- die realen Inhalte zu Scope, drei Phasen, Angebotsvergleich, drei Lösungsalternativen, primärer Zeitmetrik und menschlicher Aufsicht ergeben vollständige, vertragsgültige Antwortdokumente,
- die Trennung von `scope_in` und `scope_out` aus dem korrigierten Real-DEMO-Stand bleibt erhalten.

Damit ist früh abgesichert, dass Block 4 die bekannte Referenz fachlich aus den Block-3-Antworten ableiten kann. Die Rückwärtsprobe implementiert selbst keine Extraktion.

## Datenschutz und Retention

Rohantworten werden in Fehlerberichten als sensibel behandelt und nicht als detaillierte Telemetrie erfasst. Gespeichert werden nur Antworttexte, Statusdaten, Speicheranzahl und aggregierte aktive Sekunden.

Abgeschlossene Sessions bleiben in Block 3 als Quelle für Block 4 erhalten. Vor produktiver Block-4-Nutzung muss die in `BLOCK_3_RETENTION.md` dokumentierte Folgeregel für Löschung, Minimierung oder Archivierung abgeschlossener Rohantworten umgesetzt werden.

## Abgrenzung und Folgeblöcke

Nicht Bestandteil von Block 3 sind:

- Freitext-zu-Feld-Extraktion,
- Vorschläge oder Feldübernahme,
- automatische Fachobjektanlage,
- LLM-, Audio-, Datei- oder Connector-Verarbeitung,
- automatische Entscheidung, Validierung oder Freigabe.

Diese Grenzen entsprechen Issue #119 und lassen Issue #116 unverändert.

## UI-Prüfung

Die automatisierten Tests sichern native Formularelemente, semantische Labels, Navigation, Ownership, Konfliktverhalten und No-JavaScript-Fallback. Eine visuelle manuelle Desktop-/Mobile-Prüfung wird durch die GitHub-Schnittstelle nicht simuliert oder als durchgeführt ausgegeben; sie ist kein Abnahmekriterium von Issue #119.
