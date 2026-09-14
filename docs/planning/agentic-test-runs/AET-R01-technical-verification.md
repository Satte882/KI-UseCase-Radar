# AET-R01 – Technische Verifikation

## Status

Die technische Diagnose von AET-R01 ist abgeschlossen. Diese Verifikation ergänzt `AET-R01.md` um die tatsächliche CI-Ausführung gegen denselben Produktstand, der für die 10-Run-Kohorte fixiert wurde.

- getesteter Produktstand: `499cf809570db8ce1ebed0d03dd85860c20b9037`
- Dokumentationsbranch: `issue-429-agentic-runs`
- Diagnose-Commit vor CI: `ce62af3e1ed2ad03d873a63d4ae86c8dbc3332a2`
- Validierungs-PR: #432, ausschließlich zur CI-Auslösung, nicht gemergt
- GitHub-Actions-Run: `KI-Radar CI` #1836, Run-ID `34859932752`
- Ergebnis: **erfolgreich**

Es wurden für die Verifikation keine Produkt- oder Testdateien geändert.

## CI-Ergebnis

Der vollständige Repository-Validierungslauf war grün:

- Ruff lint: erfolgreich
- Ruff format check: erfolgreich
- Django system check: erfolgreich
- Migration check und Migrationen: erfolgreich
- Architecture Real-DEMO E2E: **1 passed**
- vollständige Pytest-Suite: **1457 passed, 275 warnings**
- Coverage im Gesamtlauf: **85 %**
- Bandit: erfolgreich
- Dependency Audit: erfolgreich (`No known vulnerabilities found, 1 ignored` gemäß bestehender CI-Konfiguration)
- Compose-Validierung lokal / Produktion / Staging: erfolgreich
- Produktions- und Development-Docker-Image: erfolgreich gebaut

Die grünen Tests widerlegen die R01-Findings nicht. Sie zeigen vielmehr, dass der bestehende Testbestand die beobachteten Zustände entweder als vorgesehenes Verhalten abbildet oder die konkret problematischen Zustände noch nicht abdeckt.

## Finale technische Einordnung der R01-Findings

### 1. Falsche Next Action nach gespeicherter Fokuswahl

**Einordnung: Bug.**

Die zentrale Journey-Logik berücksichtigt eine bereits vorhandene `StageFocusDecision` in diesem Zustand nicht. Der vorhandene Testbestand deckt den entscheidenden Zustand „Fokusentscheidung vorhanden, noch keine Prozessanalyse“ nicht ab. Die vollständige Testsuite ist grün, obwohl der Blackbox-Befund reproduzierbar aus der Code-Logik erklärbar ist.

### 2. Badge „Bestätigt“ bei ausdrücklich nicht bestätigter Ursache

**Einordnung: Bug – fachlicher Darstellungsfehler; technische Ursache ist eine zu grobe Freitext-/Leerheitssemantik.**

Jeder nicht leere Inhalt in `confirmed_causes` wird im UI als „Bestätigt“ dargestellt. Dadurch kann die sichtbare Anwendung einen fachlichen Zustand behaupten, der dem gespeicherten Text ausdrücklich widerspricht. Das ist mehr als reine kosmetische UX-Semantik, weil Ursachenstatus und Evidenz Teil der methodischen Entscheidungsgrundlage sind.

Der bestehende Testbestand prüft die Feldtrennung, aber nicht den negierenden Inhalt in `confirmed_causes`.

### 3. Pauschales „Verworfen“ für nicht bevorzugte Lösungen

**Einordnung: UX-/Domain-Semantik, kein Implementierungsfehler.**

Das aktuelle Domänenmodell kennt nur `candidate`, `preferred` und `rejected`; nicht ausgewählte aktive Optionen werden bewusst auf `rejected` gesetzt. Die vorhandenen Tests bestätigen dieses Verhalten. Für Optionen, die nur zurückgestellt oder als spätere Ergänzung offenbleiben sollen, ist die Semantik jedoch zu endgültig.

### 4. Größenlimit bei „Antworten analysieren“

**Einordnung: erwarteter technischer Schutzmechanismus mit UX-Transparenzlücke.**

Der kontrollierte Abbruch vor dem Provider-Aufruf ist vorgesehen und getestet. Problematisch ist, dass der Nutzer das effektive Größenlimit beziehungsweise eine drohende Überschreitung vor dem Analyseversuch nicht sieht.

### 5. Doppeleingabe nach fehlgeschlagener Analyse

**Einordnung: UX-/Workflow-Recovery-Lücke, kein Datenverlust.**

Die Capture-Antworten bleiben erhalten, der Übernahmepfad in reguläre Fachobjekte setzt jedoch erfolgreich erzeugte Analysevorschläge voraus. Für `input_too_large` existiert kein Vorbefüllen, Kürzungs-, Chunking- oder deterministischer Fallback-Pfad. Deshalb entsteht manuelle Neuerfassung.

## Schlussfolgerung für #429

AET-R01 bleibt unverändert als `NON_AI_DISCOVERY_COMPLETE` mit Review-Urteil `teilweise robust` bestehen. Der Run wird nicht nachgebessert oder wiederholt.

Für die Cross-Run-Analyse werden insbesondere folgende Signale weiter beobachtet:

- Qualität und Vergleichbarkeit der Fokusbegründung;
- saubere Trennung von Beobachtung, Hypothese und bestätigter Ursache;
- echte Differenzierung von Lösungsalternativen;
- Zeitpunkt der Lösungspräferenz relativ zur Evidenzlage;
- Semantik reversibler bzw. später erneut prüfbarer Lösungsoptionen;
- wiederkehrende Navigation-/Recovery-Probleme.

Damit ist die technische Verifikation von R01 abgeschlossen. Produktfixes erfolgen bewusst nicht innerhalb der laufenden 10-Run-Kohorte.