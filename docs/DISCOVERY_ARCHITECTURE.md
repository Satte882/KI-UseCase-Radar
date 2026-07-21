# Discovery & Architecture in KI-Radar

## Ziel

Der Bereich ergänzt den direkten Use-Case-Intake um einen optionalen Business-Architecture-Pfad:

```text
Value Stream
→ Phase und Problem
→ Prozessanalyse
→ Lösungsoption
→ geführter Use-Case-Intake
→ Bewertung und Freigabe
→ Delivery Package
→ externes Delivery-System
```

Ein Use Case muss nicht aus einem Value Stream entstehen. Der direkte Intake bleibt ein gleichwertiger Einstieg und behält alle vorhandenen Plausibilitäts- und Hard-Gate-Prüfungen.

## Methodische Trennung

KI-Radar behandelt vier unterschiedliche Ebenen getrennt:

1. **Value-Stream-Analyse:** End-to-End-Wertschöpfung, Empfänger, Phasen, Stakeholder und Ergebnis.
2. **Prozessanalyse:** detaillierter Ist-Ablauf, Rollen, Systeme, Daten, Regeln, Übergaben, Ausnahmen und Bottlenecks.
3. **TOGAF ADM als Vorgehensrahmen:** strukturierte Ableitung von Kontext, Business-, Daten-/Applikations- und Technologiearchitektur sowie Lösungs- und Migrationsplanung.
4. **Delivery-Handover:** umsetzbarer Scope, Anforderungen, Akzeptanzkriterien, Risiken, Abhängigkeiten und initiales Backlog.

Die Ebenen sind miteinander verknüpft, aber nicht austauschbar. Ein Value Stream ist kein Detailprozess, eine Prozessanalyse ist keine Lösungsarchitektur und ein Delivery Package ist kein Projektplan.

## TOGAF-light

KI-Radar ist kein Enterprise-Architecture-Repository und implementiert nicht das vollständige TOGAF-Metamodell. Die ADM-Bezüge sind nur dort sichtbar, wo konkrete Artefakte erfasst werden:

| ADM-Phase | KI-Radar-Artefakt |
|---|---|
| A – Architecture Vision | Scope, strategisches Ziel, Stakeholder, Leitplanken, Auslöser und Ergebnis |
| B – Business Architecture | Value Stream, Phasen, Rollen, Ist-Prozess, Regeln, Bottlenecks und Kennzahlen |
| C – Information Systems | Anwendungen, Datenobjekte, Informationsflüsse und Integrationen |
| D – Technology Architecture | Technologie-, Hosting- und Plattformleitplanken innerhalb der Lösungsoption |
| E – Opportunities & Solutions | organisatorische, klassische und KI-Lösungsoptionen mit begründeter Präferenz |
| F – Migration Planning | MVP-Scope, Akzeptanzkriterien, Tests, Abhängigkeiten, Backlog und Delivery Package |
| G/H | Freigaben, Package-Versionen und Änderungen werden dokumentiert; kein vollständiges Architecture-Governance-Modul |

## Optionalität

Der bestehende Use-Case-Intake bleibt unverändert ein vollwertiger Einstieg. Die Herkunftskette wird nur angelegt, wenn ein Vorhaben tatsächlich aus dem Architecture-Bereich abgeleitet wurde:

```text
Use Case → bevorzugte Lösungsoption → Prozessanalyse → Value-Stream-Phase → Value Stream
```

Dadurch werden Einzelvorhaben nicht künstlich mit Architekturartefakten belastet. Systematische Discovery bleibt dennoch vollständig rückverfolgbar.

## Prozessanalyse

Eine Prozessanalyse erfasst genau die Informationen, die zur Beurteilung des Problems und zur Formulierung eines Zielbilds benötigt werden:

- Prozessstart und Prozessende
- Auslöser und Ergebnis
- Ist-Ablauf
- Rollen und Verantwortlichkeiten
- Anwendungen und Arbeitsmittel
- Datenobjekte und Dokumente
- Geschäftsregeln
- Übergaben und Schnittstellen
- Bottlenecks und Ursachen
- Ausnahmen und Fehlerfälle
- Baseline und Prozesskennzahlen
- Prinzipien für den Soll-Prozess

KI-Radar erzeugt kein BPMN-Modell. Vorhandene Prozessmodelle können weiterhin in spezialisierten Werkzeugen gepflegt werden.

## Lösungsoptionen

Vor der Use-Case-Erfassung können unterschiedliche Lösungsarten verglichen werden:

- organisatorische Änderung
- regelbasierte Automatisierung
- Standardsoftware
- individuelle Software
- Analytics oder Machine Learning
- generative KI
- Assistenzsystem
- keine technische Lösung

Maximal eine Option kann je Prozessanalyse als bevorzugt markiert werden. Nur diese Option kann den vorhandenen Intake vorbefüllen. Die anschließende Bewertung und Governance bleiben vollständig verbindlich.

## Delivery-Handover

Ein Delivery Package kann nur aus einer final positiven Freigabe entstehen. Es konsolidiert Informationen aus Discovery, Prozessanalyse, Lösungsoption, Use Case, Bewertung und Freigabe.

Enthalten sind insbesondere:

- Problem- und Geschäftskontext
- Ziel, Nutzer und Nutzungsszenarien
- In-Scope und Out-of-Scope
- Lösungs-, System-, Daten- und Integrationskontext
- funktionale und nichtfunktionale Anforderungen
- Security-, Datenschutz- und Rechtsanforderungen
- menschliche Aufsicht, Logging, Betrieb und Support
- MVP-Scope
- Akzeptanzkriterien und Testfälle
- Erfolgsmessung
- Risiken, Annahmen und Abhängigkeiten
- Architekturentscheidungen
- initiales Backlog
- Link zum externen Delivery-System

Packages sind versioniert. Der Status verläuft über:

```text
Entwurf → Bereit zur Übergabe → Übergeben
```

Übergebene Versionen sind unveränderlich. Änderungen werden in einer neuen Version dokumentiert. Der Inhalt kann als Markdown exportiert und in Jira, Azure DevOps, GitHub, Confluence oder vergleichbare Systeme übernommen werden.

## Bewusste Systemgrenze

KI-Radar verwaltet keine:

- Sprints oder Arbeitspakete während der Umsetzung
- Ressourcen oder Kapazitäten
- Zeiterfassung
- Delivery-Fortschrittsberichte
- frei konfigurierbaren Workflows
- vollständigen Enterprise-Architecture-Katalog

Es sorgt dafür, dass ein fachlich begründetes und freigegebenes Vorhaben mit einem belastbaren Scope an Delivery übergeben wird. Die operative Umsetzung bleibt im spezialisierten Delivery-System.

## Umgesetzte Inkremente

1. Value Streams und optionale Herkunft eines Use Cases
2. Prozessanalyse und explizite Lösungsoptionen
3. Versioniertes Delivery Package und exportierbarer Handover

Alle drei Inkremente sind unabhängig nutzbar und erweitern den bestehenden Governance-Prozess, ohne ihn zur Pflicht für direkte Einzelvorhaben zu machen.
