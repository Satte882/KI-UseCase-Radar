# Discovery & Architecture in KI-Radar

## Ziel

Der Bereich ergänzt den direkten Use-Case-Intake um einen optionalen Business-Architecture-Pfad:

```text
Value Stream → Phase/Problem → Prozessanalyse → Lösungsoption → KI-Use-Case → Entscheidung → Delivery
```

Ein Use Case muss nicht aus einem Value Stream entstehen. Der direkte Intake bleibt ein gleichwertiger Einstieg und behält alle vorhandenen Plausibilitäts- und Hard-Gate-Prüfungen.

## Methodische Trennung

KI-Radar behandelt vier unterschiedliche Ebenen getrennt:

1. **Value-Stream-Analyse:** End-to-End-Wertschöpfung, Empfänger, Phasen, Stakeholder und Ergebnis.
2. **Prozessanalyse:** detaillierter Ist-Ablauf, Rollen, Systeme, Daten, Regeln, Übergaben, Ausnahmen und Bottlenecks.
3. **TOGAF ADM als Vorgehensrahmen:** strukturierte Ableitung von Kontext, Business-, Daten-/Applikations- und Technologiearchitektur sowie Lösungs- und Migrationsplanung.
4. **Delivery-Handover:** umsetzbarer Scope, Anforderungen, Akzeptanzkriterien, Risiken, Abhängigkeiten und initiales Backlog.

## TOGAF-light

KI-Radar ist kein Enterprise-Architecture-Repository und implementiert nicht das vollständige TOGAF-Metamodell. Die ADM-Bezüge sind nur dann sichtbar, wenn konkrete Artefakte erfasst werden:

| ADM-Phase | KI-Radar-Artefakt |
|---|---|
| A – Architecture Vision | Scope, strategisches Ziel, Stakeholder, Leitplanken, Auslöser und Ergebnis |
| B – Business Architecture | Value Stream, Phasen, Rollen, Probleme, Kennzahlen und später Prozessanalyse |
| C – Information Systems | später Datenobjekte, Anwendungen, Informationsflüsse und Integrationen |
| D – Technology Architecture | später Hosting-, Plattform- und Technologieleitplanken |
| E – Opportunities & Solutions | später explizite Lösungsoptionen und begründete Präferenz |
| F – Migration Planning | später MVP-Scope, Abhängigkeiten, Roadmap und Delivery Package |
| G/H | Entscheidungen und Änderungen werden dokumentiert; kein vollständiges Architecture-Governance-Modul |

## Scope-Steuerung

Die Erweiterung wird in drei unabhängigen Inkrementen umgesetzt:

1. Value Streams und optionale Herkunft eines Use Cases
2. Prozessanalyse und Lösungsoptionen
3. Delivery Package und exportierbarer Handover

Jedes Inkrement muss für sich nutzbar bleiben. Es werden weder ein BPMN-Modellierer noch ein frei konfigurierbares EA-Metamodell, Projektmanagement, Ressourcenplanung oder eine Workflow-Engine gebaut.
